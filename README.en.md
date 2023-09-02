# EAU par Agur

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]][hacs]
![Project Maintenance][maintenance-shield]

_Integration to integrate with [EAU par Agur][eau_agur]._

🌏
[**Français**](README.md) |
English

**This integration will set up the following platforms.**

| Platform          | Description  | Unit | Implemented        |
|-------------------|--------------|------|--------------------|
| `sensor.total_m3` | Number of m3 | m3   | :white_check_mark: |

## Installation

## Automatic

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=acesyde&repository=hassio_agur_integration&category=integration)

## Manual

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

[commits-shield]: https://img.shields.io/github/commit-activity/y/acesyde/hassio_agur_integration.svg?style=for-the-badge

[commits]: https://github.com/acesyde/hassio_agur_integration/commits/main

[hacs]: https://github.com/hacs/integration

[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge

[license-shield]: https://img.shields.io/github/license/acesyde/hassio_agur_integration.svg?style=for-the-badge

[maintenance-shield]: https://img.shields.io/badge/maintainer-Pierre%20Emmanuel%20Mercier%20%40acesyde-blue.svg?style=for-the-badge

[releases-shield]: https://img.shields.io/github/release/acesyde/hassio_agur_integration.svg?style=for-the-badge

[releases]: https://github.com/acesyde/hassio_agur_integration/releases
