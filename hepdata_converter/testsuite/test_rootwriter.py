# -*- encoding: utf-8 -*-
import os
import hepdata_converter
from hepdata_converter.testsuite import insert_path, insert_paths
from hepdata_converter.testsuite.test_writer import WriterTestSuite
import ROOT

__author__ = 'Michał Szostak'

def walk(tdirectory,
         path=None,
         depth=0):
    '''Walk the directory structure recursively and return its content.
    '''
    dirnames, objectnames = [], []
    for key in list(tdirectory.GetListOfKeys()):
        name = key.GetName()
        classname = key.GetClassName()
        is_directory = classname.startswith('TDirectory')
        if is_directory:
            dirnames.append(name)
        else:
            objectnames.append(name)
    if path:
        dirpath = os.path.join(path, tdirectory.GetName())
    elif not isinstance(tdirectory, ROOT.TFile):
        dirpath = tdirectory.GetName()
    else:
        dirpath = ''
    yield dirpath, dirnames, objectnames
    for dirname in dirnames:
        rdir = tdirectory.GetDirectory(dirname)
        for x in walk(rdir,
                      depth=depth + 1,
                      path=dirpath):
            yield x

class ROOTWriterTestSuite(WriterTestSuite):


    @insert_path('yaml_full')
    @insert_path('root/full.root')
    def test_simple_parse(self, yaml_full_path, full_root_path):
        output_file_path = os.path.join(self.current_tmp, 'datafile.root')
        hepdata_converter.convert(yaml_full_path, output_file_path,
                                  options={'output_format': 'root'})

        self.assertNotEqual(os.stat(output_file_path).st_size, 0, 'output root file is empty')

        f = ROOT.TFile.Open(output_file_path)
        f_orig = ROOT.TFile.Open(full_root_path)
        self.assertEqual(list(walk(f)), list(walk(f_orig)))
        f.Close()
        f_orig.Close()

        with open(output_file_path, 'w') as output:
            hepdata_converter.convert(yaml_full_path, output,
                                      options={'output_format': 'root'})

        self.assertNotEqual(os.stat(output_file_path).st_size, 0, 'output root file is empty')

        f = ROOT.TFile.Open(output_file_path)
        f_orig = ROOT.TFile.Open(full_root_path)
        self.assertEqual(list(walk(f)), list(walk(f_orig)))
        for path, dirs, objects in list(walk(f))[1:]:
            for obj in objects:
                o = f.Get('%s/%s' % (path, obj))
                o_orig = f_orig.Get('%s/%s' % (path, obj))
                self.assertEqual(o.__class__, o_orig.__class__)
                if o.__class__.__name__.startswith('TGraph'):
                    self.assertEqual(o.GetN(), o_orig.GetN())
                    for i in xrange(o.GetN()):
                        self.assertEqual(o.GetX()[i],o_orig.GetX()[i])
                        self.assertEqual(o.GetY()[i],o_orig.GetY()[i])
        f.Close()
        f_orig.Close()

    @insert_path('yaml_full')
    @insert_path('root/full.root')
    def test_th1_parse(self, yaml_full_path, full_root_path):
        output_file_path = os.path.join(self.current_tmp, 'datafile.root')
        hepdata_converter.convert(yaml_full_path, output_file_path,
                                  options={'output_format': 'root', 'table': 'data2.yaml'})
        pass

    @insert_paths('yaml/ins1283183', 'yaml/ins1397637', 'yaml/ins699647', 'yaml/ins1413748')
    def test_parse_all(self, test_submissions):

        for idx, test_submission in enumerate(test_submissions):
            output_file_path = os.path.join(self.current_tmp, 'data-{}.root'.format(idx))
            hepdata_converter.convert(test_submission, output_file_path,
                                      options={'output_format': 'root'})

            self.assertNotEqual(os.stat(output_file_path).st_size, 0, 'output root file is empty')
