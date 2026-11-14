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

## Capteurs

| Clé du capteur | Donnée fournie | Unité |
|----------------|----------------|-------|
| `total_liters` | Dernier index du compteur communiqué par le portail | L |
| `last_invoice` | Montant du dernier règlement communiqué par le portail | € |
| `balance` | Solde comptable du contrat | € |

Le capteur `total_liters` expose l’attribut `reading_date` avec la date réelle du relevé lorsqu’elle est fournie et valide. Cette date peut être antérieure au dernier rafraîchissement de l’intégration.

Le capteur `last_invoice` porte par défaut le nom « Dernière facture » dans l’interface, mais sa donnée provient du dernier règlement du portail.

Le solde conserve le signe fourni par le portail, y compris zéro et les montants négatifs. Il ne représente pas le coût cumulé de l’eau. Une erreur de lecture du solde laisse les autres données disponibles ; les erreurs d’authentification restent traitées au niveau du compte.

### Identifiants des entités

Les clés ci-dessus ne sont pas des identifiants complets. Pour les **nouvelles entités**, Home Assistant génère les identifiants `sensor.…` selon le format choisi dans ses paramètres : pièce, appareil parent, appareil et entité. Les éléments sans valeur sont omis ; les noms dépendent des informations disponibles et de la langue choisie pour les identifiants.

Les identifiants des **entités déjà enregistrées**, y compris les noms personnalisés, sont conservés lors d’une mise à jour. Modifier le format de nommage ne les renomme pas automatiquement. Pour appliquer un autre nom à une entité existante, modifiez son identifiant dans ses paramètres et vérifiez les références dans vos automatisations et tableaux de bord.

### Actualisation

L’intégration interroge le portail toutes les **4 heures**. La disponibilité de nouveaux relevés dépend du fournisseur : les données ne sont pas des mesures en temps réel.

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
