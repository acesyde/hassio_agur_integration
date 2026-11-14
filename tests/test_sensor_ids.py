"""Let Home Assistant name new sensors and preserve registered identifiers."""

from unittest.mock import AsyncMock, Mock

import pytest
import pytest_asyncio
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from custom_components.eau_agur.const import DOMAIN
from custom_components.eau_agur.sensor import SENSORS, EauAgurSensor


@pytest.mark.parametrize("description", SENSORS, ids=lambda description: description.key)
def test_sensor_leaves_entity_id_generation_to_home_assistant(description):
    coordinator = Mock(config_entry=Mock(entry_id="entry"))
    sensor = EauAgurSensor("entry", coordinator, description)
    assert sensor.entity_id is None
    assert sensor.has_entity_name
    assert sensor.unique_id == f"entry_{description.key}"


@pytest_asyncio.fixture
async def registry(tmp_path):
    hass = HomeAssistant(str(tmp_path))
    hass.config_entries = Mock(async_wait_initialized=AsyncMock())
    dr.async_setup(hass)
    await dr.async_load(hass, load_empty=True)
    registry = er.async_get(hass)
    await registry.async_load(load_empty=True)
    return hass, registry


@pytest.mark.asyncio
@pytest.mark.parametrize("description", SENSORS, ids=lambda description: description.key)
async def test_existing_custom_entity_id_is_preserved(registry, description):
    _, registry = registry
    unique_id = f"entry_{description.key}"
    existing = registry.async_get_or_create("sensor", DOMAIN, unique_id, suggested_object_id=description.key)
    custom_id = f"sensor.my_{description.key}"
    registry.async_update_entity(existing.entity_id, new_entity_id=custom_id)

    sensor = EauAgurSensor("entry", Mock(config_entry=Mock(entry_id="entry")), description)
    registered = registry.async_get_or_create(
        "sensor", DOMAIN, sensor.unique_id, has_entity_name=sensor.has_entity_name, object_id_base="Account balance"
    )
    assert registered.entity_id == custom_id
    assert registered.id == existing.id


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("parts", "expected"),
    [
        (
            [
                er.EntityNamePart.AREA,
                er.EntityNamePart.PARENT_DEVICE,
                er.EntityNamePart.DEVICE,
                er.EntityNamePart.ENTITY,
            ],
            "sensor.cuisine_eau_par_agur_solde_du_contrat",
        ),
        ([er.EntityNamePart.DEVICE, er.EntityNamePart.ENTITY], "sensor.eau_par_agur_solde_du_contrat"),
    ],
)
async def test_new_sensor_uses_configured_entity_id_format(registry, parts, expected):
    hass, registry = registry
    await ar.async_load(hass, load_empty=True)
    hass.config_entries.async_get_entry.return_value = Mock(
        entry_id="entry", domain=DOMAIN, disabled_by=None, pref_disable_new_entities=False
    )
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id="entry", identifiers={(DOMAIN, "entry")}, name="EAU par Agur", suggested_area="Cuisine"
    )
    registry.async_update_settings(entity_id_parts=parts)
    sensor = EauAgurSensor("entry", Mock(config_entry=Mock(entry_id="entry")), SENSORS[2])
    entry = registry.async_get_or_create(
        "sensor",
        DOMAIN,
        sensor.unique_id,
        device_id=device.id,
        has_entity_name=sensor.has_entity_name,
        object_id_base="Solde du contrat",
    )
    assert entry.entity_id == expected
