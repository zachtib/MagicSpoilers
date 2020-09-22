from django.core.management.base import BaseCommand

from announce.models import Channel


class Command(BaseCommand):
    help = 'Checks for new Cards, announces them, and saves them to the database'

    def handle(self, *args, **options):
        announce_clients = Channel.objects.clients()

        for client in announce_clients:
            client.send_text('Testing')
