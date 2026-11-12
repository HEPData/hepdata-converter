import json
import math
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import ROOT
import yaml

from hepdata_converter import convert
from hepdata_converter.testsuite.test_writer import WriterTestSuite


class FlowOnlyWriterTestCase(WriterTestSuite):
    formats = ('root', 'yoda', 'yoda.h5', 'yoda1')

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

    def table(self, bounds, columns):
        return {'independent_variables': [{'header': {'name': 'x'}, 'values': bounds}],
                'dependent_variables': columns}

    def write_submission(self, tables):
        folder = Path(self.current_tmp)
        documents = []
        for index, table in enumerate(tables, start=1):
            filename = 'data%s.yaml' % index
            documents.append({'name': 'Table %s' % index, 'description': 'Flow-bin omission',
                              'data_file': filename, 'keywords': []})
            (folder / filename).write_text(yaml.safe_dump(table))
        (folder / 'submission.yaml').write_text(yaml.safe_dump_all(documents))
        return folder

    def export(self, folder, format_):
        output = str(folder / ('output.' + format_))
        convert(str(folder), output, options={
            'output_format': format_, 'yoda_keep_qualifiers': True,
        })
        return output

    def read_yoda(self, output, format_, with_flows=False):
        # Keep native reader locale changes out of the test runner.
        script = '''
import json
import math
import sys
import yoda

entries = {}
for path, obj in yoda.read(sys.argv[1]).items():
    if sys.argv[2] == 'yoda1':
        points = obj.points()
        values = [point.y() if hasattr(point, 'y') else point.x() for point in points]
        errors = [list(point.yErrs() if hasattr(point, 'y') else point.xErrs()) for point in points]
    else:
        bins = [obj.bin(index + 1) for index in range(obj.numBins())] if hasattr(obj, 'numBins') else [obj]
        values = [estimate.val() for estimate in bins]
        errors = [None if math.isnan(estimate.val()) else list(estimate.err('shape')) for estimate in bins]
    entry = {'values': values, 'errors': errors,
             'tag': obj.annotation('tag') if obj.hasAnnotation('tag') else None}
    if sys.argv[3] == 'True' and sys.argv[2] != 'yoda1':
        flows = [obj.bin(0), obj.bin(obj.numBins() + 1)]
        entry['flows'] = [estimate.val() for estimate in flows]
        entry['flow_errors'] = [list(estimate.err('shape')) for estimate in flows]
    entries[path] = entry
print(json.dumps(entries))
'''
        return json.loads(subprocess.check_output(
            [sys.executable, '-c', script, output, format_, str(with_flows)],
            universal_newlines=True,
        ))

    def assert_values(self, entry, values, format_):
        measured = [(value, error) for value, error in zip(entry['values'], entry['errors'])
                    if format_ == 'yoda1' or not math.isnan(value)]
        self.assertEqual([value for value, _ in measured], values)
        errors = [0.5, 0.75] if format_ == 'yoda1' else [-0.5, 0.75]
        self.assertEqual([error for _, error in measured], [errors] * len(values))

    def flow_only_bounds(self):
        underflow = {'low': float('-inf'), 'high': 0}
        overflow = {'low': 0, 'high': float('inf')}
        separated_overflow = {'low': 2, 'high': float('inf')}
        return ([underflow], [overflow], [underflow, overflow],
                [underflow, separated_overflow])

    def assert_hdf5_error(self, folder, output):
        # A missing empty-output guard can terminate natively, so isolate conversion.
        script = '''
import json
import math
import sys
from hepdata_converter import convert

try:
    convert(sys.argv[1], sys.argv[2], options={'output_format': 'yoda.h5'})
except ValueError as error:
    print(json.dumps({'exception': type(error).__name__, 'message': str(error)}))
else:
    print(json.dumps({'exception': None}))
'''
        result = json.loads(subprocess.check_output(
            [sys.executable, '-c', script, str(folder), str(output)],
            universal_newlines=True,
        ))
        self.assertEqual(result, {
            'exception': 'ValueError',
            'message': 'No representable YODA objects to write to HDF5',
        })

    def test_whole_flow_only_record_has_no_root_or_yoda_text_objects(self):
        for bounds in self.flow_only_bounds():
            folder = self.write_submission([self.table(bounds, [self.column([9] * len(bounds))])])
            for format_ in ('root', 'yoda', 'yoda1'):
                with self.subTest(bounds=bounds, format_=format_):
                    output = self.export(folder, format_)
                    if format_ == 'root':
                        root_file = ROOT.TFile.Open(output)
                        try:
                            self.assertEqual(root_file.Get('Table 1').GetListOfKeys().GetSize(), 0)
                        finally:
                            root_file.Close()
                    else:
                        self.assertEqual(self.read_yoda(output, format_), {})

    def test_whole_flow_only_record_hdf5_preserves_destination(self):
        folder = self.write_submission([
            self.table([{'low': 0, 'high': 1}], [self.column([0], tag='keep-zero')]),
        ])
        existing = Path(self.export(folder, 'yoda.h5'))
        original_bytes = existing.read_bytes()
        original_objects = self.read_yoda(str(existing), 'yoda.h5')
        entry = original_objects['/REF/RIVET_ANALYSIS_NAME/d01-x01-y01']
        self.assert_values(entry, [0], 'yoda.h5')
        self.assertEqual(entry['tag'], 'keep-zero')

        for index, bounds in enumerate(self.flow_only_bounds()):
            with self.subTest(bounds=bounds):
                self.write_submission([self.table(bounds, [self.column([9] * len(bounds))])])
                absent = folder / ('absent-%s.yoda.h5' % index)
                self.assert_hdf5_error(folder, absent)
                self.assertFalse(absent.exists())
                self.assert_hdf5_error(folder, existing)
                self.assertEqual(existing.read_bytes(), original_bytes)
                self.assertEqual(self.read_yoda(str(existing), 'yoda.h5'), original_objects)
                with patch('yoda.core.writeH5') as native_writer:
                    with self.assertRaisesRegex(
                            ValueError, 'No representable YODA objects to write to HDF5'):
                        self.export(folder, 'yoda.h5')
                    native_writer.assert_not_called()
                self.assertEqual(existing.read_bytes(), original_bytes)

    def test_flow_only_tables_are_omitted_without_aborting_later_table(self):
        for bounds in self.flow_only_bounds():
            folder = self.write_submission([
                self.table(bounds, [self.column([9] * len(bounds))]),
                self.table([{'low': 0, 'high': 1}], [self.column([0])]),
            ])
            for format_ in self.formats:
                with self.subTest(bounds=bounds, format_=format_):
                    output = self.export(folder, format_)
                    if format_ == 'root':
                        root_file = ROOT.TFile.Open(output)
                        try:
                            self.assertEqual(root_file.Get('Table 1').GetListOfKeys().GetSize(), 0)
                            self.assertEqual(root_file.Get('Table 2/Graph1D_y1').GetY()[0], 0)
                        finally:
                            root_file.Close()
                    else:
                        entries = self.read_yoda(output, format_)
                        self.assertEqual(list(entries), ['/REF/RIVET_ANALYSIS_NAME/d02-x01-y01'])
                        self.assert_values(next(iter(entries.values())), [0], format_)

    def test_numeric_mask_preserves_finite_bins_flows_and_column_ids(self):
        bounds = [{'low': float('-inf'), 'high': 0}, {'low': 0, 'high': 1},
                  {'low': 1, 'high': float('inf')}]
        folder = self.write_submission([self.table(bounds, [
            self.column([9, '-', 8], tag='omit-first'),
            self.column([2, 0, 3], tag='keep-second'),
            self.column([0, '-', 0], tag='omit-third'),
            self.column([4, 1, 5], tag='keep-fourth', custom_identifier='kept-custom'),
        ])])
        for format_ in self.formats:
            with self.subTest(format_=format_):
                output = self.export(folder, format_)
                if format_ == 'root':
                    root_file = ROOT.TFile.Open(output)
                    try:
                        names = [key.GetName() for key in root_file.Get('Table 1').GetListOfKeys()]
                        self.assertTrue(names)
                        self.assertTrue(all(any('_y%s' % column in name for column in (1, 2, 3, 4))
                                            for name in names))
                        for column, values in ((1, [9, 0, 8]), (3, [0, 0, 0])):
                            histogram = root_file.Get('Table 1/Hist1D_y%s' % column)
                            self.assertEqual(histogram.GetNbinsX(), 1)
                            self.assertEqual(histogram.GetEntries(), 2)
                            self.assertEqual([histogram.GetBinContent(i) for i in (0, 1, 2)], values)
                        for column, values in ((2, [2, 0, 3]), (4, [4, 1, 5])):
                            histogram = root_file.Get('Table 1/Hist1D_y%s' % column)
                            self.assertEqual(histogram.GetNbinsX(), 1)
                            self.assertEqual([histogram.GetBinContent(i) for i in (0, 1, 2)], values)
                            graph = root_file.Get('Table 1/Graph1D_y%s' % column)
                            self.assertEqual([graph.GetY()[i] for i in (0, 1, 2)], values)
                            self.assertEqual(graph.GetErrorYlow(1), 0.5)
                            self.assertEqual(graph.GetErrorYhigh(1), 0.75)
                    finally:
                        root_file.Close()
                else:
                    entries = self.read_yoda(output, format_, with_flows=True)
                    prefix = '/REF/RIVET_ANALYSIS_NAME/'
                    self.assertEqual(set(entries), {prefix + 'd01-x01-y01', prefix + 'd01-x01-y02',
                                                   prefix + 'd01-x01-y03', prefix + 'kept-custom'})
                    for name, value, flows, tag in (
                            ('d01-x01-y01', None, [9, 8], 'omit-first'),
                            ('d01-x01-y02', 0, [2, 3], 'keep-second'),
                            ('d01-x01-y03', None, [0, 0], 'omit-third'),
                            ('kept-custom', 1, [4, 5], 'keep-fourth')):
                        entry = entries[prefix + name]
                        self.assert_values(entry, [] if value is None else [value], format_)
                        self.assertEqual(entry['tag'], tag)
                        if format_ != 'yoda1':
                            self.assertEqual(entry['flows'], flows)
                            self.assertEqual(entry['flow_errors'], [[-0.5, 0.75]] * 2)

    def test_flow_only_second_axis_is_omitted(self):
        folder = self.write_submission([
            {'independent_variables': [
                {'header': {'name': 'x'}, 'values': [{'low': 0, 'high': 1}]},
                {'header': {'name': 'y'}, 'values': [{'low': float('-inf'), 'high': 0}]},
            ], 'dependent_variables': [self.column([9])]},
            self.table([{'low': 0, 'high': 1}], [self.column([0])]),
        ])
        for format_ in self.formats:
            with self.subTest(format_=format_):
                output = self.export(folder, format_)
                if format_ == 'root':
                    root_file = ROOT.TFile.Open(output)
                    try:
                        self.assertEqual(root_file.Get('Table 1').GetListOfKeys().GetSize(), 0)
                        self.assertEqual(root_file.Get('Table 2/Graph1D_y1').GetY()[0], 0)
                    finally:
                        root_file.Close()
                else:
                    entries = self.read_yoda(output, format_)
                    self.assertEqual(list(entries), ['/REF/RIVET_ANALYSIS_NAME/d02-x01-y01'])
                    self.assert_values(next(iter(entries.values())), [0], format_)

    def test_non_flow_axes_and_unbinned_estimates_are_unchanged(self):
        tables = [self.table([{'value': value} for value in axis], [self.column(values)])
                  for axis, values in ((['forward', 'backward'], [0, 2]),
                                       ([1, 2], [3, 0]), ([0.25, 0.75], [0, 4]))]
        tables.append({'independent_variables': [], 'dependent_variables': [self.column([5])]})
        folder = self.write_submission(tables)
        for format_ in self.formats:
            with self.subTest(format_=format_):
                output = self.export(folder, format_)
                if format_ == 'root':
                    root_file = ROOT.TFile.Open(output)
                    try:
                        for index, values in enumerate(([0, 2], [3, 0], [0, 4], [5]), start=1):
                            graph = root_file.Get('Table %s/Graph1D_y1' % index)
                            self.assertEqual([graph.GetY()[i] for i in range(graph.GetN())], values)
                        self.assertEqual(root_file.Get('Table 1/Hist1D_y1').GetXaxis().GetBinLabel(1), 'forward')
                    finally:
                        root_file.Close()
                else:
                    entries = self.read_yoda(output, format_)
                    self.assertEqual(len(entries), 4)
                    for index, values in enumerate(([0, 2], [3, 0], [0, 4], [5]), start=1):
                        entry = entries['/REF/RIVET_ANALYSIS_NAME/d%02d-x01-y01' % index]
                        self.assert_values(entry, values, format_)
