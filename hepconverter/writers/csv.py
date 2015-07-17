from hepconverter.writers import Writer


class CSV(Writer):
    def write(self, data_in, data_out, *args, **kwargs):
        raise NotImplementedError

