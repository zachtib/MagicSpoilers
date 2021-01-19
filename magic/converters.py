from .models import CardFace, MagicCard, MagicSet

from scryfall.models import ScryfallCardFace, ScryfallCard, ScryfallImages, ScryfallSet


def get_image_uri(images: ScryfallImages) -> str:
    if images is None:
        return None
    return images.png


def convert_set(item: ScryfallSet) -> MagicSet:
    data = item.to_dict()
    data['scryfall_id'] = item.id

    return MagicSet.from_dict(data)


def convert_card_face(face: ScryfallCardFace) -> CardFace:
    data = face.to_dict()
    data['image_uri'] = get_image_uri(face.image_uris)

    return CardFace.from_dict(data)


def convert_card(card: ScryfallCard) -> MagicCard:
    data = card.to_dict()
    data['scryfall_id'] = card.id
    data['image_uri'] = get_image_uri(card.image_uris)
    data['card_faces'] = [convert_card_face(face) for face in card.card_faces]

    return MagicCard.from_dict(data)
