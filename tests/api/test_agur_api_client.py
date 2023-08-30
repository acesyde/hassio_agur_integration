import asyncio
import aiohttp
import pytest
from aresponses import ResponsesMockServer
from custom_components.eau_agur.api import AgurApiClient


@pytest.mark.asyncio
async def test_json_request(aresponses: ResponsesMockServer) -> None:
    """Test JSON response is handled correctly."""
    aresponses.add(
        "example.com",
        "/",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text='{"message": "Hello World!"}',
        ),
    )

    async with aiohttp.ClientSession() as session:
        client = AgurApiClient("example.com", session=session)
        response = await client.request("/")
        assert response["message"] == "Hello World!"
        await client.close()
