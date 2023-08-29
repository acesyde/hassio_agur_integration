"""Asynchronous Python client for the EAU par Agur API."""
from __future__ import annotations

import asyncio
import json
from socket import socket
from typing import Any, Mapping

import aiohttp
import async_timeout
from yarl import URL

from eau_agur.api import AgurApiConnectionError, AgurApiError
from eau_agur.api.consts import BASE_URL, DEFAULT_TIMEOUT, ACCESS_KEY, CLIENT_ID, CONVERSATION_ID


class AgurApiCLient:
    """Main class for handling connections with the Agur API."""

    def __init__(
        self,
        host: str = BASE_URL,
        timeout: int = DEFAULT_TIMEOUT,
        conversation_id: str = CONVERSATION_ID,
        client_id: str = CLIENT_ID,
        access_key: str = ACCESS_KEY,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        """Initialize connection with the Agur API."""
        self._session = session
        self._close_session = False

        self._host = host
        self._timeout = timeout
        self._conversation_id = conversation_id
        self._client_id = client_id
        self._access_key = access_key

    async def request(
        self,
        uri: str,
        method: str = "GET",
        data: Any | None = None,
        params: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        """Make a request to the Agur API."""

        url = URL.build(scheme="https", host=self._host, path=uri)

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Conversationid": self._conversation_id,
        }

        if self._session is None:
            self._session = aiohttp.ClientSession()
            self._close_session = True

        try:
            async with async_timeout.timeout(self._timeout):
                response = await self._session.request(
                    method,
                    url,
                    data=data,
                    params=params,
                    headers=headers,
                )
        except asyncio.TimeoutError as exception:
            raise AgurApiConnectionError(
                "Timeout occurred while connecting to Agur API."
            ) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            raise AgurApiConnectionError(
                "Error occurred while communicating with Agur API."
            ) from exception

        content_type = response.headers.get("Content-Type", "")
        if response.status // 100 in [4, 5]:
            contents = await response.read()
            response.close()

        if content_type == "application/json":
            raise AgurApiError(
                response.status, json.loads(contents.decode("utf8"))
            )
        raise AgurApiError(
            response.status, {"message": contents.decode("utf8")}
        )

        if "application/json" in content_type:
            return await response.json()

        text = await response.text()
        return {"message": text}

    async def __aenter__(self) -> AgurApiCLient:
        """Async enter.

        Returns:
            The AdGuard Home object.
        """
        return self

    async def close(self) -> None:
        """Close open client session."""
        if self._session and self._close_session:
            await self._session.close()

    async def __aexit__(self, *_exc_info) -> None:
        await self.close()
