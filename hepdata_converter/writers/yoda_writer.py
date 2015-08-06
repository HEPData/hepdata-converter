import csv
from hepdata_converter.writers import Writer


class YODA(Writer):
    def __init__(self, *args, **kwargs):
        super(YODA, self).__init__(single_file_output=True, *args, **kwargs)
        self.table_id = kwargs['table']
        self.table = None

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
        if isinstance(self.table_id, int):
            self.table = data_in.get_table(id=self.table_id)
        else:
            self.table = data_in.get_table(name=self.table_id)

        headers = []
        data = []
        qualifiers_marks = []

        for independent_variable in self.table.independent_variables:
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

        qualifiers = {}


        for dependent_variable in self.table.dependent_variables:
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

        data_out.write("#: name: %s\n" % self.table.metadata['name'])
        data_out.write("#: description: %s\n" % self.table.metadata['description'])
        data_out.write("#: data_file: %s\n" % self.table.metadata['data_file'])

        #license:
        if 'data_license' in self.table.metadata and self.table.metadata['data_license']:
            license_text = self.table.metadata['data_license'].get('name', '') + ' '
            + self.table.metadata['data_license'].get('url', '') + ' '
            + self.table.metadata['data_license'].get('url', 'description')

            data_out.write("#: data_license: %s\n" % license_text)

        for keyword in self.table.metadata.get('keywords', []):
            data_out.write("#: keyword %s: %s\n" % (keyword['name'], ' | '.join([str(val) for val in keyword.get('values', [])])))

        csv_writer = csv.writer(data_out, delimiter='\t', lineterminator='\n')
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

            csv_writer.writerow([qualifier_key] + row)

        csv_writer.writerow(headers)

        for i in xrange(len(data[0])):
            csv_writer.writerow([data[j][i] for j in xrange(len(data)) ])
