import pytest
from main import create_deck as create_deck_tool
from main import draw_cards as draw_cards_tool
from main import add_to_pile as add_to_pile_tool
from main import draw_from_pile as draw_from_pile_tool
from pydantic_models import (
    DeckSchema,
    DrawCardSchema,
    AddToPileSchema,
    PileWithoutCardDetailsSchema,
    DrawCardFromPileSchema,
)

create_deck = create_deck_tool.fn
draw_cards = draw_cards_tool.fn
add_to_pile = add_to_pile_tool.fn
draw_from_pile = draw_from_pile_tool.fn


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
async def test_draw_cards_from_deck():
    new_deck_id = await generate_new_deck()
    response = await draw_cards(deck_id=new_deck_id, count=10)
    assert type(response) is DrawCardSchema
    assert response.remaining == 42
    assert not response.shuffled
    assert len(response.cards) == 10


@pytest.mark.asyncio
async def test_draw_specific_cards_from_pile():
    deck_id, pile_name, pile_cards = await generate_new_pile()
    response = await draw_from_pile(
        deck_id=deck_id, pile_name=pile_name, cards=pile_cards[:5]
    )
    assert type(response) is DrawCardFromPileSchema
    assert response.deck_id == deck_id
    assert response.piles[pile_name] == PileWithoutCardDetailsSchema(remaining=5)
    assert len(response.cards) == 5
    drawn_cards = response.cards
    encoded_drawn_cards = [x.code for x in drawn_cards]
    assert set(encoded_drawn_cards) == set(pile_cards[:5])


@pytest.mark.asyncio
async def test_draw_number_of_cards_from_pile():
    deck_id, pile_name, pile_cards = await generate_new_pile()
    response = await draw_from_pile(deck_id=deck_id, pile_name=pile_name, count=5)
    assert type(response) is DrawCardFromPileSchema
    assert response.deck_id == deck_id
    assert response.piles[pile_name] == PileWithoutCardDetailsSchema(remaining=5)
    assert len(response.cards) == 5
    drawn_cards = response.cards
    encoded_drawn_cards = [x.code for x in drawn_cards]
    assert set(encoded_drawn_cards) == set(pile_cards[-5:])


@pytest.mark.asyncio
async def test_draw_number_of_cards_from_bottom_from_pile():
    deck_id, pile_name, pile_cards = await generate_new_pile()
    response = await draw_from_pile(
        deck_id=deck_id, pile_name=pile_name, count=5, position="bottom"
    )
    assert type(response) is DrawCardFromPileSchema
    assert response.deck_id == deck_id
    assert response.piles[pile_name] == PileWithoutCardDetailsSchema(remaining=5)
    assert len(response.cards) == 5
    drawn_cards = response.cards
    encoded_drawn_cards = [x.code for x in drawn_cards]
    assert set(encoded_drawn_cards) == set(pile_cards[:5])


@pytest.mark.asyncio
async def test_draw_number_of_cards_from_pile_at_random():
    deck_id, pile_name, pile_cards = await generate_new_pile()
    response = await draw_from_pile(
        deck_id=deck_id, pile_name=pile_name, count=5, position="random"
    )
    assert type(response) is DrawCardFromPileSchema
    assert response.deck_id == deck_id
    assert response.piles[pile_name] == PileWithoutCardDetailsSchema(remaining=5)
    assert len(response.cards) == 5
    drawn_cards = response.cards
    encoded_drawn_cards = [x.code for x in drawn_cards]
    assert set(encoded_drawn_cards) <= set(pile_cards)
