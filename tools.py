"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────


def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────


def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    listings = load_listings()

    if max_price is not None:
        listings = [item for item in listings if item["price"] <= max_price]
    if size is not None:
        size_lowerCase = size.lower()
        listings = [item for item in listings if size_lowerCase in item["size"].lower()]

    keywords = set(description.lower().split())

    def _score(listing):
        text_fields = [
            listing.get("title", ""),
            listing.get("description", ""),
            listing.get("category", ""),
            listing.get("brand", "") or "",
        ]
        tokens = set(" ".join(text_fields).lower().split())
        tag_tokens = {tag.lower() for tag in listing.get("style_tags", [])}
        color_tokens = {c.lower() for c in listing.get("colors", [])}
        return len(keywords & (tokens | tag_tokens | color_tokens))

    scored = [(score, item) for item in listings if (score := _score(item)) > 0]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────


def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.
    """
    client = _get_groq_client()
    items = wardrobe.get("items", [])

    item_block = (
        f"- Title: {new_item.get('title', '')}\n"
        f"- Category: {new_item.get('category', '')}\n"
        f"- Colors: {', '.join(new_item.get('colors', []))}\n"
        f"- Style tags: {', '.join(new_item.get('style_tags', []))}\n"
        f"- Description: {new_item.get('description', '')}"
    )

    if not items:
        prompt = (
            "You are a fashion stylist specializing in thrifted clothing.\n\n"
            f"A user is considering buying this item:\n{item_block}\n\n"
            "They don't have a saved wardrobe yet. Give them 1-2 general outfit ideas "
            "for this piece — suggest what types of bottoms, shoes, or layers would pair "
            "well with it, and describe the overall vibe each outfit creates. "
            "Keep the tone casual and specific."
        )
    else:
        wardrobe_lines = "\n".join(
            f"- {item['name']} ({item.get('category', '')}, "
            f"{', '.join(item.get('colors', []))})"
            for item in items
        )
        prompt = (
            "You are a fashion stylist specializing in thrifted clothing.\n\n"
            f"A user is considering buying this item:\n{item_block}\n\n"
            f"Here is what they already own:\n{wardrobe_lines}\n\n"
            "Suggest 1-2 complete outfits combining the new item with specific pieces "
            "from their wardrobe. Name each wardrobe piece you use. Describe the overall "
            "vibe for each outfit. Keep the tone casual and specific."
        )

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return response.choices[0].message.content


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────


def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    if not outfit or not outfit.strip():
        return "Error: outfit description is missing or incomplete — cannot generate a fit card."

    title = new_item.get("title", "")
    price = new_item.get("price", "")
    platform = new_item.get("platform", "")

    prompt = (
        f"You found this thrifted item: {title} for ${price} on {platform}.\n"
        f"The suggested outfit: {outfit}\n\n"
        f"Write a 2-4 sentence Instagram/TikTok OOTD caption that:\n"
        f"- Feels casual and authentic, not like a product description\n"
        f"- Mentions the item name, price, and platform once each\n"
        f"- Captures the outfit vibe in specific terms\n"
        f"Write only the caption, no hashtags, no preamble."
    )

    client = _get_groq_client()
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9,
    )
    return response.choices[0].message.content
