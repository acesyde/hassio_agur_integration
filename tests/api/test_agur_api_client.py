import asyncio
import json
from unittest.mock import patch

import aiohttp
import pytest
from aresponses import ResponsesMockServer

from custom_components.eau_agur.api import AgurApiClient
from custom_components.eau_agur.api.exceptions import (
    AgurApiConnectionError,
    AgurApiError,
    AgurApiInvalidSessionError,
    AgurApiNoBillError,
    AgurApiUnauthorizedError,
)

HOST_PATTERN = "example.com"


@pytest.mark.asyncio
async def test_json_request(aresponses: ResponsesMockServer) -> None:
    """Test JSON response is handled correctly."""
    aresponses.add(HOST_PATTERN, "/", "GET", response={"message": "Hello World!"})

    async with aiohttp.ClientSession() as session:
        client = AgurApiClient(HOST_PATTERN, session=session)
        response = await client.request("/")
        assert response["message"] == "Hello World!"
        await client.close()


@pytest.mark.asyncio
async def test_text_request(aresponses: ResponsesMockServer) -> None:
    """Test non JSON response is handled correctly."""
    aresponses.add(HOST_PATTERN, "/", "GET", aresponses.Response(status=200, text="OK"))
    async with aiohttp.ClientSession() as session:
        client = AgurApiClient(HOST_PATTERN, session=session)
        response = await client.request("/")
        assert response == {"message": "OK"}


@pytest.mark.asyncio
async def test_http_error500(aresponses: ResponsesMockServer):
    """Test HTTP 500 response handling."""
    aresponses.add(HOST_PATTERN, "/", "GET", aresponses.Response(status=500, text="Internal Server Error"))

    async with aiohttp.ClientSession() as session:
        client = AgurApiClient(HOST_PATTERN, session=session)
        with pytest.raises(AgurApiError):
            assert await client.request("/")


@pytest.mark.asyncio
async def test_http_error400(aresponses):
    """Test HTTP 404 response handling."""
    aresponses.add(
        HOST_PATTERN,
        "/",
        "GET",
        aresponses.Response(text="Bad request!", status=400),
    )

    async with aiohttp.ClientSession() as session:
        client = AgurApiClient(HOST_PATTERN, session=session)
        with pytest.raises(AgurApiError):
            assert await client.request("/")


@pytest.mark.asyncio
async def test_timeout(aresponses):
    """Test request timeout."""

    # Faking a timeout by sleeping
    async def response_handler(_):
        """Response handler for this test."""
        await asyncio.sleep(2)
        return aresponses.Response(body="Goodmorning!")

    aresponses.add(HOST_PATTERN, "/", "GET", response_handler)

    async with aiohttp.ClientSession() as session:
        client = AgurApiClient(HOST_PATTERN, session=session, timeout=1)
        with pytest.raises(AgurApiConnectionError):
            assert await client.request("/")


@pytest.mark.asyncio
async def test_client_error():
    """Test request client error."""
    # Faking a timeout by sleeping
    async with aiohttp.ClientSession() as session:
        client = AgurApiClient(HOST_PATTERN, session=session)
        with patch.object(session, "request", side_effect=aiohttp.ClientError), pytest.raises(AgurApiConnectionError):
            assert await client.request("/")


@pytest.mark.asyncio
async def test_post_login(aresponses: ResponsesMockServer):
    """Test requesting consumption data."""
    aresponses.add(
        host_pattern=HOST_PATTERN,
        path_pattern="/webapi/Utilisateur/authentification",
        method_pattern="POST",
        response={
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
                "meta": '{"rgpd_consent":true,"derniere_date_connexion":"31/08/2023 08:45:05"}',
                "profils": ["UTILISATEUR_STANDARD"],
                "isStandardOnly": True,
            },
            "tokenAuthentique": "f7154d97-788f-4e85-930f-a35ebb137dfe",
        },
    )
    async with aiohttp.ClientSession() as session:
        client = AgurApiClient(HOST_PATTERN, session=session)
        await client.login("dupond.toto@mycompany.com", "myP@ssw0rd!")


@pytest.mark.asyncio
async def test_post_login_invalid_session(aresponses: ResponsesMockServer):
    """Test requesting consumption data."""
    aresponses.add(
        host_pattern=HOST_PATTERN,
        path_pattern="/webapi/Utilisateur/authentification",
        method_pattern="POST",
        response=aresponses.Response(
            status=400,
            body=json.dumps(
                {
                    "severity": "Security",
                    "message": "Session Inconnue. Veuillez rafraîchir votre page et vous reconnecter.",
                    "according": "W/FRONT",
                    "refLog": "LogTicket-250705-0745-c8692f2c-485a-48c3-9daa-ded89ad5d246",
                }
            ),
        ),
    )
    async with aiohttp.ClientSession() as session:
        client = AgurApiClient(HOST_PATTERN, session=session)
        with pytest.raises(AgurApiInvalidSessionError):
            await client.login("dupond.toto@mycompany.com", "myP@ssw0rd!")


