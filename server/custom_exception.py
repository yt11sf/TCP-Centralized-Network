class OptionSelectedIsInvalidError(Exception):
    """Raised when the option selected by user is out of range"""
    pass

class ClientDisconnected(Exception):
    """Raised when client disconnect from server"""
    pass