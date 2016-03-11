import os
from random import randint
import tempfile
import unittest
import shutil
import time
import yaml


def _parse_path_arguments(sample_file_name):
    _sample_file_name = list(sample_file_name)
    sample_file_name = []
    for path_element in _sample_file_name:
        sample_file_name += path_element.split('/')

    return sample_file_name


def construct_testdata_path(path_elements):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'testdata', *path_elements)


class insert_data_as_file(object):
    def __init__(self, *sample_file_name):
        self.sample_file_name = _parse_path_arguments(sample_file_name)

    def __call__(self, function):
        def _inner(*args, **kwargs):
            args = list(args)
            with open(construct_testdata_path(self.sample_file_name), 'r') as f:
                args.append(f)
                function(*args, **kwargs)

        return _inner


class insert_data_as_str(object):
    def __init__(self, *sample_file_name):
        self.sample_file_name = _parse_path_arguments(sample_file_name)

    def __call__(self, function):
        def _inner(*args, **kwargs):
            with open(construct_testdata_path(self.sample_file_name), 'r') as f:
                data = f.read()
            args = list(args)
            args.append(data)
            function(*args, **kwargs)

        return _inner


class insert_path(object):
    def __init__(self, *sample_file_name):
        self.sample_file_name = _parse_path_arguments(sample_file_name)

    def __call__(self, function):
        def _inner(*args, **kwargs):
            args = list(args)
            args.append(construct_testdata_path(self.sample_file_name))
            function(*args, **kwargs)

        return _inner

class insert_paths(object):
    def __init__(self, *sample_file_name):
        self.sample_file_name = sample_file_name

    def __call__(self, function):
        def _inner(*args, **kwargs):
            args = list(args)
            directories = []
            for path in self.sample_file_name:
                directories.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'testdata', path))
            args.append(directories)
            function(*args, **kwargs)

        return _inner


class TMPDirMixin(object):
    def tearDown(self):
        shutil.rmtree(self.current_tmp)

    def setUp(self):
        self.current_tmp = os.path.join(tempfile.gettempdir(), str(int(time.time()))) + str(randint(0, 10000))
        try:
            os.mkdir(self.current_tmp)
        finally:
            pass


class ExtendedTestCase(unittest.TestCase):
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
