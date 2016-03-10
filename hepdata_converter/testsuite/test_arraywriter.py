import os
from hepdata_converter import convert
from hepdata_converter.testsuite import insert_path
from hepdata_converter.testsuite.test_writer import WriterTestSuite


class ArrayWriterTestSuite(WriterTestSuite):
    @insert_path('yaml_full')
    def test_select_table(self, submission_filepath):
        csv_content = convert(submission_filepath, options={'input_format': 'yaml',
                                                                 'output_format': 'csv',
                                                                 'table': os.path.join(submission_filepath, 'data1.yaml')})

        csv_content = convert(submission_filepath, options={'input_format': 'yaml',
                                                                 'output_format': 'csv',
                                                                 'table': 'Table 1'})

        csv_content = convert(submission_filepath, options={'input_format': 'yaml',
                                                                 'output_format': 'csv',
                                                                 'table': 0})
