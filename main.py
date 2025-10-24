from typing import Any, Literal

import httpx
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

BASE_URL = "https://deckofcardsapi.com/api/deck"

server = FastMCP(
    name="deck-of-cards",
    instructions=(
        "This server wraps the deckofcardsapi.com service. "
        "Use the tools to create decks, shuffle them, draw cards, and manage piles."
    ),
)

def _normalize_cards(cards: list[str] | None) -> list[str]:
    if not cards:
        return []
    allowed_values = {"A", "2", "3", "4", "5", "6", "7", "8", "9", "0", "J", "Q", "K"}
    allowed_suits = {"S", "D", "C", "H"}

    normalized_cards: list[str] = []
    for raw_code in cards:
        code = raw_code.strip().upper()
        if len(code) != 2:
            raise ToolError(f"Invalid card code '{raw_code}': must be exactly two characters.")
        value, suit = code[0], code[1]
        if value not in allowed_values or suit not in allowed_suits:
            raise ToolError(
                "Invalid card code "
                f"'{raw_code}': value must be one of {', '.join(sorted(allowed_values))}; "
                f"suit must be one of {', '.join(sorted(allowed_suits))}."
            )
        normalized_cards.append(code)
    return normalized_cards


def _format_cards(cards: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    if not cards:
        return []
    simplified_cards: list[dict[str, Any]] = []
    for card in cards:
        simplified_cards.append(
            {
                "code": card.get("code"),
                "value": card.get("value"),
                "suit": card.get("suit"),
                "image": card.get("image")
            }
        )
    return simplified_cards


def _deck_summary(data: dict[str, Any]) -> dict[str, Any]:
    summary = {
        "deck_id": data.get("deck_id"),
        "remaining": data.get("remaining"),
        "shuffled": data.get("shuffled"),
    }
    if "deck_count" in data:
        summary["deck_count"] = data["deck_count"]
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


@server.tool(description="Create a fresh deck. Combine multiple decks with deck_count.")
async def create_deck(deck_count: int = 1) -> dict[str, Any]:
    if deck_count < 1 or deck_count > 20:
        raise ToolError("Deck count must be between 1 and 20.")

    params: dict[str, Any] = {"deck_count": deck_count}

    data = await _api_get("new/", params=params)
    return _deck_summary(data)


@server.tool(
    description=(
        "Create a partial deck containing only the specified card codes. "
        "Cards should be provided as two-character codes (e.g. AS, 0H)."
    )
)
async def create_partial_deck(cards: list[str]) -> dict[str, Any]:
    if not cards:
        raise ToolError("Provide at least one card code to build a partial deck.")

    normalized_cards = _normalize_cards(cards)
    params = {"cards": ",".join(normalized_cards)}
    data = await _api_get("new/shuffle/", params=params)
    return _deck_summary(data)


@server.tool(description="Reshuffle the specified deck. Set shuffle_remaining_only to true to keep drawn cards out.")
async def shuffle_deck(deck_id: str, shuffle_remaining_only: bool = False) -> dict[str, Any]:
    if not deck_id:
        raise ToolError("A deck_id is required to shuffle a deck.")

    params = {"remaining": "true"} if shuffle_remaining_only else None
    data = await _api_get(f"{deck_id}/shuffle/", params=params)
    return _deck_summary(data)


@server.tool(description="Draw one or more cards from a deck.")
async def draw_cards(deck_id: str, count: int = 1) -> dict[str, Any]:
    if not deck_id:
        raise ToolError("A deck_id is required to draw cards.")
    if count < 1 or count > 52:
        raise ToolError("Count must be between 1 and 52.")

    data = await _api_get(f"{deck_id}/draw/", params={"count": count})
    return {**_deck_summary(data), "cards": _format_cards(data.get("cards"))}


@server.tool(description="Return information about the deck including remaining cards.")
async def get_deck_state(deck_id: str) -> dict[str, Any]:
    if not deck_id:
        raise ToolError("A deck_id is required to check deck state.")

    data = await _api_get(f"{deck_id}/")
    return _deck_summary(data)


@server.tool(description="Add specific cards to a named pile.")
async def add_to_pile(deck_id: str, pile_name: str, cards: list[str]) -> dict[str, Any]:
    if not deck_id:
        raise ToolError("A deck_id is required to add cards to a pile.")
    if not pile_name:
        raise ToolError("A pile_name is required.")
    if not cards:
        raise ToolError("Provide at least one card code to add to the pile.")

    normalized_cards = _normalize_cards(cards)
    params = {"cards": ",".join(normalized_cards)}
    data = await _api_get(f"{deck_id}/pile/{pile_name}/add/", params=params)
    pile_info = data.get("piles", {}).get(pile_name, {})
    return {
        **_deck_summary(data),
        "pile": {
            "name": pile_name,
            "remaining": pile_info.get("remaining"),
        },
    }


@server.tool(
    description=(
        "Draw cards from a named pile. By default draws from the top; set position to "
        "'bottom' or 'random' to change behavior. Provide explicit card codes or use count."
    )
)
async def draw_from_pile(
    deck_id: str,
    pile_name: str,
    cards: list[str] | None = None,
    count: int | None = None,
    position: Literal["top", "bottom", "random"] = "top",
) -> dict[str, Any]:
    if not deck_id:
        raise ToolError("A deck_id is required to draw from a pile.")
    if not pile_name:
        raise ToolError("A pile_name is required.")

    normalized_position = position.lower()
    valid_positions = {"top", "bottom", "random"}
    if normalized_position not in valid_positions:
        raise ToolError("Position must be one of: 'top', 'bottom', or 'random'.")

    if (cards is None or len(cards) == 0) and count is None:
        raise ToolError("Provide either specific card codes or a count.")

    if cards is not None and count is not None:
        raise ToolError("Provide either specific card codes or a count, not both.")

    if cards and normalized_position != "top":
        raise ToolError("Drawing specific cards is only supported from the top of the pile.")

    params: dict[str, Any] = {}
    if cards:
        normalized_cards = _normalize_cards(cards)
        params["cards"] = ",".join(normalized_cards)
    elif count is not None:
        if count < 1 or count > 52:
            raise ToolError("Count must be between 1 and 52.")
        params["count"] = count
    elif normalized_position != "top":
        raise ToolError("Specify count when drawing from the bottom or randomly.")

    path_parts = [deck_id, "pile", pile_name, "draw"]
    if normalized_position in {"bottom", "random"}:
        path_parts.append(normalized_position)
    path = "/".join(path_parts) + "/"

    data = await _api_get(path, params=params if params else None)
    pile_info = data.get("piles", {}).get(pile_name, {})
    return {
        **_deck_summary(data),
        "cards": _format_cards(data.get("cards")),
        "pile": {
            "name": pile_name,
            "remaining": pile_info.get("remaining"),
        },
    }


@server.tool(description="List the cards currently stored in a pile.")
async def list_pile_cards(deck_id: str, pile_name: str) -> dict[str, Any]:
    if not deck_id:
        raise ToolError("A deck_id is required to inspect a pile.")
    if not pile_name:
        raise ToolError("A pile_name is required.")

    data = await _api_get(f"{deck_id}/pile/{pile_name}/list/")
    pile_info = data.get("piles", {}).get(pile_name, {})
    return {
        **_deck_summary(data),
        "pile": {
            "name": pile_name,
            "remaining": pile_info.get("remaining"),
            "cards": _format_cards(pile_info.get("cards")),
        },
    }


@server.tool(description="Shuffle the cards contained in a named pile.")
async def shuffle_pile(deck_id: str, pile_name: str) -> dict[str, Any]:
    if not deck_id:
        raise ToolError("A deck_id is required to shuffle a pile.")
    if not pile_name:
        raise ToolError("A pile_name is required.")

    data = await _api_get(f"{deck_id}/pile/{pile_name}/shuffle/")
    pile_info = data.get("piles", {}).get(pile_name, {})
    return {
        **_deck_summary(data),
        "pile": {
            "name": pile_name,
            "remaining": pile_info.get("remaining"),
        },
    }


@server.tool(
    description=(
        "Return cards to the main deck or a specific pile. "
        "Provide cards to return specific codes; omit to return everything."
    )
)
async def return_cards(
    deck_id: str,
    pile_name: str | None = None,
    cards: list[str] | None = None,
) -> dict[str, Any]:
    if not deck_id:
        raise ToolError("A deck_id is required to return cards.")

    normalized_cards = _normalize_cards(cards)
    params = {"cards": ",".join(normalized_cards)} if normalized_cards else None

    if pile_name:
        path = f"{deck_id}/pile/{pile_name}/return/"
    else:
        path = f"{deck_id}/return/"

    data = await _api_get(path, params=params)
    response: dict[str, Any] = _deck_summary(data)

    if pile_name and "piles" in data:
        pile_info = data.get("piles", {}).get(pile_name, {})
        response["pile"] = {
            "name": pile_name,
            "remaining": pile_info.get("remaining"),
        }

    return response


def main() -> None:
    server.run(transport="sse")


if __name__ == "__main__":
    main()
