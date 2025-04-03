from hepdata_converter.common import OptionInitMixin, Option
from hepdata_converter.parsers import Parser, ParsedData, BadFormat, Table
import copy
import re


class HEPTable(Table):
    """Extension of Table including some place for temporary data needed during conversion
    """
    def __init__(self, index=None, data_file=None, table_name=None):
        super(HEPTable, self).__init__(index, data_file, table_name)

        self.xheaders = []
        self.yheaders = []


class OldHEPData(Parser):
    """Parser for Old HEPData format
    """
    help = 'Parses OLD HepData format - example OLD HepData input format: http://hepdata.cedar.ac.uk/resource/sample.input'

    @classmethod
    def options(cls):
        options = Parser.options()
        options['strict'] = Option('strict', default=True, type=bool, required=False,
                                   help='if specified any additional keywords in OldHEPData file will raise an error')
        options['use_additional_data'] = Option('use-additional-data', default=False, type=bool, required=False, variable_mapping='use_additional_data',
                                                help=('if specified additional data which does not have equivalent in new HEPData format'
                                                ' will be appended to comment section of the output document'))

        return options

    def reset(self):
        """Clean any processing data, and prepare object for reuse
        """
        self.current_table = None
        self.tables = []
        self.data = [{}]
        self.additional_data = {}
        self.lines = []
        self.set_state('document')
        self.current_file = None
        self.set_of_energies = set()

    def set_state(self, state):
        if state not in OldHEPData.states:
            raise ValueError("unknown state")
        self.current_state = state

    def __init__(self, **kwargs):
        """Constructor
        :param use_additional_data: if set to True additional data which does not have equivalent in new HEPData format
        will be appended to comment section of the output document
        :type use_additional_data: bool

        :param strict: if set to True, any additional keywords (not specified by documentation)
        will raise BadFormat exception during parsing
        :type strict: bool
        """


        # mapping of OLD HepData format's keywords to proper parsing functions
        # all possible keywords are specified here, the ones which aren't used
        # by new data format are either mapped to _pass method which does nothing,
        # or bound to _add_to_comment which adds the specified data to comment section of the
        # output

        # functions are specified by states in which parser may be, it may either be parsing table or document
        # for those two states different sets of directives are permitted
        self.mapping = {
            'document': {
                'reference':  self._parse_reference,
                'dataset':    self._set_table,

                # additional data which have no one to one mapping to new YAML format
                'author':     self._bind_parse_additional_data('author'),
                'doi':        self._bind_parse_additional_data('doi'),
                'status':     self._bind_parse_additional_data('status'),
                'experiment': self._bind_parse_additional_data('experiment'),
                'detector':   self._bind_parse_additional_data('detector'),
                'title':      self._bind_parse_additional_data('title'),

                # add it to record_ids
                'spiresId':   self._bind_parse_record_ids('spires'),
                'inspireId':  self._bind_parse_record_ids('inspire'),
                'cdsId':      self._bind_parse_record_ids('cds'),
                'durhamId':   self._bind_parse_record_ids('durham'),

                'comment':    self._parse_document_comment,
                'E':          self._pass
            },
            'table': {
                'dataend':    self._set_document,
                'location':   self._bind_set_table_metadata('location'),
                'dscomment':  self._bind_set_table_metadata('description', True),
                'dserror':    self._parse_dserror,
                'reackey':    self._parse_reackey,
                'qual':       self._parse_qual,
                'data':       self._parse_table_data,
                'xheader':    self._parse_xheaders,
                'yheader':    self._parse_yheaders,
                'obskey':     self._parse_obskey,
                'phrase':     self._parse_phrase,
                'E':          self._pass
            }
        }

        OptionInitMixin.__init__(self, options=kwargs)

    def _parse(self):
        # parse the file
        while self._parse_line(self.current_file):
            pass

        if self.use_additional_data:
            if self.additional_data:
                self.data[0]['comment'] += 'ADDITIONAL DATA IMPORTED FROM OLD HEPDATA FORMAT: \n'
            for key in self.additional_data:
                for element in self.additional_data[key]:
                    self.data[0]['comment'] += "%s: %s" % (key, element)

        return ParsedData(self.data[0], self.tables)

    def parse(self, data_in):
        # clean any possible data from previous parsing
        self.reset()
        # in case of strings we should treat them as filepaths
        if isinstance(data_in, str):
            with open(data_in, 'r') as self.current_file:
                return self._parse()
        else:
            self.current_file = data_in
            return self._parse()

    def _parse_line(self, file):
        """Parse single line (or more if particular keyword actually demands it)

        :param file:
        :type file: file
        """

        line = self._strip_comments(file.readline())
        # check if the file ended
        if not line:
            return False

        # line was empty or it was a comment, continue
        if line.strip() == '':
            return True

        # retrieve keyword and its value
        reg = re.search(r"^\*(?P<key>[^:#]*)(:\s*(?P<value>.*)\s*)?$", line)
        if reg:
            key = reg.group('key').strip()
            value = reg.group('value')

            if key in self.mapping[self.current_state]:
                self.mapping[self.current_state][key](value)
            elif self.strict:
                raise BadFormat("unknown key: *%s" % key)
        else:
            raise BadFormat("line can not be parsed: %s" % line)

        return True

    def _parse_reference(self, data):
        """

        :param data:
        :type data: str
        """
        if 'additional_resources' not in self.data[0]:
            self.data[0]['additional_resources'] = []

        location = data.split(' : ')[0].strip()
        if location.startswith('http'):
            self.data[0]['additional_resources'].append({
                'location': location,
                'description': 'web page with auxiliary material'
            })

    def _set_table(self, data):
        """Set current parsing state to 'table',
        create new table object and add it to tables collection
        """
        self.set_state('table')
        self.current_table = HEPTable(index=len(self.tables) + 1)
        self.tables.append(self.current_table)
        self.data.append(self.current_table.metadata)

    def _set_document(self, data):
        """Set current parsing state to 'document',
        set current_table to None
        """
        self.set_state('document')
        self.current_table = None

    def _pass(self, data):
        """Empty processing function, map it to keywords if they're not used in the new YAML format
        """
        pass

    def _parse_table_data(self, data):
        """Parse dataset data of the original HEPData format

        :param data: header of the table to be parsed
        :raise ValueError:
        """
        header = data.split(':')

        self.current_table.data_header = header

        for i, h in enumerate(header):
            header[i] = h.strip()

        x_count = header.count('x')
        y_count = header.count('y')

        if not self.current_table.xheaders:
            raise BadFormat("*xheader line needs to appear before *data: %s" % data)

        if not self.current_table.yheaders:
            raise BadFormat("*yheader line needs to appear before *data: %s" % data)

        # use deepcopy to avoid references in yaml... may not be required, and will very probably be refactored
        # TODO - is this appropriate behavior, or are references in YAML files acceptable, they are certainly less human readable
        self.current_table.data = {'independent_variables': [{'header': self.current_table.xheaders[i] if i < len(self.current_table.xheaders) else copy.deepcopy(self.current_table.xheaders[-1]),
                                                              'values': []} for i in range(x_count)],
                                      'dependent_variables': [{'header': self.current_table.yheaders[i] if i < len(self.current_table.yheaders) else copy.deepcopy(self.current_table.yheaders[-1]),
                                                               'qualifiers': [self.current_table.qualifiers[j][i] if i < len(self.current_table.qualifiers[j]) else copy.deepcopy(self.current_table.qualifiers[j][-1]) for j in range(len(self.current_table.qualifiers)) ],
                                                               'values': []} for i in range(y_count)]}

        xy_mapping = []

        current_x_count = 0
        current_y_count = 0

        for h in header:
            if h == 'x':
                xy_mapping.append(current_x_count)
                current_x_count += 1
            if h == 'y':
                xy_mapping.append(current_y_count)
                current_y_count += 1

        last_index = self.current_file.tell()
        line = self._strip_comments(self.current_file.readline())

        while line and not line.startswith('*'):
            data_entry_elements = line.split(';')[:-1] # split and also strip newline character at the end

            if len(data_entry_elements) == len(header):
            # this is kind of a big stretch... I assume that x is always first
                for i, h in enumerate(header):
                    single_element = data_entry_elements[i].strip()

                    # number patterns copied from old subs.pl parsing script
                    pmnum1 = r'[-+]?[\d]+\.?[\d]*'
                    pmnum2 = r'[-+]?\.[\d]+'
                    pmnum3 = r'[-+]?[\d]+\.?[\d]*\s*[eE]+\s*[+-]?\s*[\d]+'
                    pmnum = '(' + pmnum1 + '|' + pmnum2 + '|' + pmnum3 + ')'

                    # implement same regular expression matching as in old subs.pl parsing script

                    if h == 'x': # independent variables

                        r = re.search('^(?P<value>' + pmnum + ')$', single_element)
                        if r: # "value"
                            single_element = {'value': r.group('value')}
                        else:
                            r = re.search('^(?P<value>' + pmnum + r')\s*\(\s*BIN\s*=\s*(?P<low>' + pmnum + \
                                          r')\s+TO\s+(?P<high>' + pmnum + r')\s*\)$', single_element)
                            if r: # "value (BIN=low TO high)"
                                single_element = {'value': float(r.group('value')),
                                                  'low': float(r.group('low')), 'high': float(r.group('high'))}
                            else:
                                r = re.search('^(?P<low>' + pmnum + r')\s+TO\s+(?P<high>' + pmnum + ')$',
                                              single_element)
                                if r: # "low TO high"
                                    single_element = {'low': float(r.group('low')), 'high': float(r.group('high'))}
                                else: # everything else: don't try to convert to float
                                    single_element = {'value': single_element}

                        # TO DO: subs.pl also parses other formats such as "low high", "value low high" (sorted),
                        # "value +- err", and "value -err_m, +err_p".  Do we need to support these formats here?
                        # Probably not: unsupported formats will just be written as a text string.

                        self.current_table.data['independent_variables'][xy_mapping[i]]['values'].append(single_element)

                        # extract energy if SQRT(S) is one of the 'x' variables
                        xheader = self.current_table.data['independent_variables'][xy_mapping[i]]['header']
                        if xheader['name'].startswith('SQRT(S)') and xheader['units'].lower() in ('gev'):
                            for energy in list(single_element.values()):
                                try:
                                    energy = float(energy)
                                    self.set_of_energies.add(energy)
                                except:
                                    pass

                    elif h == 'y': # dependent variable

                        pmnum_pct = pmnum + r'(\s*PCT)?' # errors can possibly be given as percentages

                        r = re.search('^(?P<value>' + pmnum + r')\s+(?P<err_p>' + pmnum_pct + r'|-)\s*,\s*(?P<err_m>' +
                                      pmnum_pct + r'|-)\s*(?P<err_sys>\(\s*DSYS=[^()]+\s*\))?$', single_element)
                        element = {'errors': []}
                        if r: # asymmetric first error
                            element['value'] = r.group('value').strip()
                            err_p = r.group('err_p').strip().lstrip('+')
                            if err_p == '-': err_p = '' # represent missing error as '-' in oldhepdata format
                            err_p = err_p[:-3].strip() + '%' if err_p[-3:] == 'PCT' else err_p
                            err_m = r.group('err_m').strip().lstrip('+')
                            if err_m == '-': err_m = '' # represent missing error as '-' in oldhepdata format
                            err_m = err_m[:-3].strip() + '%' if err_m[-3:] == 'PCT' else err_m
                            if err_p and err_m and err_p[-1] != '%' and err_m[-1] == '%':
                                err_p = err_p + '%'
                            if not err_p and not err_m:
                                raise ValueError("Both asymmetric errors cannot be '-': %s" % line)
                            if r.group('err_sys'):
                                element['errors'] += [{'label': 'stat', 'asymerror': {'plus': err_p, 'minus': err_m}}]
                            else:
                                element['errors'] += [{'asymerror': {'plus': err_p, 'minus': err_m}}]

                        else:
                            r = re.search('^(?P<value>' + pmnum + r')\s*(\+-\s*(?P<error>' +
                                          pmnum_pct + r'))?\s*(?P<err_sys>\(\s*DSYS=[^()]+\s*\))?$', single_element)
                            if r: # symmetric first error
                                element['value'] = r.group('value').strip()
                                if r.group('error'):
                                    error = r.group('error').strip().lstrip('+')
                                    error = error[:-3].strip() + '%' if error[-3:] == 'PCT' else error
                                    if r.group('err_sys'):
                                        element['errors'] += [{'label': 'stat', 'symerror': error}]
                                    else:
                                        element['errors'] += [{'symerror': error}]
                            else: # everything else
                                element['value'] = single_element

                        err_sys = []
                        if r and r.group('err_sys'):
                            err_sys = r.group('err_sys').strip(' \t()').split('DSYS=')

                        for err in err_sys + self.current_table.dserrors:
                            err = err.strip(' \t,')
                            if not err:
                                continue
                            error = {}
                            label = 'sys'
                            r = re.search(r'^(\+-)?\s*(?P<error>' + pmnum_pct + r')\s*(\:\s*(?P<label>.+))?$', err)
                            if r: # symmetric systematic error
                                if r.group('label'):
                                    label += ',' + r.group('label')
                                error = r.group('error').strip().lstrip('+')
                                error = error[:-3].strip() + '%' if error[-3:] == 'PCT' else error
                                error = {'symerror': error}

                            else:
                                r = re.search('^(?P<err_p>' + pmnum_pct + r'|-)\s*,\s*(?P<err_m>' +
                                              pmnum_pct + r'|-)\s*(\:\s*(?P<label>.+))?$', err)
                                if r: # asymmetric systematic error
                                    if r.group('label'):
                                        label += ',' + r.group('label')
                                    err_p = r.group('err_p').strip().lstrip('+')
                                    if err_p == '-': err_p = '' # represent missing error as '-' in oldhepdata format
                                    err_p = err_p[:-3].strip() + '%' if err_p[-3:] == 'PCT' else err_p
                                    err_m = r.group('err_m').strip().lstrip('+')
                                    if err_m == '-': err_m = '' # represent missing error as '-' in oldhepdata format
                                    err_m = err_m[:-3].strip() + '%' if err_m[-3:] == 'PCT' else err_m
                                    if err_p and err_m and err_p[-1] != '%' and err_m[-1] == '%':
                                        err_p = err_p + '%'
                                    if not err_p and not err_m:
                                        raise ValueError("Both asymmetric errors cannot be '-': %s" % line)
                                    error = {'asymerror': {'plus': err_p, 'minus': err_m}}
                            if not r:
                                # error happened
                                raise ValueError("Error while parsing data line: %s" % line)

                            error['label'] = label
                            if element['value'] != single_element:
                                element['errors'].append(error)
                        self.current_table.data['dependent_variables'][xy_mapping[i]]['values'].append(element)

            elif data_entry_elements:
                raise BadFormat("%s data entry elements but %s expected: %s" %
                                (len(data_entry_elements), len(header), line))

            last_index = self.current_file.tell()
            l = self.current_file.readline()
            line = self._strip_comments(l)

        self.current_file.seek(last_index)

        # extract minimum and maximum from set of energies
        if self.set_of_energies:
            energy_min = min(self.set_of_energies)
            energy_max = max(self.set_of_energies)
            if energy_max > energy_min:
                energy = str(energy_min) + '-' + str(energy_max)
            else:
                energy = energy_min
            self._parse_energies(energy)

        if self.current_table.description:
            if any(word in self.current_table.description.lower() for word in ['covariance', 'correlation', 'matrix']):
                reformatted = self._reformat_matrix()

    def _reformat_matrix(self):
        """Transform a square matrix into a format with two independent variables and one dependent variable.
        """
        nxax = len(self.current_table.data['independent_variables'])
        nyax = len(self.current_table.data['dependent_variables'])
        npts = len(self.current_table.data['dependent_variables'][0]['values'])

        # check if 1 x-axis, and npts (>=2) equals number of y-axes
        if nxax != 1 or nyax != npts or npts < 2:
            return False

        # add second independent variable with each value duplicated npts times
        if len(self.current_table.xheaders) == 2:
            xheader = self.current_table.xheaders[1]
        else:
            xheader = copy.deepcopy(self.current_table.data['independent_variables'][0]['header'])
        self.current_table.data['independent_variables'].append({'header': xheader, 'values': []})
        for value in self.current_table.data['independent_variables'][0]['values']:
            self.current_table.data['independent_variables'][1]['values'].extend([copy.deepcopy(value) for npt in range(npts)])

        # duplicate values of first independent variable npts times
        self.current_table.data['independent_variables'][0]['values'] \
            = [copy.deepcopy(value) for npt in range(npts) for value in self.current_table.data['independent_variables'][0]['values']]

        # suppress header if different for second y-axis
        if self.current_table.data['dependent_variables'][0]['header'] != \
                self.current_table.data['dependent_variables'][1]['header']:
            self.current_table.data['dependent_variables'][0]['header'] = {'name': ''}

        # remove qualifier if different for second y-axis
        iqdel = [] # list of qualifier indices to be deleted
        for iq, qualifier in enumerate(self.current_table.data['dependent_variables'][0]['qualifiers']):
            if qualifier != self.current_table.data['dependent_variables'][1]['qualifiers'][iq]:
                iqdel.append(iq)
        for iq in iqdel[::-1]: # need to delete in reverse order
            del self.current_table.data['dependent_variables'][0]['qualifiers'][iq]

        # append values of second and subsequent y-axes to first dependent variable
        for iy in range(1, nyax):
            for value in self.current_table.data['dependent_variables'][iy]['values']:
                self.current_table.data['dependent_variables'][0]['values'].append(value)

        # finally, delete the second and subsequent y-axes in reverse order
        for iy in range(nyax-1, 0, -1):
            del self.current_table.data['dependent_variables'][iy]

        return True

    def _parse_dserror(self, data):
        """Parse dserror attribute of the old HEPData format

        example:
        *dserror: 7.5 PCT : overall normalization uncertainty

        :param data: data to be parsed
        :type data: str
        """
        self.current_table.dserrors.append(data.strip())

    def _parse_reackey(self, data):
        """Parse reackey attribute of the old HEPData format

        example:
        *reackey: P P --> Z0 Z0 X

        :param data: data to be parsed
        :type data: str
        """
        self.current_table.reactions.append(data.strip())

    def _parse_obskey(self, data):
        """Parse obskey attribute of the old HEPData format

        example:
        *obskey: DSIG/DPT

        :param data: data to be parsed
        :type data: str
        """
        self.current_table.observables.append(data.strip())

    def _parse_phrase(self, data):
        """Parse phrase attribute of the old HEPData format

        example:
        *phrase: Z pair Production

        :param data: data to be parsed
        :type data: str
        """
        self.current_table.phrases.append(data.strip())

    def _parse_energies(self, data):
        """Add energy given in data to tables energies
        this method is here for completeness sake, it's used in only one other place so
        can be safely extracted

        :param data: data to be appended to table's energies
        :type data: str
        """
        self.current_table.energies.append(data)

    def _parse_qual(self, data):
        """Parse qual attribute of the old HEPData format

        example qual:
        *qual: RE : P P --> Z0 Z0 X

        :param data: data to be parsed
        :type data: str
        """
        list = []
        headers = data.split(':')
        name = headers[0].strip()

        name = re.split(' IN ', name, flags=re.I) # ignore case
        units = None
        if len(name) > 1:
            units = name[1].strip()
        name = name[0].strip()

        if len(headers) < 2:
            raise BadFormat("*qual line must contain a name and values: %s" % data)

        for header in headers[1:]:
            xheader = {'name': name}
            if units:
                xheader['units'] = units

            xheader['value'] = header.strip()
            list.append(xheader)

            # extract energy if SQRT(S) is one of the qualifiers
            if name.startswith('SQRT(S)') and units.lower() in ('gev'):
                energies = re.split(' TO ', xheader['value'], flags=re.I)
                for energy in energies:
                    try:
                        energy = float(energy)
                        self.set_of_energies.add(energy)
                    except:
                        pass

        self.current_table.qualifiers.append(list)

    def _parse_header(self, data):
        """Parse header (xheader or yheader)

        :param data: data to be parsed
        :type data: str
        :return: list with header's data
        :rtype: list
        """
        return_list = []

        headers = data.split(':')

        for header in headers:
            header = re.split(' IN ', header, flags=re.I) # ignore case
            xheader = {'name': header[0].strip()}
            if len(header) > 1:
                xheader['units'] = header[1].strip()
            return_list.append(xheader)

        return return_list

    def _parse_xheaders(self, data):
        """parse xheaders from old HEPData format

        :param data: data with xheaders to be parsed
        :type data: str
        """
        self.current_table.xheaders += self._parse_header(data)

    def _parse_yheaders(self, data):
        """parse yheaders from old HEPData format

        :param data: data with yheaders to be parsed
        :type data: str
        """
        self.current_table.yheaders += self._parse_header(data)

    @staticmethod
    def _strip_comments(line):
        """Processes line stripping any comments from it

        :param line: line to be processed
        :type line: str
        :return: line with removed comments
        :rtype: str
        """
        if line == '':
            return line
        r = re.search('(?P<line>[^#]*)(#(?P<comment>.*))?', line)
        if r:
            line = r.group('line')
            if not line.endswith('\n'):
                line += '\n'
            return line
        return '\n'

    def _read_multiline(self, init_data):
        """Reads multiline symbols (ususally comments)

        :param init_data: initial data (parsed from the line containing keyword)
        :return: parsed value of the multiline symbol
        :rtype: str
        """
        result = init_data

        first = True
        while True:
            last_index = self.current_file.tell()
            line_raw = self.current_file.readline()

            # don't add newlines from full line comments
            if line_raw[0] == '#':
                continue

            # now strip comments
            # TODO - is it appropriate behavior?
            data = self._strip_comments(line_raw)
            # EOF, stop here
            if not data:
                break

            # we arrived to the next command, step back and break
            if len(data.strip()) >= 1 and data.strip()[0] == '*':
                self.current_file.seek(last_index)
                break

            if first:
                result += '\n'
                first = False

            result += data

        result = result.strip()
        if result and not result.endswith('.'):
            result += '.'

        return result

    def _parse_document_comment(self, data):
        self.data[0]['comment'] = self._read_multiline(data)

    def _bind_set_table_metadata(self, key,  multiline=False):
        """Returns parsing function which will parse data as text, and add it to the table metatadata dictionary
        with the provided key

        :param key: dictionary key under which parsed data will be added to table.metadata
        :type key: str
        :param multiline: if True this attribute will be treated as multiline
        :type multiline: bool
        :return: function with bound key and multiline attributes
        :rtype: Function
        """
        def set_table_metadata(self, data):
            if multiline:
                data = self._read_multiline(data)
            if key == 'location' and data:
                data = 'Data from ' + data
            self.current_table.metadata[key] = data.strip()

        # method must be bound, so we use __get__
        return set_table_metadata.__get__(self)

    def _bind_parse_record_ids(self, key):
        def _parse_record_ids(self, data):
            if 'record_ids' not in self.data[0]:
                self.data[0]['record_ids'] = []

            record_id = {'type': key, 'id': int(data) if data else 0}

            if self.data[0]['record_ids'].count(record_id) == 0:
                self.data[0]['record_ids'].append(record_id)
            elif self.strict:
                raise BadFormat("duplicated record: *%s" % key)

        # method must be bound, so we use __get__
        return _parse_record_ids.__get__(self)

    def _bind_parse_additional_data(self, key, multiline=False):
        """Returns parsing function which will parse data as text, and add it to the table additional data dictionary
        with the provided key

        :param key: dictionary key under which parsed data will be added to table.metadata
        :type key: str
        :param multiline: if True this attribute will be treated as multiline
        :type multiline: bool
        :return: function with bound key and multiline attributes
        :rtype: Function
        """

        def _set_additional_data_bound(self, data):
            """Concrete method for setting additional data
            :param self:
            :type self: OldHEPData
            """
            # if it's multiline, parse it
            if multiline:
                data = self._read_multiline(data)

            if key not in self.additional_data:
                self.additional_data[key] = []
            self.additional_data[key].append(data)

        # method must be bound, so we use __get__
        return _set_additional_data_bound.__get__(self)

    # employing full fledged FSM for only two states is kind of an overkill, so
    # I'll just define them here...
    states = ['document', 'table']
