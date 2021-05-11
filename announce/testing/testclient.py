from typing import List

from announce.client import BaseAnnounceClient
from magic.models import MagicCard


class TestClient(BaseAnnounceClient):

    def __init__(self):
        self.cards = []
        self.text = []
        self.errors = []

    def send_cards(self, cards: List[MagicCard]) -> bool:
        for card in cards:
            self.cards.append(card)
        return True

    def send_text(self, text: str) -> bool:
        self.text.append(text)
        return True

    def send_error(self, error) -> bool:
        self.errors.append(error)
        return True
