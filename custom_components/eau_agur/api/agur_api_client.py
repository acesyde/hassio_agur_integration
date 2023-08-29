import aiohttp

from eau_agur.api.consts import BASE_URL, DEFAULT_TIMEOUT


class AgurApiCLient:
    """Main class for handling connections with the Agur API."""

    def __init__(
        self,
        host: str = BASE_URL,
        timeout: int = DEFAULT_TIMEOUT,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        """Initialize connection with the Agur API."""
        self._session = session

        self._host = host
        self._timeout = timeout
