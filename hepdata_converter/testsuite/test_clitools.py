import os
import hepdata_converter
import unittest
from hepdata_converter.testsuite.test_writer import WriterTestSuite


class CLIToolsTestSuite(WriterTestSuite):
    def test_wrong_call(self):
        self.assertRaises(SystemExit, hepdata_converter.main, [])

    def test_convert_yaml2csv(self):
        hepdata_converter._main(['--input-format', 'yaml', '--output-format', 'csv',
                                '--table', 'Table 1', '--pack',
                                self.current_tmp, os.path.join(self.current_tmp, 'output.csv')])
        self.table_csv = (
            '#: name: Table 1\n'
            '#: description: The measured fiducial cross sections. The first systematic uncertainty is the combined systematic uncertainty excluding luminosity, the second is the luminosity\n'
            '#: data_file: data1.yaml\n'
            '#: keyword reactions: P P --> Z0 Z0 X\n'
            '#: keyword observables: SIG\n'
            '#: keyword energies: 7000\n'
            '#: RE:P P --> Z0 < LEPTON+ LEPTON- > Z0 < LEPTON+ LEPTON- > X\n'
            '\'SQRT(S) IN GEV\':\'SIG(fiducial) IN FB\':\'stat +\':\'stat -\':\'sys +\':\'sys -\':\'sys,lumi +\':\'sys,lumi -\'\n'
            '7000:25.4:3.3:-3.0:1:-1.2:1:-1\n'
            '8000:29.8:3.8:-3.5:1.7:-1.5:1.2:1.2\n'
            '9000:12.7:3.1:-2.9:1.7:1.7:0.5:0.5\n'
        )

        with open(os.path.join(self.current_tmp, 'output.csv')) as f:
            self.assertEqual(self.table_csv, f.read())

    def test_convert_yaml2yoda(self):
        hepdata_converter._main(['--input-format', 'yaml', '--output-format', 'csv',
                                '--table', 'Table 1',
                                self.current_tmp, os.path.join(self.current_tmp, 'output.csv')])

    def test_help(self):
        self.assertRaises(SystemExit, hepdata_converter.main, ['--help'])

    def test_version(self):
        r, message = hepdata_converter._main(['--version'])
        self.assertEqual(r, 0)
        self.assertTrue(message.endswith(hepdata_converter.version.__version__))
