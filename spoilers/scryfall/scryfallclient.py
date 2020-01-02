from typing import List

import requests

from spoilers.scryfall.models import ScryfallCard, ScryfallSet


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

    def get_all_sets(self):
        return self.__scryfall_request('/sets', ScryfallSet.from_dict)

    def get_all_cards_for_set_code(self, code) -> List[ScryfallCard]:
        url = f'/cards/search?order=spoiled&q=e={code}&unique=prints'
        return self.__scryfall_request(url, ScryfallCard.from_dict)
