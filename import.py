import os.path
import ntpath
import click
import json
from mqparser import MaxQuantParser
from webdav import WebDav
from rest import RestClient


def generate_failure_json(import_status):
    with open('import.json', 'w') as outfile:
        json.dump(import_status, outfile)


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

    if not rest.login(username, password):
        print("Invalid username or password.")
        start()

    if not webdav.is_available():
        print("Unable to connect to Owncloud.")
        exit(1)

    if not os.path.isfile(maxquant_file):
        print("{} not found.".format(maxquant_file))
        exit(1)

    if not parser.is_valid():
        print("The mqpar.xml file is not valid")
        exit(1)

    if not parser.files_exists():
        print("One or more of file(s) described in the mqpar.xml is not available")
        exit(1)

    import_status = {}
    if os.path.exists("import.json"):
        print("Import.json file detected.")
        with open("import.json") as file:
            import_status = json.load(file)

    if import_status.__contains__("project"):
        project_folder = import_status["project"]["folder"]
        experiment_folder = import_status["experiment"]["folder"]
        experiment_id = import_status["experiment"]["id"]
    else:
        print("Creating project and experiment ...")
        result = rest.create_project(project_name, experiment_name)
        if not "OK".__eq__(result['status']):
            print("Unable to create project or experiment ({})".format(result['status']))
            exit(1)
        project_folder = result["project_folder"]
        experiment_folder = result["experiment_folder"]
        experiment_id = result["experiment_id"]

        import_status["project"] = {}
        import_status["experiment"] = {}
        import_status["project"]["folder"] = project_folder
        import_status["experiment"]["folder"] = experiment_folder
        import_status["experiment"]["id"] = experiment_id
        generate_failure_json(import_status)

    print("Creating folders on Owncloud ...")
    webdav.mkdir(project_folder)
    webdav.mkdir("{}/{}".format(project_folder, experiment_folder))

    if import_status.__contains__("lc-ms"):
        lcms_uuid = import_status["lc-ms"]["uuid"]
        lcms_folder = import_status["lc-ms"]["folder"]
    else:
        print("Creating LC-MS/MS analysis ...")
        result = rest.create_analysis("LC-MS/MS", "lc-ms", experiment_id)
        if not "OK".__eq__(result['status']):
            print("Unable to create analysis ({})".format(result['status']))
            generate_failure_json(import_status)
            exit(1)
        lcms_uuid = result["analysis_uuid"]
        lcms_folder = result["analysis_folder"]

        import_status["lc-ms"] = {}
        import_status["lc-ms"]["uuid"] = lcms_uuid
        import_status["lc-ms"]["folder"] = lcms_folder

    webdav.mkdir("{}/{}/{}".format(project_folder, experiment_folder, lcms_folder))

    parser.parse()

    samples_count = len(parser.analysis_samples)

    print("{} Raw file(s) will be uploaded.".format(samples_count))
    for analysis_sample in parser.analysis_samples:
        if not import_status.__contains__("uploaded_files") or not import_status["uploaded_files"].__contains__(
                analysis_sample["filename"]):
            destination = "{}/{}/{}/{}".format(project_folder, experiment_folder, lcms_folder,
                                               analysis_sample["filename"])
            if webdav.upload(analysis_sample['full_path'], destination):
                result = rest.create_sample(experiment_id, analysis_sample["sample_identifier"])
                if "OK".__eq__(result['status']):
                    sample_id = result["sample_id"]
                    result = rest.create_analysis_sample(sample_id, lcms_uuid, analysis_sample["filename"])
                    if not "OK".__eq__(result['status']):
                        failure = True
                        print("Unable to create analysis sample ({})".format(result['status']))
                    else:
                        import_status["uploaded_files"] = []
                        import_status["uploaded_files"].append(analysis_sample["filename"])
                else:
                    failure = True
                    print("Unable to create sample ({})".format(result['status']))

    if import_status.__contains__("mq-an"):
        mqan_uuid = import_status["mq-an"]["uuid"]
        mqan_folder = import_status["mq-an"]["folder"]
    else:

        print("Importing MaxQuant data ...")
        result = rest.create_analysis("MaxQuant", "mq-an", experiment_id)
        if not "OK".__eq__(result['status']):
            print("Unable to create analysis ({})".format(result['status']))
            generate_failure_json(import_status)
            exit(1)
        mqan_uuid = result["analysis_uuid"]
        mqan_folder = result["analysis_folder"]

        import_status["mq-an"] = {}
        import_status["mq-an"]["uuid"] = mqan_uuid
        import_status["mq-an"]["folder"] = mqan_folder

    webdav.mkdir("{}/{}/{}".format(project_folder, experiment_folder, mqan_folder))

    fasta_count = len(parser.fasta_files)
    print("{} Fasta file(s) will be uploaded.".format(fasta_count))
    for fasta in parser.fasta_files:

        if not import_status.__contains__("uploaded_files") or not import_status["uploaded_files"].__contains__(
                ntpath.basename(fasta)):
            destination = "{}/{}/{}/{}".format(project_folder, experiment_folder, mqan_folder, ntpath.basename(fasta))

            if webdav.upload(fasta, destination):
                result = rest.create_analysis_file(mqan_uuid, ntpath.basename(fasta), "input", "fasta")
                if not "OK".__eq__(result['status']):
                    generate_failure_json(import_status)
                    print("Unable to create analysis file \"{}\" ({})".format(ntpath.basename(fasta), result['status']))
                else:
                    import_status["uploaded_files"].append(ntpath.basename(fasta))

    if not import_status.__contains__("params_saved"):

        print("Saving parameters ...")

        for key in parser.params:
            if parser.params[key] is not None:
                result = rest.add_extra_param(mqan_uuid, "params", key, parser.params[key])
                if not "OK".__eq__(result['status']):
                    print("Unable to save extra param : params \"{}\" ({})".format(key, result['status']))

        for value in parser.enzymes:
            result = rest.add_extra_param(mqan_uuid, "enzymes", "", value)
            if not "OK".__eq__(result['status']):
                print("Unable to save extra param : enzymes\"{}\" ({})".format(value, result['status']))

        for value in parser.fixed_modifications:
            result = rest.add_extra_param(mqan_uuid, "fixedModifications", "", value)
            if not "OK".__eq__(result['status']):
                print("Unable to save extra param : fixedModifications\"{}\" ({})".format(value, result['status']))

        for value in parser.variable_modifications:
            result = rest.add_extra_param(mqan_uuid, "variableModifications", "", value)
            if not "OK".__eq__(result['status']):
                print("Unable to save extra param : variableModifications\"{}\" ({})".format(value, result['status']))

        import_status["params_saved"] = True

    if not import_status["uploaded_files"].__contains__(ntpath.basename(maxquant_file)):
        print("Uploading {} ...".format(ntpath.basename(maxquant_file)))
        destination = "{}/{}/{}/{}".format(project_folder, experiment_folder, mqan_folder,
                                           ntpath.basename(maxquant_file))
        if webdav.upload(maxquant_file, destination):
            result = rest.create_analysis_file(mqan_uuid, ntpath.basename(maxquant_file), "input", "mqpart")
            if not "OK".__eq__(result['status']):
                failure = True
                print("Unable to create analysis file \"{}\" ({})".format(ntpath.basename(maxquant_file),
                                                                          result['status']))
            else:
                import_status["uploaded_files"].append(ntpath.basename(maxquant_file))

    if failure:
        generate_failure_json(import_status)


if __name__ == '__main__':
    start()
