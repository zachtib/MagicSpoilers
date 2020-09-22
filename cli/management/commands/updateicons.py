from django.core.management import BaseCommand

from spoilers.service import SpoilersService


class Command(BaseCommand):
    help = 'Download all icons for watched sets'

    def handle(self, *args, **options):
        service = SpoilersService()
        service.update_icons()
