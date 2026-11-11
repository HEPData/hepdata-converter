import json
from pathlib import Path
import subprocess
import sys

import ROOT
import yaml

from hepdata_converter import convert
from hepdata_converter.testsuite.test_writer import WriterTestSuite


class RaggedArrayWriterTestCase(WriterTestSuite):
    formats = ('root', 'yoda', 'yoda.h5', 'yoda1')

    def axis(self, count=3):
        return {'header': {'name': 'x'}, 'values': [
            {'low': index, 'high': index + 1} for index in range(count)
        ]}

    def column(self, values, tag=None, custom_identifier=None):
        column = {'header': {'name': 'y'}, 'values': [
            {'value': value, 'errors': [
                {'label': 'shape', 'asymerror': {'minus': -0.5, 'plus': 0.75}},
            ]} for value in values
        ]}
        qualifiers = []
        if tag is not None:
            qualifiers.append({'name': 'tag', 'value': tag})
        if custom_identifier is not None:
            qualifiers.append({'name': 'Custom Rivet identifier', 'value': custom_identifier})
        if qualifiers:
            column['qualifiers'] = qualifiers
        return column

    def write_submission(self, tables):
        folder = Path(self.current_tmp)
        metadata = []
        for index, table in enumerate(tables, start=1):
            filename = 'data%s.yaml' % index
            metadata.append({
                'name': 'Table %s' % index, 'description': 'Legacy unequal columns',
                'data_file': filename, 'keywords': [],
            })
            (folder / filename).write_text(yaml.safe_dump(table))
        (folder / 'submission.yaml').write_text(yaml.safe_dump_all(metadata))
        return folder

    def export(self, folder, format_):
        output = str(folder / ('output.' + format_))
        convert(str(folder), output, options={
            'output_format': format_, 'validator_schema_version': '0.1.0',
            'yoda_keep_qualifiers': True,
        })
        return output

    def read_yoda(self, output, format_, positions=()):
        # Native yoda.read changes the effective locale. Keep it out of the test runner.
        script = '''
import json
import sys
import yoda

entries = {}
for path, obj in yoda.read(sys.argv[1]).items():
    if sys.argv[2] == 'yoda1':
        points = obj.points()
        result = {'values': [point.y() for point in points],
                  'errors': [list(point.yErrs()) for point in points],
                  'positions': [point.x() for point in points]}
    else:
        bins = [obj.bin(index + 1) for index in range(obj.numBins())]
        result = {'values': [estimate.val() for estimate in bins],
                  'errors': [list(estimate.err('shape')) for estimate in bins],
                  'samples': [obj.bin(obj.indexAt(position)).val()
                              for position in json.loads(sys.argv[3])]}
    result['tag'] = obj.annotation('tag') if obj.hasAnnotation('tag') else None
    entries[path] = result
print(json.dumps(entries))
'''
        return json.loads(subprocess.check_output(
            [sys.executable, '-c', script, output, format_, json.dumps(positions)],
            universal_newlines=True,
        ))

    def assert_yoda_values(self, obj, values, format_):
        self.assertEqual(len(obj['values']), len(values))
        for actual, expected in zip(obj['values'], values):
            self.assertAlmostEqual(actual, expected)
        errors = [0.5, 0.75] if format_ == 'yoda1' else [-0.5, 0.75]
        self.assertEqual(obj['errors'], [errors] * len(values))

    def test_bad_columns_do_not_abort_valid_columns_or_later_tables(self):
        folder = self.write_submission([
            {'independent_variables': [self.axis()], 'dependent_variables': [
                self.column([91, 92], tag='omit-short'),
                self.column([0, 4, 8], tag='keep-second'),
                self.column([], tag='omit-empty'),
                self.column([93, 94, 95, 96], tag='omit-long'),
                self.column([3, 0, 9], tag='keep-fifth', custom_identifier='kept-custom'),
            ]},
            {'independent_variables': [self.axis()],
             'dependent_variables': [self.column([97])]},
            {'independent_variables': [self.axis()],
             'dependent_variables': [self.column([1, 2, 3])]},
        ])
        for format_ in self.formats:
            with self.subTest(format_=format_):
                output = self.export(folder, format_)
                if format_ == 'root':
                    root_file = ROOT.TFile.Open(output)
                    try:
                        table = root_file.Get('Table 1')
                        names = [key.GetName() for key in table.GetListOfKeys()]
                        self.assertTrue(names)
                        self.assertTrue(all('_y2' in name or '_y5' in name for name in names))
                        for column, expected in ((2, [0, 4, 8]), (5, [3, 0, 9])):
                            graph = table.Get('Graph1D_y%s' % column)
                            self.assertEqual(graph.GetN(), 3)
                            for index, value in enumerate(expected):
                                self.assertEqual(graph.GetY()[index], value)
                                self.assertEqual(graph.GetErrorYlow(index), 0.5)
                                self.assertEqual(graph.GetErrorYhigh(index), 0.75)
                            histogram = table.Get('Hist1D_y%s' % column)
                            self.assertEqual(histogram.GetNbinsX(), 3)
                            self.assertEqual([histogram.GetBinContent(i) for i in (1, 2, 3)], expected)
                        self.assertEqual(root_file.Get('Table 2').GetListOfKeys().GetSize(), 0)
                        self.assertEqual(root_file.Get('Table 3/Graph1D_y1').GetN(), 3)
                    finally:
                        root_file.Close()
                else:
                    entries = self.read_yoda(output, format_)
                    prefix = '/REF/RIVET_ANALYSIS_NAME/'
                    self.assertEqual(set(entries), {
                        prefix + 'd01-x01-y02', prefix + 'kept-custom', prefix + 'd03-x01-y01',
                    })
                    second = entries[prefix + 'd01-x01-y02']
                    fifth = entries[prefix + 'kept-custom']
                    self.assertEqual(second['tag'], 'keep-second')
                    self.assertEqual(fifth['tag'], 'keep-fifth')
                    self.assert_yoda_values(second, [0, 4, 8], format_)
                    self.assert_yoda_values(fifth, [3, 0, 9], format_)
                    self.assert_yoda_values(entries[prefix + 'd03-x01-y01'], [1, 2, 3], format_)

    def test_ragged_categorical_column_is_omitted(self):
        folder = self.write_submission([{
            'independent_variables': [{'header': {'name': 'category'}, 'values': [
                {'value': label} for label in ('forward', 'central', 'backward')
            ]}],
            'dependent_variables': [self.column([91]), self.column([0, 4, 8])],
        }])
        for format_ in self.formats:
            with self.subTest(format_=format_):
                output = self.export(folder, format_)
                if format_ == 'root':
                    root_file = ROOT.TFile.Open(output)
                    try:
                        self.assertFalse(root_file.Get('Table 1/Hist1D_y1'))
                        histogram = root_file.Get('Table 1/Hist1D_y2')
                        self.assertEqual(histogram.GetNbinsX(), 3)
                        self.assertEqual(histogram.GetXaxis().GetBinLabel(3), 'backward')
                        self.assertEqual([histogram.GetBinContent(i) for i in (1, 2, 3)], [0, 4, 8])
                    finally:
                        root_file.Close()
                else:
                    entries = self.read_yoda(output, format_)
                    self.assertEqual(list(entries), ['/REF/RIVET_ANALYSIS_NAME/d01-x01-y02'])
                    self.assert_yoda_values(next(iter(entries.values())), [0, 4, 8], format_)

    def test_mismatch_on_second_axis_does_not_abort_later_table(self):
        folder = self.write_submission([
            {'independent_variables': [self.axis(), self.axis(2)],
             'dependent_variables': [self.column([91, 92, 93])]},
            {'independent_variables': [self.axis()],
             'dependent_variables': [self.column([0, 4, 8])]},
        ])
        for format_ in self.formats:
            with self.subTest(format_=format_):
                output = self.export(folder, format_)
                if format_ == 'root':
                    root_file = ROOT.TFile.Open(output)
                    try:
                        self.assertEqual(root_file.Get('Table 1').GetListOfKeys().GetSize(), 0)
                        self.assertEqual(root_file.Get('Table 2/Graph1D_y1').GetN(), 3)
                    finally:
                        root_file.Close()
                else:
                    entries = self.read_yoda(output, format_)
                    self.assertEqual(list(entries), ['/REF/RIVET_ANALYSIS_NAME/d02-x01-y01'])
                    self.assert_yoda_values(next(iter(entries.values())), [0, 4, 8], format_)

    def test_explicit_missing_cells_keep_existing_numeric_mask(self):
        folder = self.write_submission([{
            'independent_variables': [self.axis()],
            'dependent_variables': [self.column(['-', 0, 4])],
        }])
        for format_ in self.formats:
            with self.subTest(format_=format_):
                output = self.export(folder, format_)
                if format_ == 'root':
                    root_file = ROOT.TFile.Open(output)
                    try:
                        graph = root_file.Get('Table 1/Graph1D_y1')
                        self.assertEqual(graph.GetN(), 2)
                        self.assertEqual([graph.GetX()[i] for i in (0, 1)], [1.5, 2.5])
                        self.assertEqual([graph.GetY()[i] for i in (0, 1)], [0, 4])
                        self.assertEqual(graph.GetErrorYlow(0), 0.5)
                        self.assertEqual(graph.GetErrorYhigh(0), 0.75)
                    finally:
                        root_file.Close()
                else:
                    entries = self.read_yoda(output, format_, positions=(1.5, 2.5))
                    self.assertEqual(list(entries), ['/REF/RIVET_ANALYSIS_NAME/d01-x01-y01'])
                    obj = next(iter(entries.values()))
                    self.assert_yoda_values(obj, [0, 4], format_)
                    if format_ == 'yoda1':
                        self.assertEqual(obj['positions'], [1.5, 2.5])
                    else:
                        self.assertEqual(obj['samples'], [0, 4])
