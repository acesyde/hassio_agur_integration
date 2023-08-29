# Default api client settings
BASE_URL: str = "https://ael.agur.fr"
DEFAULT_TIMEOUT: int = 10
CONVERSATION_ID: str = "JS-WEB-Netscape-8ca82bba-ef0a-4e83-b89c-5fa28609136b"
CLIENT_ID: str = "AEL-TOKEN-AGR-PRD"
ACCESS_KEY: str = "XX_fr-5DjklsdMM-AGR-PRD"

# List of endpoints
LOGIN_PATH: str = "webapi/Utilisateur/authentification"
GENERATE_TOKEN_PATH: str = "webapi/Acces/generateToken"
GET_DEFAULT_CONTRACT_PATH: str = "webapi/Abonnement/getContratParDefaut/"
GET_CONSUMPTION_PATH: str = "webapi/Facturation/listeConsommationsFacturees/{contract_id}"
