from dataclasses import dataclass, field
from typing import List, Optional

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class ScryfallSet:
    id: str
    code: str
    name: str
    uri: str
    scryfall_uri: str
    released_at: str
    icon_svg_uri: str


@dataclass_json
@dataclass
class ScryfallImages:
    small: str
    normal: str
    large: str
    png: str
    art_crop: str
    border_crop: str


@dataclass_json
@dataclass
class ScryfallCardFace:
    name: str
    type_line: str
    colors: List[str] = field(default_factory=list)
    loyalty: Optional[str] = None
    mana_cost: Optional[str] = None
    oracle_text: Optional[str] = None
    power: Optional[str] = None
    toughness: Optional[str] = None
    image_uris: Optional[ScryfallImages] = None


@dataclass_json
@dataclass
class ScryfallCard:
    id: str
    lang: str
    oracle_id: str
    uri: str
    name: str
    scryfall_uri: str
    layout: str
    type_line: str
    card_faces: List[ScryfallCardFace] = field(default_factory=list)
    color_indicator: List[str] = field(default_factory=list)
    loyalty: Optional[str] = None
    mana_cost: Optional[str] = None
    oracle_text: Optional[str] = None
    power: Optional[str] = None
    toughness: Optional[str] = None
    image_uris: Optional[ScryfallImages] = None
