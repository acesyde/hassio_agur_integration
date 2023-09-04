"""Constants for mylight_systems."""
from logging import Logger, getLogger

from homeassistant.const import Platform

LOGGER: Logger = getLogger(__package__)

# General
NAME = "EAU par Agur"
DOMAIN = "eau_agur"
PLATFORMS = [Platform.SENSOR]
VERSION = "0.0.3"
COORDINATOR = "coordinator"
ATTRIBUTION = "Data provided by https://www.agur.fr/"
SCAN_INTERVAL_IN_MINUTES = 60 * 4  # 4 hours

# Configuration
CONF_CONTRACT_NUMBER = "contract_number"
