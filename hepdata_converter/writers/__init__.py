import inspect
import pkgutil

__all__ = []

from string import lower
import abc


class Writer(object):
    __metaclass__  = abc.ABCMeta

    def __init__(self, single_file_output, *args, **kwargs):
        self.single_file_output = single_file_output

    @abc.abstractmethod
    def write(self, data_in, data_out, *args, **kwargs):
        """Writes data provided by data_in argument to data_out, data_out is implementation dependant, and can be
        directory, filelike object, etc

        :param data_in: input data (type is implementation specified)
        :param data_out: output data (type is implementation specified)
        :param args: additional arguments passed to concrete class
        :param kwargs: additional arguments passed to concrete class
        """

    @classmethod
    def get_specific_writer(cls, writer_name):
        """This method provides easier access to all writers inheriting Writer class

        :param writer_name: name of the parser (name of the parser class which should be used)
        :type writer_name: str
        :return: Writer subclass specified by parser_name
        :rtype: Writer subclass
        :raise ValueError:
        """
        for cls in cls.__subclasses__():
            if lower(cls.__name__) == lower(writer_name):
                return cls
        raise ValueError("'writer_name' is invalid")

    @classmethod
    def register_cli_options(cls, parser):
        pass


# import all packages in the parsers package, so that Parser.get_specific_parser will recognise them
for loader, name, is_pkg in pkgutil.walk_packages(__path__):
    module = loader.find_module(name).load_module(name)

    for name, value in inspect.getmembers(module):
        if name.startswith('__'):
            continue

        globals()[name] = value
        __all__.append(name)
