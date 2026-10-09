# -*- encoding: utf-8 -*-
import os
import shutil

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
                                                             'single_file': True,
                                                             'validator_schema_version': '0.1.0'})

        self.assertEqual(data, table_5_noqual)


class YAMLParserSingleTableTestSuite(WriterTestSuite):
    """Only the data file of the requested table is read and validated if the 'table' option is given."""

    options = {'input_format': 'yaml', 'output_format': 'csv', 'pack': True, 'validator_schema_version': '0.1.0'}

    @insert_path('yaml_full')
    def setUp(self, yaml_path):
        super(YAMLParserSingleTableTestSuite, self).setUp()
        # copy of the submission with an invalid data file for Table 2
        self.broken_path = os.path.join(self.current_tmp, 'yaml_full_broken')
        shutil.copytree(yaml_path, self.broken_path)
        with open(os.path.join(self.broken_path, 'data2.yaml'), 'w') as f:
            f.write('independent_variables: []\n')

    @insert_data_as_str('csv/table_1.csv')
    @insert_data_as_str('csv/table_9.csv')
    def test_other_invalid_table_is_ignored(self, table_1_content, table_9_content):
        # Table 1 is the first, Table 9 the last (7th) table of the submission
        for table, expected in [('Table 1', table_1_content), (0, table_1_content), ('data1.yaml', table_1_content),
                                ('Table 9', table_9_content), (6, table_9_content), (-1, table_9_content),
                                ('data9.yaml', table_9_content)]:
            csv_content = hepdata_converter.convert(self.broken_path, options=dict(self.options, table=table))
            self.assertMultiLineAlmostEqual(expected, csv_content)

    def test_invalid_table_is_still_validated(self):
        for table in ['Table 2', 1, 'data2.yaml', None]:
            options = dict(self.options)
            if table is not None:
                options['table'] = table
            with self.assertRaises(RuntimeError):
                hepdata_converter.convert(self.broken_path, self.current_tmp, options=options)

    def test_missing_table(self):
        for table in ['Table 10', 'data10.yaml', 7, -8]:
            with self.assertRaises(IndexError):
                hepdata_converter.convert(self.broken_path, options=dict(self.options, table=table))

    @insert_path('yaml_full')
    def test_other_tables_are_kept_without_data(self, yaml_path):
        parser = hepdata_converter.parsers.Parser.get_concrete_class('yaml')(table='Table 9', validator_schema_version='0.1.0')
        parsed = parser.parse(self.broken_path)
        self.assertEqual(['Table 1', 'Table 2', 'Table 3', 'Table 4', 'Table 5', 'Table 8', 'Table 9'],
                         [table.name for table in parsed.tables])
        self.assertEqual([1, 2, 3, 4, 5, 6, 7], [table.index for table in parsed.tables])
        self.assertEqual(['data9.yaml'], [table.data_file for table in parsed.tables if table.data])

        # same tables as without the option
        all_tables = hepdata_converter.parsers.Parser.get_concrete_class('yaml')(validator_schema_version='0.1.0').parse(yaml_path)
        parsed = parser.parse(yaml_path)
        self.assertEqual(all_tables.tables[6], parsed.tables[6])
        self.assertEqual(all_tables.data, parsed.data)

    @insert_path('yaml_full')
    def test_writer_without_table_option_gets_all_tables(self, yaml_path):
        # the yaml writer has no 'table' option and has to write all tables
        output = os.path.join(self.current_tmp, 'yaml_out')
        hepdata_converter.convert(yaml_path, output,
                                  options={'input_format': 'yaml', 'output_format': 'yaml', 'table': 'Table 1',
                                           'validator_schema_version': '0.1.0'})
        self.assertEqual(sorted(['data%s.yaml' % i for i in [1, 2, 3, 4, 5, 8, 9]] + ['submission.yaml']),
                         sorted(os.listdir(output)))
        for i in [1, 2, 3, 4, 5, 8, 9]:
            self.assertGreater(os.path.getsize(os.path.join(output, 'data%s.yaml' % i)), 100)
