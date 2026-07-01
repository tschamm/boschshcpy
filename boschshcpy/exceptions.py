class JSONRPCError(Exception):
    """Error to indicate a JSON RPC problem."""

    def __init__(self, code: int, message: str) -> None:
        # Pass args through so repr()/.args and any logging/crash-reporting
        # code that reads them directly (rather than via __str__) still sees
        # the message, instead of an empty Exception.args.
        super().__init__(code, message)
        self._code = code
        self._message = message

    @property
    def code(self) -> int:
        return self._code

    @property
    def message(self) -> str:
        return self._message

    def __str__(self) -> str:
        return f"JSONRPCError (code: {self.code}, message: {self.message})"


class SHCException(Exception):
    """Generic SHC exception."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self._message = message

    @property
    def message(self) -> str:
        return self._message

    def __str__(self) -> str:
        return f"SHC Error (message: {self.message})"


class SHCConnectionError(Exception):
    """Error to indicate a connection problem."""


class SHCAuthenticationError(Exception):
    """Error to indicate an authentication problem."""


class SHCRegistrationError(SHCException):
    """Error to indicate an error during client registration."""


class SHCSessionError(SHCException):
    """Error to indicate a session problem."""


class SHCCertificateError(SHCException):
    """Error to indicate a certificate problem."""
