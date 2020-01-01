from typing import List

import requests

from spoilers.scryfall.models import ScryfallCard, ScryfallSet


class ScryfallClient(object):
    __BASE_URL = 'https://api.scryfall.com'

    def __init__(self):
        pass

    def get_url(self, url):
        return self.__BASE_URL + url

    def get_all_sets(self):
        result = list()
        url = self.get_url('/sets')
        response = requests.get(url)
        if response.status_code != 200:
            # TODO: Log a warning here
            return result
        json = response.json()
        data = json['data']
        for item in data:
            scryfall_set = ScryfallSet.from_dict(item)
            print(scryfall_set.released_at.month)
            result.append(scryfall_set)
        return result

    def get_all_cards_for_set_code(self, code) -> List[ScryfallCard]:
        result = list()
        url = self.get_url(f'/cards/search?order=spoiled&q=e={code}&unique=prints')
        response = requests.get(url)
        if response.status_code != 200:
            # TODO: Log a warning here
            return result
        json = response.json()
        data = json['data']
        for item in data:
            scryfall_card = ScryfallCard.from_dict(item)
            result.append(scryfall_card)
        return result
