import abc
import copy
import csv
from math import sqrt
import os
from hepdata_converter.common import OptionInitMixin, Option
from hepdata_converter.writers import Writer
import abc


class ObjectWrapper(object):
    __metaclass__ = abc.ABCMeta
    accept_alphanumeric = False

    @classmethod
    def is_number_var(cls, variable):
        for element in variable['values']:
            if 'value' in element and isinstance(element['value'], (str, unicode)):
                return False
        return True
    @classmethod
    def sanitize_name(cls, name):
        return name.replace(' ', '_').replace('/', '_')

    @classmethod
    def is_value_var(cls, variable):
        return cls._is_attr_variable('value', variable)

    @classmethod
    def is_range_var(cls, variable):
        return cls._is_attr_variable('high', variable) and cls._is_attr_variable('low', variable)

    @classmethod
    def has_errors(cls, variable):
        return cls._is_attr_variable('errors', variable)

    @classmethod
    def _is_attr_variable(cls, attr_name, variable):
        for element in variable['values']:
            if attr_name not in element:
                return False
        return True

    def __init__(self, independent_variable_map, dependent_variable):
        self.xval = []
        self.yval = []
        self.xerr_minus = []
        self.xerr_plus = []
        self.yerr_minus = []
        self.yerr_plus = []
        self.independent_variables = list(independent_variable_map)
        self.independent_variable_map = independent_variable_map
        self.dependent_variable = dependent_variable

    @classmethod
    def match(cls, independent_variables_map, dependent_variable):
        if not cls.accept_alphanumeric and (len(filter(lambda x: x is False, [cls.is_number_var(var) for var in independent_variables_map])) > 0 or not cls.is_number_var(dependent_variable)):
            return False
        if len(independent_variables_map) == 0 or len(independent_variables_map[0]) == 0:
            return False
        return True

    @classmethod
    def match_and_create(cls, independent_variables_map, dependent_variable):
        if cls.match(independent_variables_map, dependent_variable):
            return cls(independent_variables_map, dependent_variable).create_objects()
        return []

    def calculate_total_errors(self):
        for independent_variable in self.independent_variable_map:
            xerr_minus = []
            self.xerr_minus.append(xerr_minus)
            xerr_plus = []
            self.xerr_plus.append(xerr_plus)
            xval = []
            self.xval.append(xval)
            ArrayWriter.calculate_total_errors(independent_variable, xerr_minus, xerr_plus, xval)
        ArrayWriter.calculate_total_errors(self.dependent_variable, self.yerr_minus, self.yerr_plus, self.yval)

    @abc.abstractmethod
    def create_objects(self):
        pass


class ObjectFactory(object):
    def __init__(self, class_list, independent_variables, dependent_variables):
        self.class_list = class_list
        self.map = {}
        self.independent_variables = independent_variables
        self.dependent_variables = dependent_variables
        for variable_index in xrange(len(dependent_variables)):
            self.map[variable_index] = list(independent_variables)

    def get_next_object(self):
        for dependent_variable_index in xrange(len(self.dependent_variables)):
            for class_wrapper in self.class_list:
                objects = class_wrapper.match_and_create(self.map[dependent_variable_index], self.dependent_variables[dependent_variable_index])
                for obj in objects:
                    yield obj


