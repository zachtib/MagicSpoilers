from magic.models import MagicCard, CardFace
import re
from typing import Union, Optional

re_regular_mana = re.compile(r'{(\w+)}')
re_hybrid_mana = re.compile(r'{(\w+)/(\w+)}')


def format_mana_costs(string: str) -> str:
    string = re_hybrid_mana.sub(r':mana-\1\2:', string)
    string = re_regular_mana.sub(r":mana-\1:", string)
    return string


def format_cardface_manamoji(face: CardFace) -> CardFace:
    face.mana_cost = format_mana_costs(face.mana_cost)
    face.oracle_text = format_mana_costs(face.oracle_text)

    return face


def format_card_manamoji(card: MagicCard) -> MagicCard:
    card.mana_cost = format_mana_costs(card.mana_cost)
    card.oracle_text = format_mana_costs(card.oracle_text)
    card.card_faces = [format_cardface_manamoji(face) for face in card.card_faces]

    return card


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
