from django.contrib.auth.models import User
from django.db import models

from announce.echo.echoclient import EchoClient
from announce.slack import SlackClient


class ChannelManager(models.Manager):

    def clients(self):
        result = []
        for channel in self.get_queryset():
            client = channel.client()
            if client is not None:
                result.append(client)
        return result


class Channel(models.Model):
    KIND_ECHO = "EC"
    KIND_SLACK = "SL"
    KIND_CHOICES = (
        (KIND_SLACK, "Slack"),
        (KIND_ECHO, "Echo (for testing)")
    )
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    kind = models.CharField(max_length=2, choices=KIND_CHOICES)
    webhook_url = models.CharField(max_length=200, blank=True)
    channel_name = models.CharField(max_length=200, blank=True)
    supports_manamoji = models.BooleanField()

    objects = ChannelManager()

    def client(self):
        if self.kind == self.KIND_SLACK:
            return SlackClient(self.webhook_url, self.channel_name, self.supports_manamoji)
        elif self.kind == self.KIND_ECHO:
            return EchoClient()
        else:
            return None

    def __str__(self):
        return self.name
