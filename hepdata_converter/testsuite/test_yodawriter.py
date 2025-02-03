# -*- encoding: utf-8 -*-
import os
import hepdata_converter
from hepdata_converter.testsuite import insert_data_as_file, insert_path, insert_paths
from hepdata_converter.testsuite.test_writer import WriterTestSuite

__author__ = 'Michał Szostak'


class YODAWriterTestSuite(WriterTestSuite):
    @insert_path('yaml_full')
    @insert_data_as_file('yoda/full.yoda')
    def test_simple_parse(self, yaml_simple_path, yoda_template):
        output_file_path = os.path.join(self.current_tmp, 'datafile.yoda')
        hepdata_converter.convert(yaml_simple_path, output_file_path,
                                  options={'output_format': 'yoda',
                                           'validator_schema_version': '0.1.0',
                                           'hepdata_doi': '10.17182/hepdata.62535.v1',
                                           'rivet_analysis_name': 'ATLAS_2012_I1203852'})

        self.assertNotEqual(os.stat(output_file_path).st_size, 0, 'output yoda file is empty')
        with open(output_file_path, 'r') as f:
            self.assertMultiLineAlmostEqual(f, yoda_template)

    @insert_paths('yaml/ins1283183', 'yaml/ins1397637', 'yaml/ins699647', 'yaml/ins1413748')
    def test_parse_all(self, test_submissions):

        for idx, test_submission in enumerate(test_submissions):
            output_file_path = os.path.join(self.current_tmp, 'data-{}.yoda'.format(idx))

            hepdata_converter.convert(test_submission, output_file_path,
                                      options={'output_format': 'yoda'})

            self.assertNotEqual(os.stat(output_file_path).st_size, 0, 'output yoda file is empty')

    @insert_path('yaml_full')
    @insert_data_as_file('yoda/full_match.yoda')
    def test_parse_pattern_match(self, yaml_simple_path, yoda_template):
        output_file_path = os.path.join(self.current_tmp, 'datafile.yoda')
        hepdata_converter.convert(yaml_simple_path, output_file_path,
                                  options={'output_format': 'yoda',
                                           'validator_schema_version': '0.1.0',
                                           'hepdata_doi': '10.17182/hepdata.62535.v1',
                                           'rivet_analysis_name': 'ATLAS_2012_I1203852',
                                           'rivet_ref_match': 'd01'})

        self.assertNotEqual(os.stat(output_file_path).st_size, 0, 'output yoda file is empty')
        with open(output_file_path, 'r') as f:
            self.assertMultiLineAlmostEqual(f, yoda_template)

    @insert_path('yaml_full')
    @insert_data_as_file('yoda/full_unmatch.yoda')
    def test_parse_pattern_unmatch(self, yaml_simple_path, yoda_template):
        output_file_path = os.path.join(self.current_tmp, 'datafile.yoda')
        hepdata_converter.convert(yaml_simple_path, output_file_path,
                                  options={'output_format': 'yoda',
                                           'validator_schema_version': '0.1.0',
                                           'hepdata_doi': '10.17182/hepdata.62535.v1',
                                           'rivet_analysis_name': 'ATLAS_2012_I1203852',
                                           'rivet_ref_unmatch': 'd07'})

        self.assertNotEqual(os.stat(output_file_path).st_size, 0, 'output yoda file is empty')
        with open(output_file_path, 'r') as f:
            self.assertMultiLineAlmostEqual(f, yoda_template)

    @insert_path('yaml_no_independent')
    @insert_data_as_file('yoda/no_independent.yoda')
    def test_parse_no_independent(self, yaml_simple_path, yoda_template):
        output_file_path = os.path.join(self.current_tmp, 'datafile.yoda')
        hepdata_converter.convert(yaml_simple_path, output_file_path,
                                  options={'output_format': 'yoda',
                                           'validator_schema_version': '0.1.0',
                                           'rivet_analysis_name': 'ATLAS_2021_I1887997'})

        self.assertNotEqual(os.stat(output_file_path).st_size, 0, 'output yoda file is empty')
        with open(output_file_path, 'r') as f:
            self.assertMultiLineAlmostEqual(f, yoda_template)

    @insert_path('yaml_inf')
    @insert_data_as_file('yoda/with_overflows.yoda')
    def test_parse_with_overflows(self, yaml_simple_path, yoda_template):
        output_file_path = os.path.join(self.current_tmp, 'datafile.yoda')
        hepdata_converter.convert(yaml_simple_path, output_file_path,
                                  options={'output_format': 'yoda',
                                           'validator_schema_version': '0.1.0',
                                           'rivet_analysis_name': 'OVERFLOW_TEST'})

        self.assertNotEqual(os.stat(output_file_path).st_size, 0, 'output yoda file is empty')
        with open(output_file_path, 'r') as f:
            self.assertMultiLineAlmostEqual(f, yoda_template)

    @insert_path('yaml_full')
    @insert_path('yoda/full.yoda.h5')
    def test_parse_h5(self, yaml_simple_path, yoda_template):
        output_file_path = os.path.join(self.current_tmp, 'datafile.yoda.h5')
        hepdata_converter.convert(yaml_simple_path, output_file_path,
                                  options={'output_format': 'yoda.h5',
                                           'validator_schema_version': '0.1.0',
                                           'hepdata_doi': '10.17182/hepdata.62535.v1',
                                           'rivet_analysis_name': 'ATLAS_2012_I1203852',
                                           'rivet_ref_match': 'd01'})

        self.assertEqual(os.stat(output_file_path).st_size, os.stat(yoda_template).st_size, 'output yoda.h5 file has wrong size')
