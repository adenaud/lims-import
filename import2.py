import click
import ntpath
import os
import time
import progressbar

from event import EventHook

from rest import RestClient
from webdav import WebDav


class Importer:

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.rest = RestClient(username)
        self.dav = WebDav(username, password)
        self.path = ""
        self.root = ""
        self.on_update = EventHook()

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
        self.on_update.fire()

        for file in os.listdir(path):
            if not file.startswith("."):
                if os.path.isdir(path + os.sep + file):
                    self.__browse(project_id, path + os.sep + file)
                else:
                    self.dav.upload(path + os.sep + file, folder + os.sep + file)
                    self.on_update.fire()

    def start(self, path):
        self.path = path
        self.root = path[path.__len__() - ntpath.basename(path).__len__():]
        self.__browse(None, self.path)


@click.command()
@click.argument("path", nargs=-1)
@click.option("--username", prompt=True)
@click.option('--password', prompt=True, hide_input=True)
def start(path, username, password):

    login_attempts = 0
    rest = RestClient(username)
    if not rest.login(username, password):
        login_attempts += 1
        print("Invalid username or password." + username)
        if login_attempts < 5:
            start()
        else:
            exec(1)

    total = 0

    for project in path:
        total += 1
        for root, dirs, files in os.walk(project):
            total += len(files)
            total += len(dirs)

    bar = progressbar.ProgressBar(max_value=total, redirect_stdout=True)

    def update_progress():
        bar.update(bar.value + 1)

    importer = Importer(username, password)
    importer.on_update += update_progress

    for project in path:
        importer.start(project)

if __name__ == '__main__':
    start()