@pytest.mark.asyncio
async def test_post_login_invalid_credentials(aresponses: ResponsesMockServer):
    """Test requesting consumption data."""
    aresponses.add(
        host_pattern=HOST_PATTERN,
        path_pattern="/webapi/Utilisateur/authentification",
        method_pattern="POST",
        response=aresponses.Response(
            status=401,
            body=json.dumps(
                {
                    "severity": "Security",
                    "message": "Par sécurité au bout de 5 essais infructueux votre compte sera bloqué. Il vous reste 5 essais.",
                    "according": "W/FRONT",
                    "refLog": "LogTicket-250705-0923-98d60ea9-2882-42fe-ab06-43475363c192",
                }
            ),
        ),
    )
    async with aiohttp.ClientSession() as session:
        client = AgurApiClient(HOST_PATTERN, session=session)
        with pytest.raises(AgurApiUnauthorizedError):
            await client.login("dupond.toto@mycompany.com", "myP@ssw0rd!")


@pytest.mark.asyncio
async def test_post_generate_temporary_token(aresponses: ResponsesMockServer):
    """Test requesting generation of a temporary token."""
    aresponses.add(
        host_pattern=HOST_PATTERN,
        path_pattern="/webapi/Acces/generateToken",
        method_pattern="POST",
        response={
            "expirationDate": "2023-08-31T10:45:02.7413425+02:00",
            "token": "314c3a24-d08d-4c86-8c12-371cc242dff6",
        },
    )
    async with aiohttp.ClientSession() as session:
        client = AgurApiClient(HOST_PATTERN, session=session)
        await client.generate_temporary_token()


@pytest.mark.asyncio
async def test_get_consumption(aresponses: ResponsesMockServer):
    """Test requesting consumption data."""
    aresponses.add(
        host_pattern=HOST_PATTERN,
        path_pattern="/webapi/TableauDeBord/derniereConsommationFacturee/12345",
        method_pattern="GET",
        response={
            "numeroContratAbonnement": "12345",
            "dateReleve": "2023-08-29T23:45:43+02:00",
            "volumeConsoEnLitres": 305,
            "volumeConsoEnM3": 0.305,
            "valeurIndex": 448667.0,
            "typeAgregat": 1,
            "anomalieReleve": -1,
        },
    )
    async with aiohttp.ClientSession() as session:
        client = AgurApiClient(HOST_PATTERN, session=session)
        value = await client.get_consumption("12345")
        assert value == 448667.0


@pytest.mark.asyncio
async def test_get_last_invoice(aresponses: ResponsesMockServer):
    """Test requesting consumption data."""
    aresponses.add(
        host_pattern=HOST_PATTERN,
        path_pattern="/webapi/TableauDeBord/dernierReglement/12345",
        method_pattern="GET",
        response={
            "montantTtc": 30.0,
            "natureCompte": "Mensualisation",
            "libelleTypeEcriture": "REGLEMENT",
            "libelleModeReglement": "PRELEVEMENT BANCAIRE",
        },
    )
    async with aiohttp.ClientSession() as session:
        client = AgurApiClient(HOST_PATTERN, session=session)
        value = await client.get_last_invoice("12345")
        assert value == 30.0


@pytest.mark.asyncio
async def test_get_last_invoice_no_bill(aresponses: ResponsesMockServer):
    """Test requesting last invoice when no bill is found."""
    aresponses.add(
        host_pattern=HOST_PATTERN,
        path_pattern="/webapi/TableauDeBord/dernierReglement/12345",
        method_pattern="GET",
        response={
            "montantTtc": None,
            "natureCompte": "Mensualisation",
            "libelleTypeEcriture": "REGLEMENT",
            "libelleModeReglement": "PRELEVEMENT BANCAIRE",
        },
    )
    async with aiohttp.ClientSession() as session:
        client = AgurApiClient(HOST_PATTERN, session=session)
        with pytest.raises(AgurApiNoBillError):
            await client.get_last_invoice("12345")


@pytest.mark.asyncio
async def test_get_last_invoice_missing_montant_ttc(aresponses: ResponsesMockServer):
    """Test requesting last invoice when montantTtc is missing from response."""
    aresponses.add(
        host_pattern=HOST_PATTERN,
        path_pattern="/webapi/TableauDeBord/dernierReglement/12345",
        method_pattern="GET",
        response={
            "natureCompte": "Mensualisation",
            "libelleTypeEcriture": "REGLEMENT",
            "libelleModeReglement": "PRELEVEMENT BANCAIRE",
        },
    )
    async with aiohttp.ClientSession() as session:
        client = AgurApiClient(HOST_PATTERN, session=session)
        with pytest.raises(AgurApiNoBillError):
            await client.get_last_invoice("12345")
