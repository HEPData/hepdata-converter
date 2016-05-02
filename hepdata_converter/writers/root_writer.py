# -*- coding: utf-8 -*-
import abc
from hepdata_converter.writers.array_writer import ArrayWriter, ObjectWrapper, ObjectFactory
import ROOT as ROOTModule
import array
import tempfile
import os
from hepdata_converter.writers.utils import error_value_processor

__author__ = 'Michał Szostak'

import logging
logging.basicConfig()
log = logging.getLogger(__name__)

class THFRootClass(ObjectWrapper):
    __metaclass__ = abc.ABCMeta

    _hist_classes = [ROOTModule.TH1F, ROOTModule.TH2F, ROOTModule.TH3F]
    _hist_axes_names = ['x', 'y', 'z']
    _hist_axes_getters = ['GetXaxis','GetYaxis','GetZaxis']
    dim = 0
    core_object = False

    @classmethod
    def match(cls, independent_variables_map, dependent_variable):
        if not ObjectWrapper.match(independent_variables_map, dependent_variable):
            return False
        elif len(independent_variables_map) == cls.dim:
            for independent_variable in independent_variables_map:
                if 'low' not in independent_variable['values'][0] or 'high' not in independent_variable['values'][0]:
                    return False
            return True
        return False

    def _create_empty_hist(self, dependent_var_title, index, yval):

        xval = []
        for i in xrange(self.dim):
            xval.append([])
            i_var = self.independent_variables[i]['values']
            for x in i_var:
                xval[i].append(x['low'])
            xval[i].append(i_var[-1]['high'])

        name = "Hist%sD_y%s_e%s" % (self.dim, self.dependent_variable_index + 1, index)

        # order bin values of independent variables
        xval_ordered = []
        for i in xrange(self.dim):
            xval_ordered.append([])
            for j, x in enumerate(xval[i]):
                if j == 0:
                    x_highest = x
                    xval_ordered[i].append(x)
                else:
                    if x > x_highest:
                        x_highest = x
                        xval_ordered[i].append(x)

        if 1 == self.dim:
            nbinsx = len(xval_ordered[0]) - 1
            binsx = array.array('d', xval_ordered[0])
            hist = self._hist_classes[self.dim - 1](self.sanitize_name(name), '', nbinsx, binsx)

        if 2 == self.dim:
            nbinsx = len(xval_ordered[0]) - 1
            binsx = array.array('d', xval_ordered[0])
            nbinsy = len(xval_ordered[1]) - 1
            binsy = array.array('d', xval_ordered[1])
            hist = self._hist_classes[self.dim - 1](self.sanitize_name(name), '', nbinsx, binsx, nbinsy, binsy)

        if 3 == self.dim:
            nbinsx = len(xval_ordered[0]) - 1
            binsx = array.array('d', xval_ordered[0])
            nbinsy = len(xval_ordered[1]) - 1
            binsy = array.array('d', xval_ordered[1])
            nbinsz = len(xval_ordered[2]) - 1
            binsz = array.array('d', xval_ordered[2])
            hist = self._hist_classes[self.dim - 1](self.sanitize_name(name), '', nbinsx, binsx, nbinsy, binsy, nbinsz, binsz)

        for i in xrange(self.dim):
            name = self.independent_variables[i]['header']['name']
            if 'units' in self.independent_variables[i]['header']:
                name += ' [%s]' % self.independent_variables[i]['header']['units']
            getattr(hist, self._hist_axes_getters[self.dim])().SetTitle(name)

        if self.dim < len(self._hist_classes):
            getattr(hist, self._hist_axes_getters[self.dim])().SetTitle(self.sanitize_name(dependent_var_title))

        for i in xrange(len(yval)):
            hist.Fill(*([self.xval[dim_i][i] for dim_i in xrange(self.dim)] + [yval[i]]))

        return hist

    def _create_hist(self, xval):

        name = "Hist%sD_y%s" % (self.dim, self.dependent_variable_index + 1)
        args = []

        # order bin values of independent variables
        xval_ordered = []
        for i in xrange(self.dim):
            xval_ordered.append([])
            for j, x in enumerate(xval[i]):
                if j == 0:
                    x_highest = x
                    xval_ordered[i].append(x)
                else:
                    if x > x_highest:
                        x_highest = x
                        xval_ordered[i].append(x)

        if 1 == self.dim:
            nbinsx = len(xval_ordered[0]) - 1
            binsx = array.array('d', xval_ordered[0])
            hist = self._hist_classes[self.dim - 1](self.sanitize_name(name), '', nbinsx, binsx)

        if 2 == self.dim:
            nbinsx = len(xval_ordered[0]) - 1
            binsx = array.array('d', xval_ordered[0])
            nbinsy = len(xval_ordered[1]) - 1
            binsy = array.array('d', xval_ordered[1])
            hist = self._hist_classes[self.dim - 1](self.sanitize_name(name), '', nbinsx, binsx, nbinsy, binsy)

        if 3 == self.dim:
            nbinsx = len(xval_ordered[0]) - 1
            binsx = array.array('d', xval_ordered[0])
            nbinsy = len(xval_ordered[1]) - 1
            binsy = array.array('d', xval_ordered[1])
            nbinsz = len(xval_ordered[2]) - 1
            binsz = array.array('d', xval_ordered[2])
            hist = self._hist_classes[self.dim - 1](self.sanitize_name(name), '', nbinsx, binsx, nbinsy, binsy, nbinsz, binsz)

        for i in xrange(self.dim):
            name = self.independent_variables[i]['header']['name']
            if 'units' in self.independent_variables[i]['header']:
                name += ' [%s]' % self.independent_variables[i]['header']['units']
            getattr(hist, self._hist_axes_getters[self.dim])().SetTitle(name)

        if self.dim < len(self._hist_classes):
            name = self.dependent_variable['header']['name']
            if 'units' in self.dependent_variable['header']:
                name += ' [%s]' % self.dependent_variable['header']['units']
            getattr(hist, self._hist_axes_getters[self.dim])().SetTitle(name)

        for i in xrange(len(self.xval[0])):
            hist.Fill(*([self.xval[dim_i][i] for dim_i in xrange(self.dim)] + [self.yval[i]]))
        return hist

    def create_objects(self):
        self.calculate_total_errors()

        error_hists = []
        error_labels = {}
        error_indices = {}

        for value in self.dependent_variable.get('values', []):

            # process the labels to ensure uniqueness
            observed_error_labels = {}
            for error in value.get('errors', []):
                label = error.get('label', '')

                if label not in observed_error_labels:
                    observed_error_labels[label] = 0
                observed_error_labels[label] += 1

                if observed_error_labels[label] > 1:
                    error['label'] = label + '_' + str(observed_error_labels[label])

                # append "_1" to first error label that has a duplicate
                if observed_error_labels[label] == 2:
                    for error1 in value.get('errors', []):
                        error1_label = error1.get('label', 'error')
                        if error1_label == label:
                            error1['label'] = label + "_1"
                            break

            for index, error in enumerate(value.get('errors', []), 1):
                if 'label' not in error:
                    error['label'] = 'error'
                label = error['label']
                if 'symerror' in error and label not in error_labels:
                    error_labels[label] = 'symerror'
                elif 'asymerror' in error and error_labels.get(label, 'symerror') == 'symerror':
                    error_labels[label] = 'asymerror'
                error_indices[index] = label

        yvals = []
        for index in xrange(1, len(error_labels) + 1):
            error_label = error_indices[index]
            if error_labels[error_label] == 'asymerror':
                yval_plus_label = error_label + '_plus'
                yval_plus = []
                yval_minus_label = error_label + '_minus'
                yval_minus = []

                for value in self.dependent_variable.get('values', []):
                    error = filter(lambda x: x.get('label') == error_label, value.get('errors', []))
                    if len(error) == 0:
                        yval_plus.append(0.0)
                        yval_minus.append(0.0)
                    elif 'symerror' in error[0]:
                        err_val = error_value_processor(value['value'], error[0]['symerror'])
                        yval_plus.append(err_val)
                        yval_minus.append(-err_val)
                    elif 'asymerror' in error[0]:
                        err_plus = error_value_processor(value['value'], error[0]['asymerror']['plus'])
                        err_min = error_value_processor(value['value'], error[0]['asymerror']['minus'])
                        yval_plus.append(err_plus)
                        yval_minus.append(err_min)
                    else:
                        yval_plus.append(0.0)
                        yval_minus.append(0.0)

                yvals += [(yval_plus_label, yval_plus, '%s%s' % (index, 'plus')),
                          (yval_minus_label, yval_minus, '%s%s' % (index, 'minus'))]
            else:
                yval = []

                for value in self.dependent_variable.get('values', []):
                    error = filter(lambda x: x.get('label') == error_label, value.get('errors', []))
                    if len(error) == 0:
                        yval.append(0.0)
                    elif 'symerror' in error[0]:
                        err_val = error_value_processor(value['value'], error[0]['symerror'])
                        yval.append(err_val)
                    else:
                        yval.append(0.0)

                yvals += [(error_label, yval, index)]

        for name, vals, index in yvals:
            try:
                error_hists.append(self._create_empty_hist(name, index, vals))
            except:
                log.error("Failed to create empty histogram")

        xval = []
        for i in xrange(self.dim):
            xval.append([])
            i_var = self.independent_variables[i]['values']
            for x in i_var:
                xval[i].append(x['low'])
            xval[i].append(i_var[-1]['high'])

        try:
            hist = self._create_hist(xval)
        except:
            log.error("Failed to create histogram")
            return [] + error_hists

        return [hist] + error_hists


