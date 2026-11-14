"""Issued invoices use the provider's date sort without scanning old history."""

import json
from unittest.mock import AsyncMock, Mock

import aiohttp
import aresponses
import pytest
from aresponses import ResponsesMockServer
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.exceptions import ConfigEntryAuthFailed

from custom_components.eau_agur.api import AgurApiClient, AgurApiError, AgurApiUnauthorizedError
from custom_components.eau_agur.api.exceptions import AgurApiConnectionError
from custom_components.eau_agur.coordinator import EauAgurDataUpdateCoordinator
from custom_components.eau_agur.sensor import SENSORS, EauAgurSensor


def invoice(number="new", amount=120, issued="2026-10-02T12:00:00+02:00"):
    return {"numeroFactureClient": number, "montantTTCFacture": amount, "dateEmissionFacture": issued}


def add_page(server, rows, total):
    server.add(
        "example.com",
        "/webapi/Facture/listeFactures",
        "GET",
        aresponses.Response(
            text=json.dumps({"resultats": rows, "nbTotalResultats": total}),
            headers={"Content-Type": "application/json"},
        ),
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("contract", ["123", "456"])
@pytest.mark.parametrize("amount", [120, 0, -20])
async def test_latest_date_spanning_pages(aresponses: ResponsesMockServer, contract, amount):
    pages = [[invoice(amount=amount), invoice("same-date", amount)], [invoice("old", 90, "2026-01-02T00:00:00+01:00")]]

    async def page(request):
        assert request.query["numeroContrat"] == contract
        assert request.query["nbElements"] == "2"
        assert request.query["tri"] == "dateEmissionFacture"
        assert request.query["triDecroissant"] == "true"
        rows = pages[int(request.query["indexPage"])]
        return aresponses.Response(
            text=json.dumps({"resultats": rows, "nbTotalResultats": 3}), headers={"Content-Type": "application/json"}
        )

    for _ in pages:
        aresponses.add("example.com", "/webapi/Facture/listeFactures", "GET", page)
    async with aiohttp.ClientSession() as session:
        assert await AgurApiClient("example.com", session=session).get_last_issued_invoice(contract) == {
            "amount": amount,
            "issue_date": "2026-10-02T12:00:00+02:00",
        }
    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_empty_invoice_list(aresponses: ResponsesMockServer):
    add_page(aresponses, [], 0)
    async with aiohttp.ClientSession() as session:
        assert await AgurApiClient("example.com", session=session).get_last_issued_invoice("123") is None


@pytest.mark.asyncio
async def test_old_invoice_pages_are_not_downloaded(aresponses: ResponsesMockServer):
    """Even with fifty pages, crossing into an older date finishes the lookup."""
    add_page(aresponses, [invoice(), invoice("old", 90, "2026-01-02T00:00:00+01:00")], 100)
    async with aiohttp.ClientSession() as session:
        assert await AgurApiClient("example.com", session=session).get_last_issued_invoice("123") == {
            "amount": 120,
            "issue_date": "2026-10-02T12:00:00+02:00",
        }
    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_invoice_order_uses_time_and_timezone(aresponses: ResponsesMockServer):
    add_page(
        aresponses,
        [invoice("new", 120, "2026-10-02T11:00:00+00:00"), invoice("old", 90, "2026-10-02T12:00:00+02:00")],
        2,
    )
    async with aiohttp.ClientSession() as session:
        assert await AgurApiClient("example.com", session=session).get_last_issued_invoice("123") == {
            "amount": 120,
            "issue_date": "2026-10-02T11:00:00+00:00",
        }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "rows",
    [
        [invoice("one", 100), invoice("two", 120)],
        [invoice("old", 90, "2026-01-02T00:00:00+01:00"), invoice()],
        [invoice(amount=True)],
        [invoice(amount=None)],
        [invoice(amount=float("inf"))],
        [invoice(issued="not a date")],
        [invoice(issued="2026-10-02T12:00:00")],
        [{"montantTTCFacture": 120}],
        [None],
    ],
)
async def test_invalid_or_ambiguous_invoices_are_not_payments(aresponses: ResponsesMockServer, rows):
    add_page(aresponses, rows, len(rows))
    async with aiohttp.ClientSession() as session:
        with pytest.raises(AgurApiError, match="Invalid issued-invoice response"):
            await AgurApiClient("example.com", session=session).get_last_issued_invoice("123")


