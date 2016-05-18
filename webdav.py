import requests
import ntpath


class WebDav:
    __url = ""
    __username = ""
    __password = ""

    def __init__(self, url, username, password):
        self.__url = url
        self.__username = username
        self.__password = password

    def mkdir(self, directory):
        print("Making Directory : {}{}".format(self.__url, directory))
        response = requests.request('MKCOL', self.__url + directory, auth=(self.__username, self.__password))
        if response.status_code != 200 and response.status_code != 201:
            print("Error creating directory :")
            print(response.text)

    def upload(self, source, destination):
        print("Uploading {} ...".format(source))
        #files = {'rawfile': (ntpath.basename(source), open(source, 'rb'), 'application/octet-stream', {'Expires': '0'})}
        #response = requests.put(self.__url + destination, files=files, auth=(self.__username, self.__password))

        with open(source, 'rb') as f:
            response = requests.put(self.__url + destination, data=f, auth=(self.__username, self.__password))

        if response.status_code != 200 and response.status_code != 201:
            print("Error uploading file :")
            print(response.text)
        print("{} uploaded.".format(source))
