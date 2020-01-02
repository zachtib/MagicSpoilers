from django.core.management.base import BaseCommand

from announce.queries import get_all_channel_clients


class Command(BaseCommand):
    help = 'Checks for new Cards, announces them, and saves them to the database'

    def handle(self, *args, **options):
        announce_clients = get_all_channel_clients()

        for client in announce_clients:
            client.send_text('Testing')
