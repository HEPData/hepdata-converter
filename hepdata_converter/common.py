class Option(object):
    def __init__(self, name, shortversion=None, default=None, variable_mapping=None, required=True, help='', auto_help=True):
        self.name = name
        self.help = help
        self.required = required
        self.auto_help = auto_help
        self.shortversion = shortversion
        self.variable_mapping = variable_mapping or self.name
        self.default = default

    def attach_to_parser(self, parser):
        parser.add_argument('--'+self.name, '-'+self.shortversion, default=self.default,
                            const=self.default, nargs='?' if not self.required else 1,
                            help=self.help, required=True)

class OptionInitMixin(object):
    """This mixin requires a class to have specified options dictionary as
    class variable

    """
    def __init__(self, options):
        self.options_values = {}
        for option in options:
            if option in self.__class__.options:
                self.options_values[self.__class__.options[option].variable_mapping] = options[option]

        # add default values
        for key, option in self.__class__.options.items():
            if key not in options:
                self.options_values[key] = option.default

    @classmethod
    def register_cli_options(cls, parser):
        for option in cls.options:
            cls.options[option].attach_to_parser(parser)

    def __getattr__(self, attr_name):
        if attr_name in self.options_values:
            return self.options_values[attr_name]
        else:
            raise AttributeError("'%s' object has no attribute '%s'" % (self.__class__.__name__, attr_name))

    def __dir__(self):
        _dir = dir(super(OptionInitMixin, self))
        _dir += [option.variable_mapping for key, option in self.__class__.options.items()]
        return _dir
