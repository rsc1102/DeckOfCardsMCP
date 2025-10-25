import pytest
from main import create_deck as create_deck_tool
from main import create_partial_deck as create_partial_deck_tool
from main import get_deck_state as get_deck_state_tool
from pydantic_models import DeckSchema

create_deck = create_deck_tool.fn
create_partial_deck = create_partial_deck_tool.fn
get_deck_state = get_deck_state_tool.fn


@pytest.mark.asyncio
async def test_create_deck_tool():
    deck_count = 1
    shuffled = False
    response = await create_deck(deck_count=deck_count, shuffled=shuffled)
    assert type(response) is DeckSchema
    assert response.remaining == 52
    assert not response.shuffled
    
    response_2 = await get_deck_state(deck_id=response.deck_id)
    assert response == response_2


@pytest.mark.asyncio
async def test_create_deck_tool_multiple_decks():
    deck_count = 6
    shuffled = False
    response = await create_deck(deck_count=deck_count, shuffled=shuffled)
    assert type(response) is DeckSchema
    assert response.remaining == 52 * deck_count
    assert not response.shuffled


@pytest.mark.asyncio
async def test_create_deck_tool_shuffled():
    deck_count = 1
    shuffled = True
    response = await create_deck(deck_count=deck_count, shuffled=shuffled)
    assert type(response) is DeckSchema
    assert response.remaining == 52
    assert response.shuffled


@pytest.mark.asyncio
async def test_create_deck_tool_multiple_shuffled_decks():
    deck_count = 6
    shuffled = True
    response = await create_deck(deck_count=deck_count, shuffled=shuffled)
    assert type(response) is DeckSchema
    assert response.remaining == 52 * deck_count
    assert response.shuffled


@pytest.mark.asyncio
async def test_create_partial_deck():
    cards = ["AS", "2S", "KS", "AD", "2D", "KD", "AC", "2C", "KC", "AH", "2H", "KH"]
    response = await create_partial_deck(cards=cards)
    assert type(response) is DeckSchema
    assert response.remaining == len(cards)
