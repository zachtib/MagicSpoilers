from datetime import date

from spoilers.models import MagicSet


def get_all_sets():
    return MagicSet.objects.all()


def get_watched_sets():
    return MagicSet.objects.filter(watched=True)


def get_all_sets_ids():
    return MagicSet.objects.values_list('scryfall_id', flat=True)


def unwatch_released_sets():
    today = date.today()
    MagicSet.objects.filter(
        watched=True,
        release_date__isnull=False,
        release_date__lt=today
    ).update(watched=False)
