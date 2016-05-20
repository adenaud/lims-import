import requests
import settings

import xml.etree.ElementTree as Xml


class WebDav:
    __url = ""
    __username = ""
    __password = ""

    def __init__(self, username, password):
        self.__url = settings.OWNCLOUD_WEBDAV_URL
        self.__username = username
        self.__password = password

    def mkdir(self, directory):
        print("Making Directory : {}{}".format(self.__url, directory))
        response = requests.request('MKCOL', self.__url + directory, auth=(self.__username, self.__password))
        if response.status_code == 503 or response.status_code == 409:
            print("Error creating directory : " + self.__get_error(response))
        elif response.status_code == 405:
            print("Directory already exists, nothing to do.")
        else:
            print("Done")

    def upload(self, source, destination):
        print("Uploading {} ...".format(source))

        with open(source, 'rb') as f:
            response = requests.put(self.__url + destination, data=f, auth=(self.__username, self.__password))
            if response.status_code == 201:
                print("Done")

            elif response.status_code == 204:
                print("The file exists, aborting.")

            else:
                print(response.status_code)
                print("Error uploading file")

    def __get_error(self, response):
        error = Xml.fromstring(response.text)
        return error.find("{http://sabredav.org/ns}message").text
