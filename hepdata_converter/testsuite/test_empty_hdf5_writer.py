import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import yaml
import yoda

from hepdata_converter import _main, convert
from hepdata_converter.testsuite import test_ragged_array_writer
from hepdata_converter.testsuite.test_writer import WriterTestSuite


class EmptyHDF5WriterTestCase(WriterTestSuite):
    error_message = 'No representable YODA objects to write to HDF5'

    def table(self, lengths):
        return {
            'independent_variables': [{'header': {'name': 'x'}, 'values': [
                {'low': index, 'high': index + 1} for index in range(3)
            ]}],
            'dependent_variables': [
                {'header': {'name': 'y'}, 'values': [
                    {'value': 4 * index, 'errors': [
                        {'label': 'shape', 'asymerror': {'minus': -0.5, 'plus': 0.75}},
                    ]} for index in range(length)
                ]} for length in lengths
            ],
        }

    def write_submission(self, tables):
        folder = Path(self.current_tmp)
        documents = []
        for index, table in enumerate(tables, start=1):
            filename = 'data%s.yaml' % index
            documents.append({'name': 'Table %s' % index, 'description': 'Empty HDF5 collection',
                              'data_file': filename, 'keywords': []})
            (folder / filename).write_text(yaml.safe_dump(table))
        (folder / 'submission.yaml').write_text(yaml.safe_dump_all(documents))
        return folder

    def options(self, **extra):
        return dict({'output_format': 'yoda.h5', 'validator_schema_version': '0.1.0'}, **extra)

    def assert_public_error(self, folder, output, options):
        # A missing guard can terminate natively, so isolate empty public conversions.
        script = '''
import json
import sys
from hepdata_converter import convert

try:
    convert(sys.argv[1], sys.argv[2], options=json.loads(sys.argv[3]))
except ValueError as error:
    print(json.dumps({'exception': type(error).__name__, 'message': str(error)}))
else:
    print(json.dumps({'exception': None}))
'''
        result = json.loads(subprocess.check_output(
            [sys.executable, '-c', script, str(folder), str(output), json.dumps(options)],
            universal_newlines=True,
        ))
        self.assertEqual(result, {'exception': 'ValueError', 'message': self.error_message})

    def read_hdf5(self, output):
        return test_ragged_array_writer.RaggedArrayWriterTestCase.read_yoda(self, str(output), 'yoda.h5')

    def test_omitted_record_does_not_create_destination(self):
        folder = self.write_submission([self.table([2, 0, 4]), self.table([1])])
        output = folder / 'absent.yoda.h5'
        self.assert_public_error(folder, output, self.options())
        self.assertFalse(output.exists())

    def test_existing_hdf5_is_unchanged_and_readable(self):
        folder = self.write_submission([self.table([3])])
        output = folder / 'existing.yoda.h5'
        convert(str(folder), str(output), options=self.options())
        original_bytes = output.read_bytes()
        original_objects = self.read_hdf5(output)
        self.assertEqual(original_objects['/REF/RIVET_ANALYSIS_NAME/d01-x01-y01']['values'], [0, 4, 8])

        self.write_submission([self.table([2, 0, 4])])
        self.assert_public_error(folder, output, self.options())
        self.assertEqual(output.read_bytes(), original_bytes)
        self.assertEqual(self.read_hdf5(output), original_objects)

    def test_native_writer_is_not_called_for_empty_collection(self):
        folder = self.write_submission([self.table([2, 0, 4])])
        output = folder / 'absent.yoda.h5'
        with patch('yoda.core.writeH5') as native_writer:
            with self.assertRaisesRegex(ValueError, self.error_message):
                convert(str(folder), str(output), options=self.options())
            native_writer.assert_not_called()
        self.assertFalse(output.exists())

    def test_all_filtered_valid_tables_are_rejected(self):
        folder = self.write_submission([self.table([3]), self.table([3])])
        for selection in ({'rivet_ref_match': 'd99'}, {'rivet_ref_unmatch': 'd0[12]'}):
            with self.subTest(selection=selection):
                output = folder / 'filtered.yoda.h5'
                self.assert_public_error(folder, output, self.options(**selection))
                self.assertFalse(output.exists())

    def test_mixed_record_delegates_and_preserves_later_valid_objects(self):
        folder = self.write_submission([self.table([2, 0, 4]), self.table([3])])
        output = folder / 'mixed.yoda.h5'
        with patch('yoda.core.writeH5', wraps=yoda.core.writeH5) as native_writer:
            convert(str(folder), str(output), options=self.options())
            native_writer.assert_called_once()
            self.assertEqual(len(native_writer.call_args[0][0]), 1)
        objects = self.read_hdf5(output)
        self.assertEqual(list(objects), ['/REF/RIVET_ANALYSIS_NAME/d02-x01-y01'])
        self.assertEqual(objects['/REF/RIVET_ANALYSIS_NAME/d02-x01-y01']['values'], [0, 4, 8])
        self.assertEqual(objects['/REF/RIVET_ANALYSIS_NAME/d02-x01-y01']['errors'], [[-0.5, 0.75]] * 3)

    def test_cli_returns_controlled_error_without_native_write(self):
        folder = self.write_submission([self.table([2, 0, 4])])
        output = folder / 'cli.yoda.h5'
        with patch('yoda.core.writeH5') as native_writer:
            code, message = _main([
                '--output-format', 'yodah5', '--validator-schema-version', '0.1.0',
                str(folder), str(output),
            ])
            native_writer.assert_not_called()
        self.assertEqual(code, 1)
        self.assertEqual(message, 'Options error: ' + self.error_message)
        self.assertFalse(output.exists())
