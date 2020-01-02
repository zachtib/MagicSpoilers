from typing import List

from .models import Channel
from .slack import SlackClient


def get_all_channel_clients() -> List[SlackClient]:
    channels = Channel.objects.all()
    clients = [channel.client() for channel in channels]

    return clients
