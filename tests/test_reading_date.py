from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.eau_agur.api.exceptions import AgurApiConnectionError
from custom_components.eau_agur.coordinator import EauAgurDataUpdateCoordinator
from custom_components.eau_agur.sensor import SENSORS, EauAgurSensor


@pytest.mark.asyncio
async def test_coordinator_keeps_index_and_current_date_together():
    coordinator = EauAgurDataUpdateCoordinator.__new__(EauAgurDataUpdateCoordinator)
    coordinator._api_client = Mock(
        generate_temporary_token=AsyncMock(),
        login=AsyncMock(),
        get_consumption=AsyncMock(return_value={"index": 10, "date": "2023-08-29"}),
        get_last_invoice=AsyncMock(return_value=20),
        get_balance=AsyncMock(return_value=0),
    )
    coordinator._email = "user@example.com"
    coordinator._password = "test-credential"  # noqa: S105
    coordinator._contract_number = "123"

    data = await coordinator._async_update_data()
    assert data == {"consumption": 10, "consumption_date": "2023-08-29", "last_invoice": 20, "balance": 0}

    coordinator._api_client.get_consumption.return_value = {"index": 10, "date": None}
    data = await coordinator._async_update_data()
    assert data["consumption"] == 10
    assert data["consumption_date"] is None


@pytest.mark.asyncio
async def test_failed_consumption_refresh_clears_date_and_value():
    coordinator = EauAgurDataUpdateCoordinator.__new__(EauAgurDataUpdateCoordinator)
    coordinator._api_client = Mock(
        generate_temporary_token=AsyncMock(),
        login=AsyncMock(),
        get_consumption=AsyncMock(side_effect=AgurApiConnectionError("offline")),
        get_last_invoice=AsyncMock(return_value=20),
        get_balance=AsyncMock(return_value=0),
    )
    coordinator._email = "user@example.com"
    coordinator._password = "test-credential"  # noqa: S105
    coordinator._contract_number = "123"

    data = await coordinator._async_update_data()
    assert data["consumption"] is None
    assert data["consumption_date"] is None


def test_only_total_liters_exposes_live_reading_date():
    coordinator = Mock(config_entry=Mock(entry_id="entry"), data={"consumption": 10, "consumption_date": "2023-08-29"})
    total = EauAgurSensor("entry", coordinator, SENSORS[0])
    invoice = EauAgurSensor("entry", coordinator, SENSORS[1])

    assert total.extra_state_attributes == {"reading_date": "2023-08-29"}
    assert total.native_value == 10
    assert total.unique_id == "entry_total_liters"
    assert invoice.extra_state_attributes is None
    coordinator.data = {"consumption": 10, "consumption_date": "2023-08-30"}
    assert total.extra_state_attributes == {"reading_date": "2023-08-30"}
    assert total.native_value == 10
    coordinator.data = {"consumption": 10, "consumption_date": None}
    assert total.extra_state_attributes is None
    assert total.native_value == 10
