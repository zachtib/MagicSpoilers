from django.contrib.auth.models import User
from django.db import models

from announce.slack import SlackClient


class Channel(models.Model):
    KIND_SLACK = "SL"
    KIND_CHOICES = (
        (KIND_SLACK, "Slack"),
    )
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    kind = models.CharField(max_length=2, choices=KIND_CHOICES)
    webhook_url = models.CharField(max_length=200)
    channel_name = models.CharField(max_length=200)
    supports_manamoji = models.BooleanField()

    def client(self):
        if self.kind == self.KIND_SLACK:
            return SlackClient(self.webhook_url, self.channel_name)
        else:
            return None

    def __str__(self):
        return self.name

