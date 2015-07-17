import abc

__all__ = []

from string import lower
import pkgutil
import inspect


class BadFormat(Exception):
    """Class for exceptions raised if bad formatting of parser's input file prohibits from
    parsing the file correctly

    """
    pass


class Table(object):
    """Simple table storage class used for handling tables without extremely deep dictionaries
    """
    def __init__(self, index=None, data_file=None, table_name=None):
        self.reactions = []
        self.observables = []
        self.energies = []
        self.qualifiers = []

        self.data_file = data_file or 'data%s.yaml' % index

        self.index = index
        self.data = []
        self.metadata = {
            'name': table_name or 'Table %s' % self.index,
            'location': None,
            'description': None,
            'keywords': [
                {'name': 'reactions', 'values': self.reactions},
                {'name': 'observables', 'values': self.observables},
                {'name': 'energies', 'values': self.energies},
            ],
            'data_file': self.data_file,
            # it seams it's required
            # TODO - is it really required? should sensible defaults be provided?
            'data_license': {
                'name': None,
                'url': None,
                'description': None # (optional)
            },
            'additional_resources': [
                # Below in the comments are listed allowed keys / values for additional_resources
                #
                # {
                # 'location': None
                # 'description': "Full source code for creating this data"
                # },
                # {'location': "root.root",
                #  'description': "Some file",
                #  'license': {
                #     'name': 'GPL 2',
                #     'url': 'url for license',
                #     'description': 'Tell me about it. This can appear in the main record display' # (optional)
                #     }
                # }
            ]
        }


class ParsedData(object):
    """Simple data storage class which should be returned by Parser.parse method

    """
    def __init__(self, data, tables):
        self.data = data
        self.tables = tables


class Parser(object):
    __metaclass__  = abc.ABCMeta

    def __init__(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    def parse(self, data_in, *args, **kwargs):
        """Parses data_in and returns parsed data in the form of ParsedData object

        :param data_in: data to process, depending on the concrete implementation object type may vary
        :param options: dictionary containing additional options for concrete Parser

        :return: Parsed data, in the YAML writer friendly format (list, dicts, and simple objects)
        :rtype: ParsedData
        """

    @classmethod
    def get_specific_parser(cls, parser_name):
        """This method provides easier access to all parsers inheriting Parser class

        :param parser_name: name of the parser (name of the parser class which should be used)
        :type parser_name: str
        :return: Parser subclass specified by parser_name
        :rtype: Parser subclass
        :raise ValueError:
        """
        for cls in cls.__subclasses__():
            if lower(cls.__name__) == lower(parser_name):
                return cls
        raise ValueError("'parser_name' is invalid")


# import all packages in the parsers package, so that Parser.get_specific_parser will recognise them
for loader, name, is_pkg in pkgutil.walk_packages(__path__):
    module = loader.find_module(name).load_module(name)

    for name, value in inspect.getmembers(module):
        if name.startswith('__'):
            continue

        globals()[name] = value
        __all__.append(name)
