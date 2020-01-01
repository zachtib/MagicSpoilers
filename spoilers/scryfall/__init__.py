from spoilers.scryfall.models import *
from spoilers.scryfall.scryfallclient import ScryfallClient


def get_client() -> ScryfallClient:
    return ScryfallClient()
