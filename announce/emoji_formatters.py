import re
from abc import ABC, abstractmethod

from magic.models import MagicCard, CardFace

re_regular_mana = re.compile(r'{(\w+)}')
re_hybrid_mana = re.compile(r'{(\w+)/(\w+)}')


class BaseManamojiFormatter(ABC):

    @abstractmethod
    def format_manamoji(self, string: str) -> str:
        raise NotImplementedError()

    def format_card_face(self, face: CardFace) -> CardFace:
        face.mana_cost = self.format_manamoji(face.mana_cost)
        face.oracle_text = self.format_manamoji(face.oracle_text)

        return face

    def format_card(self, card: MagicCard) -> MagicCard:
        card.mana_cost = self.format_manamoji(card.mana_cost)
        card.oracle_text = self.format_manamoji(card.oracle_text)
        card.card_faces = [self.format_card_face(face) for face in card.card_faces]

        return card


class NoopManamojiFormatter(BaseManamojiFormatter):
    def format_manamoji(self, string: str) -> str:
        return string


class HyphenatedManamojiFormatter(BaseManamojiFormatter):
    def format_manamoji(self, string: str) -> str:
        try:
            string = re_hybrid_mana.sub(r':mana-\1\2:', string)
            string = re_regular_mana.sub(r":mana-\1:", string)
            return string.lower()
        except TypeError:
            pass
        return string


class NonHyphenatedManamojiFormatter(BaseManamojiFormatter):
    def format_manamoji(self, string: str) -> str:
        try:
            string = re_hybrid_mana.sub(r':mana\1\2:', string)
            string = re_regular_mana.sub(r":mana\1:", string)
            return string.lower()
        except TypeError:
            pass
        return string
