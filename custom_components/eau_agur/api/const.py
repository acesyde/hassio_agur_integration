# Logging
from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

# Default api client settings
BASE_URL: str = "ael.agur.fr"
BASE_PATH: str = "/webapi"
DEFAULT_TIMEOUT: int = 10
CONVERSATION_ID: str = "JS-WEB-Netscape-8ca82bba-ef0a-4e83-b89c-5fa28609136b"
CLIENT_ID: str = "AEL-TOKEN-AGR-PRD"
ACCESS_KEY: str = "XX_fr-5DjklsdMM-AGR-PRD"

# List of endpoints
LOGIN_PATH: str = "Utilisateur/authentification"
GENERATE_TOKEN_PATH: str = "Acces/generateToken"
GET_DEFAULT_CONTRACT_PATH: str = "Abonnement/getContratParDefaut/"
GET_CONSUMPTION_PATH: str = "TableauDeBord/derniereConsommationFacturee/"
GET_LAST_INVOICE_PATH: str = "TableauDeBord/dernierReglement/"
