from django.db import models

from spoilers.models import MagicCard


class StatusUpdate(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
