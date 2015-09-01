import StringIO
import unittest
import os
import tempfile
import time
import shutil
import subprocess
import hepdata_converter
from hepdata_converter import convert
from hepdata_converter.testsuite.test_writer import WriterTestSuite


class CSVWriterTestCase(WriterTestSuite):
    def setUp(self):
        super(CSVWriterTestCase, self).setUp()
        self.table_csv = (
            '#: name: Table 1\n'
            '#: description: The measured fiducial cross sections. The first systematic uncertainty is the combined systematic uncertainty excluding luminosity, the second is the luminosity\n'
            '#: data_file: data1.yaml\n'
            '#: keyword reactions: P P --> Z0 Z0 X\n'
            '#: keyword observables: SIG\n'
            '#: keyword energies: 7000\n'
            '#: RE;P P --> Z0 < LEPTON+ LEPTON- > Z0 < LEPTON+ LEPTON- > X\n'
            '\'SQRT(S) IN GEV\';\'SIG(fiducial) IN FB\';\'stat +\';\'stat -\';\'sys +\';\'sys -\';\'sys,lumi +\';\'sys,lumi -\'\n'
            '7000;25.4;3.3;-3.0;1;-1.2;1;-1\n'
            '8000;29.8;3.8;-3.5;1.7;-1.5;1.2;1.2\n'
            '9000;12.7;3.1;-2.9;1.7;1.7;0.5;0.5\n'
        )
        self.table_2_csv = (
            '#: name: Table 9\n'
            '#: description: The observed and expected EmissT distribution in the dielectron SR-Z. The negigible estimated contribution from Z+jets is omitted in these distributions. The last bin contains the overflow.\n'
            '#: data_file: data9.yaml\n'
            '#: keyword energies: 8000\n'
            '#: SQRT(S);;8000.0;8000.0;;;8000.0;8000.0\n'
            '#: EVENTS;;25;25;;;25;25\n'
            '\'ETMISS IN GEV LOW\';\'ETMISS IN GEV HIGH\';\'Data\';\'Expected Background\';\'stat +\';\'stat -\';\'GGM 700 200 1.5\';\'GGM 900 600 1.5\'\n'
            '200.0;225.0;0.0;0.0;0.0;0.0;0.0;0.0\n'
            '225.0;250.0;6.0;0.95;0.41;-0.51;6.46;0.97\n'
            '250.0;275.0;1.0;0.9;0.41;-0.26;6.82;1.07\n'
            '275.0;300.0;1.0;0.42;0.12;-0.19;2.82;1.17\n'
            '300.0;325.0;1.0;0.34;0.16;-0.15;2.41;1.05\n'
            '325.0;350.0;2.0;0.07;0.19;-0.16;3.11;1.08\n'
            '350.0;375.0;1.0;0.68;0.56;-0.55;0.7;1.13\n'
            '375.0;400.0;1.0;0.17;0.1;-0.15;0.9;1.2\n'
            '400.0;425.0;0.0;0.24;0.11;-0.1;0.69;1.01\n'
            '425.0;450.0;1.0;0.01;0.08;0.08;0.72;0.94\n'
            '450.0;475.0;0.0;0.3;0.33;0.33;0.0;0.88\n'
            '475.0;500.0;2.0;0.16;0.17;-0.14;0.93;4.59\n'
        )

        self.table_2_unpacked_csv = (
            '#: name: Table 9\n'
            '#: description: The observed and expected EmissT distribution in the dielectron SR-Z. The negigible estimated contribution from Z+jets is omitted in these distributions. The last bin contains the overflow.\n'
            '#: data_file: data9.yaml\n'
            '#: keyword energies: 8000\n'
            '#: SQRT(S);;8000.0\n'
            '#: EVENTS;;25\n'
            '\'ETMISS IN GEV LOW\';\'ETMISS IN GEV HIGH\';\'Data\'\n'
            '200.0;225.0;0.0\n'
            '225.0;250.0;6.0\n'
            '250.0;275.0;1.0\n'
            '275.0;300.0;1.0\n'
            '300.0;325.0;1.0\n'
            '325.0;350.0;2.0\n'
            '350.0;375.0;1.0\n'
            '375.0;400.0;1.0\n'
            '400.0;425.0;0.0\n'
            '425.0;450.0;1.0\n'
            '450.0;475.0;0.0\n'
            '475.0;500.0;2.0\n'
            '\n'
            '#: SQRT(S);;8000.0\n'
            '#: EVENTS;;25\n'
            '\'ETMISS IN GEV LOW\';\'ETMISS IN GEV HIGH\';\'Expected Background\';\'stat +\';\'stat -\'\n'
            '200.0;225.0;0.0;0.0;0.0\n'
            '225.0;250.0;0.95;0.41;-0.51\n'
            '250.0;275.0;0.9;0.41;-0.26\n'
            '275.0;300.0;0.42;0.12;-0.19\n'
            '300.0;325.0;0.34;0.16;-0.15\n'
            '325.0;350.0;0.07;0.19;-0.16\n'
            '350.0;375.0;0.68;0.56;-0.55\n'
            '375.0;400.0;0.17;0.1;-0.15\n'
            '400.0;425.0;0.24;0.11;-0.1\n'
            '425.0;450.0;0.01;0.08;0.08\n'
            '450.0;475.0;0.3;0.33;0.33\n'
            '475.0;500.0;0.16;0.17;-0.14\n'
            '\n'
            '#: SQRT(S);;8000.0\n'
            '#: EVENTS;;25\n'
            '\'ETMISS IN GEV LOW\';\'ETMISS IN GEV HIGH\';\'GGM 700 200 1.5\'\n'
            '200.0;225.0;0.0\n'
            '225.0;250.0;6.46\n'
            '250.0;275.0;6.82\n'
            '275.0;300.0;2.82\n'
            '300.0;325.0;2.41\n'
            '325.0;350.0;3.11\n'
            '350.0;375.0;0.7\n'
            '375.0;400.0;0.9\n'
            '400.0;425.0;0.69\n'
            '425.0;450.0;0.72\n'
            '450.0;475.0;0.0\n'
            '475.0;500.0;0.93\n'
            '\n'
            '#: SQRT(S);;8000.0\n'
            '#: EVENTS;;25\n'
            '\'ETMISS IN GEV LOW\';\'ETMISS IN GEV HIGH\';\'GGM 900 600 1.5\'\n'
            '200.0;225.0;0.0\n'
            '225.0;250.0;0.97\n'
            '250.0;275.0;1.07\n'
            '275.0;300.0;1.17\n'
            '300.0;325.0;1.05\n'
            '325.0;350.0;1.08\n'
            '350.0;375.0;1.13\n'
            '375.0;400.0;1.2\n'
            '400.0;425.0;1.01\n'
            '425.0;450.0;0.94\n'
            '450.0;475.0;0.88\n'
            '475.0;500.0;4.59\n'
            '\n'
        )

    def test_csvwriter_options(self):
        csv_content = convert(self.submission_filepath, options={'input_format': 'yaml',
                                                                 'output_format': 'csv',
                                                                 'table': 'Table 1',
                                                                 'separator': ';',
                                                                 'pack': True})

        self.assertEqual(self.table_csv, csv_content)

    def test_2_qualifiers_2_iv_pack(self):
        csv_content = convert(self.submission_filepath, options={'input_format': 'yaml',
                                                                 'output_format': 'csv',
                                                                 'table': 'Table 9',
                                                                 'separator': ';',
                                                                 'pack': True})

        self.assertEqual(self.table_2_csv, csv_content)

    def test_multiple_tables_pack(self):
        convert(self.submission_filepath, self.current_tmp, options={'input_format': 'yaml',
                                                                     'output_format': 'csv',
                                                                     'separator': ';',
                                                                     'pack': True})

        with open(os.path.join(self.current_tmp, 'Table 1.csv'), 'r') as f:
            self.assertEqual(self.table_csv, f.read())

        with open(os.path.join(self.current_tmp, 'Table 9.csv'), 'r') as f:
            self.assertEqual(self.table_2_csv, f.read())

    def test_2_qualifiers_2_iv_unpack(self):
        csv_content = convert(self.submission_filepath, options={'input_format': 'yaml',
                                                         'output_format': 'csv',
                                                         'table': 'Table 9',
                                                         'separator': ';',
                                                         'pack': False})
        self.assertEqual(self.table_2_unpacked_csv, csv_content)

    def test_cli(self):
        csv_filepath = os.path.join(self.current_tmp, 'tab.csv')
        hepdata_converter._main(['--output-format', 'csv', '--table', 'Table 9', '--separator', ';', self.submission_filepath,
                                 csv_filepath])

        with open(csv_filepath, 'r') as csv_file:
            self.assertEqual(self.table_2_unpacked_csv, csv_file.read())

    def test_no_dir_output(self):
        csv_filepath = os.path.join(self.current_tmp, 'csv_dir')
        hepdata_converter._main(['--output-format', 'csv', '--separator', ';', self.submission_filepath,
                                 csv_filepath])

        self.assertTrue(os.path.exists(csv_filepath))
        csv_1 = os.path.join(csv_filepath, 'Table 1.csv')
        self.assertTrue(os.path.exists(csv_1))
        with open(csv_1, 'r') as csv_file:
            self.assertEqual(self.table_csv.strip(), csv_file.read().strip())

        csv_2 = os.path.join(csv_filepath, 'Table 9.csv')
        self.assertTrue(os.path.exists(csv_2))
        with open(csv_2, 'r') as csv_file:
            self.assertEqual(self.table_2_unpacked_csv.strip(), csv_file.read().strip())
