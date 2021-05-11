from typing import List, Optional

from django.contrib.auth.models import User
from django.db import models

from announce.client import BaseAnnounceClient
from announce.discord.discordclient import DiscordClient
from announce.testing.echoclient import EchoClient
from announce.slack import SlackClient
from announce.testing.testclient import TestClient


class ChannelManager(models.Manager):

    def clients(self) -> List[BaseAnnounceClient]:
        result = []
        for channel in self.get_queryset().all():
            client = channel.client()
            if client is not None:
                result.append(client)
        return result


class Channel(models.Model):
    KIND_ECHO = "EC"
    KIND_SLACK = "SL"
    KIND_DISCORD = "DI"
    KIND_TESTING = "TE"
    KIND_CHOICES = (
        (KIND_SLACK, "Slack"),
        (KIND_DISCORD, "Discord"),
        (KIND_ECHO, "Echo (for testing)"),
        (KIND_TESTING, "Test (for testing)"),
    )
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    kind = models.CharField(max_length=2, choices=KIND_CHOICES)
    webhook_url = models.CharField(max_length=200, blank=True)
    channel_name = models.CharField(max_length=200, blank=True)
    supports_manamoji = models.BooleanField()

    objects = ChannelManager()

    def client(self) -> Optional[BaseAnnounceClient]:
        if self.kind == self.KIND_SLACK:
            return SlackClient(self.webhook_url, self.channel_name, self.supports_manamoji)
        elif self.kind == self.KIND_DISCORD:
            return DiscordClient(self.webhook_url, self.channel_name, self.supports_manamoji)
        elif self.kind == self.KIND_ECHO:
            return EchoClient()
        elif self.kind == self.KIND_TESTING:
            return TestClient()
        else:
            return None

    def __str__(self):
        return self.name
