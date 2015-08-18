import inspect
import os
import pkgutil
import shutil
from hepdata_converter.common import GetConcreteSubclassMixin, OptionInitMixin

__all__ = []

from string import lower
import abc


class Writer(GetConcreteSubclassMixin, OptionInitMixin):
    __metaclass__  = abc.ABCMeta

    def __init__(self, single_file_output, *args, **kwargs):
        OptionInitMixin.__init__(self, options=kwargs)
        self.single_file_output = single_file_output

    @classmethod
    def create_dir(cls, path):
        try:
            os.makedirs(path)
        except OSError as e:
            if e.errno != 17:
                raise

    @abc.abstractmethod
    def write(self, data_in, data_out, *args, **kwargs):
        """Writes data provided by data_in argument to data_out, data_out is implementation dependant, and can be
        directory, filelike object, etc

        :param data_in: input data (type is implementation specified)
        :param data_out: output data (type is implementation specified)
        :param args: additional arguments passed to concrete class
        :param kwargs: additional arguments passed to concrete class
        """


# import all packages in the parsers package, so that Parser.get_specific_parser will recognise them
for loader, name, is_pkg in pkgutil.walk_packages(__path__):
    module = loader.find_module(name).load_module(name)

    for name, value in inspect.getmembers(module):
        if name.startswith('__'):
            continue

        globals()[name] = value
        __all__.append(name)
