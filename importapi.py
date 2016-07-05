import logging
import ntpath
import os

from jsonconfig import JsonConfig
from rest import RestClient
from webdav import WebDav


class ImportAPI:
    def __init__(self, username, password):
        self.__rest = RestClient(username)
        self.__dav = WebDav(username, password)
        self.__json = JsonConfig()
        self.__log = logging.getLogger("lims_import")
        self.__root = ""
        self.__path = ""
        self.__failure = False

    def start(self, path):
        self.__path = path
        self.__root = path[path.__len__() - ntpath.basename(path).__len__():]

        self.__json.init()

    def create_project(self, name, path, parent):

        project = self.__json.get_project(name)

        if project is None:
            description = ""
            if os.path.exists(path + os.sep + "README.txt"):
                description = open(path + os.sep + "README.txt", "r").read()
            response = self.__rest.create_project2(name, parent, description)

            if not "OK".__eq__(response['status']):
                self.__log.error("Unable to create project or experiment ({})".format(response['status']))
                exit(1)
            if parent is None:
                folder = name
            else:
                folder = self.__root + os.sep + path[self.__path.__len__() + 1:]

            self.__dav.mkdir(folder)
            project = {"id": response['project_id'], "name": name, "folder": folder, "experiments": {}}
            self.__json.add_project(project)

        return project

    def create_experiment(self, name, project):

        if project['experiments'].__contains__(name):
            experiment = project['experiments'][name]
            experiment['project'] = project
        else:
            response = self.__rest.create_experiment(name, project['id'])

            if not "OK".__eq__(response['status']):
                self.__log.error("Unable to create experiment : {}".format(response['status']))
                exit(1)

            folder = project['folder'] + os.sep + name
            self.__dav.mkdir(folder)

            experiment = {"id": response['experiment_id'], "name": name, "folder": folder, "project": project,
                          "analyses": {}, "samples": {}}
            self.__json.add_experiment(experiment)
        return experiment

    def create_analysis(self, name, analysis_type, experiment, predecessor=None):

        if experiment['analyses'].__contains__(analysis_type):
            analysis = experiment['analyses'][analysis_type]
            analysis['experiment'] = experiment
        else:

            result = self.__rest.create_analysis(name, analysis_type, experiment['id'], predecessor)

            if not "OK".__eq__(result['status']):
                self.__log.error("Unable to create analysis ({})".format(result['status']))
                exit(1)
            uuid = result["analysis_uuid"]
            folder = "{}/{}".format(experiment["folder"], analysis_type)

            self.__dav.mkdir(folder)

            analysis = {"uuid": uuid, "folder": folder, "type": analysis_type, "experiment": experiment,
                        "sample_analyses": {}, "analysis_files": {}, "saved_parameters": []}
            self.__json.add_analysis(analysis)
        return analysis

    def create_analysis_sample(self, analysis_sample, lcms_analysis):

        if not lcms_analysis['sample_analyses'].__contains__(analysis_sample['sample_identifier']):

            experiment = lcms_analysis['experiment']
            destination = "{}/{}".format(lcms_analysis['folder'], analysis_sample["filename"])

            if self.__dav.upload(analysis_sample['full_path'], destination):
                sample = self.create_sample(analysis_sample["sample_identifier"], experiment)
                if sample['id'] > 0:

                    if not lcms_analysis['sample_analyses'].__contains__(analysis_sample['sample_identifier']):
                        result1 = self.__rest.create_analysis_sample(sample['id'], lcms_analysis['uuid'],
                                                                     destination)
                        if "OK".__eq__(result1['status']):
                            analysis_s = {'id': result1['analysis_sample_id'], "sample": sample,
                                          "analysis": lcms_analysis, "filename": analysis_sample['filename']}
                            self.__json.add_sample_analysis(analysis_s)
                        else:
                            self.__failure = True
                            self.__log.error("Unable to create analysis sample ({})".format(result1['status']))

    def create_sample(self, identifier, experiment):

        if experiment['samples'].__contains__(identifier):
            return experiment['samples']['identifier']
        else:
            result = self.__rest.create_sample(experiment['id'], identifier)

            if "OK".__eq__(result['status']):
                sample = {"id": result['sample_id'], "identifier": identifier, "experiment": experiment}
                self.__json.add_sample(sample)
                return sample
            else:
                self.__failure = True
                self.__log.error("Unable to create sample ({})".format(result['status']))
                return {"id": -1}

    def import_fasta(self, fasta, analysis):

        destination = "{}/{}".format(analysis['folder'], ntpath.basename(fasta))

        if self.__dav.upload(fasta, destination):
            result = self.__rest.create_analysis_file(analysis['uuid'], destination, "attachment", "attachment0")
            if "OK".__eq__(result['status']):
                file = {"id": result['file_id'], "filename": ntpath.basename(fasta), "analysis": analysis}
                self.__json.add_analysis_file(file)
            else:
                self.__log.error("Unable to create analysis file \"{}\" ({})".format(ntpath.basename(fasta),
                                                                                     result['status']))

    def import_parameters(self, params, category, analysis):

        if not analysis['saved_parameters'].__contains__(category):

            params_failure = False

            if "params".__eq__(category):

                for key in params:
                    if params[key] is not None:
                        result = self.__rest.add_extra_param(analysis['uuid'], category, key, params[key])
                        if not "OK".__eq__(result['status']):
                            params_failure = True
                            self.__log.error(
                                "Unable to save param : params \"{}\" ({})".format(key, result['status']))
                if not params_failure:
                    self.__json.add_saved_parameters(category, analysis)
            else:
                for value in params:
                    result = self.__rest.add_extra_param(analysis['uuid'], category, "", value)
                    if not "OK".__eq__(result['status']):
                        params_failure = True
                        self.__log.error(
                            "Unable to save param : {} \"{}\" ({})".format(category, value, result['status']))
                if not params_failure:
                    self.__json.add_saved_parameters(category, analysis)

    def import_maxquant_file(self, maxquant_file, analysis):
        destination = "{}/{}".format(analysis['folder'], ntpath.basename(maxquant_file))
        if self.__dav.upload(maxquant_file, destination):
            result = self.__rest.create_analysis_file(analysis['uuid'], destination, "attachment", "attachment1")
            if not "OK".__eq__(result['status']):
                self.__failure = True
                self.__log.error("Unable to create analysis file \"{}\" ({})".format(ntpath.basename(maxquant_file),
                                                                                     result['status']))

    def import_output_folder(self, output_folder, analysis):
        result = self.__rest.create_analysis_file(analysis['uuid'], output_folder, "output", "output", False)
        if not "OK".__eq__(result['status']):
            self.__failure = True
            self.__log.error("Unable to set output folder ({})".format(result['status']))

    def finish(self):
        if self.__failure:
            self.__json.write()
        else:
            if os.path.exists("import.json"):
                os.remove("import.json")
