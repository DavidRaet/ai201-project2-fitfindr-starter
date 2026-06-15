"""
tests/test_run_agent.py

Integration tests for the run_agent() planning loop in agent.py.

Tests are written for the final implementation. After wiring only search_listings,
the parsing and no-results tests pass; the full happy-path tests fail until
suggest_outfit and create_fit_card are also wired in.
"""
import pytest
from unittest.mock import patch, MagicMock
from agent import run_agent
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

HAPPY_QUERY = "vintage graphic tee under $30"
NO_MATCH_QUERY = "zzzzzzz xyz ballgown under $1"


@pytest.fixture
def example_wardrobe():
    return get_example_wardrobe()


@pytest.fixture
def empty_wardrobe():
    return get_empty_wardrobe()


def _mock_groq(content="Mock outfit suggestion and fit card."):
    """Patch tools._get_groq_client; returns (patcher, mock_client)."""
    patcher = patch("tools._get_groq_client")
    mock_factory = patcher.start()
    mock_client = MagicMock()
    mock_factory.return_value = mock_client
    mock_client.chat.completions.create.return_value.choices[0].message.content = content
    return patcher, mock_client


# ── Query parsing ─────────────────────────────────────────────────────────────

def test_parsed_stores_description(example_wardrobe):
    patcher, _ = _mock_groq()
    session = run_agent("vintage graphic tee", example_wardrobe)
    patcher.stop()
    assert "description" in session["parsed"]
    assert len(session["parsed"]["description"]) > 0


def test_parsed_stores_price(example_wardrobe):
    patcher, _ = _mock_groq()
    session = run_agent("vintage tee under $30", example_wardrobe)
    patcher.stop()
    assert session["parsed"]["max_price"] == 30.0


def test_parsed_stores_size(example_wardrobe):
    patcher, _ = _mock_groq()
    session = run_agent("vintage tee size M", example_wardrobe)
    patcher.stop()
    assert session["parsed"]["size"].upper() == "M"


def test_parsed_none_when_no_price(example_wardrobe):
    patcher, _ = _mock_groq()
    session = run_agent("vintage graphic tee", example_wardrobe)
    patcher.stop()
    assert session["parsed"]["max_price"] is None


# ── No-results early exit ─────────────────────────────────────────────────────

def test_no_results_sets_error(example_wardrobe):
    session = run_agent(NO_MATCH_QUERY, example_wardrobe)
    assert session["error"] is not None


def test_no_results_returns_early(example_wardrobe):
    session = run_agent(NO_MATCH_QUERY, example_wardrobe)
    assert session["outfit_suggestion"] is None
    assert session["fit_card"] is None


# ── State tracking after search ───────────────────────────────────────────────

def test_search_results_populated(example_wardrobe):
    patcher, _ = _mock_groq()
    session = run_agent(HAPPY_QUERY, example_wardrobe)
    patcher.stop()
    assert isinstance(session["search_results"], list)
    assert len(session["search_results"]) > 0


def test_selected_item_is_first_result(example_wardrobe):
    patcher, _ = _mock_groq()
    session = run_agent(HAPPY_QUERY, example_wardrobe)
    patcher.stop()
    assert session["selected_item"] == session["search_results"][0]


def test_selected_item_has_required_fields(example_wardrobe):
    patcher, _ = _mock_groq()
    session = run_agent(HAPPY_QUERY, example_wardrobe)
    patcher.stop()
    item = session["selected_item"]
    for field in ["id", "title", "price", "size", "category"]:
        assert field in item


def test_session_wardrobe_stored(example_wardrobe):
    patcher, _ = _mock_groq()
    session = run_agent(HAPPY_QUERY, example_wardrobe)
    patcher.stop()
    assert session["wardrobe"] == example_wardrobe


# ── Full happy path (require all 3 tools wired) ───────────────────────────────

def test_happy_path_no_error(example_wardrobe):
    patcher, _ = _mock_groq()
    session = run_agent(HAPPY_QUERY, example_wardrobe)
    patcher.stop()
    assert session["error"] is None


def test_happy_path_outfit_populated(example_wardrobe):
    patcher, _ = _mock_groq(content="Pair with baggy jeans and chunky sneakers.")
    session = run_agent(HAPPY_QUERY, example_wardrobe)
    patcher.stop()
    assert session["outfit_suggestion"] is not None
    assert len(session["outfit_suggestion"]) > 0


def test_happy_path_fit_card_populated(example_wardrobe):
    patcher, _ = _mock_groq()
    session = run_agent(HAPPY_QUERY, example_wardrobe)
    patcher.stop()
    assert session["fit_card"] is not None
    assert len(session["fit_card"]) > 0


def test_empty_wardrobe_completes_no_error(empty_wardrobe):
    patcher, _ = _mock_groq()
    session = run_agent(HAPPY_QUERY, empty_wardrobe)
    patcher.stop()
    assert session["error"] is None
