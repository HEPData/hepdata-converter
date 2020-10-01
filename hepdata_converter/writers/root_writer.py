# -*- coding: utf-8 -*-
import abc
from hepdata_converter.writers.array_writer import ArrayWriter, ObjectWrapper, ObjectFactory
import ROOT as ROOTModule
import array
import tempfile
import os
from ctypes import c_char_p
from hepdata_converter.writers.utils import error_value_processor

__author__ = 'Michał Szostak'

import logging
logging.basicConfig()
log = logging.getLogger(__name__)

class THFRootClass(ObjectWrapper, metaclass=abc.ABCMeta):
    _hist_axes_names = ['x', 'y', 'z']
    _hist_axes_getters = ['GetXaxis', 'GetYaxis', 'GetZaxis']
    dim = 0
    core_object = False

    def get_hist_classes(self):
        return [ROOTModule.TH1F, ROOTModule.TH2F, ROOTModule.TH3F]

    @classmethod
    def match(cls, independent_variables_map, dependent_variable):
        if not ObjectWrapper.match(independent_variables_map, dependent_variable):
            return False
        elif len(independent_variables_map) == cls.dim:
            for independent_variable in independent_variables_map:
                if not independent_variable['values']:
                    return False
                for value in independent_variable['values']:
                    if 'low' not in value or 'high' not in value:
                        return False
            return True
        return False

    def _create_empty_hist(self, dependent_var_title, index, yval):

        is_number_list = self.is_number_var(self.dependent_variable)

        xval = []
        for i in range(self.dim):
            xval.append([])
            i_var = self.independent_variables[i]['values']
            for ix, x in enumerate(i_var):
                if not is_number_list[ix] and 'labels' not in self.independent_variables[i]:
                    continue  # skip defining bins for non-numeric y values unless alphanumeric bin labels are present
                if x['low'] not in xval[i]:
                    xval[i].append(x['low'])
                if x['high'] not in xval[i]:
                    xval[i].append(x['high'])

        name = "Hist%sD_y%s_e%s" % (self.dim, self.dependent_variable_index + 1, index)

        # order bin values of independent variables
        xval_ordered = []
        for i in range(self.dim):
            xval_ordered.append([])
            xval_ordered[i] = sorted(xval[i])

        if 1 == self.dim:
            nbinsx = len(xval_ordered[0]) - 1
            binsx = array.array('d', xval_ordered[0])
            hist = self.get_hist_classes()[self.dim - 1](self.sanitize_name(name), '', nbinsx, binsx)

        if 2 == self.dim:
            nbinsx = len(xval_ordered[0]) - 1
            binsx = array.array('d', xval_ordered[0])
            nbinsy = len(xval_ordered[1]) - 1
            binsy = array.array('d', xval_ordered[1])
            hist = self.get_hist_classes()[self.dim - 1](self.sanitize_name(name), '', nbinsx, binsx, nbinsy, binsy)

        if 3 == self.dim:
            nbinsx = len(xval_ordered[0]) - 1
            binsx = array.array('d', xval_ordered[0])
            nbinsy = len(xval_ordered[1]) - 1
            binsy = array.array('d', xval_ordered[1])
            nbinsz = len(xval_ordered[2]) - 1
            binsz = array.array('d', xval_ordered[2])
            hist = self.get_hist_classes()[self.dim - 1](self.sanitize_name(name), '', nbinsx, binsx, nbinsy, binsy, nbinsz, binsz)

        for i in range(self.dim):
            name = self.independent_variables[i]['header']['name']
            if 'units' in self.independent_variables[i]['header']:
                name += ' [%s]' % self.independent_variables[i]['header']['units']
            name = name.encode('ascii', 'replace').decode()
            getattr(hist, self._hist_axes_getters[i])().SetTitle(name)
            if 'labels' in self.independent_variables[i]:
                for ibin, label in enumerate(self.independent_variables[i]['labels']):
                    getattr(hist, self._hist_axes_getters[i])().SetBinLabel(ibin + 1, label)

        if self.dim < len(self.get_hist_classes()):
            getattr(hist, self._hist_axes_getters[self.dim])().SetTitle(self.sanitize_name(dependent_var_title))

        for i in range(len(yval)):
            hist.Fill(*([self.xval[dim_i][i] for dim_i in range(self.dim)] + [yval[i]]))

        return hist

    def _create_hist(self, xval):

        name = "Hist%sD_y%s" % (self.dim, self.dependent_variable_index + 1)
        args = []

        # order bin values of independent variables
        xval_ordered = []
        for i in range(self.dim):
            xval_ordered.append([])
            xval_ordered[i] = sorted(xval[i])

        if 1 == self.dim:
            nbinsx = len(xval_ordered[0]) - 1
            binsx = array.array('d', xval_ordered[0])
            hist = self.get_hist_classes()[self.dim - 1](self.sanitize_name(name), '', nbinsx, binsx)

        if 2 == self.dim:
            nbinsx = len(xval_ordered[0]) - 1
            binsx = array.array('d', xval_ordered[0])
            nbinsy = len(xval_ordered[1]) - 1
            binsy = array.array('d', xval_ordered[1])
            hist = self.get_hist_classes()[self.dim - 1](self.sanitize_name(name), '', nbinsx, binsx, nbinsy, binsy)

        if 3 == self.dim:
            nbinsx = len(xval_ordered[0]) - 1
            binsx = array.array('d', xval_ordered[0])
            nbinsy = len(xval_ordered[1]) - 1
            binsy = array.array('d', xval_ordered[1])
            nbinsz = len(xval_ordered[2]) - 1
            binsz = array.array('d', xval_ordered[2])
            hist = self.get_hist_classes()[self.dim - 1](self.sanitize_name(name), '', nbinsx, binsx, nbinsy, binsy, nbinsz, binsz)

        for i in range(self.dim):
            name = self.independent_variables[i]['header']['name']
            if 'units' in self.independent_variables[i]['header']:
                name += ' [%s]' % self.independent_variables[i]['header']['units']
            name = name.encode('ascii', 'replace').decode()
            getattr(hist, self._hist_axes_getters[i])().SetTitle(name)
            if 'labels' in self.independent_variables[i]: # set alphanumeric bin labels
                for ibin, label in enumerate(self.independent_variables[i]['labels']):
                    getattr(hist, self._hist_axes_getters[i])().SetBinLabel(ibin + 1, label)

        if self.dim < len(self.get_hist_classes()):
            name = self.dependent_variable['header']['name']
            if 'units' in self.dependent_variable['header']:
                name += ' [%s]' % self.dependent_variable['header']['units']
            name = name.encode('ascii', 'replace').decode()
            getattr(hist, self._hist_axes_getters[self.dim])().SetTitle(name)

        for i in range(len(self.xval[0])):
            hist.Fill(*([self.xval[dim_i][i] for dim_i in range(self.dim)] + [self.yval[i]]))
        return hist

    def create_objects(self):
        self.calculate_total_errors()

        error_hists = []
        error_labels = {}
        error_indices = {}
        index = 0

        is_number_list = self.is_number_var(self.dependent_variable)

        for i, value in enumerate(self.dependent_variable.get('values', [])):

            if not is_number_list[i]: continue # skip non-numeric y values

            # process the error labels to ensure uniqueness
            ArrayWriter.process_error_labels(value)

            for error in value.get('errors', []):
                if 'label' not in error:
                    error['label'] = 'error'
                label = error['label']
                if label not in error_labels:
                    index += 1
                    error_indices[index] = label
                if 'symerror' in error and label not in error_labels:
                    error_labels[label] = 'symerror'
                elif 'asymerror' in error and error_labels.get(label, 'symerror') == 'symerror':
                    error_labels[label] = 'asymerror'

        yvals = []
        for index in range(1, len(error_labels) + 1):
            error_label = error_indices[index]
            if error_labels[error_label] == 'asymerror':
                yval_plus_label = error_label + '_plus'
                yval_plus = []
                yval_minus_label = error_label + '_minus'
                yval_minus = []

                for i, value in enumerate(self.dependent_variable.get('values', [])):
                    if not is_number_list[i]: continue # skip non-numeric y values
                    error = [x for x in value.get('errors', []) if x.get('label') == error_label]
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

                for i, value in enumerate(self.dependent_variable.get('values', [])):
                    if not is_number_list[i]: continue # skip non-numeric y values
                    error = [x for x in value.get('errors', []) if x.get('label') == error_label]
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
        for i in range(self.dim):
            xval.append([])
            i_var = self.independent_variables[i]['values']
            for ix, x in enumerate(i_var):
                if not is_number_list[ix] and 'labels' not in self.independent_variables[i]:
                    continue  # skip defining bins for non-numeric y values unless alphanumeric bin labels are present
                if x['low'] not in xval[i]:
                    xval[i].append(x['low'])
                if x['high'] not in xval[i]:
                    xval[i].append(x['high'])

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
            for independent_variable in independent_variables_map:
                if not independent_variable['values']:
                    return False
            return True
        return False

    def create_objects(self):
        self.calculate_total_errors()

        # check that errors are symmetric (within a tolerance to allow for numerical rounding)
        tol = 1e-15
        if any([a - b > tol for a, b in zip(self.xerr_plus[0], self.xerr_minus[0])]) or \
           any([a - b > tol for a, b in zip(self.xerr_plus[1], self.xerr_minus[1])]) or \
           any([a - b > tol for a, b in zip(self.yerr_plus, self.yerr_minus)]):
            return []

        if len(self.xval[0]):
            graph = ROOTModule.TGraph2DErrors(len(self.xval[0]),
                                           array.array('d', self.xval[0]),
                                           array.array('d', self.xval[1]),
                                           array.array('d', self.yval),
                                           array.array('d', self.xerr_plus[0]),
                                           array.array('d', self.xerr_plus[1]),
                                           array.array('d', self.yerr_plus))
        else:
            return []

        graph.SetName("Graph2D_y%s" % (self.dependent_variable_index + 1))

        xname = self.independent_variables[0]['header']['name']
        if 'units' in self.independent_variables[0]['header']:
            xname += ' [%s]' % self.independent_variables[0]['header']['units']
        xname = xname.encode('ascii', 'replace').decode()
        yname = self.independent_variables[1]['header']['name']
        if 'units' in self.independent_variables[1]['header']:
            yname += ' [%s]' % self.independent_variables[1]['header']['units']
        yname = yname.encode('ascii', 'replace').decode()
        zname = self.dependent_variable['header']['name']
        if 'units' in self.dependent_variable['header']:
            zname += ' [%s]' % self.dependent_variable['header']['units']
        zname = zname.encode('ascii', 'replace').decode()

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
            for independent_variable in independent_variables_map:
                if not independent_variable['values']:
                    return False
            return True
        return False

    def create_objects(self):
        self.calculate_total_errors()

        if len(self.xval[0]):
            graph = ROOTModule.TGraphAsymmErrors(len(self.xval[0]),
                                              array.array('d', self.xval[0]),
                                              array.array('d', self.yval),
                                              array.array('d', self.xerr_minus[0]),
                                              array.array('d', self.xerr_plus[0]),
                                              array.array('d', self.yerr_minus),
                                              array.array('d', self.yerr_plus))
        else:
            return []

        graph.SetName("Graph1D_y%s" % (self.dependent_variable_index + 1))

        xname = self.independent_variables[0]['header']['name']
        if 'units' in self.independent_variables[0]['header']:
            xname += ' [%s]' % self.independent_variables[0]['header']['units']
        xname = xname.encode('ascii', 'replace').decode()
        yname = self.dependent_variable['header']['name']
        if 'units' in self.dependent_variable['header']:
            yname += ' [%s]' % self.dependent_variable['header']['units']
        yname = yname.encode('ascii', 'replace').decode()
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
        data_out.mkdir(table.name.replace('/','-').replace('$', '').replace('\\',''))
        data_out.cd(table.name.replace('/','-').replace('$', '').replace('\\',''))

        # if no independent variables, use bins of unit width and centred on integers (1, 2, 3, etc.)
        if not table.independent_variables and table.dependent_variables:
            if table.dependent_variables[0]['values']:
                table.independent_variables.append({'header': {'name': 'Bin number'}, 'values': []})
                for i, value in enumerate(table.dependent_variables[0]['values']):
                    table.independent_variables[0]['values'].append({'low': i+0.5, 'high': i+1.5})

        # if any non-numeric independent variable values, use bins of unit width and centred on integers (1, 2, 3, etc.)
        # store original variables as alphanumeric labels to be passed to ROOT histograms
        for ii, independent_variable in enumerate(table.independent_variables):
            if False in ObjectWrapper.is_number_var(independent_variable):
                independent_variable_bins = \
                    {'header': {'name': independent_variable['header']['name'] + ' bin'},
                     'values': [], 'labels': []}
                for i, value in enumerate(independent_variable['values']):
                    independent_variable_bins['values'].append({'low': i + 0.5, 'high': i + 1.5})
                    if 'value' in value:
                        independent_variable_bins['labels'].append(str(value['value']))
                    else:
                        independent_variable_bins['labels'].append(str(value['low']) + '-' + str(value['high']))
                table.independent_variables[ii] = independent_variable_bins

        if self.hepdata_doi:
            table_doi = 'doi:' + self.hepdata_doi + '/t' + str(table.index)
        else:
            table_doi = table.name
        f = ObjectFactory(self.class_list, table.independent_variables, table.dependent_variables)
        for graph in f.get_next_object():
            graph.SetTitle(table_doi)
            graph.Write()

    def _prepare_outputs(self, data_out, outputs):
        """ Open a ROOT file with option 'RECREATE' to create a new file (the file will
        be overwritten if it already exists), and using the ZLIB compression algorithm
        (with compression level 1) for better compatibility with older ROOT versions
        (see https://root.cern.ch/doc/v614/release-notes.html#important-notice ).

        :param data_out:
        :param outputs:
        :return:
        """
        compress = ROOTModule.ROOT.CompressionSettings(ROOTModule.ROOT.kZLIB, 1)
        if isinstance(data_out, str):
            self.file_emulation = True
            outputs.append(ROOTModule.TFile.Open(data_out, 'RECREATE', '', compress))
        # multiple tables - require directory
        elif isinstance(data_out, ROOTModule.TFile):
            outputs.append(data_out)
        else:  # assume it's a file like object
            self.file_emulation = True
            filename = os.path.join(tempfile.mkdtemp(),'tmp.root')
            outputs.append(ROOTModule.TFile.Open(filename, 'RECREATE', '', compress))

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
        for i in range(len(self.tables)):
            table = self.tables[i]

            self._write_table(output, table)

        if data_out != output and hasattr(data_out, 'write'):
            output.Flush()
            output.ReOpen('read')
            file_size = output.GetSize()
            buff = bytes(file_size)
            c_buff = c_char_p(buff)
            output.ReadBuffer(c_buff, file_size)
            data_out.write(buff)

        if self.file_emulation:
            filename = output.GetName()
            output.Close()
