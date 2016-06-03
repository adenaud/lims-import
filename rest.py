import requests
import json
import settings


class RestClient:
    __username = ""

    def __init__(self, username):
        self.__username = username

    def create_project(self, project_name, experiment_name):
        r = requests.post(settings.API_URL + "create-project", data={"project_name": project_name,
                                                                     "experiment_name": experiment_name,
                                                                     "username": self.__username})
        response = json.loads(r.text)
        return response

    def create_project2(self, project_name, parent, description):
        if parent is None:
            r = requests.post(settings.API_URL + "create-project2",
                              data={"project_name": project_name, "description": description,
                                    "username": self.__username})
        else:
            r = requests.post(settings.API_URL + "create-project2",
                              data={"project_name": project_name, "parent": parent, "description": description,
                                    "username": self.__username})
        response = json.loads(r.text)
        return response

    def create_analysis(self, analysis_name, analysis_type, experiment_id, predecessor=None):
        data = {"analysis_name": analysis_name,
                "experiment_id": experiment_id,
                "analysis_type": analysis_type,
                "username": self.__username}
        if predecessor is not None:
            data["predecessor"] = predecessor
        r = requests.post(settings.API_URL + "create-analysis", data=data)
        response = json.loads(r.text)
        return response

    def create_sample(self, experiment_id, identifier):
        r = requests.post(settings.API_URL + "create-sample", data={"identifier": identifier,
                                                                    "experiment_id": experiment_id,
                                                                    "username": self.__username})
        response = json.loads(r.text)
        return response

    def create_analysis_sample(self, sample_id, analysis_uuid, filename):
        r = requests.post(settings.API_URL + "create-analysis-sample", data={"sample_id": sample_id,
                                                                             "analysis_uuid": analysis_uuid,
                                                                             "rawfile": filename})
        response = json.loads(r.text)
        return response

    def create_analysis_file(self, analysis_uuid, filename, io_type, field):
        r = requests.post(settings.API_URL + "create-analysis-file", data={"analysis_uuid": analysis_uuid,
                                                                           "file": filename,
                                                                           "type": io_type,
                                                                           "field": field})
        response = json.loads(r.text)
        return response

    def add_extra_param(self, analysis_uuid, field, key, value):
        r = requests.post(settings.API_URL + "add-extra-param", data={"analysis_uuid": analysis_uuid,
                                                                      "field": field,
                                                                      "key": key,
                                                                      "value": value})
        response = json.loads(r.text)
        return response

    def login(self, username, password):
        response = requests.post(settings.LOGIN_URL, data={"username": username, "password": password})
        if response.text == "LOGIN_OK":
            return True
        else:
            return False
