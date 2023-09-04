from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Any

from homeassistant.components.sensor import SensorEntityDescription, SensorDeviceClass, SensorStateClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import COORDINATOR, LOGGER, DOMAIN
from .coordinator import EauAgurDataUpdateCoordinator
from .entity import EauAgurEntity


@dataclass
class EauAgurEntityDescriptionMixin:
    """Mixin for required keys."""

    value_fn: Callable[[dict[str, Any]], str | int | float | None]


@dataclass
class EauAgurEntityDescription(
    SensorEntityDescription,
    EauAgurEntityDescriptionMixin
):
    """Describes Eau par Agur sensor entity."""


def read_consumption(data: dict[str, Any]):
    """Read consumption from data."""

    consumption: float | None = data["consumption"]

    if consumption is not None and consumption > 0:
        return consumption
    return None


SENSORS = [
    EauAgurEntityDescription(
        key="total_liters",
        translation_key="total_liters",
        icon="mdi:gauge",
        native_unit_of_measurement=UnitOfVolume.LITERS,
        unit_of_measurement=UnitOfVolume.LITERS,
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=read_consumption,
    )
]


async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Eau par Agur sensor based on a config entry."""

    coordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]

    entities = []

    for entity_description in SENSORS:
        entities.append(
            EauAgurSensor(
                entry_id=entry.entry_id,
                coordinator=coordinator,
                entity_description=entity_description,
            )
        )

    LOGGER.debug("async_setup_entry adding %d entities", len(entities))

    async_add_entities(entities)


class EauAgurSensor(EauAgurEntity, SensorEntity):
    """Defines a Eau par Agur sensor."""

    def __init__(
            self,
            entry_id: str,
            coordinator: EauAgurDataUpdateCoordinator,
            entity_description: SensorEntityDescription,
    ) -> None:
        """Initialize Eau par Agur sensor."""
        super().__init__(coordinator)
        self.entity_id = f"{DOMAIN}.{entity_description.key}"
        self._attr_unique_id = f"{entry_id}_{entity_description.key}"
        self.entity_description = entity_description

    @property
    def native_value(self) -> int | float | str:
        """Return the state."""
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def available(self) -> bool:
        """Return True if last update was successful."""
        return self.coordinator.last_update_success
