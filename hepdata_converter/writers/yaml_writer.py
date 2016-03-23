import yaml
from hepdata_converter.common import Option, OptionInitMixin
from hepdata_converter.writers import Writer
import os

def str_presenter(dumper, data):
    if '\n' in data in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

class YAML(Writer):
    help = 'Writes YAML output. Output should be defined as filepath to the directory where submission.yaml and associated ' \
           'table files will be written'

    @classmethod
    def options(cls):
        options = Writer.options()
        options['single_file'] = Option('single-file', type=bool, default=False, variable_mapping='single_file',
                                        required=False, help="If set output will be written to single yaml file, instead "
                                                             "of multiple files (separating data and metadata of the tables)")
        return options

    def __init__(self, *args, **kwargs):
        super(YAML, self).__init__(single_file_output=True, *args, **kwargs)
        yaml.add_representer(str, str_presenter)

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

        if not isinstance(data_out, (str, unicode)) and not self.single_file:
            raise ValueError("output is not string, and single_file flag is not specified")

        if not self.single_file:
            self.create_dir(data_out)
            with open(os.path.join(data_out, 'submission.yaml'), 'w') as submission_file:
                yaml.dump_all([data] + [table.metadata for table in tables], submission_file)
                for table in tables:
                    with open(os.path.join(data_out, table.data_file), 'w') as table_file:
                        yaml.dump(table.data, table_file)
        else:
            if isinstance(data_out, (str, unicode)):
                with open(data_out, 'w') as submission_file:
                    yaml.dump_all([data] + [table.all_data for table in tables], submission_file)
            else: # expect filelike object
                yaml.dump_all([data] + [table.all_data for table in tables], data_out)