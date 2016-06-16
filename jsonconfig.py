import json
import logging
import os
import copy

from jsonpath_rw import parse


class JsonConfig:
    def __init__(self):
        self.__json = {"projects": {}}
        self.__log = logging.getLogger("lims_import")

    def init(self):
        if os.path.exists("import.json"):
            self.__log.info("Import.json file detected.")
            with open("import.json") as file:
                self.__json = json.load(file)

    def add_project(self, project):
        self.__json['projects'][project['name']] = copy.deepcopy(project)
        self.__json['projects'][project['name']]['experiments'] = {}
        self.__write()

    def add_experiment(self, experiment):
        project = experiment['project']
        cpy = copy.deepcopy(experiment)
        del cpy['project']
        self.__json['projects'][project['name']]["experiments"][experiment['name']] = cpy
        self.__write()
        pass

    def add_analysis(self, analysis):
        cpy = copy.deepcopy(analysis)
        experiment = cpy['experiment']
        project = experiment['project']
        del cpy['experiment']
        self.__json["projects"][project['name']]["experiments"][experiment['name']]['analyses'][
            cpy['type']] = cpy
        self.__write()

    def add_sample(self, sample):
        cpy = copy.deepcopy(sample)
        experiment = cpy['experiment']
        project = experiment['project']
        del cpy['experiment']
        self.__json["projects"][project['name']]["experiments"][experiment['name']]['samples'][
            sample['identifier']] = cpy
        self.__write()

    def add_sample_analysis(self, sample_analysis):
        cpy = copy.deepcopy(sample_analysis)
        analysis = cpy['analysis']
        experiment = analysis['experiment']
        project = experiment['project']

        del cpy['sample']
        del cpy['analysis']

        self.__json["projects"][project['name']]["experiments"][experiment['name']]['analyses'][analysis['type']][
            "sample_analyses"][sample_analysis['sample']['identifier']] = cpy
        self.__write()

    def add_analysis_file(self, analysis_file):
        cpy = copy.deepcopy(analysis_file)
        analysis = cpy['analysis']
        experiment = analysis['experiment']
        project = experiment['project']

        del cpy['analysis']

        self.__json["projects"][project['name']]["experiments"][experiment['name']]['analyses'][analysis['type']][
            "analysis_files"][cpy['filename']] = cpy
        self.__write()

    def add_saved_parameters(self, category, analysis):
        analysis_c = copy.deepcopy(analysis)
        experiment = analysis_c['experiment']
        project = experiment['project']
        self.__json["projects"][project['name']]["experiments"][experiment['name']]['analyses'][analysis['type']][
            'saved_parameters'].append(category)
        self.__write()

    def exists(self, path):
        expr = parse(path)
        matches = expr.find(self.__json)
        return len(matches) > 0

    def __contains(self, path, value):
        pass

    def __get(self, path):
        if self.exists(path):
            expr = parse(path)
            matches = expr.find(self.__json)
            return copy.deepcopy(matches[0].value)
        else:
            return None

    def get_project(self, name):
        return self.__get("projects['{}']".format(name))

    def __write(self):
        with open("import.json", "w") as file:
            file.write(json.dumps(self.__json, indent=4))
