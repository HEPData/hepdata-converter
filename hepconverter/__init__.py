import os
import yaml
from hepconverter.parsers import Parser
from hepconverter.writers import Writer


def convert(input, output_dir, options={}):
    """Converts arbitrary supported data format to the new HEPData YAML format, and writes the output files
    to the output_dir directory

    :param input: input, depending on the choosen input datatype it may be, filepath, filetype object, directory, etc
    :param output_dir: output directory to which converted YAML files will be written
    :param input_format: format of the input data, must be a string containing name of the input parser class
    :type input_format: str
    :param options: additional options used for conversion (depends on the choosen input format)
    :type options: dict
    :raise ValueError: raised if no input_format is specified
    """

    if 'input_format' not in options:
        raise ValueError("no input_format specified!")

    input_format = options['input_format']
    output_format = options.get('output_format', 'yaml')

    # nothing to do
    if input_format == output_format:
        return

    if input_format != 'yaml':
        parser = Parser.get_specific_parser(input_format)(**options)
        parsed_data = parser.parse(input)
        tables = parsed_data.tables
        data = parsed_data.data

        with open(os.path.join(output_dir, 'submission.yaml'), 'w') as submission_file:

            yaml.dump_all(data + [table.metadata for table in tables], submission_file)

        for table in tables:
            with open(os.path.join(output_dir, table.data_file), 'w') as table_file:
                yaml.dump(table.data, table_file)

    # input format is YAML, and output is something different
    # TODO - NOT IMPLEMENTED YET
    else:
        writer = Writer.get_specific_writer(output_format)(**options)
        writer.write(input, output_dir)