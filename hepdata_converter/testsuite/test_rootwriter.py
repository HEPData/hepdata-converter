# -*- encoding: utf-8 -*-
import os
import StringIO
import rootpy
import hepdata_converter
from hepdata_converter.testsuite import insert_data_as_file, insert_path, insert_data_as_str
from hepdata_converter.testsuite.test_writer import WriterTestSuite
from rootpy.io import root_open

__author__ = 'Michał Szostak'

import unittest
from hepdata_converter.writers.root_writer import ROOT


class ROOTWriterTestSuite(WriterTestSuite):
    
    @insert_path('yaml_full')
    @insert_path('root/full.root')
    def test_simple_parse(self, yaml_simple_path, full_root_path):
        output_file_path = os.path.join(self.current_tmp, 'datafile.root')
        hepdata_converter.convert(yaml_simple_path, output_file_path,
                                  options={'output_format': 'root'})

        self.assertNotEqual(os.stat(output_file_path).st_size, 0, 'output root file is empty')

        with root_open(output_file_path, 'r') as f, root_open(full_root_path, 'r') as f_orig:
            self.assertEqual(list(f.walk()), list(f_orig.walk()))

        with open(output_file_path, 'w') as output:
            hepdata_converter.convert(yaml_simple_path, output,
                                      options={'output_format': 'root'})

        self.assertNotEqual(os.stat(output_file_path).st_size, 0, 'output root file is empty')

        with root_open(output_file_path, 'r') as f, root_open(full_root_path, 'r') as f_orig:
            self.assertEqual(list(f.walk()), list(f_orig.walk()))
