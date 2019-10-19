from inspect import Parameter, signature


def get_single_param(func) -> Parameter:
    """
    Returns the single first parameter of callable. Raises a value error if
    there is more or less than 1 parameter and checks that the parameter has
    a proper type annotation.
    """

    sig = signature(func)

    if len(sig.parameters) != 1:
        raise ValueError

    param = list(sig.parameters.values())[0]

    if param.kind not in {Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD}:
        raise ValueError

    if param.annotation is Parameter.empty:
        raise ValueError

    return param
