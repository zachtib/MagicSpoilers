from django.core.management.base import BaseCommand

from spoilers.scryfall import get_client, ScryfallClient


class Command(BaseCommand):
    help = 'Checks for new Sets and adds them to the database'

    def handle(self, *args, **options):
        client: ScryfallClient = get_client()
        sets = client.get_all_sets()
        if sets is not None:
            self.stdout.write(f'Number of sets: {len(sets)}')
            for item in sets[:5]:
                self.stdout.write(str(item))
        else:
            self.stderr.write('Did not get any sets back')
