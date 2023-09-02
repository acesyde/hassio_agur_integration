"""Asynchronous Python client for the EAU par Agur API."""
from __future__ import annotations

import asyncio
import json
import socket
from typing import Any, Mapping

import aiohttp
import async_timeout
from yarl import URL

from .exceptions import AgurApiConnectionError, AgurApiError, AgurApiUnauthorizedError
from .const import BASE_URL, DEFAULT_TIMEOUT, ACCESS_KEY, CLIENT_ID, CONVERSATION_ID, LOGIN_PATH, \
    GENERATE_TOKEN_PATH, GET_DEFAULT_CONTRACT_PATH, GET_CONSUMPTION_PATH, BASE_PATH, LOGGER


class AgurApiClient:
    """Main class for handling connections with the Agur API."""

    def __init__(
            self,
            host: str = BASE_URL,
            base_path: str = BASE_PATH,
            timeout: int = DEFAULT_TIMEOUT,
            conversation_id: str = CONVERSATION_ID,
            client_id: str = CLIENT_ID,
            access_key: str = ACCESS_KEY,
            session: aiohttp.ClientSession | None = None,
    ) -> AgurApiClient:
        """Initialize connection with the Agur API."""

        self._token = None
        self._session = session
        self._close_session = False

        self._host = host
        self._base_path = base_path
        self._timeout = timeout
        self._conversation_id = conversation_id
        self._client_id = client_id
        self._access_key = access_key

        if self._base_path[-1] != "/":
            self._base_path += "/"

    async def request(
            self,
            uri: str,
            method: str = "GET",
            data: Any | None = None,
            json_data: dict | None = None,
            headers: dict[str, str] | None = None,
            params: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        """Make a request to the Agur API."""

        url = URL.build(
            scheme="https", host=self._host, path=self._base_path
        ).join(URL(uri))

        LOGGER.debug("URL: %s", url)

        if headers is None:
            headers: dict[str, Any] = {}

        headers["Content-Type"] = "application/json"
        headers["Conversationid"] = self._conversation_id

        if self._token is not None:
            headers["Token"] = self._token

        if self._session is None:
            self._session = aiohttp.ClientSession()
        self._close_session = True

        try:
            async with async_timeout.timeout(self._timeout):
                response = await self._session.request(
                    method,
                    url,
                    data=data,
                    json=json_data,
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

    async def generate_temporary_token(self) -> None:
        """Generate a temporary token."""
        try:
            response = await self.request(
                uri=GENERATE_TOKEN_PATH,
                method="POST",
                headers={
                    "token": self._access_key,
                },
                json_data={
                    "AccessKey": self._access_key,
                    "ClientId": self._client_id,
                    "ConversationId": self._conversation_id
                })

            self._token = response["token"]

        except AgurApiError as exception:
            raise AgurApiError(
                "Error occurred while generating temporary token."
            ) from exception

    async def login(self, email: str, password: str) -> bool:
        """Login to Agur API."""
        try:
            response = await self.request(
                uri=LOGIN_PATH,
                method="POST",
                json_data={
                    "identifiant": email,
                    "motDePasse": password,
                })

            self._token = response["tokenAuthentique"]

        except AgurApiError as exception:
            if exception.status == 401:
                raise AgurApiUnauthorizedError(
                    "Invalid credentials."
                ) from exception

            raise AgurApiError(
                "Error occurred while logging in."
            ) from exception

    async def get_default_contract(self) -> str:
        """Get default contract."""
        try:
            response = await self.request(
                uri=GET_DEFAULT_CONTRACT_PATH,
                method="GET")

            return response["numeroContrat"]

        except AgurApiError as exception:
            raise AgurApiError(
                "Error occurred while getting default contract."
            ) from exception

    async def get_consumption(self, contract_id: str) -> float:
        """Get consumption."""
        try:
            response = await self.request(
                f"{GET_CONSUMPTION_PATH}{contract_id}",
                "GET")

            return response["valeurIndex"]

        except AgurApiError as exception:
            raise AgurApiError(
                "Error occurred while getting consumption."
            ) from exception

    async def __aenter__(self) -> Any:
        """Async enter.

        Returns:
            The AgurApiCLient object.
        """
        return self

    async def close(self) -> None:
        """Close open client session."""
        if self._session and self._close_session:
            await self._session.close()

    async def __aexit__(self, *_exc_info) -> None:
        await self.close()
