import pytest
from main import create_deck as create_deck_tool
from main import shuffle_deck as shuffle_deck_tool
from main import draw_cards as draw_cards_tool
from pydantic_models import DeckSchema, DrawCardSchema

create_deck = create_deck_tool.fn
shuffle_deck = shuffle_deck_tool.fn
draw_cards = draw_cards_tool.fn


async def generate_new_deck():
    deck_count = 1
    shuffled = False
    response = await create_deck(deck_count=deck_count, shuffled=shuffled)
    assert type(response) is DeckSchema
    assert response.remaining == 52
    assert not response.shuffled
    return response.deck_id


@pytest.mark.asyncio
async def test_shuffle_entire_deck():
    new_deck_id = await generate_new_deck()
    response = await shuffle_deck(deck_id=new_deck_id, shuffle_remaining_only=False)
    assert type(response) is DeckSchema
    assert response.remaining == 52
    assert response.shuffled


@pytest.mark.asyncio
async def test_shuffle_remaining_deck():
    new_deck_id = await generate_new_deck()
    response = await draw_cards(deck_id=new_deck_id, count=10)
    assert type(response) is DrawCardSchema
    assert response.remaining == 42
    assert not response.shuffled

    response = await shuffle_deck(deck_id=new_deck_id, shuffle_remaining_only=True)
    assert type(response) is DeckSchema
    assert response.remaining == 42
    assert response.shuffled
