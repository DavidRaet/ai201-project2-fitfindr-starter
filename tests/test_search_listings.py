"""Tests for search_listings in tools.py — written before implementation (TDD)."""

import pytest
from tools import search_listings

def test_happy_path_returns_results():
    results = search_listings("vintage graphic tee")
    assert len(results) >= 1


def test_price_filter_excludes_expensive_items():
    results = search_listings("jeans", max_price=20)
    for item in results:
        assert item["price"] <= 20


def test_price_filter_inclusive_boundary():
    results = search_listings("vintage", max_price=18)
    for item in results:
        assert item["price"] <= 18


def test_size_filter_case_insensitive():
    results = search_listings("shirt", size="M")
    for item in results:
        assert "m" in item["size"].lower()


def test_size_filter_substring_match():
    # "xl" should match "XL (oversized)"
    results = search_listings("top", size="xl")
    for item in results:
        assert "xl" in item["size"].lower()


def test_no_match_returns_empty_list():
    results = search_listings("zzzzz")
    assert results == []


def test_no_match_does_not_raise():
    try:
        results = search_listings("xkzqjvwp")
        assert isinstance(results, list)
    except Exception as exc:
        pytest.fail(f"search_listings raised an exception: {exc}")


def test_score_ordering():
    results = search_listings("vintage graphic tee")
    assert len(results) >= 2, "Need at least 2 results to verify ordering"
    # Verify results are in non-increasing score order by checking the first
    # result is at least as relevant as the second (spot check with keyword count)
    first_title = results[0]["title"].lower() + " ".join(results[0].get("style_tags", []))
    second_title = results[1]["title"].lower() + " ".join(results[1].get("style_tags", []))
    keywords = {"vintage", "graphic", "tee"}
    first_score = len(keywords & set(first_title.split()))
    second_score = len(keywords & set(second_title.split()))
    assert first_score >= second_score


def test_combined_filters():
    results = search_listings("vintage", size="S", max_price=25)
    for item in results:
        assert item["price"] <= 25
        assert "s" in item["size"].lower()


def test_returns_list_of_dicts():
    results = search_listings("denim")
    assert isinstance(results, list)
    for item in results:
        assert isinstance(item, dict)
        for field in ("id", "title", "price", "size", "style_tags"):
            assert field in item
