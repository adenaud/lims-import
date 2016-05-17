import os.path
import settings
import ntpath
import click

from parser import MaxQuantParser
from webdav import WebDav
from rest import RestClient


@click.command()
@click.argument("maxquant_file")
@click.argument("username")
@click.argument("project_name")
@click.argument("experiment_name")
@click.option('--password', prompt=True, hide_input=True)
def start(maxquant_file, username, password, project_name, experiment_name):

    parser = MaxQuantParser(maxquant_file)
    rest = RestClient(username)
    webdav = WebDav(settings.OWNCLOUD_WEBDAV_URL, username, password)

    if not rest.login(username, password):
        print("Invalid username or password.")
        start()

    if not os.path.isfile(maxquant_file):
        print("{} not found.".format(maxquant_file))
        exit(1)

    if not parser.is_valid():
        print("The mqpar.xml file is not valid")
        exit(1)

    if not parser.files_exists():
        print("One or more of file(s) described in the mqpar.xml is not available")
        exit(1)

    exit(0)

    print("Creating project and experiment ...")
    result = rest.create_project(project_name, experiment_name)
    project_folder = result["project_folder"]
    experiment_folder = result["experiment_folder"]

    print("Creating folders on Owncloud ...")
    webdav.mkdir(project_folder)
    webdav.mkdir("{}/{}".format(project_folder, experiment_folder))

    print("Importing LC-MS/MS data ...")
    result = rest.create_analysis("LC-MS/MS", "lc-ms")
    lcms_uuid = result["analysis_uuid"]
    lcms_folder = result["analysis_folder"]
    webdav.mkdir("{}/{}/{}".format(project_folder, experiment_folder, lcms_folder))

    print("Importing MaxQuant data ...")
    result = rest.create_analysis("MaxQuant", "mq-an")
    mqan_uuid = result["analysis_uuid"]
    mqan_folder = result["analysis_folder"]
    webdav.mkdir("{}/{}/{}".format(project_folder, experiment_folder, mqan_folder))

    parser.parse()

    samples_count = len(parser.analysis_samples)
    fasta_count = len(parser.fasta_files)

    print("{} Raw file(s) will be uploaded.".format(samples_count))
    for analysis in parser.analysis_samples:
        result = rest.create_sample(analysis["sample_identifier"])
        sample_id = result["sample_id"]
        destination = "{}/{}/{}/{}".format(project_folder, experiment_folder, lcms_folder, analysis["filename"])
        webdav.upload(analysis['full_path'], destination)
        rest.create_analysis_sample(sample_id, lcms_uuid, analysis["filename"])

    print("{} Fasta file(s) will be uploaded.".format(fasta_count))
    for fasta in parser.fasta_files:
        destination = "{}/{}/{}/{}".format(project_folder, experiment_folder, mqan_folder, ntpath.basename(fasta))
        webdav.upload(fasta, destination)
        rest.create_analysis_file(lcms_uuid, fasta, "input", "fasta")


if __name__ == '__main__':
    start()
