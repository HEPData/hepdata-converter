import StringIO
import os
from hepdata_converter.parsers import Parser
from hepdata_converter.writers import Writer


def convert(input, output=None, options={}):
    """Converts arbitrary supported data format to the new HEPData YAML format, and writes the output files
    to the output_dir directory

    :param input: input, depending on the choosen input datatype it may be, filepath, filetype object, directory, etc
    :param output: output directory to which converted YAML files will be written
    :param input_format: format of the input data, must be a string containing name of the input parser class
    :type input_format: str
    :param options: additional options used for conversion (depends on the choosen input format)
    :type options: dict
    :raise ValueError: raised if no input_format is specified
    """

    if 'input_format' not in options and 'output_format' not in options:
        raise ValueError("no input_format and output_format specified!")

    input_format = options.get('input_format', 'yaml')
    output_format = options.get('output_format', 'yaml')

    # nothing to do
    if input_format == output_format:
        return

    parser = Parser.get_specific_parser(input_format)(**options)
    writer = Writer.get_specific_writer(output_format)(**options)

    if not output and not writer.single_file_output:
        raise ValueError("this output_format requires specifing 'output' argument")

    # if no output was specified create proxy output to which writer can insert data
    _output = output
    if not _output:
        _output = StringIO.StringIO()

    writer.write(parser.parse(input), _output)

    # if no output was specified return output
    if not output:
        return _output.getvalue()
