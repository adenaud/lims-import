import logging

import click
import os
import progressbar

from importer import Importer
from rest import RestClient
from webdav import WebDav


@click.command()
@click.argument("path", nargs=-1)
@click.option("--username", prompt=True)
@click.option('--password', prompt=True, hide_input=True)
def start(path, username, password):

    rest = RestClient(username)
    webdav = WebDav(username, password)

    login_attempts = 0

    if not rest.login(username, password):
        login_attempts += 1
        print("Invalid username or password." + username)
        if login_attempts < 5:
            start()
        else:
            exec(1)

    log = logging.getLogger("lims_import")
    log.setLevel(logging.DEBUG)

    sh = logging.StreamHandler()
    sh.setLevel(logging.DEBUG)

    fh = logging.FileHandler("lims-import.log")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d] \t %(message)s"))

    log.addHandler(sh)
    log.addHandler(fh)

    if not webdav.is_available():
        log.error("Unable to connect to Owncloud.")
        exit(1)

    for project in path:
        if not os.path.exists(project):
            log.error("{} not found.".format(project))
            exit(1)

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
