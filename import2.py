import click
import ntpath
import os

from rest import RestClient
from webdav import WebDav


class Importer:

    def __init__(self, path,  username, password):
        self.username = username
        self.password = password
        self.path = path
        self.rest = RestClient(username)
        self.dav = WebDav(username, password)
        self.root = path[path.__len__() - ntpath.basename(path).__len__():]

    def __browse(self, parent, path):
        name = ntpath.basename(path)

        description = ""
        if os.path.exists(path + os.sep + "README.txt"):
            description = open(path + os.sep + "README.txt", "r").read()

        print("Creating project " + name)

        response = self.rest.create_project2(name, parent, description)
        project_id = response['project_id']

        if parent is None:
            folder = name
        else:
            folder = self.root + os.sep + path[self.path.__len__()+1:]

        self.dav.mkdir(folder)

        for file in os.listdir(path):
            if not file.startswith("."):
                if os.path.isdir(path + os.sep + file):
                    self.__browse(project_id, path + os.sep + file)
                else:
                    self.dav.upload(path + os.sep + file, folder + os.sep + file)

    def start(self):
        self.__browse(None, self.path)


@click.command()
@click.argument("path")
@click.option("--username", prompt=True)
@click.option('--password', prompt=True, hide_input=True)
def start(path, username, password):

    login_attempts = 0
    rest = RestClient(username)
    if not rest.login(username, password):
        login_attempts += 1
        print("Invalid username or password.")
        if login_attempts < 5:
            start()
        else:
            exec(1)

    importer = Importer(path, username, password)
    importer.start()


if __name__ == '__main__':
    start()
