from abc import ABCMeta
import abc
import inspect
from string import lower
import textwrap


class Option(object):
    def __init__(self, name, shortversion=None, type=str, default=None, variable_mapping=None, required=True, help='', auto_help=True):
        self.name = name
        self.help = help
        self.required = required
        self.auto_help = auto_help
        self.shortversion = shortversion
        self.variable_mapping = variable_mapping or self.name
        self.default = default
        self.type = type
        if self.type is bool:
            self.action = 'store_const'
        else:
            self.action = 'store'

    def attach_to_parser(self, parser):
        args = ['--'+self.name]
        if self.shortversion:
            args.append('-'+self.shortversion)

        kwargs = {
            'default': self.default,
            'help': self.help,
            'required': self.required,
            'action': self.action
        }
        if self.type == bool:
            kwargs['const'] = True

        parser.add_argument(*args, **kwargs)


class OptionInitMixin(object):
    """This mixin requires a class to have specified options dictionary as
    class variable

    """
    help = ''

    @classmethod
    def options(cls):
        return {}

    @classmethod
    def get_help(cls, margin):
        def make_margin(lines, margin):
            return '\n'.join([margin+line for line in lines])

        r = make_margin(textwrap.wrap(cls.__name__.lower() + ': ' + cls.help + '\n', 70-len(margin)), margin) + '\n'
        r += '\n'
        r += make_margin(textwrap.wrap("Options:" + '\n', 70-len(2*margin)), 2*margin) + '\n'
        for key, option in cls.options().items():
            r += make_margin(textwrap.wrap('--' + key + ': ' + option.help + '\n', 70-len(3 * margin)), 3 * margin) + '\n\n'

        return r

    def __init__(self, options):
        self.options_values = {}
        for option in options:
            if option in self.__class__.options():
                self.options_values[self.__class__.options()[option].variable_mapping] = options[option]

        # add default values
        for key, option in self.__class__.options().items():
            if key not in options:
                self.options_values[self.__class__.options()[key].variable_mapping] = option.default

    @classmethod
    def register_cli_options(cls, parser):
        for option in cls.options():
            cls.options()[option].attach_to_parser(parser)

    def __getattr__(self, attr_name):
        if attr_name in self.options_values:
            return self.options_values[attr_name]
        else:
            raise AttributeError("'%s' object has no attribute '%s'" % (self.__class__.__name__, attr_name))

    def __dir__(self):
        _dir = dir(super(OptionInitMixin, self))
        _dir += [option.variable_mapping for key, option in self.__class__.options().items()]
        return _dir


class GetConcreteSubclassMixin(object):
    @classmethod
    def get_concrete_class(cls, class_name):
        """This method provides easier access to all writers inheriting Writer class

        :param class_name: name of the parser (name of the parser class which should be used)
        :type class_name: str
        :return: Writer subclass specified by parser_name
        :rtype: Writer subclass
        :raise ValueError:
        """
        def recurrent_class_lookup(cls):
            for cls in cls.__subclasses__():
                if lower(cls.__name__) == lower(class_name):
                    return cls
                elif len(cls.__subclasses__()) > 0:
                    r = recurrent_class_lookup(cls)
                    if r is not None:
                        return r
            return None

        cls = recurrent_class_lookup(cls)
        if cls:
            return cls
        else:
            raise ValueError("'class_name '%s' is invalid" % class_name)

    @classmethod
    def get_all_subclasses(cls, include_abstract=False):
        def recurrent_class_list(cls):
            r = []
            for cls in cls.__subclasses__():
                if include_abstract or not inspect.isabstract(cls):
                    r.append(cls)
                if len(cls.__subclasses__()) > 0:
                    r += recurrent_class_list(cls)
            return r

        return recurrent_class_list(cls)