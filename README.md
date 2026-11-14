# EAU par Agur

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![marketplace][marketplacebadge]][marketplace]
![Project Maintenance][maintenance-shield]

_Intégration pour les providers suivants :_

- [EAU par Agur][eau_agur]
- [EAU par Grand Paris Sud][eau_grandparissud]
- [EAU de Paris][eau_de_paris]

🌏
Français |
[**English**](README.en.md)

**L'intégration ajoutera les composants suivants.**

| Platform              | Description                    | Unit | Implemented        |
|-----------------------|--------------------------------|------|--------------------|
| `sensor.total_liters` | Nombre de litres consommés     | L    | :white_check_mark: |
| `sensor.last_invoice` | Montant de la dernière facture | €    | :white_check_mark: |
| `sensor.balance` | Solde comptable du contrat | € | :white_check_mark: |

Le capteur `sensor.total_liters` expose l’attribut `reading_date` avec la date réelle du relevé lorsqu’elle est fournie et valide.

Le solde conserve le signe fourni par le portail, y compris zéro et les montants négatifs. Il ne représente pas le coût cumulé de l’eau. Si sa lecture échoue, seul ce montant devient inconnu.

> [!NOTE]
> Les données sont mises à jour toutes les 24h.

## Installation

### Marketplace Home Assistant (2026.11+)

1. Dans Home Assistant, allez dans **Paramètres → Marketplace**.
2. Choisissez **Add from link**, collez `https://github.com/acesyde/hassio_agur_integration` et connectez votre compte GitHub si demandé.
3. Installez **EAU par Agur**, puis redémarrez Home Assistant.

Ou cliquez sur ce bouton :

[![Ouvrez votre instance Home Assistant et ouvrez un dépôt dans le Home Assistant Marketplace.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=acesyde&repository=hassio_agur_integration&category=integration)

> Depuis 2026.11, HACS est intégré à Home Assistant sous le nom de Marketplace. Les installations existantes via HACS sont migrées automatiquement.

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

[eau_de_paris]: https://agence.eaudeparis.fr/

[commits-shield]: https://img.shields.io/github/commit-activity/y/acesyde/hassio_agur_integration.svg?style=for-the-badge

[commits]: https://github.com/acesyde/hassio_agur_integration/commits/main

[marketplace]: https://www.home-assistant.io/integrations/marketplace/#custom-repositories

[marketplacebadge]: https://img.shields.io/badge/Marketplace-Custom-orange.svg?style=for-the-badge

[license-shield]: https://img.shields.io/github/license/acesyde/hassio_agur_integration.svg?style=for-the-badge

[maintenance-shield]: https://img.shields.io/badge/maintainer-Pierre%20Emmanuel%20Mercier%20%40acesyde-blue.svg?style=for-the-badge

[releases-shield]: https://img.shields.io/github/release/acesyde/hassio_agur_integration.svg?style=for-the-badge

[releases]: https://github.com/acesyde/hassio_agur_integration/releases
