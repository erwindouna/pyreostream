"""Exceptions for pyreostream."""


class PyReoStreamError(Exception):
    """Generic exception for pyreostream errors."""


class PyReoStreamConnectionError(PyReoStreamError):
    """Exception raised for connection errors."""


class PyReoStreamTimeoutError(PyReoStreamError):
    """Exception raised for timeout errors."""


class PyReoStreamAuthenticationError(PyReoStreamError):
    """Exception raised for authentication errors."""
