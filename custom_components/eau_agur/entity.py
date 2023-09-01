from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from eau_agur.const import ATTRIBUTION, DOMAIN, NAME, VERSION
from eau_agur.coordinator import EauAgurDataUpdateCoordinator


class EauAgurEntity(CoordinatorEntity):
    """Defines a base Eau par Agur entity."""

    _attr_attribution = ATTRIBUTION

    def __init__(
            self, coordinator: EauAgurDataUpdateCoordinator
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_unique_id = coordinator.config_entry.entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.unique_id)},
            name=NAME,
            model=VERSION,
            manufacturer=NAME,
        )
