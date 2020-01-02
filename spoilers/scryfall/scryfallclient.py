from typing import List

import requests

from magic.models import MagicSet, MagicCard
from .converters import convert_set, convert_card
from .models import ScryfallCard, ScryfallSet


class ScryfallClient(object):
    __BASE_URL = 'https://api.scryfall.com'

    def __init__(self):
        pass

    def get_url(self, url):
        return self.__BASE_URL + url

    def __scryfall_request(self, url, mapper):
        result = list()
        response = requests.get(self.get_url(url))
        if response.status_code != 200:
            # TODO: Log a warning here
            return result
        json = response.json()
        data = json['data']
        for item in data:
            result_object = mapper(item)
            result.append(result_object)
        return result

    def get_all_sets(self) -> List[MagicSet]:
        api_result = self.__scryfall_request('/sets', ScryfallSet.from_dict)
        return [convert_set(item) for item in api_result]

    def get_all_cards_for_set_code(self, code) -> List[MagicCard]:
        url = f'/cards/search?order=spoiled&q=e={code}&unique=prints'
        api_result = self.__scryfall_request(url, ScryfallCard.from_dict)
        return [convert_card(card) for card in api_result]
