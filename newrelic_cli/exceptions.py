class NewRelicException(Exception):
    """General class for API exceptions"""
    pass


class Timeout(NewRelicException):
    """The request timed out"""
    pass


class ChecksLimitExceeded(NewRelicException):
    """Requested change will increase scheduled checks past the limit"""


class ItemNotFoundError(NewRelicException):
    """Requested item was not found"""


class ItemAlreadyExistsError(NewRelicException):
    """Requested item is already present and no duplicates allowed"""
    pass


class ScriptNotFoundError(NewRelicException):
    """No script is present for synthetics monitor"""
    pass


class UnathorizedError(NewRelicException):
    """User is now authorized to perform action"""
    pass
