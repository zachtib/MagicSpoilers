import datetime

from spoilers.models import MagicSet
from spoilers.scryfall import ScryfallSet


def db_set_from_api(api: ScryfallSet) -> MagicSet:
    release_date = datetime.datetime.strptime(api.released_at, '%Y-%m-%d').date()
    today = datetime.date.today()
    watched = False
    if release_date is not None and release_date > today:
        watched = True
    return MagicSet(scryfall_id=api.id,
                    name=api.name,
                    code=api.code,
                    release_date=release_date,
                    watched=watched)
