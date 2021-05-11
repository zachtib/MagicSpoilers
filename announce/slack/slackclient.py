from typing import List, Union

import requests

from announce.client import BaseAnnounceClient
from announce.formatters import format_card_manamoji, get_image_or_none, format_card_or_face
from magic.models import MagicCard, CardFace
from .models import SlackMessage, SectionWithImage, SectionText, ImageBlock, SectionBlock


class SlackClient(BaseAnnounceClient):
    __webhook_url: str
    __channel: str
    __use_manamoji: bool

    def __init__(self, webhook_url: str, channel: str = None, use_manamoji: bool = False):
        self.__webhook_url = webhook_url
        self.__channel = channel
        self.__use_manamoji = use_manamoji

    def send(self, message: SlackMessage) -> bool:
        message.channel = self.__channel
        json = message.to_json()
        response = requests.post(self.__webhook_url, data=json)
        if response.status_code != 200:
            print(response.request.body)
            print(response)
            print(response.reason)
            print(response.text)
            print(response.content)
            response.raise_for_status()
            return False
        return True

    def send_text(self, text: str) -> bool:
        return self.send(SlackMessage(text))

    @staticmethod
    def __create_blocks_for(item: Union[MagicCard, CardFace]) -> List[Union[SectionText, SectionWithImage, ImageBlock]]:
        image_url = get_image_or_none(item)
        result = [SectionBlock.of(format_card_or_face(item))]
        if image_url is not None:
            result.append(ImageBlock(image_url, item.name))
        return result

    def send_cards(self, cards: List[MagicCard]) -> bool:
        failed_to_send = list()
        for card in cards:
            if self.__use_manamoji:
                card = format_card_manamoji(card)
            blocks = list()

            if card.is_dfc():
                for face in card.card_faces:
                    blocks.extend(SlackClient.__create_blocks_for(face))
            else:
                blocks.extend(SlackClient.__create_blocks_for(card))

            message = SlackMessage(text=card.name, blocks=blocks)
            success = self.send(message)
            if not success:
                failed_to_send.append(card)
        if len(failed_to_send) == 0:
            return True
        # TODO: Add some logging here
        print(f'Failed to send {failed_to_send}')
        return False

    def send_error(self, error: str) -> bool:
        self.send_text(error)
        return True
