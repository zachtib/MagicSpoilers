from typing import List

from announce.client import BaseAnnounceClient
from magic.models import MagicCard


class EchoClient(BaseAnnounceClient):

    def send_cards(self, cards: List[MagicCard]) -> bool:
        for card in cards:
            print(card)
        return True

    def send_text(self, text: str) -> bool:
        print(text)
        return True

    def send_error(self, error: str) -> bool:
        print(error)
        return True
