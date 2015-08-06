import copy
import csv
import os
from hepdata_converter.common import OptionInitMixin, Option
from hepdata_converter.writers import Writer


class CSV(Writer, OptionInitMixin):
    options = {
        'table': Option('table', 't', required=False, variable_mapping='table_id', default=None,
                        help=('Specifies which table should be exported, if not specified all tables will be exported '
                              '(in this case output must be a directory, not a file)')),
        'pack': Option('pack', type=bool, default=False, required=False,
                       help=('If specified, dependand variables will be put in one table, instead of creating one '
                             'table per dependant variable in CSV file'))

    }

    def __init__(self, *args, **kwargs):
        super(CSV, self).__init__(single_file_output=True, *args, **kwargs)
        OptionInitMixin.__init__(self, options=kwargs)

        self.tables = []

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
        if self.table_id:
            if isinstance(self.table_id, int):
                self.tables.append(data_in.get_table(id=self.table_id))
            else:
                self.tables.append(data_in.get_table(name=self.table_id))
        else:
            self.tables = data_in.tables

        file_emulation = False
        outputs = []

        if isinstance(data_out, str) or isinstance(data_out, unicode):
            file_emulation = True
            if len(self.tables) == 1:
                f = open(data_out, 'w')
                outputs.append(f)
            else:
                for table in self.tables:
                    outputs.append(open(os.path.join(data_out, table.name+'.csv'), 'w'))
        # multiple tables - require directory
        elif len(self.tables) > 1 and not (isinstance(data_out, str) or isinstance(data_out, unicode)):
            raise ValueError("Multiple tables, output must be a directory")
        else:
            outputs.append(data_out)

        for i in xrange(len(self.tables)):
            data_out = outputs[i]
            table = self.tables[i]

            if self.pack:
                self._write_packed_data(data_out, table)
            else:
                self._write_unpacked_data(data_out, table)

            if file_emulation:
                data_out.close()

    def _extract_independent_variables(self, table, headers, data, qualifiers_marks):
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

    def _write_metadata(self, data_out, table):
        data_out.write("#: name: %s\n" % table.metadata['name'])
        data_out.write("#: description: %s\n" % table.metadata['description'])
        data_out.write("#: data_file: %s\n" % table.metadata['data_file'])

        #license:
        if 'data_license' in table.metadata and table.metadata['data_license']:
            license_text = table.metadata['data_license'].get('name', '') + ' '
            + table.metadata['data_license'].get('url', '') + ' '
            + table.metadata['data_license'].get('url', 'description')

            data_out.write("#: data_license: %s\n" % license_text)

        for keyword in table.metadata.get('keywords', []):
            data_out.write("#: keyword %s: %s\n" % (keyword['name'], ' | '.join([str(val) for val in keyword.get('values', [])])))

    def _write_packed_data(self, data_out, table):
        """This is kind of legacy function - this functionality may be useful for some people, so even though
        now the default of writing CSV is writing unpacked data (divided by independent variable) this method is
        still available and accesable if ```pack``` flag is specified in Writer's options

        :param output: output file like object to which data will be written
        :param table: input table
        :type table: hepdata_converter.parsers.Table
        """
        headers = []
        data = []
        qualifiers_marks = []
        qualifiers = {}

        self._extract_independent_variables(table, headers, data, qualifiers_marks)

        for dependent_variable in table.dependent_variables:
            self._parse_dependent_variable(dependent_variable, headers, qualifiers, qualifiers_marks, data)

        self._write_metadata(data_out, table)
        self._write_csv_data(data_out, qualifiers, qualifiers_marks, headers, data)

    def _write_unpacked_data(self, output, table):
        headers_original = []
        data_original = []
        qualifiers_marks_original = []

        self._write_metadata(output, table)

        self._extract_independent_variables(table, headers_original, data_original, qualifiers_marks_original)

        for dependent_variable in table.dependent_variables:
            qualifiers = {}
            # make a copy of the original list
            headers = list(headers_original)
            data = list(data_original)
            qualifiers_marks = copy.deepcopy(qualifiers_marks_original)
            self._parse_dependent_variable(dependent_variable, headers, qualifiers, qualifiers_marks, data)
            self._write_csv_data(output, qualifiers, qualifiers_marks, headers, data)
            output.write('\n')

    @classmethod
    def _write_qualifiers(cls, csv_writer, qualifiers, qualifiers_marks):
        for qualifier_key in qualifiers:
            row = []
            i = 0
            for qualifier in qualifiers[qualifier_key]:
                for i in xrange(i, len(qualifiers_marks)):
                    if qualifiers_marks[i]:
                        row.append(qualifier)
                        i += 1
                        break
                    else:
                        row.append(None)
            csv_writer.writerow(['#: '+qualifier_key] + row)

    @classmethod
    def _write_csv_data(cls, output, qualifiers, qualifiers_marks, headers, data):
            csv_writer = csv.writer(output, delimiter='\t', lineterminator='\n')

            cls._write_qualifiers(csv_writer, qualifiers, qualifiers_marks)

            csv_writer.writerow(headers)

            for i in xrange(len(data[0])):
                csv_writer.writerow([data[j][i] for j in xrange(len(data)) ])

            return csv_writer

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