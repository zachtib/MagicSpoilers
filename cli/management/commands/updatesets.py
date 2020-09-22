from django.core.management.base import BaseCommand

from spoilers.service import SpoilersService


class Command(BaseCommand):
    help = 'Checks for new Sets and adds them to the database'

    def handle(self, *args, **options):
        service = SpoilersService()
        service.update_sets()
