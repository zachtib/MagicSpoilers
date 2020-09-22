from datetime import date
from unittest.mock import patch
from uuid import uuid4

import responses
from django.contrib.auth.models import User
from django.test import TestCase

from announce.models import Channel
from magic.models import MagicSet, MagicCard, CardFace
from .scryfall import ScryfallSet, ScryfallCard, ScryfallCardFace
from .scryfall.converters import convert_set, convert_card
from .service import SpoilersService
from .models import MagicSet as DbSet, MagicCard as DbCard


class ConvertersTests(TestCase):

    def test_simple_conversion(self):
        before = ScryfallSet('', '', '', '', '', '', '')
        expected = MagicSet('', '', '', '', '', '', '')

        actual = convert_set(before)

        self.assertEqual(expected, actual)

    def test_dfc_conversion(self):
        faces = [ScryfallCardFace('a', 'b'), ScryfallCardFace('c', 'd')]
        before = ScryfallCard('', '', '', '', '', '', '', '', card_faces=faces)
        expected_faces = [CardFace('a', 'b'), CardFace('c', 'd')]
        expected = MagicCard('', '', '', '', '', '', '', '', card_faces=expected_faces)

        actual = convert_card(before)

        self.assertEqual(expected, actual)


search_response = '''
{
    "object": "list",
    "total_cards": 1,
    "has_more": false,
    "data": [
        {
            "object": "card",
            "id": "645cfc1b-76f2-4823-9fb0-03cb009f8b32",
            "lang": "en",
            "oracle_id": "ed66cd31-958f-4b28-82a3-e04acc819afc",
            "uri": "https://api.scryfall.com/cards/645cfc1b-76f2-4823-9fb0-03cb009f8b32",
            "name": "Yargle, Glutton of Urborg",
            "scryfall_uri": "https://scryfall.com/card/dom/113/yargle-glutton-of-urborg?utm_source=api",
            "layout": "normal",
            "type_line": "Legendary Creature — Frog Spirit",
            "mana_cost": "{4}{B}",
            "oracle_text": "",
            "power": "9",
            "toughness": "3",
            "image_uris": {
                "small": "https://c1.scryfall.com/file/scryfall-cards/small/front/6/4/645cfc1b-76f2-4823-9fb0-03cb009f8b32.jpg?1562736801",
                "normal": "https://c1.scryfall.com/file/scryfall-cards/normal/front/6/4/645cfc1b-76f2-4823-9fb0-03cb009f8b32.jpg?1562736801",
                "large": "https://c1.scryfall.com/file/scryfall-cards/large/front/6/4/645cfc1b-76f2-4823-9fb0-03cb009f8b32.jpg?1562736801",
                "png": "https://c1.scryfall.com/file/scryfall-cards/png/front/6/4/645cfc1b-76f2-4823-9fb0-03cb009f8b32.png?1562736801",
                "art_crop": "https://c1.scryfall.com/file/scryfall-cards/art_crop/front/6/4/645cfc1b-76f2-4823-9fb0-03cb009f8b32.jpg?1562736801",
                "border_crop": "https://c1.scryfall.com/file/scryfall-cards/border_crop/front/6/4/645cfc1b-76f2-4823-9fb0-03cb009f8b32.jpg?1562736801"
            }
        }
    ]
}
'''.strip()

class SpoilerServiceTestCase(TestCase):

    def setUp(self):
        self.service = SpoilersService()

    def test_update_sets(self):
        with responses.RequestsMock() as rm:
            rm.add('GET', 'https://api.scryfall.com/sets', '''
            {
                "object": "list",
                "has_more": false,
                "data": [
                    {
                      "object": "set",
                      "id": "a4a0db50-8826-4e73-833c-3fd934375f96",
                      "code": "aer",
                      "mtgo_code": "aer",
                      "arena_code": "aer",
                      "tcgplayer_id": 1857,
                      "name": "Aether Revolt",
                      "uri": "https://api.scryfall.com/sets/a4a0db50-8826-4e73-833c-3fd934375f96",
                      "scryfall_uri": "https://scryfall.com/sets/aer",
                      "search_uri": "https://api.scryfall.com/cards/search?order=set&q=e%3Aaer&unique=prints",
                      "released_at": "2017-01-20",
                      "set_type": "expansion",
                      "card_count": 194,
                      "printed_size": 184,
                      "digital": false,
                      "nonfoil_only": false,
                      "foil_only": false,
                      "block_code": "kld",
                      "block": "Kaladesh",
                      "icon_svg_uri": "https://c2.scryfall.com/file/scryfall-symbols/sets/aer.svg?1600660800"
                    }
                ]
            }
            '''.strip())
            self.service.update_sets()

            self.assertEqual(DbSet.objects.count(), 1)
            actual = DbSet.objects.first()
            self.assertEqual(actual.code, 'aer')
            self.assertEqual(actual.name, 'Aether Revolt')

    def test_update_cards(self):
        DbSet.objects.create(
            scryfall_id=uuid4(),
            code='abc',
            name='Test Set',
            release_date=date.today(),
            watched=True,
            icon_svg_uri='asdf.png',
        )
        with responses.RequestsMock() as rm:
            rm.add('GET', 'https://api.scryfall.com/cards/search?order=spoiled&q=e=abc&unique=card', search_response)
            self.service.update_cards(True)

            self.assertEqual(DbCard.objects.count(), 1)

    @patch('builtins.print')
    def test_update_cards_calls_channel(self, mock_print):
        DbSet.objects.create(
            scryfall_id=uuid4(),
            code='abc',
            name='Test Set',
            release_date=date.today(),
            watched=True,
            icon_svg_uri='asdf.png',
        )
        user = User.objects.create_user('asdf')
        Channel.objects.create(
            owner=user,
            name='test',
            kind=Channel.KIND_ECHO,
            supports_manamoji=False
        )
        with responses.RequestsMock() as rm:
            rm.add('GET', 'https://api.scryfall.com/cards/search?order=spoiled&q=e=abc&unique=card', search_response)
            self.service.update_cards()

            self.assertEqual(DbCard.objects.count(), 1)

            expected = MagicCard(scryfall_id='645cfc1b-76f2-4823-9fb0-03cb009f8b32', lang='en', oracle_id='ed66cd31-958f-4b28-82a3-e04acc819afc', uri='https://api.scryfall.com/cards/645cfc1b-76f2-4823-9fb0-03cb009f8b32', name='Yargle, Glutton of Urborg', scryfall_uri='https://scryfall.com/card/dom/113/yargle-glutton-of-urborg?utm_source=api', layout='normal', type_line='Legendary Creature — Frog Spirit', card_faces=[], color_indicator=[], loyalty=None, mana_cost='{4}{B}', oracle_text='', power='9', toughness='3', image_uri='https://c1.scryfall.com/file/scryfall-cards/png/front/6/4/645cfc1b-76f2-4823-9fb0-03cb009f8b32.png?1562736801')

            mock_print.assert_called_with(expected)