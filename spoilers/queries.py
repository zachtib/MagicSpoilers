from datetime import date
from typing import List, Set

from django.db.models import TextField
from django.db.models.functions import Cast

from spoilers.models import MagicSet, MagicCard


def get_all_sets():
    return MagicSet.objects.all()


def get_watched_sets():
    return MagicSet.objects.filter(watched=True)


def get_all_sets_ids() -> Set[str]:
    return set(MagicSet.objects.values_list('scryfall_id', flat=True))


def unwatch_released_sets():
    today = date.today()
    MagicSet.objects.filter(
        watched=True,
        release_date__isnull=False,
        release_date__lt=today
    ).update(watched=False)


def get_card_ids_in_set(magic_set: MagicSet):
    return set(MagicCard.objects.filter(magic_set=magic_set)
               .values_list('scryfall_id', flat=True))


def save_cards(cards: List[MagicCard]):
    MagicCard.objects.bulk_create(cards)
