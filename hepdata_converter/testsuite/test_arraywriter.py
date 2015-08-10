import unittest
import os
import tempfile
import shutil
import time
from hepdata_converter import convert
from hepdata_converter.testsuite.test_writer import WriterTestSuite


class ArrayWriterTestSuite(WriterTestSuite):
    def test_select_table(self):
        csv_content = convert(self.submission_filepath, options={'input_format': 'yaml',
                                                                 'output_format': 'csv',
                                                                 'table': os.path.join(os.path.dirname(self.submission_filepath), 'data1.yaml')})

        csv_content = convert(self.submission_filepath, options={'input_format': 'yaml',
                                                                 'output_format': 'csv',
                                                                 'table': 'Table 1'})

        csv_content = convert(self.submission_filepath, options={'input_format': 'yaml',
                                                                 'output_format': 'csv',
                                                                 'table': 0})
