"""Exceptions for EAU par Agur."""


class AgurApiError(Exception):
    """Generic Agur API exception."""


class AgurApiConnectionError(AgurApiError):
    """Agur API connection exception."""


class AgurApiUnauthorizedError(AgurApiError):
    """Agur API unauthorized exception."""
