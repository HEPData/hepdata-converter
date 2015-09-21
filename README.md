[![Build Status](https://api.travis-ci.org/HEPData/hepdata-converter.svg)](https://travis-ci.org/HEPData/hepdata-converter)

[![Coverage Status](https://coveralls.io/repos/HEPData/hepdata-converter/badge.svg?branch=master&service=github)](https://coveralls.io/github/HEPData/hepdata-converter?branch=master)

[![PyPi](https://img.shields.io/pypi/dm/hepdata-converter.svg)](https://pypi.python.org/pypi/hepdata-converter/)

[![PyPi](https://img.shields.io/github/license/hepdata/hepdata-converter.svg)](https://github.com/HEPData/hepdata-converter/blob/master/LICENSE.txt)



# HEP Data Converter

This software library provides support for converting old HEPData format used by: [http://hepdata.cedar.ac.uk]

Old format detailed description: [http://hepdata.cedar.ac.uk/resource/sample.input]

## Usage

Library exposes single function which enables conversion from several different formats (YODA, YAML, Old HEPData) format to several other (YODA, YAML, ROOT, CSV). Conversion can be conducted between any format supported as input into any format supported as output. This is possible by means of using simple in memory intermediary format:

*HERE SHOULD GO IMAGE WITH THE 'ARCHITECTURE'*



### Conversion between different formats

#### Python code
```
import hepconverter

hepconverter.convert(input_file, output_directory, options={'input_format': 'oldhepdata'})

```

#### CLI
```
$ hepdata-converter --input-format oldhepdata /path/to/input /path/to/output
```



## Extending library with new input formats

To extend library with new formats (both input and output) one only needs to subclass specified class (for reading
```hepconverter.parsers.Parser```, for writing ```hepconverter.writers.Writer```, and make sure that files containing these implementations
are respectively in ```hepconcerter.parsers``` or ```hepconverter.writers``` package)

### Creating new Parser

In order to create new Parser you need to create class inheriting Parser class and override ```def parse(self, data_in, *args, **kwargs):``` abstract method. If you're trying to extend the library you should put the file containing new Parser in ```hepdata_converter/parsers``` directory, the name of the class is important - the new parser will be available by this name (case insensitive). If your goal is a simple hack then the package containing new parser class can be whererver, but the parser class has to be imported before using hepdata_converter.convert function.

Example is below:

```
# -*- encoding: utf-8 -*-
from hepdata_converter.common import Option
from hepdata_converter.parsers import Parser, ParsedData


class FOO(Parser):
    help = 'FOO Parser help text displayed in CLI after typing hepdata-converter --help'

    @classmethod
    def options(cls):
        options = Parser.options()
        # add foo_option which is bool and has default value of True
        # it will be automatically added as named argument to __init__ function
        # as foo_option (code below will work):
        # foo = FOO(foo_option=False)
        #
        # additionally it will be accessible inside the class instance as
        # self.foo_option

        options['foo_option'] = Option('foo-option', default=True, type=bool, required=False,
                                       help='Description of the option printed in CLI')

    def parse(self, data_in, *args, **kwargs):
        # WARNING it is developers responsibility to be able to handle
        # data_in regardless whether it is string (path) or filelike
        # object

        # list of hepdata_converter.Table objects
        tables = []
        # dictionary corresponding to submission.yaml general element (comment, license - not table data)
        metadata = {}

        # ... parse data_in into metadata and tables

        return ParsedData(metadata, tables)

```

If this class is put in (eg) ```hepdata_converter/parsers/foo_parser.py``` then it could be accessed in the code as:

```
import hepdata_converter

hepdata_converter.convert('/path/to/input', '/path/to/output',
                          options={'input_format': 'foo'})
```

It can also be accessed from CLI:

```
$ hepdata-converter --input-format foo /path/to/input /path/to/output
```

**WARNING**: it is developers responsibility to be able to handle
```data_in``` in ```def parse(self, data_in, *args, **kwargs):``` regardless whether it is string (path) or filelike
object


### Creating new Writer

Creation of new Writer is similar to creating new Parser (see above), but for the sake of completness the full description is provided below.
In order to create new Writer you need to create class inheriting Writer class and override ```def write(self, data_in, data_out, *args, **kwargs):``` abstract method. If you're trying to extend the library you should put the file containing new Parser in ```hepdata_converter/writers``` directory, the name of the class is important - the new writer will be available by this name (case insensitive). If your goal is a simple hack then the package containing new writer class can be whererver, but the writer class has to be imported before using hepdata_converter.convert function.

Example is below:

```
# -*- encoding: utf-8 -*-
from hepdata_converter.common import Option
from hepdata_converter.writers import Writer


class FOO(Writer):
    help = 'FOO Writer help text displayed in CLI after typing hepdata-converter --help'

    @classmethod
    def options(cls):
        options = Writer.options()
        # add foo_option which is bool and has default value of True
        # it will be automatically added as named argument to __init__ function
        # as foo_option (code below will work):
        # foo = FOO(foo_option=False)
        #
        # additionally it will be accessible inside the class instance as
        # self.foo_option

        options['foo_option'] = Option('foo-option', default=True, type=bool, required=False,
                                       help='Description of the option printed in CLI')

    def write(self, data_in, data_out, *args, **kwargs):
        # data_in is directly passed from Parser.parse method
        # and is instance of ParsedData

        # WARNING it is developers responsibility to be able to handle
        # data_out regardless whether it is string (path) or filelike
        # object

        pass

```

If this class is put in (eg) ```hepdata_converter/writers/foo_writer.py``` then it could be accessed in the code as:

```
import hepdata_converter

hepdata_converter.convert('/path/to/input', '/path/to/output',
                          options={'output_format': 'foo'})
```

It can also be accessed from CLI:

```
$ hepdata-converter --output-format foo /path/to/input /path/to/output
```

**WARNING**: it is developers responsibility to be able to handle
```data_out``` in ```def write(self, data_in, data_out, *args, **kwargs):``` regardless whether it is string (path) or filelike
object
