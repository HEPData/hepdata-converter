import yaml
from hepdata_converter.writers import Writer
import os


class YAML(Writer):
    def __init__(self, *args, **kwargs):
        super(YAML, self).__init__(single_file_output=False, *args, **kwargs)

    def write(self, data_in, data_out, *args, **kwargs):
        """

        :param data_in:
        :type data_in: hepconverter.parsers.ParsedData
        :param data_out: path of the directory to which yaml files will be written
        :type data_out: str
        :param args:
        :param kwargs:
        """


        tables = data_in.tables
        data = data_in.data

        with open(os.path.join(data_out, 'submission.yaml'), 'w') as submission_file:

            yaml.dump_all(data + [table.metadata for table in tables], submission_file)

        for table in tables:
            with open(os.path.join(data_out, table.data_file), 'w') as table_file:
                yaml.dump(table.data, table_file)
