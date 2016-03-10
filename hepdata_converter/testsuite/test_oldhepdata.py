import hepdata_converter
from hepdata_converter.parsers import yaml_parser
from hepdata_converter.parsers.oldhepdata_parser import OldHEPData
from hepdata_converter.testsuite import insert_data_as_file, insert_path
from hepdata_converter.testsuite.test_writer import WriterTestSuite


class OldHEPDataTestSuite(WriterTestSuite):
    """Test suite for OldHEPData parser (and YAML writer).
    These are mostly class tests, and unit tests
    """

    @insert_data_as_file('oldhepdata/sample.input')
    @insert_path('oldhepdata/yaml')
    def test_parse_submission(self, oldhepdata_file, yaml_path):
        oldhepdata_p = OldHEPData()
        oldhepdata_parsed_data = oldhepdata_p.parse(oldhepdata_file)

        yaml_p = yaml_parser.YAML()
        yaml_parsed_data = yaml_p.parse(yaml_path)

        self.assertEqual(yaml_parsed_data, oldhepdata_parsed_data)

    @insert_path('oldhepdata/sample.input')
    @insert_path('oldhepdata/yaml')
    def test_cli(self, oldhepdata_path, oldhepdata_yaml_path):
        hepdata_converter._main(['--input-format', 'oldhepdata', '--output-format', 'yaml',
                                 oldhepdata_path, self.current_tmp])

        self.assertDirsEqual(oldhepdata_yaml_path, self.current_tmp)