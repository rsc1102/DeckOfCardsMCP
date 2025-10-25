## 🃏 Deck of Cards MCP Server 

This project exposes the [deckofcardsapi.com](https://deckofcardsapi.com/) endpoints via an MCP server built with [FastMCP](https://gofastmcp.com/).

Cloud Hosting Link: [https://fastmcp.cloud/app/deck-of-cards](https://fastmcp.cloud/app/deck-of-cards)

### Local Setup
- Install [uv](https://docs.astral.sh/uv/getting-started/installation/) package manager.
- Install dependencies: `uv sync`
- Run the server: `bash run.sh server`
- Run tests: `bash run.sh tests`

### Available tools
- `create_deck`: Create a new deck, optionally combining multiple decks.
- `create_partial_deck`: Build a deck limited to specific card codes.
- `shuffle_deck`: Shuffle an existing deck, with the option to only shuffle remaining cards.
- `draw_cards`: Draw one or more cards from a deck.
- `get_deck_state`: Retrieve the current deck metadata.
- `add_to_pile`: Move specified cards into a named pile.
- `draw_from_pile`: Draw explicit cards, or use `position` (`top`, `bottom`, `random`) with an optional `count`.
- `list_pile_cards`: Inspect the cards stored in a pile.
- `shuffle_pile`: Shuffle the cards stored in a pile.
- `return_cards`: Return cards from the deck or a pile back to the main deck.

All tools propagate Deck of Cards API errors as MCP `ToolError`s with descriptive messages.

### Note
1. Jokers are not supported.
2. Pile names must be 1-32 characters using only letters, numbers, hyphen, or underscore.
3. Piles do not work with multiple decks.
