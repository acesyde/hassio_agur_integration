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
        "conversation_id": "JS-WEB-Netscape-8ca82bba-ef0a-4e83-b89c-5fa28609136b",
        "client_id": "AEL-TOKEN-AGR-PRD",
        "access_key": "XX_fr-5DjklsdMM-AGR-PRD",
    },
    "grandparissud": {
        "display_name": "Grand Paris Sud",
        "base_url": "abonne-eau.grandparissud.fr",
        "conversation_id": "JS-WEB-Netscape-5d0fd8bd-ab70-4764-99a4-55545f0b4941",
        "client_id": "AEL-TOKEN-GPS-PRD",
        "access_key": "REGPS-hc-GPS-MP-PRD",
    },
}
