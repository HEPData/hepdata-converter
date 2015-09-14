import unittest
import os
import tempfile
import shutil
import time
import yaml
from hepdata_converter.writers import Writer


class WriterTestSuite(unittest.TestCase):
    def tearDown(self):
        shutil.rmtree(self.current_tmp)

    def setUp(self):
        self.current_tmp = os.path.join(tempfile.gettempdir(), str(int(time.time())))
        os.mkdir(self.current_tmp)

    def test_create_dir(self):
        dir_to_create = os.path.join(self.current_tmp, 'tmp')
        Writer.create_dir(dir_to_create)
        self.assertTrue(os.path.exists(dir_to_create))
        # make sure calling this function with existing directory works without errors as well
        Writer.create_dir(dir_to_create)

    def assertMultiLineAlmostEqual(self, first, second, msg=None):
        if hasattr(first, 'readlines'):
            lines = first.readlines()
        elif isinstance(first, (str, unicode)):
            lines = first.split('\n')

        if hasattr(second, 'readlines'):
            orig_lines = second.readlines()
        elif isinstance(second, (str, unicode)):
            orig_lines = second.split('\n')

        self.assertEqual(len(lines), len(orig_lines))
        for i in xrange(len(lines)):
            self.assertEqual(lines[i].strip(), orig_lines[i].strip())
    
    def assertDirsEqual(self, first_dir, second_dir, file_content_parser=lambda x: list(yaml.load_all(x)), exclude=[], msg=None):
        self.assertEqual(list(os.walk(first_dir))[1:], list(os.walk(second_dir))[1:], msg)
        dirs = list(os.walk(first_dir))
        for file in dirs[0][2]:
            if file not in exclude:
                with open(os.path.join(first_dir, file)) as f1, open(os.path.join(second_dir, file)) as f2:
                    # separated into 2 variables to ease debugging if the need arises
                    d1 = file_content_parser(f1.read())
                    d2 = file_content_parser(f2.read())
                    self.assertEqual(d1, d2)
