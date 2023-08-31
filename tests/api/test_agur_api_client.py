import json

import aiohttp
import pytest
from aresponses import ResponsesMockServer
from custom_components.eau_agur.api import AgurApiClient


@pytest.mark.asyncio
async def test_json_request(aresponses: ResponsesMockServer) -> None:
    """Test JSON response is handled correctly."""
    aresponses.add(
        "example.com",
        "/",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text='{"message": "Hello World!"}',
        ),
    )

    async with aiohttp.ClientSession() as session:
        client = AgurApiClient("example.com", session=session)
        response = await client.request("/")
        assert response["message"] == "Hello World!"
        await client.close()


@pytest.mark.asyncio
async def test_text_request(aresponses: ResponsesMockServer) -> None:
    """Test non JSON response is handled correctly."""
    aresponses.add(
        "example.com",
        "/",
        "GET",
        aresponses.Response(status=200, text="OK")
    )
    async with aiohttp.ClientSession() as session:
        client = AgurApiClient("example.com", session=session)
        response = await client.request("/")
        assert response == {"message": "OK"}


@pytest.mark.asyncio
async def test_post_login(aresponses: ResponsesMockServer):
    """Test requesting consumption data."""
    aresponses.add(
        "example.com",
        "/Utilisateur/authentification",
        "POST",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=json.dumps({
                "utilisateurInfo": {
                    "dateCreation": "2022-01-01T00:00:00+01:00",
                    "dateModification": "2023-02-15T15:16:29+01:00",
                    "mailValide": True,
                    "userWebId": 12345,
                    "identifiant": "dupond.toto@mycompany.com",
                    "titre": "M",
                    "nom": "DUPOND",
                    "prenom": "TOTO",
                    "email": "dupond.toto@mycompany.com",
                    "meta": "{\"rgpd_consent\":true,\"derniere_date_connexion\":\"31/08/2023 08:45:05\"}",
                    "profils": [
                        "UTILISATEUR_STANDARD"
                    ],
                    "isStandardOnly": True
                },
                "tokenAuthentique": "f7154d97-788f-4e85-930f-a35ebb137dfe"
            }),
        ),
    )
    async with aiohttp.ClientSession() as session:
        client = AgurApiClient("example.com", session=session)
        is_authenticated = await client.login("dupond.toto@mycompany.com", "myP@ssw0rd!")
        assert is_authenticated is True


@pytest.mark.asyncio
async def test_get_default_contract(aresponses: ResponsesMockServer):
    """Test requesting default contract data."""
    aresponses.add(
        "example.com",
        "/Abonnement/getContratParDefaut/",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=json.dumps({
                "numeroContrat": "12345",
                "nomClientTitulaire": "DUPOND TOTO",
                "codeEtatContrat": "SE",
                "libelleEtatContrat": "EN SERVICE",
                "libelleLongEtatContrat": "EN SERVICE",
                "typeContrat": {
                    "code": "EA",
                    "libelle": "Eau"
                },
                "codeCategorieContrat": 100,
                "libelleCategorieContrat": "DOMESTIQUES ET ASSIMILÉS",
                "libelleTypePrelevement": "Mensualisation",
                "codeModeDistribFacture": "03",
                "libelleModeDistribFacture": "Dématérialisé",
                "codeCategorieFacturation": "100",
                "libelleCategorieFacturation": "DOMESTIQUES ET ASSIMILÉS",
                "numeroPhysiqueAppareil": "ABCDEF",
                "diametreCompteur": "15,0",
                "identifiantAppareil": "000000",
                "dateEtat": "2022-09-06T00:00:00+02:00",
                "codeRythmeReleve": "AN",
                "libelleRythmeReleve": "ANNEE",
                "codeRythmeFacturation": "SE",
                "libelleRythmeFacturation": "SEMESTRIEL",
                "numeroClientTitulaire": "000000",
                "numeroClientPayeur": "000000",
                "nomClientPayeur": "DUPOND TOTO",
                "numeroPointLivraison": "000000",
                "adresseLivraisonConstruite": "RUE DU COIN\r\n 33380 MIOS",
                "adresseLivraison": {
                    "adresse": " RUE DU COIN",
                    "complementAdresse": "LOTISSEMENT 2000",
                    "codePostal": "33380",
                    "ville": "MIOS",
                    "pays": {
                        "code": "FRA"
                    }
                },
                "compteur": {
                    "diametre": "15,0",
                    "datePoseAppareil": "2019-04-26T00:00:00+02:00",
                    "isTelereleve": "true"
                },
                "dateDeMiseEnService": "2015-03-06T00:00:00+01:00",
                "dateCreation": "2015-03-06T00:00:00+01:00",
                "traiteJuridique": {
                    "identifiantTraiteSecondaire": "000",
                    "libelleTraiteSecondaire": "COBAN MIOS ASST",
                    "codeTypeTraiteSecondaire": "000"
                },
                "traiteFacturation": {
                    "id": 000,
                    "code": "000",
                    "libelle": "COBAN"
                },
                "isResiliable": True,
                "isIndexSaisisable": True,
                "isDefautContrat": True,
                "libelle": "",
                "idReferenceBancaire": 000000,
                "chorusInfo": {}
            }),
        ),
    )
    async with aiohttp.ClientSession() as session:
        client = AgurApiClient("example.com", session=session)
        numero_contrat = await client.get_default_contract()
        assert numero_contrat == "12345"


@pytest.mark.asyncio
async def test_get_consumption(aresponses: ResponsesMockServer):
    """Test requesting consumption data."""
    aresponses.add(
        "example.com",
        "/TableauDeBord/derniereConsommationFacturee/12345",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=json.dumps({
                "numeroContratAbonnement": "12345",
                "dateReleve": "2023-08-29T23:45:43+02:00",
                "volumeConsoEnLitres": 305,
                "volumeConsoEnM3": 0.305,
                "valeurIndex": 448667.0,
                "typeAgregat": 1,
                "anomalieReleve": -1
            }),
        ),
    )
    async with aiohttp.ClientSession() as session:
        client = AgurApiClient("example.com", session=session)
        value = await client.get_consumption("12345")
        assert value == 448667.0
