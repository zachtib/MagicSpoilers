from django.db import models


class MagicSet(models.Model):
    scryfall_id = models.UUIDField(unique=True)
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    release_date = models.DateField()
    watched = models.BooleanField()
    icon_svg_uri = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class MagicCard(models.Model):
    scryfall_id = models.UUIDField(unique=True)
    name = models.CharField(max_length=200)
    magic_set = models.ForeignKey(MagicSet, on_delete=models.CASCADE, related_name='cards')

    def __str__(self):
        return self.name
