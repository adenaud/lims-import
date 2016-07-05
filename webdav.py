import logging

import requests
import settings
import os

from requests.exceptions import ConnectionError


import xml.etree.ElementTree as Xml


class WebDav:
    __url = ""
    __username = ""
    __password = ""

    def __init__(self, username, password):
        self.__url = settings.OWNCLOUD_WEBDAV_URL
        self.__username = username
        self.__password = password
        self.__log = logging.getLogger("lims_import")

    def is_available(self):
        available = False
        try:
            response = requests.request("PROPFIND", self.__url, auth=(self.__username, self.__password))
            if response.status_code == 207:
                available = True
            else:
                self.__log.error(response.text)
        except ConnectionError:
            pass
        return available

    def mkdir(self, directory):
        self.__log.info("Making Directory : {}{}".format(self.__url, directory))

        response = requests.request('MKCOL', self.__url + directory, auth=(self.__username, self.__password))
        if response.status_code == 503 or response.status_code == 409:
            self.__log.error("Error creating directory : " + self.__get_error(response))
        elif response.status_code == 405:
            self.__log.warning("Directory already exists, nothing to do.")
        else:
            self.__log.info("Done")

    def upload(self, source, destination):
        success = False
        self.__log.info("Uploading {} ...".format(source))

        if os.path.getsize(source) > 0:
            if not self.__file_exists(destination):

                with open(source, 'rb') as f:
                    response = requests.put(self.__url + destination, data=f, auth=(self.__username, self.__password))
                    if response.status_code == 201:
                        self.__log.info("Done")
                        success = True

                    elif response.status_code == 204:
                        self.__log.warning("The file exists, skipping.")
                        success = True

                    elif self.__get_file_size(destination) != os.path.getsize(source):
                        self.__log.error("Error the size of the uploaded file don't correspond to the original")

                    else:
                        self.__log.error(response.status_code)
                        self.__log.error("Error uploading file")
            else:
                self.__log.warning("The file exists, skipping.")
                success = True
        else:
            self.__log.warning("The file is empty, skipping.")
            success = True
        return success

    def __file_exists(self, path):
        response = requests.request('PROPFIND', self.__url + path, auth=(self.__username, self.__password))
        if response.status_code == 207:
            return True
        else:
            return False

    def __get_file_size(self, path):
        response = requests.request("PROPFIND", self.__url + path, auth=(self.__username, self.__password))
        xml = Xml.fromstring(response.content)
        return int(xml.find(".//{DAV:}getcontentlength").text)

    def __get_error(self, response):
        error = Xml.fromstring(response.text)
        return error.find("{http://sabredav.org/ns}message").text
