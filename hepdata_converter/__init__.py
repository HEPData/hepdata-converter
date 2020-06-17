from io import StringIO
import argparse
import sys
from . import version
from hepdata_validator import LATEST_SCHEMA_VERSION
from .parsers import Parser
from .writers import Writer


def convert(input, output=None, options={}):
    """Converts a supported ``input_format`` (*oldhepdata*, *yaml*)
    to a supported ``output_format`` (*csv*, *root*, *yaml*, *yoda*).

    :param input: location of input file for *oldhepdata* format or input directory for *yaml* format
    :param output: location of output directory to which converted files will be written
    :param options: additional options such as ``input_format`` and ``output_format`` used for conversion
    :type input: str
    :type output: str
    :type options: dict
    :raise ValueError: raised if no ``input_format`` or ``output_format`` is specified
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
        _output = StringIO()

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
    parser.add_argument("--hepdata-doi", '-d', action='store', default='', help='Pass HEPData DOI, e.g. "10.17182/hepdata.74247.v1"')
    parser.add_argument("--validator-schema-version", '-s', action='store', default=LATEST_SCHEMA_VERSION, help='hepdata_validator schema version (default: %s)' % LATEST_SCHEMA_VERSION)
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
        print(message)
    else:
        print((message, sys.stderr))
    sys.exit(r)
