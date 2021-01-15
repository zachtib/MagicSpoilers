from typing import List

from magic.models import MagicCard


class EchoClient:
    def send_cards(self, cards: List[MagicCard]) -> bool:
        for card in cards:
            print(card)
        return True

    def send_text(self, text: str) -> bool:
        print(text)
        return True
