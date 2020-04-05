from django.db.models import Count
from django.shortcuts import render

from spoilers.models import MagicSet
from status.models import StatusUpdate


def status_page(request):
    try:
        update = StatusUpdate.objects.latest('timestamp')
    except StatusUpdate.DoesNotExist:
        update = None
    watched_sets = MagicSet.objects.filter(watched=True) \
        .annotate(num_cards=Count('cards'))

    return render(request, 'status.html', {
        'latest_update': update,
        'watched_sets': watched_sets,
    })
