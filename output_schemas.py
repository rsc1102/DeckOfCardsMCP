from pydantic import BaseModel
from typing import Optional


class DeckSchema(BaseModel):
    deck_id: str
    shuffled: bool
    remaining: int


class CardSchema(BaseModel):
    code: str
    value: str
    suit: str
    image: str


class DrawCardSchema(BaseModel):
    deck_id: str
    cards: list[CardSchema]
    remaining: int
    shuffled: bool


class PileSchema(BaseModel):
    name: str
    remaining: int
    cards: Optional[list[CardSchema]] = None


class PileOutputSchema(BaseModel):
    deck_id: str
    remaining: int
    pile: PileSchema


class ReturnCardSchema(BaseModel):
    deck_id: str
    shuffled: bool
    remaining: int
    pile: Optional[PileSchema] = None
