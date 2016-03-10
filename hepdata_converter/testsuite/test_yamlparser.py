# -*- encoding: utf-8 -*-
import hepdata_converter
from hepdata_converter.testsuite import insert_path, insert_data_as_str
from hepdata_converter.testsuite.test_writer import WriterTestSuite

__author__ = 'Michał Szostak'


class YAMLWriterTestSuite(WriterTestSuite):
    @insert_path('yaml_qual')
    @insert_data_as_str('csv/table_5_noqual.csv')
    def test_no_qal_parse(self, yaml_path, table_5_noqual):
        data = hepdata_converter.convert(yaml_path, options={'input_format': 'yaml',
                                                             'output_format': 'csv',
                                                             'single_file': True})

        self.assertEqual(data, table_5_noqual)
