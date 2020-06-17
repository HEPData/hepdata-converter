def error_value_processor(value, error):
    """
    If an error is a percentage, we convert to a float, then
    calculate the percentage of the supplied value.

    :param value: base value, e.g. 10
    :param error: e.g. 20.0%
    :return: the absolute error, e.g. 12 for the above case.
    """
    if isinstance(error, str):
        try:
            if "%" in error:
                error_float = float(error.replace("%", ""))
                error_abs = value / 100 * error_float
                return error_abs
            elif error == "":
                error = 0.0
            else:
                error = float(error)
        except:
            pass

    return error
