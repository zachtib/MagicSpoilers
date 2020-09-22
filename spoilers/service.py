import uuid

from announce.models import Channel
from status.models import StatusUpdate
from .models import MagicSet, MagicCard
from .scryfall import ScryfallClient


class SpoilersService:

    def __init__(self):
        self.scryfall = ScryfallClient()

    def update_sets(self):
        MagicSet.objects.unwatch_released_sets()
        api_sets = self.scryfall.get_all_sets()

        if api_sets is not None:
            print(f'Number of sets from the api: {len(api_sets)}')
            db_set_ids = MagicSet.objects.get_all_set_ids()
            filtered_sets = filter(lambda i: uuid.UUID(i.scryfall_id) not in db_set_ids, api_sets)
            new_records = [MagicSet.from_dataclass(api) for api in filtered_sets]
            for watched_set in filter(lambda i: i.watched, new_records):
                print(f'Watching a new set: {watched_set.name}')

            if len(new_records) > 0:
                MagicSet.objects.bulk_create(new_records)
                StatusUpdate.objects.create()

        else:
            print('Did not get any sets back')

    def update_icons(self):
        api_sets = self.scryfall.get_all_sets()

        if api_sets is not None:
            print(f'Number of sets from the api: {len(api_sets)}')
            watched_sets = MagicSet.objects.watched()
            for magic_set in watched_sets:
                for api_set in api_sets:
                    if api_set.code == magic_set.code:
                        magic_set.icon_svg_uri = api_set.icon_svg_uri
                        magic_set.save()
        else:
            print('Did not get any sets back')

    def update_cards(self, quiet=False):
        watched_sets = MagicSet.objects.watched()
        channel_clients = Channel.objects.clients()
        print(f'Announcing to {len(channel_clients)} channels')

        # noinspection PyBroadException
        try:
            watched_set: MagicSet
            for watched_set in watched_sets:
                known_card_ids_in_set = watched_set.get_card_ids()
                cards_from_api = self.scryfall.get_all_cards_for_set_code(watched_set.code)
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
                        for announce_client in channel_clients:
                            announce_client.send_cards(new_cards)
                    cards_to_insert = [watched_set.create_card_from_dataclass(card_data) for card_data in new_cards]
                    MagicCard.objects.bulk_create(cards_to_insert)
                    StatusUpdate.objects.create()
                else:
                    print(f'No new cards found for {watched_set.name}')
        except Exception as e:
            if not quiet:
                for announce_client in channel_clients:
                    announce_client.send_text(str(e))
            else:
                print(str(e))
