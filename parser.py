import xml.etree.cElementTree as Xml
import ntpath
import redis
import os.path


class MaxQuantParser:

    raw_files = []
    fasta_files = []
    analysis_samples = []
    __filename = ""

    enzymes = []
    variable_modifications = []
    fixed_modifications = []
    params = {}

    def __init__(self, filename):
        self.__filename = filename
        self.redis = redis.StrictRedis(host="172.17.0.2", port=6379, db=0)

    def is_valid(self):
        with open(self.__filename) as file:
            try:
                Xml.fromstring(file.read())
                return True
            except Xml.ParseError:
                return False

    def files_exists(self):
        with open(self.__filename) as file:
            content = file.read()
            root = Xml.fromstring(content)
            raw_files = root.find("filePaths")
            file_exist = True
            for raw_file in raw_files:
                if not os.path.exists(raw_file.text):
                    print("{} not found.".format(raw_file.text))
                    file_exist = False

            fasta_files = root.find("fastaFiles")
            for fasta_file in fasta_files:
                if not os.path.exists(fasta_file.text):
                    print("{} not found.".format(fasta_file.text))
                    file_exist = False
        return file_exist

    def parse(self):
        with open(self.__filename) as file:
            content = file.read()
            root = Xml.fromstring(content)
            self.__browse(root)

    def __browse(self, parent):
        for element in parent:

            if "filePaths".__eq__(element.tag):
                print("Upload files and and sample analysis")
                i = 0
                for file in element:
                    self.raw_files.append(file.text)
                    analysis = {"sample_identifier": parent.find("experiments")[i].text,
                                "filename": ntpath.basename(file.text),
                                "full_path": file.text,
                                "fractions": int(parent.find("fractions")[i].text),
                                "paramGroupIndices": int(parent.find("paramGroupIndices")[i].text)}
                    self.analysis_samples.append(analysis)
                    i += 1
            elif ("experiments".__eq__(element.tag) or "fractions".__eq__(element.tag) or "paramGroupIndices".__eq__(
                    element.tag)):
                pass
            elif "fastaFiles".__eq__(element.tag):
                for fasta in element:
                    self.fasta_files.append(fasta.text)
            elif "enzymes".__eq__(element.tag):
                for enzyme in element:
                    self.enzymes.append(enzyme.text)
            elif "variableModifications".__eq__(element.tag):
                for variableModification in element:
                    self.variable_modifications.append(variableModification.text)
            elif "fixedModifications".__eq__(element.tag):
                for fixedModification in element:
                    self.fixed_modifications.append(fixedModification.text)
            elif len(element) > 0:
                self.__browse(element)

            else:
                self.params[element.tag] = element.text
