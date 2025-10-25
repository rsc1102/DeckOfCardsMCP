from pydantic import BaseModel, HttpUrl


class DeckSchema(BaseModel):
    deck_id: str
    shuffled: bool
    remaining: int


class CardSchema(BaseModel):
    code: str
    value: str
    suit: str
    image: HttpUrl


class DrawCardSchema(BaseModel):
    deck_id: str
    cards: list[CardSchema]
    remaining: int


class PileWithoutCardDetailsSchema(BaseModel):
    remaining: int


class PileWithCardDetailsSchema(BaseModel):
    remaining: int
    cards: list[CardSchema]


class AddToPileSchema(BaseModel):
    deck_id: str
    remaining: int
    piles: dict[str, PileWithoutCardDetailsSchema]


class ShufflePileSchema(BaseModel):
    deck_id: str
    remaining: int
    piles: dict[str, PileWithoutCardDetailsSchema]


class ListPilesSchema(BaseModel):
    deck_id: str
    remaining: int
    piles: dict[str, PileWithCardDetailsSchema | PileWithoutCardDetailsSchema]


class DrawCardFromPileSchema(BaseModel):
    deck_id: str
    piles: dict[str, PileWithoutCardDetailsSchema]
    cards: list[CardSchema]


class ReturnCardSchema(BaseModel):
    deck_id: str
    remaining: int
    piles: dict[str, PileWithoutCardDetailsSchema]
