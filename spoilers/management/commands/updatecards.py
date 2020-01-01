from django.core.management.base import BaseCommand

from spoilers.scryfall import get_client, ScryfallClient


class Command(BaseCommand):
    help = 'Checks for new Cards, announces them, and saves them to the database'

    def handle(self, *args, **options):
        client: ScryfallClient = get_client()
        cards = client.get_all_cards_for_set_code('ptg')
        if cards is not None:
            self.stdout.write(f'Number of cards: {len(cards)}')
            for card in cards[:5]:
                self.stdout.write(str(card))
        else:
            self.stderr.write('Did not get any cards back')
