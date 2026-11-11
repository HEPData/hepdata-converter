import csv
import os
from pathlib import Path

import yaml
import hepdata_converter
from hepdata_converter import convert
from hepdata_converter.testsuite import insert_path, insert_data_as_str
from hepdata_converter.testsuite.test_writer import WriterTestSuite


class CSVWriterTestCase(WriterTestSuite):

    @insert_path('yaml_full')
    def setUp(self, submission_filepath):
        super(CSVWriterTestCase, self).setUp()
        self.submission_filepath = submission_filepath

    def test_missing_dependent_values(self):
        submission = Path(self.current_tmp)
        (submission / 'submission.yaml').write_text(yaml.safe_dump({
            'name': 'Table 1', 'description': 'Unequal column lengths',
            'data_file': 'data.yaml', 'keywords': [],
        }))
        (submission / 'data.yaml').write_text(yaml.safe_dump({
            'independent_variables': [
                {'header': {'name': 'X'}, 'values': [{'value': i} for i in (1, 2, 3)]},
            ],
            'dependent_variables': [
                {'header': {'name': 'Y1'}, 'values': [{'value': i} for i in (10, 20)]},
                {'header': {'name': 'Y2'}, 'values': [{'value': 30}]},
            ],
        }))

        cases = [
            (True, [
                ['X', 'Y1', 'Y2'], ['1', '10', '30'], ['2', '20', ''], ['3', '', ''],
            ]),
            (False, [
                ['X', 'Y1'], ['1', '10'], ['2', '20'], ['3', ''],
                ['X', 'Y2'], ['1', '30'], ['2', ''], ['3', ''],
            ]),
        ]
        for packed, expected in cases:
            with self.subTest(packed=packed):
                result = convert(str(submission), options={
                    'output_format': 'csv', 'table': 'Table 1', 'pack': packed,
                    'validator_schema_version': '0.1.0',
                })
                records = [line for line in result.splitlines() if line and not line.startswith('#:')]
                self.assertEqual(list(csv.reader(records)), expected)

    @insert_data_as_str('csv/table_1.csv')
    def test_csvwriter_options(self, table_1_content):
        csv_content = convert(self.submission_filepath, options={'input_format': 'yaml',
                                                                 'output_format': 'csv',
                                                                 'table': 'Table 1',
                                                                 'pack': True,
                                                                 'validator_schema_version': '0.1.0'})

        self.assertMultiLineAlmostEqual(table_1_content, csv_content)

    @insert_data_as_str('csv/table_9.csv')
    def test_2_qualifiers_2_iv_pack(self, table_9_content):
        csv_content = convert(self.submission_filepath, options={'input_format': 'yaml',
                                                                 'output_format': 'csv',
                                                                 'table': 'Table 9',
                                                                 'pack': True,
                                                                 'validator_schema_version': '0.1.0'})

        self.assertMultiLineAlmostEqual(table_9_content, csv_content)

    @insert_data_as_str('csv/table_1.csv')
    @insert_data_as_str('csv/table_9.csv')
    def test_multiple_tables_pack(self, table_1_content, table_9_content):
        convert(self.submission_filepath, self.current_tmp, options={'input_format': 'yaml',
                                                                     'output_format': 'csv',
                                                                     'pack': True,
                                                                     'validator_schema_version': '0.1.0'})

        with open(os.path.join(self.current_tmp, 'Table1.csv'), 'r') as f:
            self.assertMultiLineAlmostEqual(table_1_content, f.read())

        with open(os.path.join(self.current_tmp, 'Table9.csv'), 'r') as f:
            self.assertMultiLineAlmostEqual(table_9_content, f.read())

    @insert_data_as_str('csv/table_9_unpacked.csv')
    def test_2_qualifiers_2_iv_unpack(self, table_9_content):
        csv_content = convert(self.submission_filepath, options={'input_format': 'yaml',
                                                         'output_format': 'csv',
                                                         'table': 'Table 9',
                                                         'validator_schema_version': '0.1.0',
                                                         'separator': ';',
                                                         'pack': False})
        self.assertMultiLineAlmostEqual(table_9_content, csv_content)

    @insert_data_as_str('csv/table_9_unpacked.csv')
    def test_cli(self, table_9_content):
        csv_filepath = os.path.join(self.current_tmp, 'tab.csv')
        hepdata_converter._main(['--output-format', 'csv',
                                 '--table', 'Table 9',
                                 '--validator-schema-version', '0.1.0',
                                 '--separator', ';',
                                 self.submission_filepath, csv_filepath])

        with open(csv_filepath, 'r') as csv_file:
            self.assertEqual(table_9_content, csv_file.read())

    @insert_data_as_str('csv/table_1.csv')
    @insert_data_as_str('csv/table_9_unpacked_comma.csv')
    def test_no_dir_output(self, table_1_content, table_9_content):
        csv_filepath = os.path.join(self.current_tmp, 'csv_dir')
        hepdata_converter._main(['--output-format', 'csv',
                                 '--validator-schema-version', '0.1.0',
                                 '--separator', ',',
                                 self.submission_filepath,
                                 csv_filepath])

        self.assertTrue(os.path.exists(csv_filepath))
        csv_1 = os.path.join(csv_filepath, 'Table1.csv')
        self.assertTrue(os.path.exists(csv_1))
        with open(csv_1, 'r') as csv_file:
            self.assertMultiLineAlmostEqual(table_1_content.strip(), csv_file.read().strip())

        csv_2 = os.path.join(csv_filepath, 'Table9.csv')
        self.assertTrue(os.path.exists(csv_2))
        with open(csv_2, 'r') as csv_file:
            self.assertMultiLineAlmostEqual(table_9_content.strip(), csv_file.read().strip())

    @insert_path('oldhepdata/sample.input')
    @insert_path('csv/full')
    def test_diroutput(self, oldhepdata_path, csv_path):
        hepdata_converter._main(['-i', 'oldhepdata',
                                 '-o', 'csv',
                                 '-d', '10.17182/hepdata.62535.v1',
                                 oldhepdata_path, self.current_tmp])

        self.assertDirsEqual(self.current_tmp, csv_path, file_content_parser=lambda x: x)
