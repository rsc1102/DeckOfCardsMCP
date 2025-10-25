import pytest
from main import create_deck as create_deck_tool
from main import draw_cards as draw_cards_tool
from main import add_to_pile as add_to_pile_tool
from main import return_cards as return_cards_tool
from pydantic_models import (
    DeckSchema,
    DrawCardSchema,
    AddToPileSchema,
    PileWithoutCardDetailsSchema,
    ReturnCardSchema,
)

create_deck = create_deck_tool.fn
draw_cards = draw_cards_tool.fn
add_to_pile = add_to_pile_tool.fn
return_cards = return_cards_tool.fn


async def generate_new_deck():
    deck_count = 1
    shuffled = False
    response = await create_deck(deck_count=deck_count, shuffled=shuffled)
    assert type(response) is DeckSchema
    assert response.remaining == 52
    assert not response.shuffled
    return response.deck_id


async def generate_new_pile():
    new_deck_id = await generate_new_deck()
    response = await draw_cards(deck_id=new_deck_id, count=10)
    assert type(response) is DrawCardSchema
    assert response.remaining == 42
    assert not response.shuffled

    drawn_cards = response.cards
    encoded_drawn_cards = [x.code for x in drawn_cards]
    pile_name = "my_pile"
    response = await add_to_pile(
        deck_id=new_deck_id, pile_name=pile_name, cards=encoded_drawn_cards
    )
    assert type(response) is AddToPileSchema
    assert response.deck_id == new_deck_id
    assert response.remaining == 42
    assert response.piles[pile_name] == PileWithoutCardDetailsSchema(remaining=10)
    return new_deck_id, pile_name, encoded_drawn_cards


@pytest.mark.asyncio
async def test_return_drawn_cards():
    deck_id = await generate_new_deck()
    response = await draw_cards(deck_id=deck_id, count=10)
    assert type(response) is DrawCardSchema
    assert response.remaining == 42
    assert not response.shuffled
    response = await return_cards(deck_id=deck_id)
    assert type(response) is ReturnCardSchema
    assert response.deck_id == deck_id
    assert response.remaining == 52


@pytest.mark.asyncio
async def test_return_specific_drawn_cards():
    deck_id = await generate_new_deck()
    response = await draw_cards(deck_id=deck_id, count=10)
    assert type(response) is DrawCardSchema
    assert response.remaining == 42
    assert not response.shuffled
    drawn_cards = response.cards
    encoded_drawn_cards = [x.code for x in drawn_cards]

    response = await return_cards(deck_id=deck_id, cards=encoded_drawn_cards[:5])
    assert type(response) is ReturnCardSchema
    assert response.deck_id == deck_id
    assert response.remaining == 47


@pytest.mark.asyncio
async def test_return_pile_to_deck():
    deck_id, pile_name, _ = await generate_new_pile()
    response = await return_cards(deck_id=deck_id, pile_name=pile_name)
    assert type(response) is ReturnCardSchema
    assert response.deck_id == deck_id
    assert response.remaining == 52


@pytest.mark.asyncio
async def test_return_specific_cards_from_pile_to_deck():
    deck_id, pile_name, cards = await generate_new_pile()
    response = await return_cards(deck_id=deck_id, pile_name=pile_name, cards=cards[:5])
    assert type(response) is ReturnCardSchema
    assert response.deck_id == deck_id
    assert response.remaining == 47
