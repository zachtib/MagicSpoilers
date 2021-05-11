from abc import ABC, abstractmethod
from typing import List

from magic.models import MagicCard


class BaseAnnounceClient(ABC):

    @abstractmethod
    def send_cards(self, cards: List[MagicCard]) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def send_text(self, text: str) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def send_error(self, error: str) -> bool:
        raise NotImplementedError()
