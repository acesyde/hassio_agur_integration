"""Account balances preserve signed amounts without affecting other readings."""

import json
from unittest.mock import AsyncMock, Mock

import aiohttp
import pytest
from aresponses import ResponsesMockServer
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.exceptions import ConfigEntryAuthFailed

from custom_components.eau_agur.api import AgurApiClient, AgurApiError, AgurApiUnauthorizedError
from custom_components.eau_agur.api.exceptions import AgurApiConnectionError
from custom_components.eau_agur.coordinator import EauAgurDataUpdateCoordinator
from custom_components.eau_agur.sensor import SENSORS, EauAgurSensor


@pytest.mark.asyncio
@pytest.mark.parametrize("contract", ["12345", "67890"])
@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        (12.34, 12.34),
        (0, 0),
        (-12.34, -12.34),
        ("12.34", 12.34),
        ("1234,56", 1234.56),
        ("1.234,56", 1234.56),
        ("0,00", 0),
        ("-12,34", -12.34),
    ],
)
async def test_balance_amounts(aresponses: ResponsesMockServer, contract, payload, expected):
    aresponses.add(
        "example.com",
        f"/webapi/Facturation/soldeComptableContratAbonnement/{contract}",
        "GET",
        aresponses.Response(text=json.dumps(payload), headers={"Content-Type": "application/json"}),
    )
    async with aiohttp.ClientSession() as session:
        assert await AgurApiClient("example.com", session=session).get_balance(contract) == expected
    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload", [None, True, {}, [], "", "NaN", "Infinity", "1.234", "12.34,56", "12 €", float("inf")]
)
async def test_invalid_balance_is_not_zero(aresponses: ResponsesMockServer, payload):
    aresponses.add(
        "example.com",
        "/webapi/Facturation/soldeComptableContratAbonnement/123",
        "GET",
        aresponses.Response(text=json.dumps(payload), headers={"Content-Type": "application/json"}),
    )
    async with aiohttp.ClientSession() as session:
        with pytest.raises(AgurApiError, match="Invalid balance response"):
            await AgurApiClient("example.com", session=session).get_balance("123")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "exception"), [(401, AgurApiUnauthorizedError), (404, AgurApiError), (500, AgurApiError)]
)
async def test_balance_http_errors(aresponses: ResponsesMockServer, status, exception):
    aresponses.add(
        "example.com",
        "/webapi/Facturation/soldeComptableContratAbonnement/123",
        "GET",
        aresponses.Response(status=status, text="error"),
    )
    async with aiohttp.ClientSession() as session:
        with pytest.raises(exception):
            await AgurApiClient("example.com", session=session).get_balance("123")


@pytest.fixture
def coordinator():
    coordinator = EauAgurDataUpdateCoordinator.__new__(EauAgurDataUpdateCoordinator)
    coordinator._api_client = Mock(
        generate_temporary_token=AsyncMock(),
        login=AsyncMock(),
        get_consumption=AsyncMock(return_value={"index": 10, "date": "2026-11-14"}),
        get_last_invoice=AsyncMock(return_value=20),
        get_balance=AsyncMock(return_value=50),
    )
    coordinator._email = "test@example.com"
    coordinator._password = "test-credential"  # noqa: S105
    coordinator._contract_number = "123"
    return coordinator


@pytest.mark.asyncio
async def test_balance_refresh_preserves_zero_and_credit(coordinator):
    for amount in (50, 0, -10):
        coordinator._api_client.get_balance.return_value = amount
        data = await coordinator._async_update_data()
        assert data == {"consumption": 10, "consumption_date": "2026-11-14", "last_invoice": 20, "balance": amount}
    coordinator._api_client.get_balance.assert_awaited_with("123")


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", [AgurApiError("invalid response"), AgurApiConnectionError("timeout")])
async def test_balance_failure_keeps_other_readings(coordinator, failure):
    assert (await coordinator._async_update_data())["balance"] == 50
    coordinator._api_client.get_balance.side_effect = failure
    data = await coordinator._async_update_data()
    assert data == {"consumption": 10, "consumption_date": "2026-11-14", "last_invoice": 20, "balance": None}
    coordinator._api_client.get_balance.side_effect = None
    coordinator._api_client.get_balance.return_value = 0
    assert (await coordinator._async_update_data())["balance"] == 0


@pytest.mark.asyncio
async def test_balance_authentication_failure_is_not_swallowed(coordinator):
    coordinator._api_client.get_balance.side_effect = AgurApiUnauthorizedError("expired")
    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator._async_update_data()


def test_last_invoice_exposes_native_euro_unit():
    coordinator = Mock(config_entry=Mock(entry_id="entry"), data={"last_invoice": 30})
    description = next(description for description in SENSORS if description.key == "last_invoice")
    sensor = EauAgurSensor("entry", coordinator, description)
    assert sensor.native_unit_of_measurement == "€"
    assert sensor.native_value == 30
    assert sensor.unique_id == "entry_last_invoice"


def test_balance_sensor_keeps_signed_values_and_existing_ids():
    coordinator = Mock(config_entry=Mock(entry_id="entry"), data={"balance": 50}, last_update_success=True)
    sensors = {description.key: EauAgurSensor("entry", coordinator, description) for description in SENSORS}
    balance = sensors["balance"]
    assert balance.unique_id == "entry_balance"
    assert sensors["total_liters"].unique_id == "entry_total_liters"
    assert sensors["last_invoice"].unique_id == "entry_last_invoice"
    assert balance.device_class == SensorDeviceClass.MONETARY
    assert balance.native_unit_of_measurement == "€"
    assert balance.state_class == SensorStateClass.TOTAL
    for amount in (50, 0, -10, None):
        coordinator.data["balance"] = amount
        assert balance.native_value == amount
    assert balance.extra_state_attributes is None
