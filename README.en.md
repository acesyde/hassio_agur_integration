# EAU par Agur

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![marketplace][marketplacebadge]][marketplace]
![Project Maintenance][maintenance-shield]

_The following providers are supported :_

- [EAU par Agur][eau_agur]
- [EAU par Grand Paris Sud][eau_grandparissud]
- [EAU de Paris][eau_de_paris]

🌏
[**Français**](README.md) |
English

**This integration will set up the following platforms.**

| Platform              | Description      | Unit | Implemented        |
|-----------------------|------------------|------|--------------------|
| `sensor.total_liters` | Number of liters | L    | :white_check_mark: |
| `sensor.last_invoice` | Last invoice     | €    | :white_check_mark: |

The `sensor.total_liters` sensor exposes a `reading_date` attribute when the actual reading date is provided and valid.

> [!NOTE]
> Data is updated every 24h.

## Installation

### Home Assistant Marketplace (2026.11+)

1. In Home Assistant, go to **Settings → Marketplace**.
2. Choose **Add from link**, paste `https://github.com/acesyde/hassio_agur_integration` and connect your GitHub account if asked.
3. Install **EAU par Agur**, then restart Home Assistant.

Or click this button:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Marketplace.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=acesyde&repository=hassio_agur_integration&category=integration)

> Since 2026.11, HACS is built into Home Assistant as the Marketplace. Existing HACS installs are migrated automatically.

### Manual

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory (folder) there, you need to create it.
   3In the `custom_components` directory (folder) create a new folder called `eau_agur`.
3. Download _all_ the files from the `custom_components/eau_agur/` directory (folder) in this repository.
4. Place the files you downloaded in the new directory (folder) you created.
5. Restart Home Assistant
6. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "EAU par Agur"

## Configuration is done in the UI

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

***

[eau_agur]: https://www.agur.fr/

[eau_grandparissud]: https://abonne-eau.grandparissud.fr/

[eau_de_paris]: https://agence.eaudeparis.fr/

[commits-shield]: https://img.shields.io/github/commit-activity/y/acesyde/hassio_agur_integration.svg?style=for-the-badge

[commits]: https://github.com/acesyde/hassio_agur_integration/commits/main

[marketplace]: https://www.home-assistant.io/integrations/marketplace/#custom-repositories

[marketplacebadge]: https://img.shields.io/badge/Marketplace-Custom-orange.svg?style=for-the-badge

[license-shield]: https://img.shields.io/github/license/acesyde/hassio_agur_integration.svg?style=for-the-badge

[maintenance-shield]: https://img.shields.io/badge/maintainer-Pierre%20Emmanuel%20Mercier%20%40acesyde-blue.svg?style=for-the-badge

[releases-shield]: https://img.shields.io/github/release/acesyde/hassio_agur_integration.svg?style=for-the-badge

[releases]: https://github.com/acesyde/hassio_agur_integration/releases
