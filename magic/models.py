from dataclasses import dataclass, field
from typing import List, Optional

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class MagicSet:
    scryfall_id: str
    code: str
    name: str
    uri: str
    scryfall_uri: str
    released_at: str


@dataclass_json
@dataclass
class CardFace:
    name: str
    type_line: str
    colors: List[str] = field(default_factory=list)
    loyalty: Optional[str] = None
    mana_cost: Optional[str] = None
    oracle_text: Optional[str] = None
    power: Optional[str] = None
    toughness: Optional[str] = None
    image_uri: Optional[str] = None


@dataclass_json
@dataclass
class MagicCard:
    scryfall_id: str
    lang: str
    oracle_id: str
    uri: str
    name: str
    scryfall_uri: str
    layout: str
    type_line: str
    card_faces: List[CardFace] = field(default_factory=list)
    color_indicator: List[str] = field(default_factory=list)
    loyalty: Optional[str] = None
    mana_cost: Optional[str] = None
    oracle_text: Optional[str] = None
    power: Optional[str] = None
    toughness: Optional[str] = None
    image_uri: Optional[str] = None

    def is_dfc(self):
        return self.card_faces is not None and len(self.card_faces) > 0
