import json
from typing import List

import requests

from announce.client import BaseAnnounceClient
from announce.emoji_formatters import BaseManamojiFormatter
from announce.formatters import format_card_or_face
from magic.models import MagicCard


class DiscordClient(BaseAnnounceClient):
    __webhook_url: str
    __channel: str
    __manamoji_formatter: BaseManamojiFormatter

    def __init__(self, webhook_url: str, channel: str, manamoji_formatter: BaseManamojiFormatter):
        self.__webhook_url = webhook_url
        self.__channel = channel
        self.__manamoji_formatter = manamoji_formatter

    def send_cards(self, cards: List[MagicCard]) -> bool:
        failed_to_send = list()
        for card in cards:
            card = self.__manamoji_formatter.format_card(card)
            content = []
            embeds = []
            if card.is_dfc():
                for face in card.card_faces:
                    content.append(format_card_or_face(face))
                    embeds.append({
                        'image': {
                            'url': face.image_uri
                        }
                    })
            else:
                content.append(format_card_or_face(card))
                embeds.append({
                    'image': {
                        'url': card.image_uri
                    }
                })
            data = json.dumps({
                'content': '\n'.join(content),
                'embeds': embeds,
            })
            requests.post(self.__webhook_url, data=data, headers={
                'Content-Type': 'application/json'
            })
        for card in failed_to_send:
            self.send_error(f'Error sending {card.name}')
        return True

    def send_text(self, text: str) -> bool:
        data = {
            'content': text,
        }
        requests.post(self.__webhook_url, data=data)
        return True

    def send_error(self, error: str) -> bool:
        return self.send_text(error)
