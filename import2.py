import click

from mqparser import MaxQuantParser
from rest import RestClient
from webdav import WebDav


@click.command()
@click.argument("maxquant_file")
@click.argument("username")
@click.argument("project_name")
@click.argument("experiment_name")
@click.option('--password', prompt=True, hide_input=True)
def start(maxquant_file, username, password, project_name, experiment_name):
    parser = MaxQuantParser(maxquant_file)
    rest = RestClient(username)
    webdav = WebDav(username, password)

    failure = False

if __name__ == '__main__':
    start()
