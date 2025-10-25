import re

import httpx
from fastmcp.exceptions import ToolError
from typing import Any
from pydantic_models import DeckSchema, CardSchema


BASE_URL = "https://deckofcardsapi.com/api/deck"
PILE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,32}$")


def _normalize_cards(cards: list[str] | None) -> list[str]:
    if not cards:
        return []
    allowed_values = {"A", "2", "3", "4", "5", "6", "7", "8", "9", "0", "J", "Q", "K"}
    allowed_suits = {"S", "D", "C", "H"}

    normalized_cards: list[str] = []
    for raw_code in cards:
        code = raw_code.strip().upper()
        if len(code) != 2:
            raise ToolError(
                f"Invalid card code '{raw_code}': must be exactly two characters."
            )
        value, suit = code[0], code[1]
        if value not in allowed_values or suit not in allowed_suits:
            raise ToolError(
                "Invalid card code "
                f"'{raw_code}': value must be one of {', '.join(sorted(allowed_values))}; "
                f"suit must be one of {', '.join(sorted(allowed_suits))}."
            )
        normalized_cards.append(code)
    return normalized_cards


def _validate_pile_name(pile_name: str) -> str:
    """Ensure pile names stay within a URL-safe, documented character set."""
    if not PILE_NAME_PATTERN.fullmatch(pile_name):
        raise ToolError(
            "Pile names must be 1-32 characters of letters, numbers, hyphen, or underscore."
        )
    return pile_name


def _format_cards(cards: list[dict[str, Any]] | None) -> list[CardSchema]:
    if not cards:
        return []
    simplified_cards: list[CardSchema] = []
    for card in cards:
        simplified_cards.append(
            CardSchema(
                code=card["code"],
                value=card["value"],
                suit=card["suit"],
                image=card["image"],
            )
        )
    return simplified_cards


def _deck_summary(data: dict[str, Any]) -> DeckSchema:
    summary = DeckSchema(
        deck_id=data["deck_id"], remaining=data["remaining"], shuffled=data["shuffled"]
    )
    return summary


async def _api_get(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    url = f"{BASE_URL}/{path.lstrip('/')}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise ToolError(
            f"Deck of Cards API returned HTTP {exc.response.status_code} for {exc.request.url}"
        ) from exc
    except httpx.TimeoutException as exc:
        raise ToolError("Deck of Cards API did not respond in time.") from exc
    except httpx.HTTPError as exc:
        raise ToolError(f"Unable to reach the Deck of Cards API: {exc}") from exc

    try:
        data = response.json()
    except ValueError as exc:
        raise ToolError("Deck of Cards API returned invalid JSON.") from exc

    if data.get("success") is False:
        message = data.get("error") or "Deck of Cards API reported an error."
        raise ToolError(message)

    return data
