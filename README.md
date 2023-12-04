# EAU par Agur

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]][hacs]
![Project Maintenance][maintenance-shield]

_Intégration pour les providers suivants :_
- [EAU par Agur][eau_agur]
- [EAU par Grand Paris Sud][eau_grandparissud]

🌏
Français |
[**English**](README.en.md)

**L'intégration ajoutera les composants suivants.**

| Platform              | Description                | Unit | Implemented        |
|-----------------------|----------------------------|------|--------------------|
| `sensor.total_liters` | Nombre de litres consommés | L    | :white_check_mark: |

> [!NOTE]
> Les données sont mises à jour toutes les 24h.

## Installation

### Automatique

[![Ouvrez votre instance Home Assistant et ajouter un dépôt personnalisé.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=acesyde&repository=hassio_agur_integration&category=integration)

### Manuelle

1. À l'aide de l'outil de votre choix, ouvrez le répertoire (dossier) de votre configuration HA (où vous
   trouvez `configuration.yaml`).
2. Si vous n'avez pas le répertoire `custom_components`, il vous faudra le créer.
3. Dans le répertoire `custom_components`, créez un nouveau dossier nommé `eau_agur`.
4. Téléchargez _tous_ les fichiers du répertoire (dossier) `custom_components/eau_agur/` dans ce référentiel.
5. Placez les fichiers que vous avez téléchargés dans le nouveau répertoire (dossier) que vous avez créé.
6. Redémarrer Home Assistant.
7. Dans l'interface utilisateur HA, allez dans "Configuration" -> "Intégrations", cliquez sur "+" et recherchez "EAU par
   Agur".

## Les contributions sont les bienvenues !

Si vous souhaitez y contribuer, veuillez lire les [Directives de contribution](CONTRIBUTING.md)

***

[eau_agur]: https://www.agur.fr/

[eau_grandparissud]: https://abonne-eau.grandparissud.fr/

[commits-shield]: https://img.shields.io/github/commit-activity/y/acesyde/hassio_agur_integration.svg?style=for-the-badge

[commits]: https://github.com/acesyde/hassio_agur_integration/commits/main

[hacs]: https://github.com/hacs/integration

[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge

[license-shield]: https://img.shields.io/github/license/acesyde/hassio_agur_integration.svg?style=for-the-badge

[maintenance-shield]: https://img.shields.io/badge/maintainer-Pierre%20Emmanuel%20Mercier%20%40acesyde-blue.svg?style=for-the-badge

[releases-shield]: https://img.shields.io/github/release/acesyde/hassio_agur_integration.svg?style=for-the-badge

[releases]: https://github.com/acesyde/hassio_agur_integration/releases