@pytest.mark.asyncio
@pytest.mark.parametrize("second_page", [[invoice()], []])
async def test_repeated_or_incomplete_pages_are_rejected(aresponses: ResponsesMockServer, second_page):
    add_page(aresponses, [invoice()], 2)
    add_page(aresponses, second_page, 2)
    async with aiohttp.ClientSession() as session:
        with pytest.raises(AgurApiError, match="Invalid issued-invoice response"):
            await AgurApiClient("example.com", session=session).get_last_issued_invoice("123")
    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        None,
        {},
        {"resultats": [], "nbTotalResultats": True},
        {"resultats": [], "nbTotalResultats": -1},
        {"resultats": {}, "nbTotalResultats": 0},
    ],
)
async def test_invalid_invoice_envelope(aresponses: ResponsesMockServer, payload):
    aresponses.add(
        "example.com",
        "/webapi/Facture/listeFactures",
        "GET",
        aresponses.Response(text=json.dumps(payload), headers={"Content-Type": "application/json"}),
    )
    async with aiohttp.ClientSession() as session:
        with pytest.raises(AgurApiError, match="Invalid issued-invoice response"):
            await AgurApiClient("example.com", session=session).get_last_issued_invoice("123")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "exception"), [(401, AgurApiUnauthorizedError), (404, AgurApiError), (500, AgurApiError)]
)
async def test_invoice_http_errors(aresponses: ResponsesMockServer, status, exception):
    aresponses.add(
        "example.com", "/webapi/Facture/listeFactures", "GET", aresponses.Response(status=status, text="error")
    )
    async with aiohttp.ClientSession() as session:
        with pytest.raises(exception):
            await AgurApiClient("example.com", session=session).get_last_issued_invoice("123")


@pytest.fixture
def coordinator():
    coordinator = EauAgurDataUpdateCoordinator.__new__(EauAgurDataUpdateCoordinator)
    coordinator._api_client = Mock(
        generate_temporary_token=AsyncMock(),
        login=AsyncMock(),
        get_consumption=AsyncMock(return_value={"index": 10, "date": None}),
        get_last_invoice=AsyncMock(return_value=30),
        get_balance=AsyncMock(return_value=50),
        get_last_issued_invoice=AsyncMock(return_value={"amount": 120, "issue_date": "2026-10-02T12:00:00+02:00"}),
    )
    coordinator._email = "test@example.com"
    coordinator._password = "test-credential"  # noqa: S105
    coordinator._contract_number = "123"
    return coordinator


@pytest.mark.asyncio
@pytest.mark.parametrize("amount", [120, 0, -20, None])
async def test_invoice_and_payment_remain_separate(coordinator, amount):
    date = "2026-10-02T12:00:00+02:00" if amount is not None else None
    coordinator._api_client.get_last_issued_invoice.return_value = (
        {"amount": amount, "issue_date": date} if date else None
    )
    data = await coordinator._async_update_data()
    assert data["last_invoice"] == 30
    assert data["last_issued_invoice"] == amount
    assert data["last_issued_invoice_date"] == date
    sensors = {
        description.key: EauAgurSensor("entry", Mock(config_entry=Mock(entry_id="entry"), data=data), description)
        for description in SENSORS
    }
    assert sensors["last_invoice"].native_value == 30
    assert sensors["last_invoice"].unique_id == "entry_last_invoice"
    issued = sensors["last_issued_invoice"]
    assert issued.native_value == amount
    assert issued.native_unit_of_measurement == "€"
    assert issued.device_class == SensorDeviceClass.MONETARY
    assert issued.state_class is None
    assert issued.unique_id == "entry_last_issued_invoice"
    assert issued.entity_id is None
    assert issued.extra_state_attributes == ({"issue_date": date} if date else None)
    assert sensors["last_invoice"].extra_state_attributes is None


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", [AgurApiError("bad response"), AgurApiConnectionError("timeout")])
async def test_invoice_error_keeps_other_readings(coordinator, failure):
    assert (await coordinator._async_update_data())["last_issued_invoice"] == 120
    coordinator._api_client.get_last_issued_invoice.side_effect = failure
    data = await coordinator._async_update_data()
    assert data["last_issued_invoice"] is None
    assert data["last_issued_invoice_date"] is None
    sensor = EauAgurSensor("entry", Mock(config_entry=Mock(entry_id="entry"), data=data), SENSORS[-1])
    assert sensor.extra_state_attributes is None
    assert data["last_invoice"] == 30
    assert data["consumption"] == 10
    assert data["balance"] == 50


@pytest.mark.asyncio
async def test_invoice_authentication_failure_propagates(coordinator):
    coordinator._api_client.get_last_issued_invoice.side_effect = AgurApiUnauthorizedError("expired")
    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator._async_update_data()