class TH3FRootClass(THFRootClass):
    dim = 3


class TH2FRootClass(THFRootClass):
    dim = 2


class TH1FRootClass(THFRootClass):
    dim = 1


class TGraph2DErrorsClass(ObjectWrapper):
    @classmethod
    def match(cls, independent_variables_map, dependent_variable):
        if not super(TGraph2DErrorsClass, cls).match(independent_variables_map, dependent_variable):
            return False
        if len(independent_variables_map) == 2:
            return True
        return False

    def create_objects(self):
        self.calculate_total_errors()

        self.independent_variable_map.pop(0)
        self.independent_variable_map.pop(0)

        if self.xerr_plus[0] != self.xerr_minus[0] or self.xerr_plus[1] != self.xerr_minus[1] \
                or self.yerr_plus != self.yerr_minus:
            return []

        graph = ROOTModule.TGraph2DErrors(len(self.xval[0]),
                                       array.array('d', self.xval[0]),
                                       array.array('d', self.xval[1]),
                                       array.array('d', self.yval),
                                       array.array('d', self.xerr_plus[0]),
                                       array.array('d', self.xerr_plus[1]),
                                       array.array('d', self.yerr_plus))

        graph.SetName("Graph2D_y%s" % (self.dependent_variable_index + 1))

        xname = self.independent_variables[0]['header']['name']
        if 'units' in self.independent_variables[0]['header']:
            xname += ' [%s]' % self.independent_variables[0]['header']['units']
        yname = self.independent_variables[1]['header']['name']
        if 'units' in self.independent_variables[1]['header']:
            yname += ' [%s]' % self.independent_variables[1]['header']['units']
        zname = self.dependent_variable['header']['name']
        if 'units' in self.dependent_variable['header']:
            zname += ' [%s]' % self.dependent_variable['header']['units']

        graph.GetXaxis().SetTitle(xname)
        graph.GetYaxis().SetTitle(yname)
        graph.GetZaxis().SetTitle(zname)

        return [graph]


