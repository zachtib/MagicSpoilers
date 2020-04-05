import uuid

from django.core.management.base import BaseCommand

from spoilers.models import MagicSet, MagicCard
from spoilers.scryfall import get_client, ScryfallClient
from spoilers.queries import get_watched_sets, get_card_ids_in_set, save_cards
from announce.queries import get_all_channel_clients
from spoilers.converters import db_card_from_dataclass
from status.models import StatusUpdate


class Command(BaseCommand):
    help = 'Checks for new Cards, announces them, and saves them to the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--quiet',
            action='store_true',
            help='Just update the database, don\'t announce',
        )

    def handle(self, *args, **options):
        quiet = options.get('quiet', False)
        client: ScryfallClient = get_client()
        watched_sets = get_watched_sets()
        announce_clients = list()
        if not quiet:
            announce_clients = get_all_channel_clients()
        self.stdout.write(f'Announcing to {len(announce_clients)} channels')

        watched_set: MagicSet
        for watched_set in watched_sets:
            known_card_ids_in_set = get_card_ids_in_set(watched_set)
            cards_from_api = client.get_all_cards_for_set_code(watched_set.code)
            new_cards = list()
            for card in cards_from_api:
                if len(new_cards) >= 10 and not quiet:
                    continue
                if uuid.UUID(card.scryfall_id) not in known_card_ids_in_set:
                    new_cards.append(card)
            if len(new_cards) > 10 and not quiet:
                new_cards = new_cards[:10]
            if len(new_cards) > 0:
                if not quiet:
                    for announce_client in announce_clients:
                        announce_client.send_cards(new_cards)
                cards_to_insert = [db_card_from_dataclass(watched_set, card_data) for card_data in new_cards]
                save_cards(cards_to_insert)
                StatusUpdate.objects.create()
            else:
                self.stdout.write(f'No new cards found for {watched_set.name}')
