[![Build Status](https://api.travis-ci.org/HEPData/hepdata-converter.svg)](https://travis-ci.org/HEPData/hepdata-converter)

# HEP Data Converter

This software library provides support for converting old HEPData format used by: [http://hepdata.cedar.ac.uk]

Old format detailed description: [http://hepdata.cedar.ac.uk/resource/sample.input]

## Usage

Library exposes single function which enables conversion from old HEPData format to the yaml based new one.


### Conversion TO YAML
```
import hepconverter

hepconverter.convert(input_file, output_directory, options={'input_format': 'oldhepdata'})

```

### Conversion FROM YAML (not implemented yet)

```
import hepconverter

hepconverter.convert(input_file, output_directory, options={'input_format': 'yaml',
                                                            'output_format': 'csv'})
```


## Extending library with new input formats

To extend library with new formats (both input and output) one only needs to subclass specified class (for reading
```hepconverter.parsers.Parser, for writing``` ```hepconverter.writers.Writer```, and make sure that files containing these implementations
are respectively in ```hepconcerter.parsers``` or ```hepconverter.writers``` package)