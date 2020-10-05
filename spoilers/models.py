from datetime import date, datetime

from django.db import models

from magic.models import MagicSet as MagicSetDataClass, MagicCard as MagicCardDataClass


class MagicSetManager(models.Manager):

    def watched(self):
        return self.get_queryset().filter(watched=True)

    def get_all_set_ids(self):
        return set(self.get_queryset().values_list('scryfall_id', flat=True))

    def unwatch_released_sets(self):
        """
        Update all sets where the non-null release date is in the past to
        no longer be watched

        :return: The number of changed rows
        """
        today = date.today()
        return self.get_queryset().filter(
            watched=True,
            continuous=False,
            release_date__isnull=False,
            release_date__lt=today
        ).update(watched=False)


class MagicSet(models.Model):
    scryfall_id = models.UUIDField(unique=True)
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    release_date = models.DateField()
    watched = models.BooleanField()
    icon_svg_uri = models.CharField(max_length=100)
    continuous = models.BooleanField(default=False)

    def get_card_ids(self):
        """
        Look up the set of all ids for a given MagicSet so that the set
        can be compared against a value from the server to determine new
        cards

        :return: the set of ids belonging to cards in this set
        """
        return set(self.cards.values_list('scryfall_id', flat=True))

    def create_card_from_dataclass(self, data: MagicCardDataClass):
        return MagicCard(scryfall_id=data.scryfall_id,
                         name=data.name,
                         magic_set=self)

    objects = MagicSetManager()

    def __str__(self):
        return self.name

    @classmethod
    def from_dataclass(cls, data: MagicSetDataClass):
        release_date = datetime.strptime(data.released_at, '%Y-%m-%d').date()
        today = date.today()
        watched = False
        if release_date is not None and release_date > today:
            watched = True
        return MagicSet(scryfall_id=data.scryfall_id,
                        name=data.name,
                        code=data.code,
                        release_date=release_date,
                        watched=watched,
                        icon_svg_uri=data.icon_svg_uri)


class MagicCardManager(models.Manager):
    pass


class MagicCard(models.Model):
    scryfall_id = models.UUIDField(unique=True)
    name = models.CharField(max_length=200)
    magic_set = models.ForeignKey(MagicSet, on_delete=models.CASCADE, related_name='cards')

    objects = MagicCardManager()

    def __str__(self):
        return self.name