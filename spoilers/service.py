import uuid

from django.db import IntegrityError, transaction

from announce.models import Channel
from magic.repository import MagicRepository, SearchSpec
from status.models import StatusUpdate
from .models import MagicSet, MagicCard


class SpoilersService:

    def __init__(self):
        self.repo = MagicRepository()

    def update_sets(self):
        MagicSet.objects.unwatch_released_sets()
        api_sets = self.repo.sets()

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
        api_sets = self.repo.sets()

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

        watched_set: MagicSet
        for watched_set in watched_sets:
            known_card_ids_in_set = watched_set.get_card_ids()
            cards_from_api = self.repo.search(SearchSpec(expansion=watched_set.code, order='spoiled', unique='card'))
            new_cards = list()
            for card in cards_from_api:
                if len(new_cards) >= 10 and not quiet:
                    continue
                if uuid.UUID(card.scryfall_id) not in known_card_ids_in_set:
                    card_to_insert = watched_set.create_card_from_dataclass(card)
                    failed = False
                    try:
                        with transaction.atomic():
                            card_to_insert.save()
                        new_cards.append(card)
                    except IntegrityError as e:
                        # uuid already exists, card may have been mistakenly added to another set
                        failed = True
                        duplicate = MagicCard.objects.get(scryfall_id=card.scryfall_id)
                        duplicate.delete()
                    if failed:
                        try:
                            with transaction.atomic():
                                card_to_insert.save()
                        except IntegrityError as e:
                            # Error still happening
                            if not quiet:
                                for announce_client in channel_clients:
                                    announce_client.send_text(f'Encountered IntegrityError inserting {card}: {e}')
            if len(new_cards) > 10 and not quiet:
                new_cards = new_cards[:10]
            if len(new_cards) > 0:
                if not quiet:
                    for announce_client in channel_clients:
                        announce_client.send_cards(new_cards)
                StatusUpdate.objects.create()
            else:
                print(f'No new cards found for {watched_set.name}')
