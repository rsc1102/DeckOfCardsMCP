from typing import Any, Literal

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from utils import (
    _api_get,
    _deck_summary,
    _format_cards,
    _normalize_cards,
    _validate_pile_name,
)
from pydantic_models import (
    DeckSchema,
    DrawCardSchema,
    ReturnCardSchema,
    AddToPileSchema,
    DrawCardFromPileSchema,
    ShufflePileSchema,
    ListPilesSchema,
    PileWithoutCardDetailsSchema,
    PileWithCardDetailsSchema,
)

server = FastMCP(
    name="deck-of-cards",
    instructions=(
        "This server wraps the deckofcardsapi.com service. "
        "Use the tools to create decks, shuffle them, draw cards, and manage piles."
    ),
)


@server.tool(
    description="Create a new deck or multi-deck shoe; set deck_count (1-20) to stack decks and shuffled=True to start pre-shuffled.",
)
async def create_deck(deck_count: int = 1, shuffled: bool = False) -> DeckSchema:
    if deck_count < 1 or deck_count > 20:
        raise ToolError("Deck count must be between 1 and 20.")

    params: dict[str, Any] = {"deck_count": deck_count}

    if shuffled:
        data = await _api_get("new/shuffle/", params=params)
    else:
        data = await _api_get("new/", params=params)

    return _deck_summary(data)


@server.tool(
    description=(
        "Create a partial deck containing only the specified card codes. "
        "Cards should be provided as two-character codes (e.g. AS, 0H)."
    )
)
async def create_partial_deck(cards: list[str]) -> DeckSchema:
    if not cards:
        raise ToolError("Provide at least one card code to build a partial deck.")

    normalized_cards = _normalize_cards(cards)
    params = {"cards": ",".join(normalized_cards)}
    data = await _api_get("new/shuffle/", params=params)
    return _deck_summary(data)


@server.tool(
    description="Reshuffle the specified deck. Set shuffle_remaining_only to true to keep drawn cards out."
)
async def shuffle_deck(
    deck_id: str, shuffle_remaining_only: bool = False
) -> DeckSchema:
    if not deck_id:
        raise ToolError("A deck_id is required to shuffle a deck.")

    params = {"remaining": "true"} if shuffle_remaining_only else None
    data = await _api_get(f"{deck_id}/shuffle/", params=params)
    return _deck_summary(data)


@server.tool(description="Draw one or more cards from a deck.")
async def draw_cards(deck_id: str, count: int = 1) -> DrawCardSchema:
    if not deck_id:
        raise ToolError("A deck_id is required to draw cards.")
    if count < 1 or count > 52:
        raise ToolError("Count must be between 1 and 52.")

    data = await _api_get(f"{deck_id}/draw/", params={"count": count})
    deck_summary = _deck_summary(data)
    cards = _format_cards(data.get("cards"))
    return DrawCardSchema(
        deck_id=deck_summary.deck_id,
        shuffled=deck_summary.shuffled,
        remaining=deck_summary.remaining,
        cards=cards,
    )


@server.tool(description="Return information about the deck including remaining cards.")
async def get_deck_state(deck_id: str) -> DeckSchema:
    if not deck_id:
        raise ToolError("A deck_id is required to check deck state.")

    data = await _api_get(f"{deck_id}/")
    return _deck_summary(data)


