import logging
import ntpath
import os

from event import EventHook
from webdav import WebDav
from mqparser import MaxQuantParser
from importapi import ImportAPI


class AnalysisType:

    LCMSMS = "lcmsms"
    MAXQUANT = "maxquant"
    GENERIC = "generic"


class Importer:
    def __init__(self, username, password):
        self.__username = username
        self.__password = password
        self.__dav = WebDav(username, password)
        self.__api = ImportAPI(username, password)
        self.__log = logging.getLogger("lims_import")

        self.on_update = EventHook()

    def start(self, path):
        self.__api.start(path)
        self.__browse(path)

    def __browse(self, path, project=None):

        if os.path.exists(path + os.sep + "README.txt"):
            self.__log.info("1. Creating project {} ...".format(ntpath.basename(path)))
            project = self.__api.create_project(ntpath.basename(path), path, project)
            self.on_update.fire()
        else:
            self.__dav.mkdir(path)

        for file in os.listdir(path):
            if project is not None and MaxQuantParser.is_maxquant_file(path + os.sep + file):
                self.__log.info("MaxQuant file detected")
                experiment = self.__api.create_experiment(project['name'], project)
                self.__import_maxquant(experiment, path, file)

            elif "combined".__eq__(file):
                self.__browse(path + os.sep + file + os.sep + "txt", project)
                self.__dav.mkdir(path + os.sep + file)

            elif not file.startswith("."):
                if os.path.isdir(path + os.sep + file):
                    self.__browse(path + os.sep + file, project)
                else:
                    self.__dav.upload(path + os.sep + file, path + os.sep + file)
                    self.on_update.fire()

        self.__api.finish()

    def __import_maxquant(self, experiment, path, maxquant_file):

        self.__log.info("2. Importing LC-MS/MS data ...")
        lcms = self.__api.create_analysis("LC-MSMS", AnalysisType.LCMSMS, experiment)

        parser = MaxQuantParser(path + os.sep + maxquant_file)
        parser.parse()

        self.__log.info("3. Importing {} raw file(s) ...".format(len(parser.analysis_samples)))
        for analysis_sample in parser.analysis_samples:
            self.__api.create_analysis_sample(analysis_sample, lcms)

        self.__log.info("4. Importing MaxQuant data ...")
        mqan = self.__api.create_analysis("MaxQuant", AnalysisType.MAXQUANT, experiment, lcms)

        self.__log.info("5. Importing {} fasta file(s) ...".format(len(parser.fasta_files)))
        for fasta in parser.fasta_files:
            self.__api.import_fasta(fasta, mqan)

        self.__log.info("6. Importing MaxQuant parameters ...")
        self.__api.import_parameters(parser.params, "params", mqan)
        self.__api.import_parameters(parser.enzymes, "enzymes", mqan)
        self.__api.import_parameters(parser.fixed_modifications, "fixedModifications", mqan)
        self.__api.import_parameters(parser.variable_modifications, "variableModifications", mqan)
        self.__api.import_parameters(parser.raw_files, "raw", mqan)
        self.__api.import_parameters(parser.fasta_files, "fasta", mqan)

        self.__log.info("7. Uploading MaxQuant file ({}) ...".format(maxquant_file))
        self.__api.import_maxquant_file(path + os.sep + maxquant_file, mqan)

        self.__log.info("8. Setting output folder ...")
        self.__api.import_output_folder(path + os.sep + "combined", mqan)
