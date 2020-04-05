from django.core.management import BaseCommand

from spoilers.queries import get_watched_sets
from spoilers.scryfall import get_client, ScryfallClient


class Command(BaseCommand):
    help = 'Download all icons for watched sets'

    def handle(self, *args, **options):
        client: ScryfallClient = get_client()
        api_sets = client.get_all_sets()

        if api_sets is not None:
            self.stdout.write(f'Number of sets from the api: {len(api_sets)}')
            watched_sets = get_watched_sets()
            for magic_set in watched_sets:
                for api_set in api_sets:
                    if api_set.code == magic_set.code:
                        magic_set.icon_svg_uri = api_set.icon_svg_uri
                        magic_set.save()
        else:
            self.stderr.write('Did not get any sets back')
