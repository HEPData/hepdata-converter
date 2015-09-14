# -*- encoding: utf-8 -*-
import os
import StringIO
import rootpy
import hepdata_converter
from hepdata_converter.testsuite import insert_data_as_file, insert_path, insert_data_as_str
from hepdata_converter.testsuite.test_writer import WriterTestSuite
from rootpy.io import root_open

__author__ = 'Michał Szostak'


class YODAWriterTestSuite(WriterTestSuite):
    
    @insert_path('yaml_full')
    @insert_data_as_file('yoda/full.yoda')
    def test_simple_parse(self, yaml_simple_path, yoda_template):
        output_file_path = os.path.join(self.current_tmp, 'datafile.yoda')
        hepdata_converter.convert(yaml_simple_path, output_file_path,
                                  options={'output_format': 'yoda'})

        self.assertNotEqual(os.stat(output_file_path).st_size, 0, 'output yoda file is empty')
        with open(output_file_path, 'r') as f:
            self.assertMultiLineAlmostEqual(f, yoda_template)