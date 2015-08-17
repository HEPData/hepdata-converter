import unittest
import os
import tempfile
import shutil
import time
from hepdata_converter.writers import Writer


class WriterTestSuite(unittest.TestCase):
    def tearDown(self):
        shutil.rmtree(self.current_tmp)

    def setUp(self):
        self.submission_data = (
            u"---\n"
            u"---\n"
            u'name: "Table 1"\n'
            u'location: Page 17 of preprint\n'
            u'description: The measured fiducial cross sections. The first systematic uncertainty is the combined systematic uncertainty excluding luminosity, the second is the luminosity\n'
            u'keywords: # used for searching, possibly multiple values for each keyword\n'
            u'  - { name: reactions, values: [P P --> Z0 Z0 X]}\n'
            u'  - { name: observables, values: [SIG]}\n'
            u'  - { name: energies, values: [7000]} # centre-of-mass energy in GeV\n'
            u'data_file: data1.yaml\n'
            u'data_license:\n'
            u'---\n'
            u'name: "Table 9"\n'
            u'description: The observed and expected EmissT distribution in the dielectron SR-Z. The negigible estimated contribution from Z+jets is omitted in these distributions. The last bin contains the overflow.\n'
            u'keywords: # used for searching, possibly multiple values for each keyword\n'
            u'  - { name: energies, values: [8000]} # centre-of-mass energy in GeV\n'
            u'data_file: data9.yaml\n')

        self.table_filename = 'data1.yaml'

        self.table_data = (
            u"---\n"
            u"name: 'data1.yaml' #optional, only required if we have a file with everything in it.\n"
            u"independent_variables:\n"
            u"  - header: {name: SQRT(S), units: GEV}\n"
            u"    values:\n"
            u"      - value: 7000\n"
            u"      - value: 8000\n"
            u"      - value: 9000\n"
            u"dependent_variables:\n"
            u"  - header: {name: SIG(fiducial), units: FB}\n"
            u"    qualifiers:\n"
            u"      - {name: RE, value: P P --> Z0 < LEPTON+ LEPTON- > Z0 < LEPTON+ LEPTON- > X}\n"
            u"    values:\n"
            u"      - value: 25.4\n"
            u"        errors:\n"
            u"          - {asymerror: {plus: 3.3, minus: -3.0}, label: stat}\n"
            u"          - {asymerror: {plus: 1, minus: -1.2}, label: sys}\n"
            u"          - {asymerror: {plus: 1, minus: -1}, label: 'sys,lumi'}\n"
            u"  \n"
            u"      - value: 29.8\n"
            u"        errors:\n"
            u"          - {asymerror: {plus: 3.8, minus: -3.5}, label: stat}\n"
            u"          - {asymerror: {plus: 1.7, minus: -1.5}, label: sys}\n"
            u"          - {symerror: 1.2, label: 'sys,lumi'}\n"
            u"  \n"
            u"      - value: 12.7\n"
            u"        errors:\n"
            u"          - {asymerror:{plus: 3.1, minus: -2.9}, label: stat}\n"
            u"          - {symerror: 1.7, label: sys}\n"
            u"          - {symerror: 0.5, label: 'sys,lumi'}\n")

        self.table_data_2_qual = (
            u"independent_variables:\n"
            u"  - header: {name: 'ETMISS', units: 'GEV'}\n"
            u"    values:\n"
            u"      - {low: 200.0, high: 225.0}\n"
            u"      - {low: 225.0, high: 250.0}\n"
            u"      - {low: 250.0, high: 275.0}\n"
            u"      - {low: 275.0, high: 300.0}\n"
            u"      - {low: 300.0, high: 325.0}\n"
            u"      - {low: 325.0, high: 350.0}\n"
            u"      - {low: 350.0, high: 375.0}\n"
            u"      - {low: 375.0, high: 400.0}\n"
            u"      - {low: 400.0, high: 425.0}\n"
            u"      - {low: 425.0, high: 450.0}\n"
            u"      - {low: 450.0, high: 475.0}\n"
            u"      - {low: 475.0, high: 500.0}\n"
            u"dependent_variables:\n"
            u"  - header: {name: Data}\n"
            u"    qualifiers:\n"
            u"      - {name: SQRT(S), value: '8000.0', units: 'GeV'}\n"
            u"      - {name: EVENTS, value: '25', units: 'GEV'}\n"
            u"    values:\n"
            u"      - value: 0.0\n"
            u"      - value: 6.0\n"
            u"      - value: 1.0\n"
            u"      - value: 1.0\n"
            u"      - value: 1.0\n"
            u"      - value: 2.0\n"
            u"      - value: 1.0\n"
            u"      - value: 1.0\n"
            u"      - value: 0.0\n"
            u"      - value: 1.0\n"
            u"      - value: 0.0\n"
            u"      - value: 2.0\n"
            u"  - header: {name: 'Expected Background'}\n"
            u"    qualifiers:\n"
            u"      - {name: SQRT(S), value: '8000.0', units: 'GeV'}\n"
            u"      - {name: EVENTS, value: '25', units: 'GEV'}\n"
            u"    values:\n"
            u"      - value: 0.0\n"
            u"        errors:\n"
            u"          - {symerror: 0.0}\n"
            u"      - value: 0.95\n"
            u"        errors:\n"
            u"          - {asymerror: {plus: 0.41, minus: -0.51}}\n"
            u"      - value: 0.9\n"
            u"        errors:\n"
            u"          - {asymerror: {plus: 0.41, minus: -0.26}}\n"
            u"      - value: 0.42\n"
            u"        errors:\n"
            u"          - {asymerror: {plus: 0.12, minus: -0.19}}\n"
            u"      - value: 0.34\n"
            u"        errors:\n"
            u"          - {asymerror: {plus: 0.16, minus: -0.15}}\n"
            u"      - value: 0.07\n"
            u"        errors:\n"
            u"          - {asymerror: {plus: 0.19, minus: -0.16}}\n"
            u"      - value: 0.68\n"
            u"        errors:\n"
            u"          - {asymerror: {plus: 0.56, minus: -0.55}}\n"
            u"      - value: 0.17\n"
            u"        errors:\n"
            u"          - {asymerror: {plus: 0.1, minus: -0.15}}\n"
            u"      - value: 0.24\n"
            u"        errors:\n"
            u"          - {asymerror: {plus: 0.11, minus: -0.1}}\n"
            u"      - value: 0.01\n"
            u"        errors:\n"
            u"          - {symerror: 0.08}\n"
            u"      - value: 0.3\n"
            u"        errors:\n"
            u"          - {symerror: 0.33}\n"
            u"      - value: 0.16\n"
            u"        errors:\n"
            u"          - {asymerror: {plus: 0.17, minus: -0.14}}\n"
            u"  - header: {name: 'GGM 700 200 1.5'}\n"
            u"    qualifiers:\n"
            u"      - {name: SQRT(S), value: '8000.0', units: 'GeV'}\n"
            u"      - {name: EVENTS, value: '25', units: 'GEV'}\n"
            u"    values:\n"
            u"      - value: 0.0\n"
            u"      - value: 6.46\n"
            u"      - value: 6.82\n"
            u"      - value: 2.82\n"
            u"      - value: 2.41\n"
            u"      - value: 3.11\n"
            u"      - value: 0.7\n"
            u"      - value: 0.9\n"
            u"      - value: 0.69\n"
            u"      - value: 0.72\n"
            u"      - value: 0.0\n"
            u"      - value: 0.93\n"
            u"  - header: {name: 'GGM 900 600 1.5'}\n"
            u"    qualifiers:\n"
            u"      - {name: SQRT(S), value: '8000.0', units: 'GeV'}\n"
            u"      - {name: EVENTS, value: '25', units: 'GEV'}\n"
            u"    values:\n"
            u"      - value: 0.0\n"
            u"      - value: 0.97\n"
            u"      - value: 1.07\n"
            u"      - value: 1.17\n"
            u"      - value: 1.05\n"
            u"      - value: 1.08\n"
            u"      - value: 1.13\n"
            u"      - value: 1.2\n"
            u"      - value: 1.01\n"
            u"      - value: 0.94\n"
            u"      - value: 0.88\n"
            u"      - value: 4.59\n")

        self.table_filename_2 = 'data9.yaml'

        self.current_tmp = os.path.join(tempfile.gettempdir(), str(int(time.time())))
        os.mkdir(self.current_tmp)

        self.submission_filepath = os.path.join(self.current_tmp, 'submission.yaml')
        with open(self.submission_filepath, 'w') as submission:
            submission.write(self.submission_data)
        with open(os.path.join(self.current_tmp, self.table_filename), 'w') as table:
            table.write(self.table_data)
        with open(os.path.join(self.current_tmp, self.table_filename_2), 'w') as table:
            table.write(self.table_data_2_qual)

    def test_create_dir(self):
        dir_to_create = os.path.join(self.current_tmp, 'tmp')
        Writer.create_dir(dir_to_create)
        self.assertTrue(os.path.exists(dir_to_create))
        # make sure calling this function with existing directory works without errors as well
        Writer.create_dir(dir_to_create)
