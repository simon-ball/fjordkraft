class FjordKraftException(Exception):
    """
    Top level exception class
    """


class APIInaccessibleException(FjordKraftException):
    """Something went wrong with reading the API"""