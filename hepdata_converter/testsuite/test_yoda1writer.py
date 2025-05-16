# -*- encoding: utf-8 -*-
import os
import hepdata_converter
from hepdata_converter.testsuite import insert_data_as_file, insert_path, insert_paths
from hepdata_converter.testsuite.test_writer import WriterTestSuite

__author__ = 'Michał Szostak'


class YODA1WriterTestSuite(WriterTestSuite):
    @insert_path('yaml_full')
    @insert_data_as_file('yoda1/full.yoda')
    def test_simple_parse(self, yaml_simple_path, yoda_template):
        output_file_path = os.path.join(self.current_tmp, 'datafile.yoda')
        hepdata_converter.convert(yaml_simple_path, output_file_path,
                                  options={'output_format': 'yoda1',
                                           'validator_schema_version': '0.1.0',
                                           'hepdata_doi': '10.17182/hepdata.62535.v1',
                                           'yoda_keep_qualifiers' : True,
                                           'rivet_analysis_name': 'ATLAS_2012_I1203852'})

        self.assertNotEqual(os.stat(output_file_path).st_size, 0, 'output yoda file is empty')
        with open(output_file_path, 'r') as f:
            self.assertMultiLineAlmostEqual(f, yoda_template)

    @insert_paths('yaml/ins1283183', 'yaml/ins1397637', 'yaml/ins699647', 'yaml/ins1413748')
    def test_parse_all(self, test_submissions):

        for idx, test_submission in enumerate(test_submissions):
            output_file_path = os.path.join(self.current_tmp, 'data-{}.yoda'.format(idx))

            hepdata_converter.convert(test_submission, output_file_path,
                                      options={'output_format': 'yoda1'})

            self.assertNotEqual(os.stat(output_file_path).st_size, 0, 'output yoda file is empty')


    @insert_path('yaml_inf')
    @insert_data_as_file('yoda1/with_overflows.yoda')
    def test_parse_with_overflows(self, yaml_simple_path, yoda_template):
        output_file_path = os.path.join(self.current_tmp, 'datafile.yoda')
        hepdata_converter.convert(yaml_simple_path, output_file_path,
                                  options={'output_format': 'yoda1',
                                           'validator_schema_version': '0.1.0',
                                           'rivet_analysis_name': 'OVERFLOW_TEST'})

        self.assertNotEqual(os.stat(output_file_path).st_size, 0, 'output yoda file is empty')
        with open(output_file_path, 'r') as f:
            self.assertMultiLineAlmostEqual(f, yoda_template)
