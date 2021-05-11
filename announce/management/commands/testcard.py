from django.core.management.base import BaseCommand

from announce.models import Channel
from spoilers.scryfall import ScryfallClient


class Command(BaseCommand):
    help = 'Checks for new Cards, announces them, and saves them to the database'

    def handle(self, *args, **options):
        scryfall = ScryfallClient()
        cards = scryfall.get_all_cards_for_set_code('leb')[:2]
        announce_clients = Channel.objects.clients()

        for client in announce_clients:
            client.send_cards(cards)
