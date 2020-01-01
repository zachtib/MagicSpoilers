from django.contrib.auth.models import User
from django.db import models


class SlackChannel(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    webhook_url = models.CharField(max_length=200)
    channel_name = models.CharField(max_length=200)
