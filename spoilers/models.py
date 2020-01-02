from django.db import models


class MagicSet(models.Model):
    scryfall_id = models.UUIDField()
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    release_date = models.DateField()
    watched = models.BooleanField()

    def __str__(self):
        return self.name


class MagicCard(models.Model):
    scryfall_id = models.UUIDField()
    name = models.CharField(max_length=200)
    magic_set = models.ForeignKey(MagicSet, on_delete=models.CASCADE)
