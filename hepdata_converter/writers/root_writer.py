# -*- coding: utf-8 -*-
from math import sqrt
import time
from hepdata_converter.writers.array_writer import ArrayWriter
import rootpy.io
import rootpy.ROOT
import numpy

__author__ = 'Michał Szostak'


class ROOT(ArrayWriter):
    help = 'Writes to ROOT format (binary) converts tables into files containing TH1 objects'

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

    def _write_table(self, data_out, table):
        data_out.mkdir(table.name)
        data_out.cd(table.name)
        for independent_variable in table.independent_variables:
            for dependent_variable in table.dependent_variables:

                xval = []
                yval = []
                xerr_minus = []
                xerr_plus = []
                yerr_minus = []
                yerr_plus = []

                self.calculate_total_errors(independent_variable, xerr_minus, xerr_plus, xval)
                self.calculate_total_errors(dependent_variable, yerr_minus, yerr_plus, yval)

                graph = rootpy.ROOT.TGraphAsymmErrors(len(xval),
                                                      numpy.array(xval, dtype=float),
                                                      numpy.array(yval, dtype=float),
                                                      numpy.array(xerr_minus, dtype=float),
                                                      numpy.array(xerr_plus, dtype=float),
                                                      numpy.array(yerr_minus, dtype=float),
                                                      numpy.array(yerr_plus, dtype=float))

                graph.title = table.name
                graph.xaxis.title = independent_variable['header']['name']
                graph.yaxis.title = dependent_variable['header']['name']
                graph.write()

    def _prepare_outputs(self, data_out, outputs):
        if isinstance(data_out, str) or isinstance(data_out, unicode):
            self.file_emulation = True
            outputs.append(rootpy.io.root_open(data_out, 'w'))
        # multiple tables - require directory
        elif isinstance(data_out, rootpy.ROOT.TFile):
            outputs.append(data_out)
        else: # assume it's a file like object
            self.file_emulation = True
            outputs.append(rootpy.io.TemporaryFile())

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
        output = outputs[0]

        for i in xrange(len(self.tables)):
            table = self.tables[i]

            self._write_table(output, table)

        if data_out != output and hasattr(data_out, 'write'):
            output.flush()
            output.re_open('read')
            buff = bytearray(output.get_size())
            output.read_buffer(buff, output.get_size())
            data_out.write(buff)

        if self.file_emulation:
            output.close()