from hepdata_converter.common import Option
from hepdata_converter.writers.array_writer import ArrayWriter, ObjectWrapper, ObjectFactory
import yoda, yaml


class EstimateYodaClass(ObjectWrapper):
    dim = -1
    _estimate_classes = [yoda.core.Estimate0D, yoda.core.Estimate1D, yoda.core.Estimate2D, yoda.core.Estimate3D]

    @classmethod
    def get_estimate_cls(cls):
        return cls._estimate_classes[cls.dim]

    @classmethod
    def match(cls, independent_variables_map, dependent_variable):
        if not ObjectWrapper.match(independent_variables_map, dependent_variable):
            return False
        elif len(independent_variables_map) == cls.dim:
            for independent_variable in independent_variables_map:
                if not independent_variable['values']:
                    return False
            return True
        return False

    def _set_error_breakdown(self, idx, estimate):
        if idx not in self.err_breakdown:
            return
        errs = self.err_breakdown[idx]
        nSources = len(errs.keys())
        for source in errs:
            label =  source
            if label.upper() == "TOTAL" or \
                (nSources == 1 and source == 'error'):
                label = '' # total uncertainty
            errUp = errs[source]['up']
            errDn = errs[source]['dn']
            estimate.setErr([errDn, errUp], label)

    def _create_estimate(self):

        if not len(self.yval):
            return None

        if not self.dim:
            # no binning, just the Estimate0D
            rtn = yoda.core.Estimate0D()
            rtn.setVal(self.yval[0])
            self._set_error_breakdown(0, rtn)
            return rtn

        # Check whether axis type is continuous (float) or
        # discrete (int, string). If in doubt, stick to string.
        isCAxis = [ ]; isIntAxis = [ ]
        for dim_i in range(self.dim):
            vals = self.independent_variable_map[dim_i]['values']
            allUpper = all('high' in vals[i] and isinstance(vals[i]['high'], (int,float)) for i in range(len(vals)))
            allLower = all('low'  in vals[i] and isinstance(vals[i]['low'],  (int,float)) for i in range(len(vals)))
            isCAxis.append( allUpper and allLower )
            allInt = all('value' in vals[i] and ( isinstance(vals[i]['value'], int) or \
                        (isinstance(vals[i]['value'], float) and vals[i]['value'].is_integer())) for i in range(len(vals)))
            isIntAxis.append( allInt )

        # 1D or higher: need to construct binning from edges
        # this excludes under/over/otherflows, so use local
        # indices to pinpoint corresponding bin position
        estimates = [ ]
        edges = [[ ] for _ in range(self.dim)]
        for i in range(len(self.yval)):

            # Check that number of y values does not exceed number of x values.
            too_many_y_values = False
            for dim_i in range(self.dim):
                if i > len(self.xval[dim_i]) - 1:
                    too_many_y_values = True
            if too_many_y_values: break

            localIndices = [ ]
            for dim_i in range(self.dim):
                v = self.xval[dim_i][i]
                m = self.xerr_minus[dim_i][i]
                p = self.xerr_plus[dim_i][i]
                if isCAxis[dim_i]:
                    if not len(edges[dim_i]):
                        edges[dim_i].append(v - m)
                    if not (v+p) in edges[dim_i]:
                        edges[dim_i].append(float(v+p))
                    localIndices.append( edges[dim_i].index(float(v+p)) )
                elif isIntAxis[dim_i]:
                    if not len(edges[dim_i]) or v not in edges[dim_i]:
                        edges[dim_i].append(int(v))
                    localIndices.append( edges[dim_i].index(int(v)) )
                else:
                    v = '{0} - {1}'.format(v-m, v+p) if m and p else str(v)
                    if not len(edges[dim_i]) or v not in edges[dim_i]:
                        edges[dim_i].append(v)
                    localIndices.append( edges[dim_i].index(v) )
            # make Estimate
            estimates.append([ localIndices, yoda.core.Estimate() ])
            estimates[-1][1].setVal(self.yval[i])
            self._set_error_breakdown(i, estimates[-1][1])
        # make BinnedEstimate and set bin contents
        rtn = self.get_estimate_cls()(*edges)
        for localIndices, est in estimates:
            rtn.set(localIndices, est)
        return rtn


    def create_objects(self):
        self.calculate_total_errors()

        estimate = self._create_estimate()

        return [estimate]


class Estimate0DYodaClass(EstimateYodaClass):
    dim = 0


class Estimate1DYodaClass(EstimateYodaClass):
    dim = 1


class Estimate2DYodaClass(EstimateYodaClass):
    dim = 2


class Estimate3DYodaClass(EstimateYodaClass):
    dim = 3


class YODA(ArrayWriter):
    help = 'Writes YODA output for table specified by --table parameter, the output should be defined as ' \
           'filepath to output yoda file'

    class_list = [Estimate3DYodaClass, Estimate2DYodaClass, Estimate1DYodaClass, Estimate0DYodaClass]

    @classmethod
    def options(cls):
        options = ArrayWriter.options()
        options['rivet_analysis_name'] = Option('rivet-analysis-name', 'r', type=str, default='RIVET_ANALYSIS_NAME',
                                                required=False, variable_mapping='rivet_analysis_name',
                                                help='Rivet analysis name, e.g. "ATLAS_2016_I1424838"')
        return options

    def __init__(self, *args, **kwargs):
        super(YODA, self).__init__(*args, **kwargs)
        self.extension = 'yoda'

    def _prepare_outputs(self, data_out, outputs):
        if isinstance(data_out, str):
            self.file_emulation = True
            outputs.append(open(data_out, 'w'))
        # multiple tables - require directory
        else:  # assume it's a file like object
            self.file_emulation = True
            outputs.append(data_out)

    def _write_table(self, data_out, table):
        table_num = str(table.index)
        if self.hepdata_doi:
            table_doi = 'doi:' + self.hepdata_doi + '/t' + table_num
        else:
            table_doi = table.name
        f = ObjectFactory(self.class_list, table.independent_variables, table.dependent_variables)
        for idep, estimate in enumerate(f.get_next_object()):
            if estimate is None:
                continue
            rivet_identifier = 'd' + table_num.zfill(2) + '-x01-y' + str(idep + 1).zfill(2)
            # Allow the standard Rivet identifier to be overridden by a custom value specified in the qualifiers.
            if 'qualifiers' in table.dependent_variables[idep]:
                for qualifier in table.dependent_variables[idep]['qualifiers']:
                    if qualifier['name'] == 'Custom Rivet identifier':
                        rivet_identifier = qualifier['value']
            rivet_path = '/REF/' + self.rivet_analysis_name + '/' + rivet_identifier
            estimate.setTitle(table_doi)
            estimate.setPath(rivet_path)
            estimate.setAnnotation('IsRef', '1')
            yoda.core.writeYODA(estimate, data_out)
            data_out.write('\n')

    def write(self, data_in, data_out, *args, **kwargs):
        """

        :param data_in:
        :type data_in: hepconverter.parsers.ParsedData
        :param data_out: filelike object
        :type data_out: file
        :param args:
        :param kwargs:
        """
        self._get_tables(data_in)

        self.file_emulation = False
        outputs = []
        self._prepare_outputs(data_out, outputs)
        output = outputs[0]

        for i in range(len(self.tables)):
            table = self.tables[i]

            self._write_table(output, table)

        if self.file_emulation:
            output.close()
