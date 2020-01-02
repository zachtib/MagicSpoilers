from django.core.management.base import BaseCommand

from spoilers.converters import db_set_from_api
from spoilers.models import MagicSet
from spoilers.queries import get_all_sets_ids, unwatch_released_sets
from spoilers.scryfall import get_client, ScryfallClient


class Command(BaseCommand):
    help = 'Checks for new Sets and adds them to the database'

    def handle(self, *args, **options):
        unwatch_released_sets()
        client: ScryfallClient = get_client()
        api_sets = client.get_all_sets()
        if api_sets is not None:
            self.stdout.write(f'Number of sets from the api: {len(api_sets)}')
            db_set_ids = get_all_sets_ids()
            filtered_sets = filter(lambda i: i.id not in db_set_ids, api_sets)
            new_records = [db_set_from_api(api) for api in filtered_sets]
            for watched_set in filter(lambda i: i.watched, new_records):
                self.stdout.write(f'Watching a new set: {watched_set.name}')
            MagicSet.objects.bulk_create(new_records)
        else:
            self.stderr.write('Did not get any sets back')
