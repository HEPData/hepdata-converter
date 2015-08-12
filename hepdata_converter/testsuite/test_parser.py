import unittest
from hepdata_converter.parsers import Parser
from hepdata_converter.parsers.oldhepdata_parser import OldHEPData


class ParserTestSuite(unittest.TestCase):
    """Test suite for Parser factory class
    """

    def test_get_specific_parser_oldhepdata(self):
        self.assertEqual(Parser.get_concrete_class('oldhepdata').__class__, OldHEPData.__class__)

    def test_get_specific_parser_nonexist(self):
        self.assertRaises(ValueError, Parser.get_concrete_class, 'nonexisting_parser')