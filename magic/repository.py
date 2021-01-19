from dataclasses import dataclass
from typing import List

from scryfall.client import ScryfallClient
from .models import MagicCard, MagicSet
from .converters import convert_card, convert_set


@dataclass
class SearchSpec:
    expansion: str
    order: str
    unique: str


class MagicRepository(object):

    def __init__(self):
        self.scryfall_client = ScryfallClient()

    def sets(self) -> List[MagicSet]:
        scryfall_result = self.scryfall_client.get_sets()
        return [convert_set(s) for s in scryfall_result]

    def search(self, spec: SearchSpec) -> List[MagicCard]:
        querystring = f'order={spec.order}&q=e={spec.expansion}&unique={spec.unique}'
        scryfall_result = self.scryfall_client.search_cards(querystring)
        return [convert_card(card) for card in scryfall_result]
