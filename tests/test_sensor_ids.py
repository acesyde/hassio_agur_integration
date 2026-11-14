"""Sensor ID suggestions must use the sensor platform's domain."""

from unittest.mock import AsyncMock, Mock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from custom_components.eau_agur.const import DOMAIN
from custom_components.eau_agur.sensor import SENSORS, EauAgurSensor


@pytest.mark.parametrize("description", SENSORS, ids=lambda description: description.key)
def test_sensor_id_uses_sensor_domain(description):
    coordinator = Mock(config_entry=Mock(entry_id="entry"))
    sensor = EauAgurSensor("entry", coordinator, description)
    assert sensor.entity_id == f"sensor.{description.key}"
    assert sensor.unique_id == f"entry_{description.key}"


@pytest.mark.asyncio
@pytest.mark.parametrize("description", SENSORS, ids=lambda description: description.key)
async def test_existing_custom_entity_id_is_preserved(tmp_path, description):
    hass = HomeAssistant(str(tmp_path))
    hass.config_entries = Mock(async_wait_initialized=AsyncMock())
    dr.async_setup(hass)
    await dr.async_load(hass, load_empty=True)
    registry = er.async_get(hass)
    await registry.async_load(load_empty=True)
    unique_id = f"entry_{description.key}"
    existing = registry.async_get_or_create("sensor", DOMAIN, unique_id, suggested_object_id=description.key)
    custom_id = f"sensor.my_{description.key}"
    registry.async_update_entity(existing.entity_id, new_entity_id=custom_id)

    sensor = EauAgurSensor("entry", Mock(config_entry=Mock(entry_id="entry")), description)
    domain, object_id = sensor.entity_id.split(".")
    registered = registry.async_get_or_create(domain, DOMAIN, sensor.unique_id, suggested_object_id=object_id)
    assert registered.entity_id == custom_id
    assert registered.id == existing.id
