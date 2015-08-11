import copy
import csv
from hepdata_converter.writers.array_writer import ArrayWriter


class YODA(ArrayWriter):
    help = 'Writes YODA output for table specified by --table parameter, the output should be defined as ' \
           'filepath to output yoda file'

    def __init__(self, *args, **kwargs):
        super(YODA, self).__init__(single_file_output=True, *args, **kwargs)

    def _write_table(self, data_out, table):
        headers_original = []
        qualifiers_marks_original = []

        for independent_variable in table.independent_variables:
            data_original = []

            self._extract_independent_variables(table, headers_original, data_original, qualifiers_marks_original)

            for dependent_variable in table.dependent_variables:
                where = "BELLE"
                experiment = "2013"
                inspire_id = "I1245023"

                id = "%s_%s_%s" % (where, experiment, inspire_id)

                data_out.write("# BEGIN YODA_SCATTER2D /REF/%s/d%2d-x%2d-y%2d" % id)
                data_out.write("Path=/REF/%s/d01-x01-y01" % id)
                data_out.write("Type=Scatter2D")
                data_out.write("# xval   xerr-   xerr+   yval   yerr-   yerr+")

                headers = list(headers_original)
                qualifiers = {}
                qualifiers_marks = copy(qualifiers_marks_original)
                # make a copy of the original list
                data = list(data_original)

                self._parse_dependent_variable(dependent_variable, headers, qualifiers, qualifiers_marks, data)

                # arguments = [independent_variable]

                # data_out.write("\t".join(arguments))
