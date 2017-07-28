import yaml
# We try to load using the CSafeLoader for speed improvements.
try:
    from yaml import CSafeLoader as Loader
except ImportError: #pragma: no cover
    from yaml import SafeLoader as Loader #pragma: no cover
from hepdata_validator.submission_file_validator import SubmissionFileValidator
from hepdata_validator.data_file_validator import DataFileValidator
from hepdata_converter.parsers import Parser, ParsedData, Table
from multiprocessing import Pool
import os

class YAML(Parser):
    help = 'Parses New HEPData YAML format. Input parameter should be path to ' \
           'the directory where submission.yaml file ' \
           'is present (or direct filepath to the submission.yaml file)'

    pool = Pool()

    def __init__(self, *args, **kwargs):
        super(YAML, self).__init__(*args, **kwargs)

    def _pretty_print_errors(self, message_dict):
        return ' '.join(
                ['%s: %s' % (key, ' | '.join([e.message for e in val])) for
                 key, val in message_dict.items()])

    def parse(self, data_in, *args, **kwargs):
        """
        :param data_in: path to submission.yaml
        :param args:
        :param kwargs:
        :raise ValueError:
        """
        if not os.path.exists(data_in):
            raise ValueError("File / Directory does not exist: %s" % data_in)

        if os.path.isdir(data_in):
            submission_filepath = os.path.join(data_in, 'submission.yaml')
            if not os.path.exists(submission_filepath):
                submission_filepath = os.path.join(data_in, 'submission.yml')
                if not os.path.exists(submission_filepath):
                    raise ValueError("No submission file in %s" % data_in)
            data_in = submission_filepath

        # first validate submission file:
        with open(data_in, 'r') as submission_file:
            submission_data = list(yaml.load_all(submission_file, Loader=Loader))

            if len(submission_data) == 0:
                raise RuntimeError("Submission file (%s) is empty" % data_in)

            submission_file_validator = SubmissionFileValidator()
            if not submission_file_validator.validate(file_path=data_in,
                                                      data=submission_data):
                raise RuntimeError(
                    "Submission file (%s) did not pass validation: %s" %
                    (data_in, self._pretty_print_errors(
                        submission_file_validator.get_messages())))

        metadata = {}
        tables = []

        # validator for table data
        data_file_validator = DataFileValidator()

        for i in range(0, len(submission_data)):
            if not submission_data[i]: # empty YAML document
                continue
            if 'data_file' not in submission_data[i]:
                metadata = submission_data[i] # information about whole submission
                continue
            table_filepath = os.path.join(os.path.dirname(data_in),
                                          submission_data[i]['data_file'])
            with open(table_filepath, 'r') as table_file:
                if not os.path.exists(table_filepath):
                    raise ValueError(
                        "table file: %s does not exist" % table.data_file)

                table_data = yaml.load(table_file, Loader=Loader)

                if not data_file_validator.validate(data=table_data,
                                                    file_path=table_filepath):
                    raise RuntimeError(
                        "Data file (%s) did not pass validation: %s" %
                        (table_filepath, self._pretty_print_errors(
                            data_file_validator.get_messages())))

                table = Table(index=i, metadata=submission_data[i],
                              data=table_data)
                tables.append(table)

        return ParsedData(metadata, tables)
