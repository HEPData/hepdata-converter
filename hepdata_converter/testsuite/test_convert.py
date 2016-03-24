import StringIO
import os
import yaml
import hepdata_converter
from hepdata_converter.testsuite import insert_path
from hepdata_converter.testsuite.test_writer import WriterTestSuite


class ConvertTestSuite(WriterTestSuite):
    """Test suite for Parser factory class
    """

    def setUp(self):
        super(ConvertTestSuite, self).setUp()
        self.simple_submission = (
            "*reference: ARXIV:1211.6096 : 2012 # arXiv number\n"
            "*reference: CERN-PH-EP-2012-318 : 2012 # preprint number\n"
            "*reference: JHEP 1303,128 (2013) : 2013 # journal reference\n"
            "*comment: CERN-LHC.  Measurements of the cross section for ZZ ...\n"
            "*dataset:\n"
            "*location: Page 17 of preprint\n"
            "*dscomment: The measured fiducial cross sections.  The first systematic uncertainty is the combined systematic uncertainty excluding luminosity, the second is the luminosity\n"
            "*reackey: P P --> Z0 Z0 X\n"
            "*obskey: SIG\n"
            "*qual: RE : P P --> Z0 < LEPTON+ LEPTON- > Z0 < LEPTON+ LEPTON- > X : P P --> Z0 < LEPTON+ LEPTON- > Z0* < LEPTON+ LEPTON- > X : P P --> Z0 < LEPTON+ LEPTON- > Z0 < NU NUBAR > X\n"
            "*xheader: SQRT(S) IN GEV\n"
            "*yheader: SIG(fiducial) IN FB\n"
            "*data: x : y : y : y\n"
            "7000; 25.4 +3.3,-3.0 (DSYS=+1.2,-1.0,DSYS=1.0:lumi); 29.8 +3.8,-3.5 (DSYS=+1.7,-1.5,DSYS=1.2:lumi); 12.7 +3.1,-2.9 (DSYS=1.7,DSYS=0.5:lumi);\n"
            "*dataend:\n"
        )

        self.correct_submit_output = (
            "additional_resources: []\n"
            "comment: 'CERN-LHC.  Measurements of the cross section for ZZ ...'\n"
            "---\n"
            "additional_resources: []\n"
            "data_file: data1.yaml\n"
            "data_license: {description: null, name: null, url: null}\n"
            "description: 'The measured fiducial cross sections.  The first systematic uncertainty\n"
            "  is the combined systematic uncertainty excluding luminosity, the second is the luminosity.'\n"
            "keywords:\n"
            "- name: reactions\n"
            "  values: ['P P --> Z0 Z0 X']\n"
            "- name: observables\n"
            "  values: ['SIG']\n"
            "- name: energies\n"
            "  values: []\n"
            "location: 'Data from Page 17 of preprint'\n"
            "name: Table 1\n"
        )

        self.correct_table_output = (
            "dependent_variables:\n"
            "- header: {name: SIG(fiducial), units: FB}\n"
            "  qualifiers:\n"
            "  - {name: RE, value: P P --> Z0 < LEPTON+ LEPTON- > Z0 < LEPTON+ LEPTON- > X}\n"
            "  values:\n"
            "  - errors:\n"
            "    - asymerror: {minus: '-3.0', plus: '3.3'}\n"
            "      label: stat\n"
            "    - asymerror: {minus: '-1.0', plus: '1.2'}\n"
            "      label: sys\n"
            "    - {label: 'sys,lumi', symerror: '1.0'}\n"
            "    value: '25.4'\n"
            "- header: {name: SIG(fiducial), units: FB}\n"
            "  qualifiers:\n"
            "  - {name: RE, value: P P --> Z0 < LEPTON+ LEPTON- > Z0* < LEPTON+ LEPTON- > X}\n"
            "  values:\n"
            "  - errors:\n"
            "    - asymerror: {minus: '-3.5', plus: '3.8'}\n"
            "      label: stat\n"
            "    - asymerror: {minus: '-1.5', plus: '1.7'}\n"
            "      label: sys\n"
            "    - {label: 'sys,lumi', symerror: '1.2'}\n"
            "    value: '29.8'\n"
            "- header: {name: SIG(fiducial), units: FB}\n"
            "  qualifiers:\n"
            "  - {name: RE, value: P P --> Z0 < LEPTON+ LEPTON- > Z0 < NU NUBAR > X}\n"
            "  values:\n"
            "  - errors:\n"
            "    - asymerror: {minus: '-2.9', plus: '3.1'}\n"
            "      label: stat\n"
            "    - {label: sys, symerror: '1.7'}\n"
            "    - {label: 'sys,lumi', symerror: '0.5'}\n"
            "    value: '12.7'\n"
            "independent_variables:\n"
            "- header: {name: SQRT(S), units: GEV}\n"
            "  values: ['7000']\n"
        )

    def test_bad_argumets(self):
        self.assertRaises(ValueError, hepdata_converter.convert, None, None)

    def test_submission(self):
        hepdata_converter.convert(StringIO.StringIO(self.simple_submission), self.current_tmp, options={'input_format': 'oldhepdata'})

        with open(os.path.join(self.current_tmp, 'submission.yaml')) as submission_file:
            self.assertEqual(list(yaml.load_all(submission_file)), list(yaml.load_all(self.correct_submit_output)))

    def test_not_implemented_writer(self):
        """This feature is not implemented yet, but to get test coverage it is tested,
        when this functionality is implemented this test case should either be modified or deleted
        """
        self.assertRaises(ValueError, hepdata_converter.convert, None, None, options={'input_format': 'yaml', 'output_format': 'not_implemented'})

    @insert_path('yaml_full')
    def test_same_type_conversion(self, yaml_path):
        hepdata_converter.convert(yaml_path, self.current_tmp, options={'input_format': 'yaml', 'output_format': 'yaml'})
        # exclude data6.yaml and data7.yaml because they are not listed in submission.yaml
        self.assertDirsEqual(yaml_path, self.current_tmp, exclude=['data6.yaml', 'data7.yaml'])