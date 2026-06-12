"""Tests for create_fit_card in tools.py — written before implementation (TDD)."""

import pytest
from unittest.mock import patch, MagicMock
from tools import create_fit_card
from utils.data_loader import load_listings


@pytest.fixture
def sample_item():
    return load_listings()[0]


@pytest.fixture
def sample_outfit():
    return "Pair with high-waisted jeans and white sneakers for a clean streetwear look."


def _patched_client(content="Caption from LLM."):
    """Return a (patch context manager, mock_client) pair with canned LLM content."""
    patcher = patch("tools._get_groq_client")
    mock_factory = patcher.start()
    mock_client = MagicMock()
    mock_factory.return_value = mock_client
    mock_client.chat.completions.create.return_value.choices[0].message.content = content
    return patcher, mock_client


def test_returns_nonempty_string(sample_item, sample_outfit):
    patcher, _ = _patched_client()
    try:
        result = create_fit_card(sample_outfit, sample_item)
        assert isinstance(result, str)
        assert len(result) > 0
    finally:
        patcher.stop()


def test_does_not_raise(sample_item, sample_outfit):
    patcher, _ = _patched_client()
    try:
        try:
            create_fit_card(sample_outfit, sample_item)
        except Exception as exc:
            pytest.fail(f"create_fit_card raised an exception: {exc}")
    finally:
        patcher.stop()


def test_llm_called_exactly_once(sample_item, sample_outfit):
    patcher, mock_client = _patched_client()
    try:
        create_fit_card(sample_outfit, sample_item)
        assert mock_client.chat.completions.create.call_count == 1
    finally:
        patcher.stop()


def test_llm_response_content_is_returned(sample_item, sample_outfit):
    expected = "Thrifted this gem for under $20 on Depop and I'm obsessed!"
    patcher, _ = _patched_client(content=expected)
    try:
        result = create_fit_card(sample_outfit, sample_item)
        assert result == expected
    finally:
        patcher.stop()


def test_item_title_appears_in_prompt(sample_item, sample_outfit):
    patcher, mock_client = _patched_client()
    try:
        create_fit_card(sample_outfit, sample_item)
        call_args = mock_client.chat.completions.create.call_args
        assert call_args is not None, "LLM was never called"
        prompt_text = str(call_args)
        assert sample_item["title"].lower() in prompt_text.lower(), (
            f"Expected item title '{sample_item['title']}' in LLM prompt, but got:\n{prompt_text}"
        )
    finally:
        patcher.stop()


def test_item_price_appears_in_prompt(sample_item, sample_outfit):
    patcher, mock_client = _patched_client()
    try:
        create_fit_card(sample_outfit, sample_item)
        call_args = mock_client.chat.completions.create.call_args
        assert call_args is not None, "LLM was never called"
        prompt_text = str(call_args)
        assert str(sample_item["price"]) in prompt_text, (
            f"Expected item price '{sample_item['price']}' in LLM prompt, but got:\n{prompt_text}"
        )
    finally:
        patcher.stop()


def test_item_platform_appears_in_prompt(sample_item, sample_outfit):
    patcher, mock_client = _patched_client()
    try:
        create_fit_card(sample_outfit, sample_item)
        call_args = mock_client.chat.completions.create.call_args
        assert call_args is not None, "LLM was never called"
        prompt_text = str(call_args)
        assert sample_item["platform"].lower() in prompt_text.lower(), (
            f"Expected platform '{sample_item['platform']}' in LLM prompt, but got:\n{prompt_text}"
        )
    finally:
        patcher.stop()


def test_outfit_appears_in_prompt(sample_item, sample_outfit):
    patcher, mock_client = _patched_client()
    try:
        create_fit_card(sample_outfit, sample_item)
        call_args = mock_client.chat.completions.create.call_args
        assert call_args is not None, "LLM was never called"
        prompt_text = str(call_args)
        assert sample_outfit.lower() in prompt_text.lower(), (
            f"Expected outfit text in LLM prompt, but got:\n{prompt_text}"
        )
    finally:
        patcher.stop()


def test_uses_higher_temperature(sample_item, sample_outfit):
    patcher, mock_client = _patched_client()
    try:
        create_fit_card(sample_outfit, sample_item)
        call_args = mock_client.chat.completions.create.call_args
        assert call_args is not None, "LLM was never called"
        temperature = call_args.kwargs.get("temperature") or call_args[1].get("temperature")
        assert temperature is not None, "temperature kwarg was not passed to LLM"
        assert temperature >= 0.8, f"Expected temperature >= 0.8 for variety, got {temperature}"
    finally:
        patcher.stop()


def test_empty_outfit_returns_error_string(sample_item):
    result = create_fit_card("", sample_item)
    assert isinstance(result, str)
    assert len(result) > 0
    assert "error" in result.lower() or "missing" in result.lower() or "incomplete" in result.lower()


def test_whitespace_only_outfit_returns_error_string(sample_item):
    result = create_fit_card("   ", sample_item)
    assert isinstance(result, str)
    assert len(result) > 0
    assert "error" in result.lower() or "missing" in result.lower() or "incomplete" in result.lower()


def test_missing_api_key_raises_value_error(sample_item, sample_outfit):
    with patch.dict("os.environ", {"GROQ_API_KEY": ""}):
        with pytest.raises(ValueError):
            create_fit_card(sample_outfit, sample_item)
