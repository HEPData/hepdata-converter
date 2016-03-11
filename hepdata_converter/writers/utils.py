
def error_value_processor(value, error):
    """
    If an error is a percentage, we convert to a float, then
    calculate the percentage of the supplied value
    :param value: base value, e.g. 10
    :param error: e.g. 20.0%
    :return: the absolute error, e.g. 12 for the above case.
    """
    if type(error) is str:
        if "%" in error:
            error = error.replace("%", "")
            error = float(error)

            error_abs = (value/100) * error
            return error_abs

    return error