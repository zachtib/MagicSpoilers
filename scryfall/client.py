from typing import List

import requests

from .models import ScryfallCard, ScryfallSet


class ScryfallClient(object):
    __BASE_URL = 'https://api.scryfall.com'

    def __scryfall_request(self, url, mapper):
        result = list()
        response = requests.get(self.__BASE_URL + url)
        if response.status_code != 200:
            # TODO: Log a warning here
            return result
        json = response.json()
        data = json['data']
        for item in data:
            result_object = mapper(item)
            result.append(result_object)
        return result

    def get_sets(self) -> List[ScryfallSet]:
        return self.__scryfall_request('/sets', ScryfallSet.from_dict)

    def search_cards(self, querystring) -> List[ScryfallCard]:
        url = f'/cards/search?{querystring}'
        return self.__scryfall_request(url, ScryfallCard.from_dict)
