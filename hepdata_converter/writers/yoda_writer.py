import copy
from hepdata_converter.common import Option
from hepdata_converter.writers.array_writer import ArrayWriter, ObjectWrapper, ObjectFactory
import yoda


class ScatterYodaClass(ObjectWrapper):
    dim = -1
    _scatter_classes = [yoda.core.Scatter1D, yoda.core.Scatter2D, yoda.core.Scatter3D]
    _point_classes = [yoda.core.Point1D, yoda.core.Point2D, yoda.core.Point3D]

    @classmethod
    def get_scatter_cls(cls):
        return cls._scatter_classes[cls.dim]

    @classmethod
    def get_point_cls(cls):
        return cls._point_classes[cls.dim]

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

    def _create_scatter(self):
        graph = self.get_scatter_cls()()

        for i in xrange(len(self.yval)):
            args = []

            for dim_i in xrange(self.dim):
                args.append(self.xval[dim_i][i])
            args.append(self.yval[i])
            for dim_i in xrange(self.dim):
                args.append([self.xerr_minus[dim_i][i], self.xerr_plus[dim_i][i]])
            args.append([self.yerr_minus[i], self.yerr_plus[i]])

            graph.addPoint(self.get_point_cls()(*args))

        return graph

    def create_objects(self):
        self.calculate_total_errors()

        graph = self._create_scatter()

        return [graph]


class Scatter1DYodaClass(ScatterYodaClass):
    dim = 0


class Scatter2DYodaClass(ScatterYodaClass):
    dim = 1


class Scatter3DYodaClass(ScatterYodaClass):
    dim = 2


class YODA(ArrayWriter):
    help = 'Writes YODA output for table specified by --table parameter, the output should be defined as ' \
           'filepath to output yoda file'

    class_list = [Scatter3DYodaClass, Scatter2DYodaClass, Scatter1DYodaClass]

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
        if isinstance(data_out, (str, unicode)):
            self.file_emulation = True
            outputs.append(open(data_out, 'w'))
        # multiple tables - require directory
        else:  # assume it's a file like object
            self.file_emulation = True
            outputs.append(data_out)

    def _write_table(self, data_out, table):
        # if any non-numeric independent variables, use bins of unit width and centred on integers (1, 2, 3, etc.)
        for ii, independent_variable in enumerate(table.independent_variables):
            if False in ObjectWrapper.is_number_var(independent_variable):
                for i, value in enumerate(independent_variable['values']):
                    table.independent_variables[ii]['values'][i] = {'low': i + 0.5, 'high': i + 1.5}
        table_num = str(table.index)
        if self.hepdata_doi:
            table_doi = 'doi:' + self.hepdata_doi + '/t' + table_num
        else:
            table_doi = table.name
        f = ObjectFactory(self.class_list, table.independent_variables, table.dependent_variables)
        for idep, graph in enumerate(f.get_next_object()):
            graph.title = table_doi
            graph.path = '/REF/' + self.rivet_analysis_name + '/' \
                         + 'd' + table_num.zfill(2) + '-x01-y' + str(idep + 1).zfill(2)
            graph.setAnnotation('IsRef', '1')
            yoda.core.writeYODA(graph, data_out)

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

        for i in xrange(len(self.tables)):
            table = self.tables[i]

            self._write_table(output, table)

        if self.file_emulation:
            output.close()
