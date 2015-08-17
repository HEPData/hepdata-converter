# -*- encoding: utf-8 -*-
import os
import StringIO
import hepdata_converter
from hepdata_converter.testsuite.test_writer import WriterTestSuite
from hepdata_converter.testsuite.testdata import OLD_HEPDATA_LONG

__author__ = 'Michał Szostak'


class YAMLWriterTestSuite(WriterTestSuite):
    def test_single_file_output(self):
        data = hepdata_converter.convert(StringIO.StringIO(OLD_HEPDATA_LONG),
                                         options={
                                             'input_format': 'oldhepdata',
                                             'output_format': 'yaml',
                                             'single_file': True})

        yaml_single_output_path = os.path.join(self.current_tmp, 'output.yaml')

        hepdata_converter._main(['--input-format', 'oldhepdata', '--output-format', 'yaml', '--single-file',
                                 os.path.join(os.path.dirname(os.path.abspath(__file__)), 'testdata', 'sample.input'),
                                 yaml_single_output_path])

        self.assertTrue(os.path.exists(yaml_single_output_path))

        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'testdata', 'sample.input_single.yaml')) as f:
            template_data = f.read()
            self.assertEqual(template_data, data)

            with open(yaml_single_output_path, 'r') as _f:
                self.assertEqual(template_data, _f.read())



