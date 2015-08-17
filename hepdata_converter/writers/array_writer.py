import abc
import copy
import csv
import os
from hepdata_converter.common import OptionInitMixin, Option
from hepdata_converter.writers import Writer


class ArrayWriter(Writer):
    __metaclass__  = abc.ABCMeta
    options = {
        'table': Option('table', 't', required=False, variable_mapping='table_id', default=None,
                        help=('Specifies which table should be exported, if not specified all tables will be exported '
                              '(in this case output must be a directory, not a file)')),
    }

    def __init__(self, *args, **kwargs):
        super(ArrayWriter, self).__init__(single_file_output=True, *args, **kwargs)
        self.tables = []
        self.extension = None

    @abc.abstractmethod
    def _write_table(self, data_out, table):
        pass

    def write(self, data_in, data_out, *args, **kwargs):
        """

        :param data_in:
        :type data_in: hepconverter.parsers.ParsedData
        :param data_out: filelike object
        :type data_out: file
        :param args:
        :param kwargs:
        """
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

        file_emulation = False
        outputs = []

        if isinstance(data_out, str) or isinstance(data_out, unicode):
            file_emulation = True
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

        for i in xrange(len(self.tables)):
            data_out = outputs[i]
            table = self.tables[i]

            self._write_table(data_out, table)

            if file_emulation:
                data_out.close()

    @classmethod
    def _extract_independent_variables(cls, table, headers, data, qualifiers_marks):
        for independent_variable in table.independent_variables:
            headers.append(independent_variable['header']['name'] + ' IN %s' % independent_variable['header']['units'])
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