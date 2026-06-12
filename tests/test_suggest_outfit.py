"""Tests for suggest_outfit in tools.py — written before implementation (TDD)."""

import pytest
from unittest.mock import patch, MagicMock
from tools import suggest_outfit
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe, load_listings


@pytest.fixture
def sample_item():
    return load_listings()[0]


@pytest.fixture
def example_wardrobe():
    return get_example_wardrobe()


@pytest.fixture
def empty_wardrobe():
    return get_empty_wardrobe()


def _patched_client(content="Outfit suggestion from LLM."):
    """Return a (patch context manager, mock_client) pair with canned LLM content."""
    patcher = patch("tools._get_groq_client")
    mock_factory = patcher.start()
    mock_client = MagicMock()
    mock_factory.return_value = mock_client
    mock_client.chat.completions.create.return_value.choices[0].message.content = content
    return patcher, mock_client


def test_returns_nonempty_string_with_full_wardrobe(sample_item, example_wardrobe):
    patcher, _ = _patched_client()
    try:
        result = suggest_outfit(sample_item, example_wardrobe)
        assert isinstance(result, str)
        assert len(result) > 0
    finally:
        patcher.stop()


def test_returns_nonempty_string_with_empty_wardrobe(sample_item, empty_wardrobe):
    patcher, _ = _patched_client()
    try:
        result = suggest_outfit(sample_item, empty_wardrobe)
        assert isinstance(result, str)
        assert len(result) > 0
    finally:
        patcher.stop()


def test_does_not_raise_with_full_wardrobe(sample_item, example_wardrobe):
    patcher, _ = _patched_client()
    try:
        try:
            suggest_outfit(sample_item, example_wardrobe)
        except Exception as exc:
            pytest.fail(f"suggest_outfit raised an exception with full wardrobe: {exc}")
    finally:
        patcher.stop()


def test_does_not_raise_with_empty_wardrobe(sample_item, empty_wardrobe):
    patcher, _ = _patched_client()
    try:
        try:
            suggest_outfit(sample_item, empty_wardrobe)
        except Exception as exc:
            pytest.fail(f"suggest_outfit raised an exception with empty wardrobe: {exc}")
    finally:
        patcher.stop()


def test_llm_called_exactly_once_full_wardrobe(sample_item, example_wardrobe):
    patcher, mock_client = _patched_client()
    try:
        suggest_outfit(sample_item, example_wardrobe)
        assert mock_client.chat.completions.create.call_count == 1
    finally:
        patcher.stop()


def test_llm_called_exactly_once_empty_wardrobe(sample_item, empty_wardrobe):
    patcher, mock_client = _patched_client()
    try:
        suggest_outfit(sample_item, empty_wardrobe)
        assert mock_client.chat.completions.create.call_count == 1
    finally:
        patcher.stop()


def test_llm_response_content_is_returned(sample_item, example_wardrobe):
    expected = "Pair with wide-leg khaki trousers and chunky sneakers for a relaxed streetwear look."
    patcher, _ = _patched_client(content=expected)
    try:
        result = suggest_outfit(sample_item, example_wardrobe)
        assert result == expected
    finally:
        patcher.stop()


def test_wardrobe_item_names_appear_in_prompt(sample_item, example_wardrobe):
    patcher, mock_client = _patched_client()
    try:
        suggest_outfit(sample_item, example_wardrobe)
        call_args = mock_client.chat.completions.create.call_args
        assert call_args is not None, "LLM was never called"
        prompt_text = str(call_args)
        first_item_name = example_wardrobe["items"][0]["name"]
        assert first_item_name.lower() in prompt_text.lower(), (
            f"Expected wardrobe item name '{first_item_name}' in LLM prompt, but got:\n{prompt_text}"
        )
    finally:
        patcher.stop()


def test_missing_api_key_raises_value_error(sample_item, example_wardrobe):
    with patch.dict("os.environ", {"GROQ_API_KEY": ""}):
        with pytest.raises(ValueError):
            suggest_outfit(sample_item, example_wardrobe)
