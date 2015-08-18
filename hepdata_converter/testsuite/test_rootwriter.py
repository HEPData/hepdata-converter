import os
import hepdata_converter
from hepdata_converter.testsuite import insert_data_as_file, insert_path
from hepdata_converter.testsuite.test_writer import WriterTestSuite

__author__ = 'mszostak'

import unittest
from hepdata_converter.writers.root_writer import ROOT


class ROOTWriterTestSuite(WriterTestSuite):
    
    @insert_path('yaml_simple')
    def test_simple_parse(self, yaml_simple_path):
        hepdata_converter.convert(yaml_simple_path, options={'output_format': 'root',
                                                             'table': 'Table 1'})
