import os


def _parse_path_arguments(sample_file_name):
    _sample_file_name = list(sample_file_name)
    sample_file_name = []
    for path_element in _sample_file_name:
        sample_file_name += path_element.split('/')
    return sample_file_name

def _construct_testdata_path(path_elements):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'testdata', *path_elements)

class insert_data_as_file(object):
    def __init__(self, *sample_file_name):
        self.sample_file_name = _parse_path_arguments(sample_file_name)

    def __call__(self, function):
        def _inner(*args, **kwargs):
            args = list(args)
            with open(_construct_testdata_path(self.sample_file_name), 'r') as f:
                args.append(f)
                function(*args, **kwargs)

        return _inner


class insert_data_as_str(object):
    def __init__(self, *sample_file_name):
        self.sample_file_name = _parse_path_arguments(sample_file_name)
    def __call__(self, function):
        def _inner(*args, **kwargs):
            with open(_construct_testdata_path(self.sample_file_name), 'r') as f:
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
            args.append(_construct_testdata_path(self.sample_file_name))
            function(*args, **kwargs)

        return _inner