class ArrayWriter(Writer):
    __metaclass__ = abc.ABCMeta

    @staticmethod
    def calculate_total_errors(variable, min_errs, max_errs, values):
        for entry in variable['values']:
            if 'value' in entry:
                values.append(entry['value'])
                if 'errors' in entry:
                    errors_min = 0.0
                    errors_max = 0.0
                    for error in entry['errors']:
                        if 'asymerror' in error:
                            errors_min += pow(error['asymerror']['minus'], 2)
                            errors_max += pow(error['asymerror']['plus'], 2)
                        elif 'symerror' in error:
                            errors_min += pow(error['symerror'], 2)
                            errors_max += pow(error['symerror'], 2)
                    min_errs.append(sqrt(errors_min))
                    max_errs.append(sqrt(errors_max))
                else:
                    min_errs.append(0.0)
                    max_errs.append(0.0)
            else:
                middle_val = (entry['high'] - entry['low']) * 0.5 + entry['low']
                values.append(middle_val)
                min_errs.append(entry['high'] - middle_val)
                max_errs.append(middle_val - entry['low'])

    @classmethod
    def options(cls):
        return {
                'table': Option('table', 't', required=False, variable_mapping='table_id', default=None,
                                help=('Specifies which table should be exported, if not specified all tables will be exported '
                                      '(in this case output must be a directory, not a file)')),
        }

    def __init__(self, *args, **kwargs):
        kwargs['single_file_output'] = True
        super(ArrayWriter, self).__init__(*args, **kwargs)
        self.tables = []
        self.extension = None

    @abc.abstractmethod
    def _write_table(self, data_out, table):
        pass

    def _get_tables(self, data_in):
        # get table to work on
        if self.table_id is not None:
            if isinstance(self.table_id, int):
                self.tables.append(data_in.get_table(id=self.table_id))
            else:
                try:
                    tab = data_in.get_table(file=self.table_id)
                except IndexError:
                    tab = data_in.get_table(name=self.table_id)

                self.tables.append(tab)
        else:
            self.tables = data_in.tables

    def _prepare_outputs(self, data_out, outputs):
        if isinstance(data_out, str) or isinstance(data_out, unicode):
            self.file_emulation = True
            if len(self.tables) == 1:
                f = open(data_out, 'w')
                outputs.append(f)
            # data_out is a directory
            else:
                # create output dir if it doesn't exist
                self.create_dir(data_out)
                for table in self.tables:
                    outputs.append(open(os.path.join(data_out, table.name + '.' + self.extension), 'w'))
        # multiple tables - require directory
        elif len(self.tables) > 1 and not (isinstance(data_out, str) or isinstance(data_out, unicode)):
            raise ValueError("Multiple tables, output must be a directory")
        else:
            outputs.append(data_out)

    def write(self, data_in, data_out, *args, **kwargs):
        """

        :param data_in:
        :type data_in: hepconverter.parsers.ParsedData
        :param data_out: filelike object
        :type data_out: file
        :param args:
        :param kwargs:
        """
        self._get_tables(data_in)

        self.file_emulation = False
        outputs = []

        self._prepare_outputs(data_out, outputs)

        for i in xrange(len(self.tables)):
            data_out = outputs[i]
            table = self.tables[i]

            self._write_table(data_out, table)

            if self.file_emulation:
                data_out.close()

    @classmethod
    def _extract_independent_variables(cls, table, headers, data, qualifiers_marks):
        for independent_variable in table.independent_variables:
            name = independent_variable['header']['name']
            if 'units' in independent_variable['header']:
                name += ' IN %s' % independent_variable['header']['units']
            headers.append(name)
            x_data_low = []
            x_data_high = []
            for value in independent_variable['values']:

                if 'high' in value and 'low' in value:
                    x_data_low.append(value['low'])
                    x_data_high.append(value['high'])
                else:
                    x_data_low.append(value['value'])
                    x_data_high.append(value['value'])

            data.append(x_data_low)
            if x_data_high != x_data_low:
                data.append(x_data_high)
                header = headers[-1]
                headers[-1] = header + ' LOW'
                headers.append(header + ' HIGH')
                qualifiers_marks.append(False)

    @classmethod
    def _parse_dependent_variable(cls, dependent_variable, headers, qualifiers, qualifiers_marks, data):
        units = ''
        if 'units' in dependent_variable['header']:
            units = ' IN %s' % dependent_variable['header']['units']
        headers.append(dependent_variable['header']['name'] + units)

        qualifiers_marks.append(True)

        # peek at first value and create empty lists
        y_order = []
        y_data = {'values': []}
        y_order.append(y_data['values'])
        # :TODO: GET ALL ERRORS FROM ALL ENTRIES
        for error in dependent_variable['values'][0].get('errors', []):
            headers.append(error.get('label', 'stat') + ' +')
            qualifiers_marks.append(False)
            headers.append(error.get('label', 'stat') + ' -')
            qualifiers_marks.append(False)

            plus = []
            y_data[error.get('label', 'stat')+'_plus'] = plus
            y_order.append(plus)
            minus = []
            y_data[error.get('label', 'stat')+'_minus'] = minus
            y_order.append(minus)

        for value in dependent_variable['values']:
            y_data['values'].append(value['value'])
            # :TODO: HANDLE SITUATION WHERE ENTRY HAS PARITAL ERRORS (NOT ALL OF THEM)
            if 'errors' not in value:
                for key, val in y_data.items():
                    if key != 'values':
                        val.append(0)
            else:
                for i in xrange(len(value.get('errors', []))):
                    error = value['errors'][i]

                    if 'symerror' in error:
                        error_plus = error['symerror']
                        error_minus = error['symerror']
                    else:
                        error_plus = error['asymerror']['plus']
                        error_minus = error['asymerror']['minus']

                    y_data[error.get('label', 'stat')+'_plus'].append(error_plus)
                    y_data[error.get('label', 'stat')+'_minus'].append(error_minus)

        for entry in y_order:
            data.append(entry)

        for qualifier in dependent_variable.get('qualifiers', []):
            if qualifier['name'] not in qualifiers:
                qualifiers[qualifier['name']] = []
            qualifiers[qualifier['name']].append(qualifier['value'])