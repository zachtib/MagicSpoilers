import datetime

from spoilers.models import MagicSet, MagicCard
from magic.models import MagicSet as MagicSetDataClass, MagicCard as MagicCardDataClass


def db_model_from_dataclass(data: MagicSetDataClass) -> MagicSet:
    release_date = datetime.datetime.strptime(data.released_at, '%Y-%m-%d').date()
    today = datetime.date.today()
    watched = False
    if release_date is not None and release_date > today:
        watched = True
    return MagicSet(scryfall_id=data.scryfall_id,
                    name=data.name,
                    code=data.code,
                    release_date=release_date,
                    watched=watched,
                    icon_svg_uri=data.icon_svg_uri)


def db_card_from_dataclass(magic_set: MagicSet, data: MagicCardDataClass) -> MagicCard:
    return MagicCard(scryfall_id=data.scryfall_id,
                     name=data.name,
                     magic_set=magic_set)
