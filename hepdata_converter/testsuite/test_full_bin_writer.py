import json
import math
import subprocess
import sys
from copy import deepcopy
from unittest.mock import patch

import ROOT
import yoda

from hepdata_converter.testsuite import test_ragged_array_writer as ragged
from hepdata_converter.testsuite.test_writer import WriterTestSuite
from hepdata_converter.writers.array_writer import ObjectFactory
from hepdata_converter.writers.root_writer import ROOT as RootWriter
from hepdata_converter.writers.yoda_writer import YODA


class FullBinWriterTestCase(WriterTestSuite):
    axis = ragged.RaggedArrayWriterTestCase.axis
    column = ragged.RaggedArrayWriterTestCase.column
    write_submission = ragged.RaggedArrayWriterTestCase.write_submission
    export = ragged.RaggedArrayWriterTestCase.export

    def read_estimates(self, output, format_):
        # Isolate yoda.read's locale change from the test runner.
        script = '''
import json
import math
import sys
import yoda
result = {}
for path, obj in yoda.read(sys.argv[1]).items():
    if sys.argv[2] == 'yoda1':
        result[path] = {'type': type(obj).__name__, 'values': [p.y() for p in obj.points()],
                        'positions': [p.x() for p in obj.points()]}
    else:
        result[path] = {'type': type(obj).__name__, 'count': obj.numBins(),
                        'values': [b.val() for b in obj.bins()],
                        'masked': [b.isMasked() for b in obj.bins()],
                        'errors': [None if math.isnan(b.val()) else list(b.err('shape')) for b in obj.bins()]}
    result[path]['tag'] = obj.annotation('tag') if obj.hasAnnotation('tag') else None
print(json.dumps(result))
'''
        return json.loads(subprocess.check_output(
            [sys.executable, '-c', script, output, format_], universal_newlines=True))

    def test_eight_supplied_bins_keep_one_measurement_in_actual_serializers(self):
        folder = self.write_submission([{
            'independent_variables': [self.axis(8)],
            'dependent_variables': [self.column([2.792], tag='one-measurement')],
        }])
        for format_ in ('root', 'yoda', 'yoda.h5', 'yoda1'):
            with self.subTest(format_=format_):
                if format_ == 'yoda1':
                    with patch('yoda.core.writeYODA1', wraps=yoda.core.writeYODA1) as writer:
                        output = self.export(folder, format_)
                        writer.assert_called_once()
                else:
                    output = self.export(folder, format_)
                if format_ == 'root':
                    f = ROOT.TFile.Open(output)
                    try:
                        hist = f.Get('Table 1/Hist1D_y1')
                        self.assertEqual(hist.GetNbinsX(), 8)
                        self.assertEqual(hist.GetEntries(), 1)
                        self.assertAlmostEqual(hist.GetBinContent(1), 2.792, places=6)
                        self.assertEqual([hist.GetBinContent(i) for i in range(2, 9)], [0] * 7)
                        self.assertEqual(f.Get('Table 1/Graph1D_y1').GetN(), 1)
                        errors = f.Get('Table 1/Hist1D_y1_e1plus')
                        self.assertEqual(errors.GetNbinsX(), 8)
                        self.assertEqual(errors.GetEntries(), 1)
                        self.assertEqual(errors.GetBinContent(1), 0.75)
                        self.assertEqual(errors.GetBinContent(8), 0)
                    finally:
                        f.Close()
                else:
                    obj = self.read_estimates(output, format_)['/REF/RIVET_ANALYSIS_NAME/d01-x01-y01']
                    self.assertEqual(obj['tag'], 'one-measurement')
                    if format_ == 'yoda1':
                        self.assertEqual(obj['values'], [2.792])
                        self.assertEqual(obj['positions'], [0.5])
                    else:
                        self.assertEqual(obj['count'], 8)
                        self.assertEqual(obj['values'][0], 2.792)
                        self.assertTrue(all(math.isnan(v) for v in obj['values'][1:]))
                        self.assertEqual(obj['masked'], [False] * 8)
                        self.assertEqual(obj['errors'][0], [-0.5, 0.75])

    def test_empty_columns_keep_geometry_without_measurements_and_keep_identifiers(self):
        folder = self.write_submission([{
            'independent_variables': [self.axis()],
            'dependent_variables': [self.column([], tag='empty'),
                self.column([0, 4], tag='measured', custom_identifier='custom-second')],
        }])
        for format_ in ('root', 'yoda', 'yoda.h5', 'yoda1'):
            with self.subTest(format_=format_):
                output = self.export(folder, format_)
                if format_ == 'root':
                    f = ROOT.TFile.Open(output)
                    try:
                        hist = f.Get('Table 1/Hist1D_y1')
                        self.assertTrue(hist)
                        self.assertEqual(hist.GetNbinsX(), 3)
                        self.assertEqual(hist.GetEntries(), 0)
                        self.assertFalse(f.Get('Table 1/Graph1D_y1'))
                        second = f.Get('Table 1/Hist1D_y2')
                        self.assertEqual(second.GetNbinsX(), 3)
                        self.assertEqual(second.GetEntries(), 2)
                        self.assertEqual([second.GetBinContent(i) for i in (1, 2, 3)], [0, 4, 0])
                    finally:
                        f.Close()
                else:
                    entries = self.read_estimates(output, format_)
                    first = entries['/REF/RIVET_ANALYSIS_NAME/d01-x01-y01']
                    second = entries['/REF/RIVET_ANALYSIS_NAME/custom-second']
                    self.assertEqual(first['tag'], 'empty')
                    self.assertEqual(second['tag'], 'measured')
                    if format_ == 'yoda1':
                        self.assertEqual(first['values'], [])
                        self.assertEqual(second['values'], [0, 4])
                    else:
                        self.assertEqual(first['count'], 3)
                        self.assertTrue(all(math.isnan(v) for v in first['values']))
                        self.assertEqual(first['masked'], [False] * 3)
                        self.assertEqual(second['values'][:2], [0, 4])
                        self.assertTrue(math.isnan(second['values'][2]))

    def test_missing_cells_keep_full_axes_and_sparse_values_errors_and_source(self):
        axes = [self.axis(8)]
        dep = self.column([0, 1, 2, '0', 4, 7])
        dep['values'][0] = {}
        dep['values'][1] = {'value': None}
        dep['values'][2] = {'value': '-'}
        dep['values'][4] = {'low': 3, 'high': 5}
        original = deepcopy((axes, dep))
        objects = list(ObjectFactory(RootWriter.class_list, axes, [dep]).get_next_object())
        hist = next(obj for obj in objects if obj.GetName() == 'Hist1D_y1')
        self.assertEqual(hist.GetNbinsX(), 8)
        self.assertEqual(hist.GetEntries(), 3)
        graph = next(obj for obj in objects if obj.GetName() == 'Graph1D_y1')
        self.assertEqual([graph.GetX()[i] for i in range(graph.GetN())], [3.5, 4.5, 5.5])
        self.assertEqual([graph.GetY()[i] for i in range(graph.GetN())], [0, 4, 7])
        self.assertEqual([graph.GetErrorYlow(i) for i in range(graph.GetN())], [0.5, 1, 0.5])
        obj = list(ObjectFactory(YODA.class_list, axes, [dep]).get_next_object())[0]
        self.assertEqual(obj.xEdges(), list(range(9)))
        self.assertEqual([obj.bin(obj.indexAt(x)).val() for x in (3.5, 4.5, 5.5)], [0, 4, 7])
        for x in (0.5, 1.5, 2.5, 6.5, 7.5):
            self.assertTrue(math.isnan(obj.bin(obj.indexAt(x)).val()))
            self.assertFalse(obj.bin(obj.indexAt(x)).isMasked())
        self.assertEqual((axes, dep), original)

    def test_each_axis_keeps_its_own_geometry_but_unmatched_values_are_not_filled(self):
        axes = [self.axis(3), self.axis(2)]
        dep = self.column([91, 92, 93])
        original = deepcopy((axes, dep))
        objs = list(ObjectFactory(RootWriter.class_list, axes, [dep]).get_next_object())
        hist = next(obj for obj in objs if obj.GetName() == 'Hist2D_y1')
        self.assertEqual((hist.GetNbinsX(), hist.GetNbinsY()), (3, 2))
        self.assertEqual(hist.GetEntries(), 2)
        self.assertEqual(hist.GetBinContent(hist.FindBin(0.5, 0.5)), 91)
        self.assertEqual(hist.GetBinContent(hist.FindBin(1.5, 1.5)), 92)
        obj = list(ObjectFactory(YODA.class_list, axes, [dep]).get_next_object())[0]
        self.assertEqual(obj.xEdges(), [0, 1, 2, 3])
        self.assertEqual(obj.yEdges(), [0, 1, 2])
        self.assertEqual(obj.bin(obj.indexAt(0.5, 0.5)).val(), 91)
        self.assertEqual(obj.bin(obj.indexAt(1.5, 1.5)).val(), 92)
        self.assertTrue(math.isnan(obj.bin(obj.indexAt(2.5, 1.5)).val()))
        self.assertEqual((axes, dep), original)

    def test_categorical_and_discrete_geometry_include_empty_supplied_bins(self):
        folder = self.write_submission([{
            'independent_variables': [{'header': {'name': 'category'}, 'values': [
                {'value': v} for v in ('forward', 'central', 'backward')]}],
            'dependent_variables': [self.column([0])],
        }])
        output = self.export(folder, 'root')
        f = ROOT.TFile.Open(output)
        try:
            hist = f.Get('Table 1/Hist1D_y1')
            self.assertEqual(hist.GetNbinsX(), 3)
            self.assertEqual([hist.GetXaxis().GetBinLabel(i) for i in (1, 2, 3)],
                             ['forward', 'central', 'backward'])
            self.assertEqual(hist.GetEntries(), 1)
        finally:
            f.Close()
        for values in (('forward', 'central', 'backward'), (1, 3, 7)):
            axes = [{'header': {'name': 'x'}, 'values': [{'value': v} for v in values]}]
            obj = list(ObjectFactory(YODA.class_list, axes, [self.column([0])]).get_next_object())[0]
            self.assertEqual(obj.numBins(), 3)
            self.assertEqual(obj.bin(obj.indexAt(values[0])).val(), 0)
            self.assertTrue(math.isnan(obj.bin(obj.indexAt(values[-1])).val()))
            self.assertFalse(obj.bin(obj.indexAt(values[-1])).isMasked())

    def test_only_structural_gaps_are_masked_not_supplied_empty_bins(self):
        axes = [{'header': {'name': 'x'}, 'values': [
            {'low': 0, 'high': 1}, {'low': 3, 'high': 4}]}]
        obj = list(ObjectFactory(YODA.class_list, axes, [self.column([5])]).get_next_object())[0]
        self.assertEqual(obj.xEdges(), [0, 1, 3, 4])
        self.assertEqual(obj.bin(obj.indexAt(0.5)).val(), 5)
        self.assertTrue(obj.bin(obj.indexAt(2)).isMasked())
        self.assertFalse(obj.bin(obj.indexAt(3.5)).isMasked())
        self.assertTrue(math.isnan(obj.bin(obj.indexAt(3.5)).val()))

    def test_finite_empty_anchor_keeps_measured_flows_but_only_flow_axis_is_omitted(self):
        for entries, values, native_index in (
            ([{'low': float('-inf'), 'high': 0}, {'low': 0, 'high': 1}], [9], 0),
            ([{'low': 0, 'high': 1}, {'low': 1, 'high': float('inf')}], ['-', 9], 2),
        ):
            axes = [{'header': {'name': 'x'}, 'values': entries}]
            dep = self.column(values)
            objs = list(ObjectFactory(RootWriter.class_list, axes, [dep]).get_next_object())
            hist = next(obj for obj in objs if obj.GetName() == 'Hist1D_y1')
            self.assertEqual(hist.GetNbinsX(), 1)
            self.assertEqual(hist.GetEntries(), 1)
            self.assertEqual(hist.GetBinContent(native_index), 9)
            obj = list(ObjectFactory(YODA.class_list, axes, [dep]).get_next_object())[0]
            self.assertEqual(obj.numBins(), 1)
            self.assertEqual(obj.bin(native_index).val(), 9)
            self.assertTrue(math.isnan(obj.bin(1).val()))
        axes = [{'header': {'name': 'x'}, 'values': [
            {'low': float('-inf'), 'high': 0}, {'low': 0, 'high': float('inf')}]}]
        for classes in (RootWriter.class_list, YODA.class_list):
            self.assertEqual(list(ObjectFactory(classes, axes, [self.column([1, 2])]).get_next_object()), [None])

    def test_large_axis_bounds_keep_flow_direction_without_fixed_offsets(self):
        for low in (1e20, -1e20):
            high = low + 1e15
            for entries, values, index in (
                ([{'low': float('-inf'), 'high': low}, {'low': low, 'high': high}], [9], 0),
                ([{'low': low, 'high': high}, {'low': high, 'high': float('inf')}], ['-', 9], 2),
            ):
                with self.subTest(low=low, flow_index=index):
                    axes = [{'header': {'name': 'x'}, 'values': entries}]
                    objects = list(ObjectFactory(RootWriter.class_list, axes, [self.column(values)]).get_next_object())
                    hist = next(obj for obj in objects if obj.GetName() == 'Hist1D_y1')
                    self.assertEqual(hist.GetNbinsX(), 1)
                    self.assertEqual(hist.GetEntries(), 1)
                    self.assertEqual(hist.GetBinContent(index), 9)
                    obj = list(ObjectFactory(YODA.class_list, axes, [self.column(values)]).get_next_object())[0]
                    self.assertEqual(obj.numBins(), 1)
                    self.assertEqual(obj.bin(index).val(), 9)
                    self.assertTrue(math.isnan(obj.bin(1).val()))

    def test_nonfinite_representatives_with_finite_bounds_do_not_become_flows(self):
        for value in (float('nan'), float('inf'), float('-inf')):
            with self.subTest(value=value):
                axes = [{'header': {'name': 'x'}, 'values': [
                    {'value': value, 'low': 0, 'high': 1}, {'low': 1, 'high': 2}]}]
                obj = list(ObjectFactory(YODA.class_list, axes, [self.column([9])]).get_next_object())[0]
                self.assertEqual(obj.xEdges(), [0, 1, 2])
                self.assertEqual(obj.bin(obj.indexAt(0.5)).val(), 9)
                self.assertTrue(math.isnan(obj.bin(0).val()))
                self.assertTrue(math.isnan(obj.bin(obj.numBins() + 1).val()))

    def test_wholly_unbounded_axes_are_omitted_without_stopping_later_tables(self):
        bounds = {'header': {'name': 'x'}, 'values': [
            {'low': float('-inf'), 'high': float('inf')}]}
        folder = self.write_submission([
            {'independent_variables': [bounds], 'dependent_variables': [self.column([])]},
            {'independent_variables': [bounds], 'dependent_variables': [self.column([9])]},
            {'independent_variables': [self.axis()], 'dependent_variables': [self.column([0])]},
        ])
        script = """
import sys
from hepdata_converter import convert
convert(sys.argv[1], sys.argv[2], options={'output_format': sys.argv[3],
    'validator_schema_version': '0.1.0', 'yoda_keep_qualifiers': True})
"""
        for format_ in ('root', 'yoda', 'yoda.h5', 'yoda1'):
            with self.subTest(format_=format_):
                output = str(folder / ('unbounded.' + format_))
                result = subprocess.run([sys.executable, '-c', script, str(folder), output, format_],
                                        capture_output=True, universal_newlines=True)
                self.assertEqual(result.returncode, 0, result.stderr[-3000:])
                if format_ == 'root':
                    f = ROOT.TFile.Open(output)
                    try:
                        self.assertEqual(f.Get('Table 1').GetListOfKeys().GetSize(), 0)
                        self.assertEqual(f.Get('Table 2').GetListOfKeys().GetSize(), 0)
                        self.assertEqual(f.Get('Table 3/Hist1D_y1').GetNbinsX(), 3)
                        self.assertEqual(f.Get('Table 3/Hist1D_y1').GetEntries(), 1)
                    finally:
                        f.Close()
                else:
                    entries = self.read_estimates(output, format_)
                    self.assertEqual(list(entries), ['/REF/RIVET_ANALYSIS_NAME/d03-x01-y01'])
