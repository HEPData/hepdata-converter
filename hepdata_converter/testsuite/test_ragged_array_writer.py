import json
import math
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
import math
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
        bins = obj.bins()
        result = {'values': [estimate.val() for estimate in bins],
                  'errors': [None if math.isnan(estimate.val()) else list(estimate.err('shape')) for estimate in bins],
                  'masked': [estimate.isMasked() for estimate in bins],
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
        # Binned YODA preserves empty cells as NaN; Scatter stores measured points only.
        measured = [(value, error) for value, error in zip(obj['values'], obj['errors'])
                    if format_ == 'yoda1' or not math.isnan(value)]
        self.assertEqual(len(measured), len(values))
        for (actual, _), expected in zip(measured, values):
            self.assertAlmostEqual(actual, expected)
        errors = [0.5, 0.75] if format_ == 'yoda1' else [-0.5, 0.75]
        self.assertEqual([error for _, error in measured], [errors] * len(values))

    def test_missing_suffixes_preserve_available_bins_and_column_identifiers(self):
        folder = self.write_submission([
            {'independent_variables': [self.axis()], 'dependent_variables': [
                self.column([91, 92], tag='keep-short'),
                self.column([0, 4, 8], tag='keep-second'),
                self.column([], tag='omit-empty'),
                self.column([93, 94, 95, 96], tag='keep-long'),
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
                        self.assertTrue(all(any('_y%s' % column in name for column in (1, 2, 3, 4, 5))
                                            for name in names))
                        for column, expected in ((1, [91, 92]), (2, [0, 4, 8]),
                                                 (4, [93, 94, 95]), (5, [3, 0, 9])):
                            graph = table.Get('Graph1D_y%s' % column)
                            self.assertEqual(graph.GetN(), len(expected))
                            for index, value in enumerate(expected):
                                self.assertEqual(graph.GetY()[index], value)
                                self.assertEqual(graph.GetErrorYlow(index), 0.5)
                                self.assertEqual(graph.GetErrorYhigh(index), 0.75)
                            histogram = table.Get('Hist1D_y%s' % column)
                            self.assertEqual(histogram.GetNbinsX(), 3)
                            self.assertEqual(histogram.GetEntries(), len(expected))
                            self.assertEqual([histogram.GetBinContent(i + 1)
                                              for i in range(len(expected))], expected)
                        self.assertEqual(table.Get('Hist1D_y3').GetNbinsX(), 3)
                        self.assertEqual(table.Get('Hist1D_y3').GetEntries(), 0)
                        self.assertEqual(root_file.Get('Table 2/Graph1D_y1').GetN(), 1)
                        self.assertEqual(root_file.Get('Table 2/Graph1D_y1').GetY()[0], 97)
                        self.assertEqual(root_file.Get('Table 3/Graph1D_y1').GetN(), 3)
                    finally:
                        root_file.Close()
                else:
                    entries = self.read_yoda(output, format_)
                    prefix = '/REF/RIVET_ANALYSIS_NAME/'
                    self.assertEqual(set(entries), {
                        prefix + 'd01-x01-y01', prefix + 'd01-x01-y02', prefix + 'd01-x01-y04',
                        prefix + 'd01-x01-y03', prefix + 'kept-custom', prefix + 'd02-x01-y01', prefix + 'd03-x01-y01',
                    })
                    second = entries[prefix + 'd01-x01-y02']
                    fifth = entries[prefix + 'kept-custom']
                    self.assertEqual(second['tag'], 'keep-second')
                    self.assertEqual(fifth['tag'], 'keep-fifth')
                    self.assert_yoda_values(entries[prefix + 'd01-x01-y01'], [91, 92], format_)
                    self.assert_yoda_values(entries[prefix + 'd01-x01-y04'], [93, 94, 95], format_)
                    self.assert_yoda_values(entries[prefix + 'd02-x01-y01'], [97], format_)
                    self.assert_yoda_values(second, [0, 4, 8], format_)
                    self.assert_yoda_values(fifth, [3, 0, 9], format_)
                    self.assert_yoda_values(entries[prefix + 'd03-x01-y01'], [1, 2, 3], format_)

    def test_ragged_categorical_column_preserves_available_labels(self):
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
                        short = root_file.Get('Table 1/Hist1D_y1')
                        self.assertEqual(short.GetNbinsX(), 3)
                        self.assertEqual(short.GetXaxis().GetBinLabel(1), 'forward')
                        self.assertEqual(short.GetBinContent(1), 91)
                        histogram = root_file.Get('Table 1/Hist1D_y2')
                        self.assertEqual(histogram.GetNbinsX(), 3)
                        self.assertEqual(histogram.GetXaxis().GetBinLabel(3), 'backward')
                        self.assertEqual([histogram.GetBinContent(i) for i in (1, 2, 3)], [0, 4, 8])
                    finally:
                        root_file.Close()
                else:
                    entries = self.read_yoda(output, format_)
                    self.assertEqual(set(entries), {'/REF/RIVET_ANALYSIS_NAME/d01-x01-y01',
                                                   '/REF/RIVET_ANALYSIS_NAME/d01-x01-y02'})
                    self.assert_yoda_values(entries['/REF/RIVET_ANALYSIS_NAME/d01-x01-y01'], [91], format_)
                    self.assert_yoda_values(entries['/REF/RIVET_ANALYSIS_NAME/d01-x01-y02'], [0, 4, 8], format_)

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
                        histogram = root_file.Get('Table 1/Hist2D_y1')
                        self.assertEqual(histogram.GetNbinsX(), 3)
                        self.assertEqual(histogram.GetNbinsY(), 2)
                        self.assertEqual(histogram.GetBinContent(histogram.FindBin(0.5, 0.5)), 91)
                        self.assertEqual(histogram.GetBinContent(histogram.FindBin(1.5, 1.5)), 92)
                        self.assertEqual(root_file.Get('Table 2/Graph1D_y1').GetN(), 3)
                    finally:
                        root_file.Close()
                else:
                    entries = self.read_multidimensional_yoda(output, format_)
                    self.assertEqual(entries, {'values': [91, 92], 'errors':
                                              ([[0.5, 0.75]] * 2 if format_ == 'yoda1'
                                               else [[-0.5, 0.75]] * 2)})

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

    def read_multidimensional_yoda(self, output, format_):
        script = """
import json
import math
import sys
import yoda
obj = yoda.read(sys.argv[1])['/REF/RIVET_ANALYSIS_NAME/d01-x01-y01']
if sys.argv[2] == 'yoda1':
    points = obj.points()
    assert [(point.x(), point.y()) for point in points] == [(0.5, 0.5), (1.5, 1.5)]
    values = [point.z() for point in points]
    errors = [list(point.zErrs()) for point in points]
else:
    assert obj.xEdges() == [0.0, 1.0, 2.0, 3.0]
    assert obj.yEdges() == [0.0, 1.0, 2.0]
    bins = [obj.bin(obj.indexAt(value, value)) for value in (0.5, 1.5)]
    values = [estimate.val() for estimate in bins]
    errors = [list(estimate.err('shape')) for estimate in bins]
print(json.dumps({'values': values, 'errors': errors}))
"""
        return json.loads(subprocess.check_output(
            [sys.executable, '-c', script, output, format_], universal_newlines=True))

    def test_interior_nonnumeric_hole_and_missing_suffix_use_same_coordinates(self):
        folder = self.write_submission([{
            'independent_variables': [self.axis(5)],
            'dependent_variables': [self.column([3, '-', 0, 9])],
        }])
        for format_ in self.formats:
            with self.subTest(format_=format_):
                output = self.export(folder, format_)
                if format_ == 'root':
                    root_file = ROOT.TFile.Open(output)
                    try:
                        graph = root_file.Get('Table 1/Graph1D_y1')
                        self.assertEqual(graph.GetN(), 3)
                        self.assertEqual([graph.GetX()[i] for i in range(3)], [0.5, 2.5, 3.5])
                        self.assertEqual([graph.GetY()[i] for i in range(3)], [3, 0, 9])
                        self.assertEqual([graph.GetErrorYlow(i) for i in range(3)], [0.5] * 3)
                        self.assertEqual([graph.GetErrorYhigh(i) for i in range(3)], [0.75] * 3)
                        self.assertEqual(root_file.Get('Table 1/Hist1D_y1').GetXaxis().GetXmax(), 5)
                    finally:
                        root_file.Close()
                else:
                    entry = self.read_yoda(output, format_, positions=(0.5, 2.5, 3.5))[
                        '/REF/RIVET_ANALYSIS_NAME/d01-x01-y01']
                    self.assert_yoda_values(entry, [3, 0, 9], format_)
                    if format_ == 'yoda1':
                        self.assertEqual(entry['positions'], [0.5, 2.5, 3.5])
                    else:
                        self.assertEqual(entry['samples'], [3, 0, 9])

    def test_missing_value_entries_do_not_fabricate_measurements(self):
        from copy import deepcopy
        from hepdata_converter.writers.array_writer import ObjectFactory
        from hepdata_converter.writers.root_writer import ROOT as RootWriter
        from hepdata_converter.writers.yoda_writer import YODA

        axes = [self.axis(8)]
        dependent = self.column([0, 1, 2, '0', 4, 7])
        dependent['values'][0] = {}
        dependent['values'][1] = {'value': None}
        dependent['values'][2] = {'value': '-'}
        dependent['values'][4] = {'low': 3, 'high': 5}
        dependent['values'].extend([{'low': None, 'high': 8}, {'low': 8, 'high': None}])
        original = deepcopy((axes, dependent))
        root_objects = list(ObjectFactory(RootWriter.class_list, axes, [dependent]).get_next_object())
        graph = next(obj for obj in root_objects if obj.GetName() == 'Graph1D_y1')
        self.assertEqual(graph.GetN(), 3)
        self.assertEqual([graph.GetX()[i] for i in range(3)], [3.5, 4.5, 5.5])
        self.assertEqual([graph.GetY()[i] for i in range(3)], [0, 4, 7])
        self.assertEqual([graph.GetErrorYlow(i) for i in range(3)], [0.5, 1.0, 0.5])
        self.assertEqual([graph.GetErrorYhigh(i) for i in range(3)], [0.75, 1.0, 0.75])
        estimates = list(ObjectFactory(YODA.class_list, axes, [dependent]).get_next_object())
        self.assertEqual(len(estimates), 1)
        obj = estimates[0]
        self.assertEqual(obj.xEdges(), list(range(9)))
        self.assertEqual([obj.bin(obj.indexAt(x)).val() for x in (3.5, 4.5, 5.5)], [0, 4, 7])
        self.assertEqual((axes, dependent), original)

    def test_private_views_preserve_input_values_errors_and_labels(self):
        from copy import deepcopy
        from hepdata_converter.writers.array_writer import ObjectFactory
        from hepdata_converter.writers.root_writer import ROOT as RootWriter

        axis = self.axis(3)
        axis['labels'] = ['first', 'second', 'third']
        dependent = self.column(['0', '4'])
        dependent['values'][0]['errors'].append(
            {'label': 'shape', 'symerror': 0.25})
        original = deepcopy((axis, dependent))
        objects = list(ObjectFactory(RootWriter.class_list, [axis], [dependent]).get_next_object())
        histogram = next(obj for obj in objects if obj.GetName() == 'Hist1D_y1')
        self.assertEqual(histogram.GetNbinsX(), 3)
        self.assertEqual([histogram.GetXaxis().GetBinLabel(i) for i in (1, 2, 3)],
                         ['first', 'second', 'third'])
        self.assertEqual((axis, dependent), original)

    def test_every_mapped_axis_limits_the_available_prefix(self):
        from copy import deepcopy
        from hepdata_converter.writers.array_writer import ObjectFactory

        class CaptureWrapper:
            core_object = True

            @classmethod
            def match_and_create(cls, axes, dependent, index):
                return [(axes, dependent, index)]

        for lengths in ((4, 2), (2, 4), (4, 3, 2), (2, 0), ()):
            with self.subTest(lengths=lengths):
                axes = [self.axis(length) for length in lengths]
                columns = [self.column([0, 4, 8]), self.column([1])]
                original = deepcopy((axes, columns))
                objects = list(ObjectFactory([CaptureWrapper], axes, columns).get_next_object())
                for index, obj in enumerate(objects):
                    count = min(lengths) if lengths else len(columns[index]['values'])
                    if not count:
                        self.assertIsNone(obj)
                    else:
                        actual_axes, dependent, position = obj
                        self.assertEqual(position, index)
                        self.assertEqual(len(dependent['values']), max(lengths) if lengths else count)
                        self.assertEqual([len(axis['values']) for axis in actual_axes], list(lengths))
                        for missing in dependent['values'][min(count, len(columns[index]['values'])):]:
                            self.assertEqual(missing, {})
                self.assertEqual((axes, columns), original)

    def test_finite_geometry_anchors_partial_flow_measurements(self):
        from copy import deepcopy
        from hepdata_converter.writers.array_writer import ObjectFactory
        from hepdata_converter.writers.root_writer import ROOT as RootWriter
        from hepdata_converter.writers.yoda_writer import YODA

        axis = self.axis(2)
        axis['values'][0] = {'low': float('-inf'), 'high': 1}
        columns = [self.column([9]), self.column([2, 0, 99])]
        original = deepcopy((axis, columns))
        objects = list(ObjectFactory(RootWriter.class_list, [axis], columns).get_next_object())
        hist = next(obj for obj in objects if obj.GetName() == 'Hist1D_y1')
        self.assertEqual(hist.GetNbinsX(), 1)
        self.assertEqual(hist.GetEntries(), 1)
        self.assertEqual(hist.GetBinContent(0), 9)
        estimates = list(ObjectFactory(YODA.class_list, [axis], columns).get_next_object())
        self.assertEqual(estimates[0].numBins(), 1)
        self.assertEqual(estimates[0].bin(0).val(), 9)
        self.assertTrue(math.isnan(estimates[0].bin(1).val()))
        self.assertEqual((axis, columns), original)

    def test_all_missing_columns_keep_empty_geometry_and_later_identifiers(self):
        for categorical in (False, True):
            axis = self.axis()
            if categorical:
                axis = {'header': {'name': 'category'}, 'values': [
                    {'value': value} for value in ('first', 'second', 'third')]}
            folder = self.write_submission([{
                'independent_variables': [axis],
                'dependent_variables': [self.column(['-', '-', '-'], tag='omit'),
                    self.column([0, 4, 8], tag='keep-second'),
                    self.column([3], tag='keep-custom', custom_identifier='kept-custom')],
            }])
            for format_ in self.formats:
                with self.subTest(format_=format_, categorical=categorical):
                    output = self.export(folder, format_)
                    if format_ == 'root':
                        root_file = ROOT.TFile.Open(output)
                        try:
                            names = [key.GetName() for key in root_file.Get('Table 1').GetListOfKeys()]
                            self.assertIn('Hist1D_y1', names)
                            self.assertEqual(root_file.Get('Table 1/Hist1D_y1').GetEntries(), 0)
                            graph = root_file.Get('Table 1/Graph1D_y2')
                            self.assertEqual([graph.GetY()[i] for i in range(graph.GetN())], [0, 4, 8])
                            histogram = root_file.Get('Table 1/Hist1D_y3')
                            self.assertEqual(histogram.GetNbinsX(), 3)
                            self.assertEqual(histogram.GetBinContent(1), 3)
                            if categorical:
                                self.assertEqual(histogram.GetXaxis().GetBinLabel(1), 'first')
                        finally:
                            root_file.Close()
                    else:
                        entries = self.read_yoda(output, format_)
                        self.assertEqual(set(entries), {'/REF/RIVET_ANALYSIS_NAME/d01-x01-y01',
                                                       '/REF/RIVET_ANALYSIS_NAME/d01-x01-y02',
                                                       '/REF/RIVET_ANALYSIS_NAME/kept-custom'})
                        second = entries['/REF/RIVET_ANALYSIS_NAME/d01-x01-y02']
                        self.assertEqual(second['tag'], 'keep-second')
                        self.assert_yoda_values(second, [0, 4, 8], format_)
                        custom = entries['/REF/RIVET_ANALYSIS_NAME/kept-custom']
                        self.assertEqual(custom['tag'], 'keep-custom')
                        self.assert_yoda_values(custom, [3], format_)

    def test_nonnumeric_hole_before_overflow_preserves_native_flow(self):
        folder = self.write_submission([{
            'independent_variables': [{'header': {'name': 'x'}, 'values': [
                {'low': 0, 'high': 1}, {'low': 1, 'high': 2},
                {'low': 2, 'high': float('inf')}, {'low': 3, 'high': 4}]}],
            'dependent_variables': [self.column(['-', 7, 9])],
        }])
        for format_ in self.formats:
            with self.subTest(format_=format_):
                output = self.export(folder, format_)
                if format_ == 'root':
                    root_file = ROOT.TFile.Open(output)
                    try:
                        histogram = root_file.Get('Table 1/Hist1D_y1')
                        self.assertEqual(histogram.GetNbinsX(), 4)
                        self.assertEqual(histogram.GetBinContent(2), 7)
                        self.assertEqual(histogram.GetBinContent(5), 9)
                    finally:
                        root_file.Close()
                else:
                    entry = self.read_yoda(output, format_)[
                        '/REF/RIVET_ANALYSIS_NAME/d01-x01-y01']
                    self.assert_yoda_values(entry, [7], format_)
                    if format_ != 'yoda1':
                        script = """
import json
import math
import sys
import yoda
obj = yoda.read(sys.argv[1])['/REF/RIVET_ANALYSIS_NAME/d01-x01-y01']
overflow = obj.bin(obj.indexAt(float('inf')))
print(json.dumps({'value': overflow.val(), 'error': list(overflow.err('shape')),
                  'gap_masked': obj.bin(obj.indexAt(2.5)).isMasked(),
                  'empty_nan': math.isnan(obj.bin(obj.indexAt(3.5)).val()),
                  'empty_masked': obj.bin(obj.indexAt(3.5)).isMasked()}))
"""
                        flow = json.loads(subprocess.check_output(
                            [sys.executable, '-c', script, output], universal_newlines=True))
                        self.assertEqual(flow, {'value': 9, 'error': [-0.5, 0.75],
                                                'gap_masked': True, 'empty_nan': True,
                                                'empty_masked': False})

    def test_masked_source_rows_preserve_flow_coordinates_on_either_axis(self):
        from hepdata_converter.writers.array_writer import ObjectFactory
        from hepdata_converter.writers.yoda_writer import YODA

        finite = {'low': 1, 'high': 2}
        for flow in ({'low': float('-inf'), 'high': 1},
                     {'low': 2, 'high': float('inf')}):
            for flow_axis in (0, 1):
                for missing in ({}, {'value': '-'}):
                    with self.subTest(flow=flow, flow_axis=flow_axis, missing=missing):
                        axes = [self.axis(3), self.axis(3)]
                        axes[flow_axis]['values'] = [{'low': 0, 'high': 1}, finite, flow]
                        dependent = self.column([0, 7, 9])
                        dependent['values'][0] = missing
                        obj = list(ObjectFactory(YODA.class_list, axes, [dependent]).get_next_object())[0]
                        finite_coords = [1.5, 1.5]
                        flow_coords = [2.5, 2.5]
                        flow_coords[flow_axis] = float('-inf') if flow['low'] == float('-inf') else float('inf')
                        self.assertEqual(obj.bin(obj.indexAt(*finite_coords)).val(), 7)
                        self.assertEqual(obj.bin(obj.indexAt(*flow_coords)).val(), 9)
                        self.assertEqual(list(obj.bin(obj.indexAt(*flow_coords)).err('shape')), [-0.5, 0.75])
