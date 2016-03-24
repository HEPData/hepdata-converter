import abc
import copy
import os
from hepdata_converter.common import GetConcreteSubclassMixin, OptionInitMixin

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
    def __eq__(self, other):
        if self.metadata != other.metadata:
            return False
        if self.data != other.data:
            return False
        if self.all_data != other.all_data:
            return False
        if self.index != other.index:
            return False
        return True

    def __init__(self, index=None, data_file=None, table_name=None, metadata=None, data=None):
        self.data = data or []
        self.index = index
        self.qualifiers = []
        self.dserrors = []

        self.metadata = metadata or {
            'name': table_name or 'Table %s' % self.index,
            'location': None,
            'description': None,
            'keywords': [
                {'name': 'reactions', 'values': []},
                {'name': 'observables', 'values': []},
                {'name': 'energies', 'values': []},
            ],
            'data_file': data_file or 'data%s.yaml' % index,
            # it seems it's required
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
        for keyword in self.metadata['keywords']:
            if keyword['name'] == 'reactions':
                self.reactions = keyword['values']
            elif keyword['name'] == 'observables':
                self.observables = keyword['values']
            elif keyword['name'] == 'energies':
                self.energies = keyword['values']

        self.data_file = self.metadata['data_file']

        if self.data:
            for dependent_variable in self.data.get('dependent_variables', []):
                self.qualifiers.append(dependent_variable.get('qualifiers', []))

    @property
    def name(self):
        return self.metadata['name']

    @property
    def additional_resources(self):
        return self.metadata['additional_resources']

    @property
    def data_license(self):
        return self.metadata['data_license']

    @property
    def keywords(self):
        return self.metadata['keywords']

    @property
    def location(self):
        return self.metadata['location']

    @property
    def description(self):
        return self.metadata['description']

    @property
    def independent_variables(self):
        return self.data['independent_variables']

    @property
    def dependent_variables(self):
        return self.data['dependent_variables']

    @property
    def all_data(self):
        _all = copy.copy(self.metadata)
        if 'data_file' in self.metadata:
            del _all['data_file']

        _all['independent_variables'] = self.independent_variables
        _all['dependent_variables'] = self.dependent_variables

        return _all

class ParsedData(object):
    """Simple data storage class which should be returned by Parser.parse method

    """
    def __init__(self, data, tables):
        self.data = data
        self.tables = tables

    def __eq__(self, other):
        if self.data != other.data:
            return False
        if self.tables != other.tables:
            return False
        return True

    def get_table(self, **kwargs):
        assert len(kwargs) == 1
        key, search_val = kwargs.items()[0]
        assert key in ('id', 'name', 'file')

        if key == 'id':
            return self.tables[search_val]
        elif key == 'file':
            for table in self.tables:
                if table.data_file == os.path.basename(search_val):
                    return table
            raise IndexError("No table with filename = %s" % search_val)
        elif key == 'name':
            for table in self.tables:
                if table.name == search_val:
                    return table
            raise IndexError("No table with name = %s" % search_val)


class Parser(GetConcreteSubclassMixin, OptionInitMixin):
    __metaclass__  = abc.ABCMeta

    def __init__(self, *args, **kwargs):
        OptionInitMixin.__init__(self, options=kwargs)

    @abc.abstractmethod
    def parse(self, data_in, *args, **kwargs):
        """Parses data_in and returns parsed data in the form of ParsedData object

        :param data_in: data to process, depending on the concrete implementation object type may vary
        :param options: dictionary containing additional options for concrete Parser

        :return: Parsed data, in the YAML writer friendly format (list, dicts, and simple objects)
        :rtype: ParsedData
        """

# import all packages in the parsers package, so that Parser.get_specific_parser will recognise them
for loader, name, is_pkg in pkgutil.walk_packages(__path__):
    module = loader.find_module(name).load_module(name)

    for name, value in inspect.getmembers(module):
        if name.startswith('__'):
            continue

        globals()[name] = value
        __all__.append(name)
