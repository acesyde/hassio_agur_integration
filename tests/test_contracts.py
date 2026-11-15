"""Contract discovery and selection preserve existing installations."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import AbortFlow
from homeassistant.exceptions import ConfigEntryAuthFailed

from custom_components.eau_agur import config_flow
from custom_components.eau_agur.api import AgurApiClient, AgurApiError, AgurApiUnauthorizedError
from custom_components.eau_agur.coordinator import EauAgurDataUpdateCoordinator


def contract(number):
    return {"numeroContrat": number, "adresseLivraisonConstruite": "Adresse fictive", "libelleEtatContrat": "Actif"}


def page(rows, total):
    return {"resultats": rows, "nbTotalResultats": total}


@pytest.mark.asyncio
@pytest.mark.parametrize("total", [0, 1, 25, 26, 50])
async def test_contract_list_includes_all_pages(total):
    rows = [contract(f"{number:05}") for number in range(total)]
    pages = [page(rows[start : start + 25], total) for start in range(0, total, 25)] or [page([], 0)]
    client = AgurApiClient()
    client.request = AsyncMock(side_effect=pages)
    result = await client.get_contracts()
    assert list(result) == [row["numeroContrat"] for row in rows]
    assert client.request.await_count == len(pages)
    for index, call in enumerate(client.request.await_args_list):
        assert call.args == ("Abonnement/contrats",)
        assert call.kwargs["params"]["indexPage"] == str(index)
        assert call.kwargs["params"]["nbElements"] == "25"
        assert call.kwargs["params"]["userWebId"] == ""
        assert call.kwargs["params"]["recherche"] == ""
    if total:
        assert "00000" in result["00000"] and "Adresse fictive" in result["00000"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "responses",
    [
        [None],
        [{}],
        [page({}, 0)],
        [page([], True)],
        [page([], -1)],
        [page([None], 1)],
        [page([{}], 1)],
        [page([contract(123)], 1)],
        [page([contract("")], 1)],
        [page([contract("001")], 0)],
        [page([contract("001")], 2), page([], 2)],
        [page([contract("001")], 2), page([contract("001")], 2)],
        [page([contract("001")], 2), page([contract("002")], 3)],
        [page([contract("001")], 2), AgurApiError(500)],
    ],
)
async def test_bad_contract_lists_are_not_partially_accepted(responses):
    client = AgurApiClient()
    client.request = AsyncMock(side_effect=responses)
    with pytest.raises(AgurApiError):
        await client.get_contracts()


@pytest.mark.asyncio
async def test_contract_auth_failure():
    client = AgurApiClient()
    client.request = AsyncMock(side_effect=AgurApiError(401))
    with pytest.raises(AgurApiUnauthorizedError):
        await client.get_contracts()


def make_flow(entries=()):
    flow = config_flow.EauAgurFlowHandler()
    flow.handler = "eau_agur"
    flow.context = {"source": "user"}
    flow.hass = SimpleNamespace(config_entries=Mock())
    flow.hass.config_entries.flow.async_progress_by_handler.return_value = []
    flow.hass.config_entries.async_entry_for_domain_unique_id.side_effect = lambda domain, unique_id: next(
        (entry for entry in entries if entry.unique_id == unique_id), None
    )
    flow._async_current_entries = Mock(return_value=entries)
    return flow


@pytest.mark.asyncio
@pytest.mark.parametrize("numbers", [[], ["001"], ["001", "002"]])
async def test_login_selects_single_contract_or_offers_choice(numbers):
    flow = make_flow()
    session = Mock()
    client = Mock(
        generate_temporary_token=AsyncMock(),
        login=AsyncMock(),
        get_default_contract=AsyncMock(return_value="001"),
        get_contracts=AsyncMock(return_value={n: n for n in numbers}),
    )
    with (
        patch.object(config_flow, "async_create_clientsession", return_value=session),
        patch.object(config_flow, "AgurApiClient", return_value=client),
    ):
        result = await flow.async_step_user(
            {"email": "test@example.com", "password": "test-password", "provider": "agur"}
        )
    session.detach.assert_called_once()
    if not numbers:
        assert result["type"] == "abort" and result["reason"] == "no_contracts"
    elif len(numbers) == 1:
        assert result["type"] == "create_entry"
        assert result["data"]["contract_number"] == "001"
        assert result["context"]["unique_id"] == "agur:001"
    else:
        assert result["step_id"] == "contract"
        assert next(iter(result["data_schema"].schema)).default() == "001"
        result = await flow.async_step_contract({"contract_number": "002"})
        assert result["type"] == "create_entry"
        assert result["data"]["contract_number"] == "002"
        assert result["title"] == "Eau par Agur — 002"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "provider,number,unique_id,duplicate",
    [
        ("agur", "001", "001", True),  # legacy entry
        ("agur", "001", "agur:001", True),
        ("agur", "002", "agur:002", False),
        ("eauparis", "001", "001", False),
    ],
)
async def test_duplicate_checks_include_legacy_entries_and_provider(provider, number, unique_id, duplicate):
    entry = SimpleNamespace(source="user", unique_id=unique_id, data={"provider": provider, "contract_number": number})
    original_data = entry.data.copy()
    flow = make_flow([entry])
    flow._contracts = {"001": "001", "002": "002"}
    flow._default_contract = "001"
    flow._contract_data = {"email": "another@example.com", "password": "test-password", "provider": "agur"}
    try:
        result = await flow.async_step_contract({"contract_number": "001"})
    except AbortFlow as exception:
        assert duplicate and exception.reason == "already_configured"
    else:
        assert result["type"] == ("abort" if duplicate else "create_entry")
        if duplicate:
            assert result["reason"] == "already_configured"
    assert entry.data == original_data and entry.unique_id == unique_id


@pytest.mark.asyncio
async def test_invalid_choice_and_missing_default():
    flow = make_flow()
    flow._contracts = {"002": "002", "003": "003"}
    flow._default_contract = "001"
    flow._contract_data = {"provider": "agur"}
    result = await flow.async_step_contract({"contract_number": "999"})
    assert result["errors"] == {"base": "invalid_contract"}
    field = next(iter(result["data_schema"].schema))
    assert field.default is config_flow.vol.UNDEFINED
    result = await flow.async_step_contract({"contract_number": "002"})
    assert result["data"]["contract_number"] == "002"


@pytest.mark.asyncio
async def test_simultaneous_addition_of_same_contract_aborts():
    flow = make_flow()
    flow._contracts = {"001": "001"}
    flow._contract_data = {"provider": "agur"}
    flow.hass.config_entries.flow.async_progress_by_handler.side_effect = lambda *args, **kwargs: [
        {"flow_id": "another-flow", "context": {"source": "user", "unique_id": "agur:001"}}
    ]
    with pytest.raises(AbortFlow, match="already_in_progress"):
        await flow.async_step_contract({"contract_number": "001"})


@pytest.mark.asyncio
async def test_contract_list_failure_releases_session_and_creates_no_entry():
    flow = make_flow()
    session = Mock()
    client = Mock(
        generate_temporary_token=AsyncMock(),
        login=AsyncMock(),
        get_contracts=AsyncMock(side_effect=AgurApiError("invalid contract list")),
    )
    with (
        patch.object(config_flow, "async_create_clientsession", return_value=session),
        patch.object(config_flow, "AgurApiClient", return_value=client),
    ):
        result = await flow.async_step_user(
            {"email": "test@example.com", "password": "test-password", "provider": "agur"}
        )
    assert result["step_id"] == "user" and result["errors"] == {"base": "unknown"}
    session.detach.assert_called_once()
    flow.hass.config_entries.async_update_entry.assert_not_called()


@pytest.mark.asyncio
async def test_each_coordinator_keeps_its_stored_contract(tmp_path):
    hass = HomeAssistant(str(tmp_path))
    coordinators = []
    for number in ("001", "002"):
        entry = Mock(
            entry_id=number, data={"email": "test@example.com", "password": "test-password", "contract_number": number}
        )
        client = Mock(
            generate_temporary_token=AsyncMock(),
            login=AsyncMock(),
            get_consumption=AsyncMock(return_value={"index": 10, "date": None}),
            get_last_invoice=AsyncMock(return_value=20),
            get_balance=AsyncMock(return_value=30),
            get_last_issued_invoice=AsyncMock(return_value=None),
        )
        coordinator = EauAgurDataUpdateCoordinator(hass, client, entry)
        assert coordinator.config_entry is entry
        entry.async_on_unload.assert_called_once()
        coordinator.data = await coordinator._async_update_data()
        for method in (
            client.get_consumption,
            client.get_last_invoice,
            client.get_balance,
            client.get_last_issued_invoice,
        ):
            method.assert_awaited_once_with(number)
        client.get_default_contract.assert_not_called()
        coordinators.append(coordinator)
    coordinators[1]._api_client.login.side_effect = AgurApiUnauthorizedError("expired")
    with pytest.raises(ConfigEntryAuthFailed):
        await coordinators[1]._async_update_data()
    assert (await coordinators[0]._async_update_data()) == coordinators[0].data
