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


@pytest.mark.asyncio
async def test_adding_contract_preserves_legacy_device_and_entities(registry):
    hass, entities = registry
    devices = dr.async_get(hass)
    entries = {
        "legacy": Mock(
            entry_id="legacy",
            unique_id="001",
            title="EAU par Agur",
            data={"provider": "agur", "contract_number": "001"},
            disabled_by=None,
            pref_disable_new_entities=False,
        ),
        "new": Mock(
            entry_id="new",
            unique_id="agur:002",
            title="Eau par Agur — 002",
            data={"provider": "agur", "contract_number": "002"},
            disabled_by=None,
            pref_disable_new_entities=False,
        ),
    }
    hass.config_entries.async_get_entry.side_effect = entries.get
    snapshots = []
    original_device = None
    for entry_id in ("legacy", "new", "legacy"):
        coordinator = Mock(config_entry=entries[entry_id], data={"balance": 10 if entry_id == "legacy" else 20})
        for description in SENSORS:
            sensor = EauAgurSensor(entry_id, coordinator, description)
            device = devices.async_get_or_create(config_entry_id=entry_id, **sensor.device_info)
            registered = entities.async_get_or_create(
                "sensor",
                DOMAIN,
                sensor.unique_id,
                config_entry=entries[entry_id],
                device_id=device.id,
                suggested_object_id=f"{entry_id}_{description.key}",
            )
            if entry_id == "legacy" and len(snapshots) < len(SENSORS):
                registered = entities.async_update_entity(
                    registered.entity_id,
                    new_entity_id=f"sensor.custom_{description.key}",
                    name=f"Custom {description.key}",
                    disabled_by=er.RegistryEntryDisabler.USER,
                )
                snapshots.append((registered.id, registered.entity_id, registered.name, registered.disabled_by))
                original_device = device.id
                devices.async_update_device(device.id, name_by_user="Maison")
            elif entry_id == "legacy":
                assert (registered.id, registered.entity_id, registered.name, registered.disabled_by) in snapshots
                assert device.id == original_device
                assert device.name == "EAU par Agur" and device.name_by_user == "Maison"
            else:
                assert device.id != original_device
                assert device.name == "Eau par Agur — 002"
        assert EauAgurSensor(entry_id, coordinator, SENSORS[2]).native_value == (10 if entry_id == "legacy" else 20)
    assert len(devices.devices) == 2
    assert len(entities.entities) == 2 * len(SENSORS)
