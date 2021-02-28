class JSONRPCError(Exception):
    """Error to indicate a JSON RPC problem."""

    def __init__(self, code, message):
        super().__init__()
        self._code = code
        self._message = message

    @property
    def code(self):
        return self._code

    @property
    def message(self):
        return self._message

    def __str__(self):
        return f"JSONRPCError (code: {self.code}, message: {self.message})"


class SHCConnectionError(Exception):
    """Error to indicate a connection problem."""


class SHCAuthenticationError(Exception):
    """Error to indicate an authentication problem."""


class SHCmDNSError(Exception):
    """Error to indicate a mDNS problem."""


class SHCRegistrationError(Exception):
    """Error to indicate an error during client registration."""


class SHCSessionError(Exception):
    """Error to indicate a session problem."""


class SHCException(Exception):
    """Generic SHC exception."""
