import StringIO
import unittest
import os
import tempfile
import time
import shutil
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
            '#: RE\tP P --> Z0 < LEPTON+ LEPTON- > Z0 < LEPTON+ LEPTON- > X\n'
            'SQRT(S) IN GEV\tSIG(fiducial) IN FB\tstat +\tstat -\tsys +\tsys -\tsys,lumi +\tsys,lumi -\n'
            '7000\t25.4\t3.3\t-3.0\t1\t-1.2\t1\t-1\n'
            '8000\t29.8\t3.8\t-3.5\t1.7\t-1.5\t1.2\t1.2\n'
            '9000\t12.7\t3.1\t-2.9\t1.7\t1.7\t0.5\t0.5\n'
        )
        self.table_2_csv = (
            '#: name: Table 9\n'
            '#: description: The observed and expected EmissT distribution in the dielectron SR-Z. The negigible estimated contribution from Z+jets is omitted in these distributions. The last bin contains the overflow.\n'
            '#: data_file: data9.yaml\n'
            '#: keyword energies: 8000\n'
            '#: SQRT(S)\t\t8000.0\t8000.0\t\t\t8000.0\t8000.0\n'
            '#: EVENTS\t\t25\t25\t\t\t25\t25\n'
            'ETMISS IN GEV LOW\tETMISS IN GEV HIGH\tData\tExpected Background\tstat +\tstat -\tGGM 700 200 1.5\tGGM 900 600 1.5\n'
            '200.0\t225.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\n'
            '225.0\t250.0\t6.0\t0.95\t0.41\t-0.51\t6.46\t0.97\n'
            '250.0\t275.0\t1.0\t0.9\t0.41\t-0.26\t6.82\t1.07\n'
            '275.0\t300.0\t1.0\t0.42\t0.12\t-0.19\t2.82\t1.17\n'
            '300.0\t325.0\t1.0\t0.34\t0.16\t-0.15\t2.41\t1.05\n'
            '325.0\t350.0\t2.0\t0.07\t0.19\t-0.16\t3.11\t1.08\n'
            '350.0\t375.0\t1.0\t0.68\t0.56\t-0.55\t0.7\t1.13\n'
            '375.0\t400.0\t1.0\t0.17\t0.1\t-0.15\t0.9\t1.2\n'
            '400.0\t425.0\t0.0\t0.24\t0.11\t-0.1\t0.69\t1.01\n'
            '425.0\t450.0\t1.0\t0.01\t0.08\t0.08\t0.72\t0.94\n'
            '450.0\t475.0\t0.0\t0.3\t0.33\t0.33\t0.0\t0.88\n'
            '475.0\t500.0\t2.0\t0.16\t0.17\t-0.14\t0.93\t4.59\n'
        )

        self.table_2_packed_csv = (
            '#: name: Table 9\n'
            '#: description: The observed and expected EmissT distribution in the dielectron SR-Z. The negigible estimated contribution from Z+jets is omitted in these distributions. The last bin contains the overflow.\n'
            '#: data_file: data9.yaml\n'
            '#: keyword energies: 8000\n'
            '#: SQRT(S)\t\t8000.0\n'
            '#: EVENTS\t\t25\n'
            'ETMISS IN GEV LOW\tETMISS IN GEV HIGH\tData\n'
            '200.0\t225.0\t0.0\n'
            '225.0\t250.0\t6.0\n'
            '250.0\t275.0\t1.0\n'
            '275.0\t300.0\t1.0\n'
            '300.0\t325.0\t1.0\n'
            '325.0\t350.0\t2.0\n'
            '350.0\t375.0\t1.0\n'
            '375.0\t400.0\t1.0\n'
            '400.0\t425.0\t0.0\n'
            '425.0\t450.0\t1.0\n'
            '450.0\t475.0\t0.0\n'
            '475.0\t500.0\t2.0\n'
            '\n'
            '#: SQRT(S)\t\t8000.0\n'
            '#: EVENTS\t\t25\n'
            'ETMISS IN GEV LOW\tETMISS IN GEV HIGH\tExpected Background\tstat +\tstat -\n'
            '200.0\t225.0\t0.0\t0.0\t0.0\n'
            '225.0\t250.0\t0.95\t0.41\t-0.51\n'
            '250.0\t275.0\t0.9\t0.41\t-0.26\n'
            '275.0\t300.0\t0.42\t0.12\t-0.19\n'
            '300.0\t325.0\t0.34\t0.16\t-0.15\n'
            '325.0\t350.0\t0.07\t0.19\t-0.16\n'
            '350.0\t375.0\t0.68\t0.56\t-0.55\n'
            '375.0\t400.0\t0.17\t0.1\t-0.15\n'
            '400.0\t425.0\t0.24\t0.11\t-0.1\n'
            '425.0\t450.0\t0.01\t0.08\t0.08\n'
            '450.0\t475.0\t0.3\t0.33\t0.33\n'
            '475.0\t500.0\t0.16\t0.17\t-0.14\n'
            '\n'
            '#: SQRT(S)\t\t8000.0\n'
            '#: EVENTS\t\t25\n'
            'ETMISS IN GEV LOW\tETMISS IN GEV HIGH\tGGM 700 200 1.5\n'
            '200.0\t225.0\t0.0\n'
            '225.0\t250.0\t6.46\n'
            '250.0\t275.0\t6.82\n'
            '275.0\t300.0\t2.82\n'
            '300.0\t325.0\t2.41\n'
            '325.0\t350.0\t3.11\n'
            '350.0\t375.0\t0.7\n'
            '375.0\t400.0\t0.9\n'
            '400.0\t425.0\t0.69\n'
            '425.0\t450.0\t0.72\n'
            '450.0\t475.0\t0.0\n'
            '475.0\t500.0\t0.93\n'
            '\n'
            '#: SQRT(S)\t\t8000.0\n'
            '#: EVENTS\t\t25\n'
            'ETMISS IN GEV LOW\tETMISS IN GEV HIGH\tGGM 900 600 1.5\n'
            '200.0\t225.0\t0.0\n'
            '225.0\t250.0\t0.97\n'
            '250.0\t275.0\t1.07\n'
            '275.0\t300.0\t1.17\n'
            '300.0\t325.0\t1.05\n'
            '325.0\t350.0\t1.08\n'
            '350.0\t375.0\t1.13\n'
            '375.0\t400.0\t1.2\n'
            '400.0\t425.0\t1.01\n'
            '425.0\t450.0\t0.94\n'
            '450.0\t475.0\t0.88\n'
            '475.0\t500.0\t4.59\n'
            '\n'
        )

    def test_csvwriter_options(self):
        csv_content = convert(self.submission_filepath, options={'input_format': 'yaml',
                                                                 'output_format': 'csv',
                                                                 'table': 'Table 1',
                                                                 'pack': True})

        self.assertEqual(self.table_csv, csv_content)

    def test_2_qualifiers_2_iv_pack(self):
        csv_content = convert(self.submission_filepath, options={'input_format': 'yaml',
                                                                 'output_format': 'csv',
                                                                 'table': 'Table 9',
                                                                 'pack': True})

        self.assertEqual(self.table_2_csv, csv_content)

    def test_multiple_tables_pack(self):
        convert(self.submission_filepath, self.current_tmp, options={'input_format': 'yaml',
                                                                     'output_format': 'csv',
                                                                     'pack': True})

        with open(os.path.join(self.current_tmp, 'Table 1.csv'), 'r') as f:
            self.assertEqual(self.table_csv, f.read())

        with open(os.path.join(self.current_tmp, 'Table 9.csv'), 'r') as f:
            self.assertEqual(self.table_2_csv, f.read())

    def test_2_qualifiers_2_iv_unpack(self):
        csv_content = convert(self.submission_filepath, options={'input_format': 'yaml',
                                                         'output_format': 'csv',
                                                         'table': 'Table 9',
                                                         'pack': False})
        self.assertEqual(self.table_2_packed_csv, csv_content)

