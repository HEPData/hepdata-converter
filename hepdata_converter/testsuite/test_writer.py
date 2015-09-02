import unittest
import os
import tempfile
import shutil
import time
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
