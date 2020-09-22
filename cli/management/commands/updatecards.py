from django.core.management.base import BaseCommand

from spoilers.service import SpoilersService


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
        service = SpoilersService()
        service.update_cards(quiet)
