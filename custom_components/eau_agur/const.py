"""Constants for mylight_systems."""

from logging import Logger, getLogger

from homeassistant.const import Platform

LOGGER: Logger = getLogger(__package__)

# General
NAME = "EAU par Agur"
DOMAIN = "eau_agur"
PLATFORMS = [Platform.SENSOR]
VERSION = "0.1.0"
COORDINATOR = "coordinator"
ATTRIBUTION = "Data provided by https://www.agur.fr/"
SCAN_INTERVAL_IN_MINUTES = 60 * 4  # 4 hours

# Configuration
CONF_CONTRACT_NUMBER = "contract_number"
CONF_PROVIDER = "provider"

# Providers

PROVIDERS = {
    "agur": {
        "display_name": "Eau par Agur",
        "base_url": "ael.agur.fr",
        "default_timeout": 10,
        "client_id": "AEL-TOKEN-AGR-PRD",
        "access_key": "XX_fr-5DjklsdMM-AGR-PRD",
    },
    "grandparissud": {
        "display_name": "Grand Paris Sud",
        "base_url": "abonne-eau.grandparissud.fr",
        "client_id": "AEL-TOKEN-GPS-PRD",
        "access_key": "REGPS-hc-GPS-MP-PRD",
    },
}
