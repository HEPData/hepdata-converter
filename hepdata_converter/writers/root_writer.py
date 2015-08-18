# -*- coding: utf-8 -*-
from hepdata_converter.writers.array_writer import ArrayWriter
import ROOT as CERNROOT
__author__ = 'Michał Szostak'


class ROOT(ArrayWriter):
    help = 'Writes to ROOT format (binary) converts tables into files containing TH1 objects'

    def _write_table(self, data_out, table):
        dependent_variable = CERNROOT.TH1F("hscaled", "scaled histogram", 10, 0., 10.)