class TGraphAsymmErrorsRootClass(ObjectWrapper):
    @classmethod
    def match(cls, independent_variables_map, dependent_variable):
        if not super(TGraphAsymmErrorsRootClass, cls).match(independent_variables_map, dependent_variable):
            return False
        if len(independent_variables_map) == 1:
            return True
        return False

    def create_objects(self):
        self.calculate_total_errors()

        self.independent_variable_map.pop(0)

        graph = ROOTModule.TGraphAsymmErrors(len(self.xval[0]),
                                          array.array('d', self.xval[0]),
                                          array.array('d', self.yval),
                                          array.array('d', self.xerr_minus[0]),
                                          array.array('d', self.xerr_plus[0]),
                                          array.array('d', self.yerr_minus),
                                          array.array('d', self.yerr_plus))

        graph.SetName("Graph1D_y%s" % (self.dependent_variable_index + 1))

        xname = self.independent_variables[0]['header']['name']
        if 'units' in self.independent_variables[0]['header']:
            xname += ' [%s]' % self.independent_variables[0]['header']['units']
        yname = self.dependent_variable['header']['name']
        if 'units' in self.dependent_variable['header']:
            yname += ' [%s]' % self.dependent_variable['header']['units']
        graph.GetXaxis().SetTitle(xname)
        graph.GetYaxis().SetTitle(yname)

        return [graph]


class ROOT(ArrayWriter):
    help = 'Writes to ROOT format (binary) converts tables into files containing TH1 objects'
    class_list = [TH3FRootClass, TH2FRootClass, TH1FRootClass, TGraph2DErrorsClass, TGraphAsymmErrorsRootClass]

    def __init__(self, *args, **kwargs):
        super(ROOT, self).__init__(*args, **kwargs)
        self.extension = 'root'

    def _write_table(self, data_out, table):
        data_out.mkdir(table.name)
        data_out.cd(table.name)

        f = ObjectFactory(self.class_list, table.independent_variables, table.dependent_variables)
        for graph in f.get_next_object():
            graph.title = table.name
            graph.Write()

    def _prepare_outputs(self, data_out, outputs):
        if isinstance(data_out, (str, unicode)):
            self.file_emulation = True
            outputs.append(ROOTModule.TFile.Open(data_out, 'UPDATE'))
        # multiple tables - require directory
        elif isinstance(data_out, ROOTModule.TFile):
            outputs.append(data_out)
        else:  # assume it's a file like object
            self.file_emulation = True
            filename = os.path.join(tempfile.mkdtemp(),'tmp.root')
            outputs.append(ROOTModule.TFile.Open(filename,'RECREATE'))

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
            output.Flush()
            output.ReOpen('read')
            file_size = output.GetSize()
            buff = bytearray(file_size)
            output.ReadBuffer(buff, file_size)
            data_out.write(buff)

        if self.file_emulation:
            filename = output.GetName()
            output.Close()
