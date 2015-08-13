import tempfile
import unittest
import StringIO
import time
import os
import shutil
import hepdata_converter
from hepdata_converter.parsers.oldhepdata_parser import OldHEPData
from testdata import OLD_HEPDATA_LONG


class OldHEPDataTestSuite(unittest.TestCase):
    """Test suite for OldHEPData parser (and YAML writer).
    These are mostly class tests, and unit tests
    """

    def tearDown(self):
        shutil.rmtree(self.tmp_dir_name)

    def setUp(self):
        self.tmp_dir_name = os.path.join(tempfile.gettempdir(), str(int(time.time())))
        os.mkdir(self.tmp_dir_name)

    def test_parse_submission(self):
        parser = OldHEPData()
        parsed_data = parser.parse(StringIO.StringIO(OLD_HEPDATA_LONG))

        # test parsing of independent_variables
        self.assertEqual(parsed_data.tables[0].data['independent_variables'][0], {'values': ['7000'], 'header': {'name': 'SQRT(S)', 'units': 'GEV'}})

        # test parsing of dependent_variables
        self.assertEqual(parsed_data.tables[0].data['dependent_variables'], [
            {'header': {'units': 'FB', 'name': 'SIG(fiducial)'}, 'qualifiers': [{'name': 'RE', 'value': 'P P --> Z0 < LEPTON+ LEPTON- > Z0 < LEPTON+ LEPTON- > X'}], 'values': [
                {'value': '25.4',
                 'errors': [
                    {'asymerror': {'plus': '3.3', 'minus': '-3.0'}, 'label': 'stat'},
                    {'asymerror': {'minus': '-1.0', 'plus': '1.2'}, 'label': 'sys'},
                    {'symerror': '1.0', 'label': 'sys,lumi'},
                 ]
                }
            ]},
            {'header': {'units': 'FB', 'name': 'SIG(fiducial)'}, 'qualifiers': [{'name': 'RE', 'value': 'P P --> Z0 < LEPTON+ LEPTON- > Z0* < LEPTON+ LEPTON- > X'}], 'values': [
                {
                    'value': '29.8',
                    'errors': [{'asymerror': {'plus': '3.8', 'minus': '-3.5'}, 'label': 'stat'},
                               {'asymerror': {'plus': '1.7', 'minus': '-1.5'}, 'label': 'sys'},
                               {'symerror': '1.2', 'label': 'sys,lumi'}]
                }
            ]},
            {'header': {'units': 'FB', 'name': 'SIG(fiducial)'}, 'qualifiers': [{'name': 'RE', 'value': 'P P --> Z0 < LEPTON+ LEPTON- > Z0 < NU NUBAR > X'}], 'values': [
                {
                    'value': '12.7',
                    'errors': [
                        {'asymerror': {'plus': '3.1', 'minus': '-2.9'}, 'label': 'stat'},
                        {'symerror': '1.7', 'label': 'sys'},
                        {'symerror': '0.5', 'label': 'sys,lumi'}
                    ]
                }
            ]
            }])

    def test_cli(self):
        hepdata_converter._main(['--input-format', 'oldhepdata', '--output-format', 'yaml',
                                 os.path.join(os.path.dirname(os.path.abspath(__file__)), 'testdata', 'sample.input'),
                                 self.tmp_dir_name])