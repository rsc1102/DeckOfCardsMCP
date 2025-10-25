import pytest
from src.main import create_deck as create_deck_tool
from src.main import draw_cards as draw_cards_tool
from src.main import add_to_pile as add_to_pile_tool
from src.main import draw_from_pile as draw_from_pile_tool
from src.main import shuffle_pile as shuffle_pile_tool
from src.main import list_pile_cards as list_pile_cards_tool
from src.pydantic_models import (
    DeckSchema,
    DrawCardSchema,
    AddToPileSchema,
    PileWithoutCardDetailsSchema,
    ShufflePileSchema,
    ListPilesSchema,
    PileWithCardDetailsSchema,
)

create_deck = create_deck_tool.fn
draw_cards = draw_cards_tool.fn
add_to_pile = add_to_pile_tool.fn
draw_from_pile = draw_from_pile_tool.fn
shuffle_pile = shuffle_pile_tool.fn
list_pile_cards = list_pile_cards_tool.fn


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
async def test_shuffle_pile():
    deck_id, pile_name, _ = await generate_new_pile()
    response = await shuffle_pile(deck_id=deck_id, pile_name=pile_name)
    assert type(response) is ShufflePileSchema
    assert response.remaining == 42
    assert response.piles[pile_name] == PileWithoutCardDetailsSchema(remaining=10)


@pytest.mark.asyncio
async def test_list_cards_in_pile():
    deck_id, pile_name, cards = await generate_new_pile()
    response = await list_pile_cards(deck_id=deck_id, pile_name=pile_name)
    assert type(response) is ListPilesSchema
    assert response.remaining == 42
    pile = response.piles[pile_name]
    assert isinstance(pile, PileWithCardDetailsSchema)
    assert pile.remaining == 10
    listed_cards = pile.cards
    encoded_listed_cards = [x.code for x in listed_cards]
    assert set(encoded_listed_cards) == set(cards)


@pytest.mark.asyncio
async def test_transfer_cards_between_piles():
    deck_id, pile_name, cards = await generate_new_pile()
    pile2_name = "my_pile_2"
    response = await add_to_pile(deck_id=deck_id, pile_name=pile2_name, cards=cards[:5])
    assert type(response) is AddToPileSchema
    assert response.deck_id == deck_id
    assert response.remaining == 42
    assert response.piles[pile_name] == PileWithoutCardDetailsSchema(remaining=5)
    assert response.piles[pile2_name] == PileWithoutCardDetailsSchema(remaining=5)

    response = await list_pile_cards(deck_id=deck_id, pile_name=pile_name)
    assert type(response) is ListPilesSchema
    assert response.remaining == 42
    pile = response.piles[pile_name]
    assert isinstance(pile, PileWithCardDetailsSchema)
    assert pile.remaining == 5
    listed_cards = pile.cards
    encoded_listed_cards = [x.code for x in listed_cards]
    assert set(encoded_listed_cards) <= set(cards)

    pile2 = response.piles[pile2_name]
    assert isinstance(pile2, PileWithoutCardDetailsSchema)
    assert pile2.remaining == 5
