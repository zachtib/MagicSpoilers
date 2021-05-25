from typing import List, Optional
from django.utils.translation import gettext_lazy as _

from django.contrib.auth.models import User
from django.db import models

from announce.client import BaseAnnounceClient
from announce.discord.discordclient import DiscordClient
from announce.emoji_formatters import BaseManamojiFormatter, NoopManamojiFormatter, HyphenatedManamojiFormatter, \
    NonHyphenatedManamojiFormatter
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
    class Kind(models.TextChoices):
        ECHO = 'EC', 'Echo (for testing)'
        SLACK = 'SL', 'Slack'
        DISCORD = 'DI', 'Discord'
        TESTING = 'TE', 'Testing'

    class EmojiStyle(models.TextChoices):
        NONE = 'NO', 'None'
        HYPHENATED = 'HY', 'Hyphenated'
        NON_HYPHENATED = 'NH', 'Non-hyphenated'

    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    kind = models.CharField(max_length=2, choices=Kind.choices)
    webhook_url = models.CharField(max_length=200, blank=True)
    channel_name = models.CharField(max_length=200, blank=True)
    supports_manamoji = models.BooleanField()
    manamoji_style = models.CharField(max_length=2, choices=EmojiStyle.choices, default=EmojiStyle.NONE)

    objects = ChannelManager()

    def client(self) -> Optional[BaseAnnounceClient]:
        if self.kind == Channel.Kind.SLACK:
            return SlackClient(self.webhook_url, self.channel_name, self.supports_manamoji)
        elif self.kind == Channel.Kind.DISCORD:
            return DiscordClient(self.webhook_url, self.channel_name, self.supports_manamoji)
        elif self.kind == Channel.Kind.ECHO:
            return EchoClient()
        elif self.kind == Channel.Kind.TESTING:
            return TestClient()
        else:
            return None

    def emoji_formatter(self) -> BaseManamojiFormatter:
        if self.supports_manamoji == False or self.manamoji_style == Channel.EmojiStyle.NONE:
            return NoopManamojiFormatter()
        elif self.manamoji_style == Channel.EmojiStyle.HYPHENATED:
            return HyphenatedManamojiFormatter()
        elif self.manamoji_style == Channel.EmojiStyle.NON_HYPHENATED:
            return NonHyphenatedManamojiFormatter()

    def __str__(self):
        return self.name
