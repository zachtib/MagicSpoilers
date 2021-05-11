from typing import List

from announce.client import BaseAnnounceClient
from magic.models import MagicCard


class DiscordClient(BaseAnnounceClient):
    __webhook_url: str
    __channel: str
    __use_manamoji: bool

    def __init__(self, webhook_url: str, channel: str = None, use_manamoji: bool = False):
        self.__webhook_url = webhook_url
        self.__channel = channel
        self.__use_manamoji = use_manamoji

    def send_cards(self, cards: List[MagicCard]) -> bool:
        pass

    def send_text(self, text: str) -> bool:
        pass

    def send_error(self, error: str) -> bool:
        pass