@server.tool(
    description=(
        "Add specific cards to a named pile. Pile names must be 1-32 characters using "
        "letters, numbers, hyphen, or underscore."
    )
)
async def add_to_pile(
    deck_id: str, pile_name: str, cards: list[str]
) -> AddToPileSchema:
    if not deck_id:
        raise ToolError("A deck_id is required to add cards to a pile.")
    if not pile_name:
        raise ToolError("A pile_name is required.")
    if not cards:
        raise ToolError("Provide at least one card code to add to the pile.")

    _validate_pile_name(pile_name)

    normalized_cards = _normalize_cards(cards)
    params = {"cards": ",".join(normalized_cards)}
    data = await _api_get(f"{deck_id}/pile/{pile_name}/add/", params=params)
    pile_info = data.get("piles", {})
    piles: dict[str, PileWithoutCardDetailsSchema] = {}
    for key, val in pile_info.items():
        piles[key] = PileWithoutCardDetailsSchema(remaining=val["remaining"])

    deck_summary = _deck_summary(data)
    return AddToPileSchema(
        deck_id=deck_summary.deck_id,
        remaining=deck_summary.remaining,
        piles=piles,
    )


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
) -> DrawCardFromPileSchema:
    if not deck_id:
        raise ToolError("A deck_id is required to draw from a pile.")
    if not pile_name:
        raise ToolError("A pile_name is required.")
    _validate_pile_name(pile_name)

    normalized_position = position.lower()
    valid_positions = {"top", "bottom", "random"}
    if normalized_position not in valid_positions:
        raise ToolError("Position must be one of: 'top', 'bottom', or 'random'.")

    if cards is not None and count is not None:
        raise ToolError("Provide either specific card codes or a count, not both.")

    if cards and normalized_position != "top":
        raise ToolError(
            "Drawing specific cards is only supported from the top of the pile."
        )

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
    pile_info = data.get("piles", {})
    piles: dict[str, PileWithoutCardDetailsSchema] = {}
    for key, val in pile_info.items():
        piles[key] = PileWithoutCardDetailsSchema(remaining=val["remaining"])

    deck_summary = _deck_summary(data)
    list_cards = _format_cards(data.get("cards"))
    return DrawCardFromPileSchema(
        deck_id=deck_summary.deck_id,
        remaining=deck_summary.remaining,
        piles=piles,
        cards=list_cards,
    )


@server.tool(description="List the cards currently stored in a pile.")
async def list_pile_cards(deck_id: str, pile_name: str) -> ListPilesSchema:
    if not deck_id:
        raise ToolError("A deck_id is required to inspect a pile.")
    if not pile_name:
        raise ToolError("A pile_name is required.")
    _validate_pile_name(pile_name)

    data = await _api_get(f"{deck_id}/pile/{pile_name}/list/")
    pile_info = data.get("piles", {})
    piles: dict[str, PileWithoutCardDetailsSchema | PileWithCardDetailsSchema] = {}
    for key, val in pile_info.items():
        if "card" in val:
            cards = _format_cards(val.get("cards"))
            piles[key] = PileWithCardDetailsSchema(
                remaining=val["remaining"], cards=cards
            )
        else:
            piles[key] = PileWithoutCardDetailsSchema(remaining=val["remaining"])
    deck_summary = _deck_summary(data)
    return ListPilesSchema(
        deck_id=deck_summary.deck_id,
        remaining=deck_summary.remaining,
        piles=piles,
    )


@server.tool(description="Shuffle the cards contained in a named pile.")
async def shuffle_pile(deck_id: str, pile_name: str) -> ShufflePileSchema:
    if not deck_id:
        raise ToolError("A deck_id is required to shuffle a pile.")
    if not pile_name:
        raise ToolError("A pile_name is required.")
    _validate_pile_name(pile_name)

    data = await _api_get(f"{deck_id}/pile/{pile_name}/shuffle/")
    pile_info = data.get("piles", {})
    piles: dict[str, PileWithoutCardDetailsSchema] = {}
    for key, val in pile_info.items():
        piles[key] = PileWithoutCardDetailsSchema(remaining=val["remaining"])
    deck_summary = _deck_summary(data)
    return ShufflePileSchema(
        deck_id=deck_summary.deck_id,
        remaining=deck_summary.remaining,
        piles=piles,
    )


@server.tool(
    description=(
        "Return cards to the main deck or a specific pile. "
        "Provide cards to return specific codes; omit to return everything."
    ),
)
async def return_cards(
    deck_id: str,
    pile_name: str | None = None,
    cards: list[str] | None = None,
) -> ReturnCardSchema:
    if not deck_id:
        raise ToolError("A deck_id is required to return cards.")

    normalized_cards = _normalize_cards(cards)
    params = {"cards": ",".join(normalized_cards)} if normalized_cards else None

    if pile_name:
        _validate_pile_name(pile_name)
        path = f"{deck_id}/pile/{pile_name}/return/"
    else:
        path = f"{deck_id}/return/"

    data = await _api_get(path, params=params)
    deck_summary = _deck_summary(data)
    pile_info = data.get("piles", {})
    piles: dict[str, PileWithoutCardDetailsSchema] = {}
    for key, val in pile_info.items():
        piles[key] = PileWithoutCardDetailsSchema(remaining=val["remaining"])

    return ReturnCardSchema(
        deck_id=deck_summary.deck_id,
        remaining=deck_summary.remaining,
        shuffled=deck_summary.shuffled,
        piles=piles,
    )


def main() -> None:
    server.run(transport="http")


if __name__ == "__main__":
    main()
