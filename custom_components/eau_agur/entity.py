from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, CONF_CONTRACT_NUMBER, CONF_PROVIDER, DOMAIN, NAME, VERSION
from .coordinator import EauAgurDataUpdateCoordinator


class EauAgurEntity(CoordinatorEntity):
    """Defines a base Eau par Agur entity."""

    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator: EauAgurDataUpdateCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_unique_id = coordinator.config_entry.entry_id
        entry = coordinator.config_entry
        contract_identity = f"{entry.data.get(CONF_PROVIDER)}:{entry.data.get(CONF_CONTRACT_NUMBER)}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.unique_id)},
            name=entry.title if entry.unique_id == contract_identity else NAME,
            model=VERSION,
            manufacturer=NAME,
        )
