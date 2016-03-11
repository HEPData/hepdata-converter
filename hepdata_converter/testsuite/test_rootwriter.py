# -*- encoding: utf-8 -*-
import os
import rootpy
import hepdata_converter
from hepdata_converter.testsuite import insert_path, insert_paths
from hepdata_converter.testsuite.test_writer import WriterTestSuite
from rootpy.io import root_open

__author__ = 'Michał Szostak'


class ROOTWriterTestSuite(WriterTestSuite):
    
    @insert_path('yaml_full')
    @insert_path('root/full.root')
    def test_simple_parse(self, yaml_full_path, full_root_path):
        output_file_path = os.path.join(self.current_tmp, 'datafile.root')
        hepdata_converter.convert(yaml_full_path, output_file_path,
                                  options={'output_format': 'root'})

        self.assertNotEqual(os.stat(output_file_path).st_size, 0, 'output root file is empty')

        with root_open(output_file_path, 'r') as f, root_open(full_root_path, 'r') as f_orig:
            self.assertEqual(list(f.walk()), list(f_orig.walk()))

        with open(output_file_path, 'w') as output:
            hepdata_converter.convert(yaml_full_path, output,
                                      options={'output_format': 'root'})

        self.assertNotEqual(os.stat(output_file_path).st_size, 0, 'output root file is empty')

        with root_open(output_file_path, 'r') as f, root_open(full_root_path, 'r') as f_orig:
            self.assertEqual(list(f.walk()), list(f_orig.walk()))
            for path, dirs, objects in list(f.walk())[1:]:
                for object in objects:
                    o = f.get('%s/%s' % (path, object))
                    o_orig = f_orig.get('%s/%s' % (path, object))
                    self.assertEqual(o.__class__, o_orig.__class__)
                    if o.__class__.__name__ == rootpy.plotting.graph.Graph.__name__:
                        self.assertEqual(list(o.x()), list(o_orig.x()))
                        self.assertEqual(list(o.y()), list(o_orig.y()))

    @insert_path('yaml_full')
    @insert_path('root/full.root')
    def test_th1_parse(self, yaml_full_path, full_root_path):
        output_file_path = os.path.join(self.current_tmp, 'datafile.root')
        hepdata_converter.convert(yaml_full_path, output_file_path,
                                  options={'output_format': 'root', 'table': 'data2.yaml'})
        pass

    @insert_paths('yaml/ins1283183', 'yaml/ins1397637', 'yaml/ins699647')
    def test_parse_all(self, test_submissions):

        for idx, test_submission in enumerate(test_submissions):
            output_file_path = os.path.join(self.current_tmp, 'data-{}.root'.format(idx))

            hepdata_converter.convert(test_submission, output_file_path,
                                      options={'output_format': 'root'})

            self.assertNotEqual(os.stat(output_file_path).st_size, 0, 'output root file is empty')
