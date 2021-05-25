from typing import Union, Optional

from magic.models import MagicCard, CardFace


def get_image_or_none(item: Union[MagicCard, CardFace]) -> str:
    return item.image_uri


def bottom_right_corner_of(item: Union[MagicCard, CardFace]) -> Optional[str]:
    if item.power is not None and item.toughness is not None:
        return f'{item.power}/{item.toughness}'
    elif item.loyalty is not None:
        return item.loyalty
    else:
        return None


def format_card_or_face(item: Union[MagicCard, CardFace]) -> str:
    result = item.name
    if item.mana_cost is not None and len(item.mana_cost) > 0:
        result += ' '
        result += item.mana_cost
    result += '\n'
    result += item.type_line
    result += '\n'
    result += item.oracle_text
    corner = bottom_right_corner_of(item)
    if corner is not None:
        result += '\n'
        result += corner
    return result
