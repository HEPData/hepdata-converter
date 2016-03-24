import os
import hepdata_converter
from hepdata_converter import convert
from hepdata_converter.testsuite import insert_path, insert_data_as_str
from hepdata_converter.testsuite.test_writer import WriterTestSuite


class CSVWriterTestCase(WriterTestSuite):

    @insert_path('yaml_full')
    def setUp(self, submission_filepath):
        super(CSVWriterTestCase, self).setUp()
        self.submission_filepath = submission_filepath

    @insert_data_as_str('csv/table_1.csv')
    def test_csvwriter_options(self, table_1_content):
        csv_content = convert(self.submission_filepath, options={'input_format': 'yaml',
                                                                 'output_format': 'csv',
                                                                 'table': 'Table 1',
                                                                 'pack': True})

        self.assertMultiLineAlmostEqual(table_1_content, csv_content)

    @insert_data_as_str('csv/table_9.csv')
    def test_2_qualifiers_2_iv_pack(self, table_9_content):
        csv_content = convert(self.submission_filepath, options={'input_format': 'yaml',
                                                                 'output_format': 'csv',
                                                                 'table': 'Table 9',
                                                                 'pack': True})

        self.assertMultiLineAlmostEqual(table_9_content, csv_content)

    @insert_data_as_str('csv/table_1.csv')
    @insert_data_as_str('csv/table_9.csv')
    def test_multiple_tables_pack(self, table_1_content, table_9_content):
        convert(self.submission_filepath, self.current_tmp, options={'input_format': 'yaml',
                                                                     'output_format': 'csv',
                                                                     'pack': True})

        with open(os.path.join(self.current_tmp, 'Table1.csv'), 'r') as f:
            self.assertMultiLineAlmostEqual(table_1_content, f.read())

        with open(os.path.join(self.current_tmp, 'Table9.csv'), 'r') as f:
            self.assertMultiLineAlmostEqual(table_9_content, f.read())

    @insert_data_as_str('csv/table_9_unpacked.csv')
    def test_2_qualifiers_2_iv_unpack(self, table_9_content):
        csv_content = convert(self.submission_filepath, options={'input_format': 'yaml',
                                                         'output_format': 'csv',
                                                         'table': 'Table 9',
                                                         'separator': ';',
                                                         'pack': False})
        self.assertMultiLineAlmostEqual(table_9_content, csv_content)

    @insert_data_as_str('csv/table_9_unpacked.csv')
    def test_cli(self, table_9_content):
        csv_filepath = os.path.join(self.current_tmp, 'tab.csv')
        hepdata_converter._main(['--output-format', 'csv', '--table', 'Table 9', '--separator', ';', self.submission_filepath,
                                 csv_filepath])

        with open(csv_filepath, 'r') as csv_file:
            self.assertEqual(table_9_content, csv_file.read())

    @insert_data_as_str('csv/table_1.csv')
    @insert_data_as_str('csv/table_9_unpacked_comma.csv')
    def test_no_dir_output(self, table_1_content, table_9_content):
        csv_filepath = os.path.join(self.current_tmp, 'csv_dir')
        hepdata_converter._main(['--output-format', 'csv', '--separator', ',', self.submission_filepath,
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
                                 oldhepdata_path, self.current_tmp])

        self.assertDirsEqual(self.current_tmp, csv_path, file_content_parser=lambda x: x)
