import StringIO
import argparse
import sys
import version
from parsers import Parser
from writers import Writer


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

    parser = Parser.get_concrete_class(input_format)(**options)
    writer = Writer.get_concrete_class(output_format)(**options)

    if not output and not writer.single_file_output:
        raise ValueError("this output_format requires specifying 'output' argument")

    # if no output was specified create proxy output to which writer can insert data
    _output = output
    if not _output:
        _output = StringIO.StringIO()

    writer.write(parser.parse(input), _output)

    # if no output was specified return output
    if not output:
        return _output.getvalue()


def make_exit(message='', code=0):
    return code, message


def generate_help_epilogue():
    margin = '   '

    r = 'Parsers:\n'
    r += '[use them as --input-format parameter]\n'
    r += '\n'

    for cls in Parser.get_all_subclasses():
        r += cls.get_help(margin)

    r += '\nWriters:\n'
    r += '[use them as --output-format parameter]\n'
    r += '\n'

    for cls in Writer.get_all_subclasses():
        r += cls.get_help(margin)

    return r


def _main(arguments=sys.argv):
    # if version is specified ignore any other arguments
    if '--version' in arguments or '-v' in arguments:
        return make_exit(message="hepdata-converter version: %s" % version.__version__)

    parser = argparse.ArgumentParser(description="CLI tools for converting between HEP data formats", add_help=True,
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog=generate_help_epilogue())
    parser.add_argument("--input-format", '-i', action='store', default='yaml', help='format of the input file/s (default: yaml) [choose one option from Parsers section below]')
    parser.add_argument("--output-format", '-o', action='store', default='yaml', help='format of the output file/s (default: yaml) [choose one option from Writers section below]')
    parser.add_argument("--version", '-v', action='store_const', const=True, default=False, help='Show hepdata-converter version')
    parser.add_argument("input")
    parser.add_argument("output")

    if arguments == sys.argv:
        arguments = sys.argv[1:]

    program_args = vars(parser.parse_known_args(arguments)[0])

    input_format = program_args['input_format']
    output_format = program_args['output_format']

    Parser.get_concrete_class(input_format).register_cli_options(parser)
    Writer.get_concrete_class(output_format).register_cli_options(parser)

    # reparse arguments, now with added options from concrete parsers / writers
    program_args = vars(parser.parse_args(arguments))
    try:
        convert(program_args['input'], program_args['output'], program_args)
        return make_exit()
    except ValueError as e:
        return make_exit(message="Options error: %s" % str(e), code=1)


def main(arguments=sys.argv):
    r, message = _main(arguments)
    if r == 0:
        print message
    else:
        print >> sys.stderr, message
    sys.exit(r)
