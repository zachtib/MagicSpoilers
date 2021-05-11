from typing import List

import requests

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
        data = {
            'content': text,
        }
        response = requests.post(self.__webhook_url, data=data)
        print(response)
        print(response.content)
        print(response.text)
        return True

    def send_error(self, error: str) -> bool:
        return self.send_text(error)
