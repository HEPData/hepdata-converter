import copy
import csv
from hepdata_converter.common import Option
from hepdata_converter.writers.array_writer import ArrayWriter


class CSV(ArrayWriter):
    help = 'Writes to CSV format, it can write either one table (specified by --table parameter) or all tables from the ' \
           'input file. In the case of one table output must be filepath to the new csv file, in the case of multiple tables ' \
           'the output must be specified to be a directory to which all table files should be written'

    @classmethod
    def options(cls):
        options = ArrayWriter.options()
        options['pack'] = Option('pack', type=bool, default=False, required=False,
                                 help=('If specified, dependent variables will be put in one table, instead of creating one '
                                       'table per dependent variable in CSV file'))
        options['separator'] = Option('separator', type=str, default=',', required=False,
                                      help='Defines separator for CSV file, the default is comma: ","')

        return options

    def __init__(self, *args, **kwargs):
        super(CSV, self).__init__(*args, **kwargs)
        self.extension = 'csv'

    def _write_metadata(self, data_out, table):
        if self.hepdata_doi:
            table_doi = self.hepdata_doi + '/t' + str(table.index)
            data_out.write(f"#: table_doi: {table_doi}\n")
        data_out.write(f"#: name: {table.metadata['name']}\n")
        data_out.write(f"#: description: {table.metadata['description']}\n")
        data_out.write(f"#: data_file: {table.metadata['data_file']}\n")

        #license:
        if 'data_license' in table.metadata and table.metadata['data_license']:
            license_text = (table.metadata['data_license'].get('name') or '') + ' ' + \
                           (table.metadata['data_license'].get('url') or '') + ' ' + \
                           (table.metadata['data_license'].get('description') or '')

            data_out.write(f"#: data_license: {license_text}\n")

        for keyword in table.metadata.get('keywords', []):
            data_out.write(f"#: keyword {keyword['name']}: {' | '.join([str(val) for val in keyword.get('values', [])])}\n")

    def _write_table(self, data_out, table):
        if self.pack:
            self._write_packed_data(data_out, table)
        else:
            self._write_unpacked_data(data_out, table)

    def _write_csv_data(self, output, qualifiers, qualifiers_marks, headers, data):

            lineterminator = '\n'
            self._write_qualifiers(output, qualifiers, qualifiers_marks, self.separator, lineterminator)

            # Use defaults of quotechar='"' and quoting=csv.QUOTE_MINIMAL instead of previous quotechar="'" and quoting=csv.QUOTE_NONNUMERIC.
            csv_writer = csv.writer(output, delimiter=self.separator, lineterminator=lineterminator)
            csv_writer.writerow(headers)

            for i in range(len(data[0])):
                csv_writer.writerow([str(data[j][i]) for j in range(len(data))])

            return csv_writer

    @classmethod
    def _write_qualifiers(cls, writer, qualifiers, qualifiers_marks, field_separator, newline):
        for qualifier_key in qualifiers:
            row = []
            i = 0
            for qualifier in qualifiers[qualifier_key]:
                for i in range(i, len(qualifiers_marks)):
                    if qualifiers_marks[i]:
                        row.append(qualifier)
                        i += 1
                        break
                    else:
                        row.append(None)
            writer.write(str(field_separator.join([str(val) if val is not None else '' for val in
                                                       ['#: ' + qualifier_key] + row]) + newline).replace('utf8', 'replace'))

    def _write_packed_data(self, data_out, table):
        """This is kind of legacy function - this functionality may be useful for some people, so even though
        now the default of writing CSV is writing unpacked data (divided by independent variable) this method is
        still available and accessible if ```pack``` flag is specified in Writer's options

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

        self._extract_independent_variables(table, headers_original, data_original, qualifiers_marks_original)

        self._write_metadata(output, table)

        for dependent_variable in table.dependent_variables:
            qualifiers = {}
            # make a copy of the original list
            headers = list(headers_original)
            data = list(data_original)
            qualifiers_marks = copy.deepcopy(qualifiers_marks_original)
            self._parse_dependent_variable(dependent_variable, headers, qualifiers, qualifiers_marks, data)
            self._write_csv_data(output, qualifiers, qualifiers_marks, headers, data)
            output.write('\n')
