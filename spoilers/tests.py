import os
from datetime import date
from unittest import mock
from unittest.mock import patch
from uuid import uuid4

import responses
from django.contrib.auth.models import User
from django.test import TestCase

from announce.models import Channel
from announce.testing.testclient import TestClient
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

    def create_test_set_user_and_channel(self):
        test_set = DbSet.objects.create(
            scryfall_id=uuid4(),
            code='abc',
            name='Test Set',
            release_date=date.today(),
            watched=True,
            icon_svg_uri='asdf.png',
        )
        user = User.objects.create_user('asdf')
        channel = Channel.objects.create(
            owner=user,
            name='test',
            kind=Channel.Kind.ECHO,
            supports_manamoji=False
        )
        return test_set, user, channel

    @patch('builtins.print')
    def test_update_cards_calls_channel(self, mock_print):
        _, _, _ = self.create_test_set_user_and_channel()
        with responses.RequestsMock() as rm:
            rm.add('GET', 'https://api.scryfall.com/cards/search?order=spoiled&q=e=abc&unique=card', search_response)
            self.service.update_cards()

            self.assertEqual(DbCard.objects.count(), 1)

            expected = MagicCard(scryfall_id='645cfc1b-76f2-4823-9fb0-03cb009f8b32', lang='en',
                                 oracle_id='ed66cd31-958f-4b28-82a3-e04acc819afc',
                                 uri='https://api.scryfall.com/cards/645cfc1b-76f2-4823-9fb0-03cb009f8b32',
                                 name='Yargle, Glutton of Urborg',
                                 scryfall_uri='https://scryfall.com/card/dom/113/yargle-glutton-of-urborg?utm_source=api',
                                 layout='normal', type_line='Legendary Creature — Frog Spirit', card_faces=[],
                                 color_indicator=[], loyalty=None, mana_cost='{4}{B}', oracle_text='', power='9',
                                 toughness='3',
                                 image_uri='https://c1.scryfall.com/file/scryfall-cards/png/front/6/4/645cfc1b-76f2-4823-9fb0-03cb009f8b32.png?1562736801')

            mock_print.assert_called_with(expected)

    def basic_land_response(self, land) -> str:
        return '''
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
                    "name": "%s",
                    "scryfall_uri": "https://scryfall.com/card/dom/113/yargle-glutton-of-urborg?utm_source=api",
                    "layout": "normal",
                    "type_line": "Basic Land - %s",
                    "oracle_text": "",
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
        '''.strip() % (land, land)

    @patch('builtins.print')
    def test_plains_does_not_call_channel(self, mock_print):
        self.create_test_set_user_and_channel()
        with responses.RequestsMock() as rm:
            rm.add('GET', 'https://api.scryfall.com/cards/search?order=spoiled&q=e=abc&unique=card',
                   self.basic_land_response('Plains'))
            self.service.update_cards()

            self.assertEqual(DbCard.objects.count(), 1)

            mock_print.assert_called_with('No new cards found for Test Set')
            card: DbCard = DbCard.objects.first()
            self.assertEqual(card.name, 'Plains')

    @patch('builtins.print')
    def test_swamp_does_not_call_channel(self, mock_print):
        self.create_test_set_user_and_channel()
        with responses.RequestsMock() as rm:
            rm.add('GET', 'https://api.scryfall.com/cards/search?order=spoiled&q=e=abc&unique=card',
                   self.basic_land_response('Swamp'))
            self.service.update_cards()

            self.assertEqual(DbCard.objects.count(), 1)

            mock_print.assert_called_with('No new cards found for Test Set')
            card: DbCard = DbCard.objects.first()
            self.assertEqual(card.name, 'Swamp')


class IntegrityErrorTestCase(TestCase):

    def setUp(self) -> None:
        khm = DbSet.objects.create(scryfall_id='43057fad-b1c1-437f-bc48-0045bce6d8c9',
                                   code='khm',
                                   name='Kaldheim',
                                   release_date='2021-02-05',
                                   watched=True,
                                   icon_svg_uri='foobar')

        DbCard.objects.create(magic_set=khm, scryfall_id="d18396f9-ae20-4471-84ab-a2148319bc39",
                              name="Anri Slays the Troll")
        DbCard.objects.create(magic_set=khm, scryfall_id="19312f53-5b9d-4e76-91e8-65f444bb68c9",
                              name="Nike Defies Destiny")
        DbCard.objects.create(magic_set=khm, scryfall_id="7fb94456-5266-47db-b514-a0e17e34b771", name="Poison the Cup")
        DbCard.objects.create(magic_set=khm, scryfall_id="24e58478-c6a8-4f86-854a-a489c99bd777",
                              name="Usher of the Fallen")
        DbCard.objects.create(magic_set=khm, scryfall_id="74f68014-489d-4f51-a959-0f335541cb4e", name="Vault Robber")
        DbCard.objects.create(magic_set=khm, scryfall_id="fab2fca4-a99f-4ffe-9c02-edb6e0be2358",
                              name="Cosima, God of the Voyage // The Omenkeel")
        DbCard.objects.create(magic_set=khm, scryfall_id="2627acb7-57d9-4429-9bc5-e7dd444d8d48",
                              name="Gates of Istfell")
        DbCard.objects.create(magic_set=khm, scryfall_id="dfc1df84-9c47-444b-9d58-d9c7bed51c66",
                              name="Beskir Shieldmate")
        DbCard.objects.create(magic_set=khm, scryfall_id="c22c7383-ba4d-4b3c-91d6-2d6528e19825",
                              name="Smashing Success")
        DbCard.objects.create(magic_set=khm, scryfall_id="a54d0170-a375-4e65-b98d-3e94a3aeef90",
                              name="Tuskeri Firewalker")
        DbCard.objects.create(magic_set=khm, scryfall_id="0b02149a-4a8f-4be9-9944-3d216248b549",
                              name="\"Surtland Frostfire\"")
        DbCard.objects.create(magic_set=khm, scryfall_id="3a9fb75e-c8e5-417b-83d4-5105af9c66c1", name="Revitalize")
        DbCard.objects.create(magic_set=khm, scryfall_id="0f75c3ad-839a-4658-9706-5d9df7ce6dff",
                              name="\"Writing Werewolf Fanfics\"")
        DbCard.objects.create(magic_set=khm, scryfall_id="40bcc7cb-65dd-4bc6-8606-a162fa6c65f7",
                              name="Dwarven Reinforcements")
        DbCard.objects.create(magic_set=khm, scryfall_id="82c2a0f7-0f53-4627-8be8-227fde331a69",
                              name="Skemfar Elderhall")
        DbCard.objects.create(magic_set=khm, scryfall_id="735470df-65d8-43e9-837e-4869c8e4f052",
                              name="Gnottvold Slumbermound")
        DbCard.objects.create(magic_set=khm, scryfall_id="b251aa7c-d011-4b52-ab92-415d536c0182", name="Tundra Fumarole")
        DbCard.objects.create(magic_set=khm, scryfall_id="4fa13084-3e68-49f4-8cc9-6d02286fd150", name="Scorn Effigy")
        DbCard.objects.create(magic_set=khm, scryfall_id="44d4cd64-8560-48f5-b0bc-f75286c1c91c",
                              name="Goldmaw Champion")
        DbCard.objects.create(magic_set=khm, scryfall_id="4de5ff64-6fe7-4fc5-be27-cdbaa14545ab", name="Axgard Braggart")
        DbCard.objects.create(magic_set=khm, scryfall_id="212462b7-e23e-4c87-93aa-9cadefbf1ac8",
                              name="Fearless Liberator")
        DbCard.objects.create(magic_set=khm, scryfall_id="f9c77d35-8418-48fb-b7d7-7cfa763545c5", name="Axguard Armory")
        DbCard.objects.create(magic_set=khm, scryfall_id="1ef89770-2dbb-4a57-99f7-191591bb8e38", name="Runed Crown")
        DbCard.objects.create(magic_set=khm, scryfall_id="89ecb530-e429-4b50-a24c-8437614cf224",
                              name="\"Resolute Valkyrie\"")
        DbCard.objects.create(magic_set=khm, scryfall_id="3606519e-5677-4c21-a34e-be195b6669fa",
                              name="\"Reidane, God of Justice\" // \"Reidane's Shield\"")
        DbCard.objects.create(magic_set=khm, scryfall_id="f670c380-6faa-42ec-ab41-6be8137169b2",
                              name="Karfell Kennel-Master")
        DbCard.objects.create(magic_set=khm, scryfall_id="86a4c348-1012-4339-960a-c7bc7fd84fbb", name="Clarion Spirit")
        DbCard.objects.create(magic_set=khm, scryfall_id="68011f60-6202-48f4-8255-fb94764e2951",
                              name="Aegar, the Freezing Flame")
        DbCard.objects.create(magic_set=khm, scryfall_id="03dff23e-d7e3-4d75-a9dc-fdf4a42f31e0",
                              name="Firja's Judgment")
        DbCard.objects.create(magic_set=khm, scryfall_id="af46c8c8-5dfa-4ebb-b0b9-cd25d01dd432",
                              name="Gnottvold Recluse")
        DbCard.objects.create(magic_set=khm, scryfall_id="3f406ce3-dce1-42d3-b76c-8e8c4b2770cb", name="Frostpeak Yeti")
        DbCard.objects.create(magic_set=khm, scryfall_id="be43a643-6cb7-4bb6-a28d-8ad30b7fbb6d",
                              name="\"Beasts of Littjara\"")
        DbCard.objects.create(magic_set=khm, scryfall_id="771e307c-b2e3-47ac-aac2-59f0c3542fa6", name="Forest")
        DbCard.objects.create(magic_set=khm, scryfall_id="5cbfbafa-f58f-40b2-a374-68ac35b77d89", name="Plains")
        DbCard.objects.create(magic_set=khm, scryfall_id="69419307-53d5-40d7-82da-cab2e7bfbda4", name="Mountain")
        DbCard.objects.create(magic_set=khm, scryfall_id="1a25a714-c7f3-4697-8b69-8f966b4d370a", name="Island")
        DbCard.objects.create(magic_set=khm, scryfall_id="9f9e61c0-b185-4704-913f-9284ed0ce250", name="Swamp")
        DbCard.objects.create(magic_set=khm, scryfall_id="cd31ec15-2fe0-40ab-b320-bc4333db4787",
                              name="Battle for Bretagard")
        DbCard.objects.create(magic_set=khm, scryfall_id="421376e4-a4ad-427c-bc9c-d315308dcf68",
                              name="Narfi, Betrayer King")
        DbCard.objects.create(magic_set=khm, scryfall_id="f7b877e2-60eb-46cd-acd7-8555b9e7e993",
                              name="\"Mystic Reflection\"")
        DbCard.objects.create(magic_set=khm, scryfall_id="45c48042-178f-432e-9eee-10bfa1e0795f",
                              name="Funeral Longboat")
        DbCard.objects.create(magic_set=khm, scryfall_id="9bf5e4ad-a6e9-4b7c-a1ec-8246d3a3b6ca", name="Goldvein Pick")
        DbCard.objects.create(magic_set=khm, scryfall_id="fd4aade3-b1e3-43d1-b4a8-6b55ecdb4327", name="Draugr's Helm")
        DbCard.objects.create(magic_set=khm, scryfall_id="d6b26c95-f90d-43fb-8c99-2a3aa13ac2c6",
                              name="Wings of the Cosmos")
        DbCard.objects.create(magic_set=khm, scryfall_id="89cef049-6a47-4264-b2bc-b9d291a09c4c",
                              name="\"Shirtless Snow Wizard\"")
        DbCard.objects.create(magic_set=khm, scryfall_id="4911016c-b92a-47cc-9553-b424d7be196a",
                              name="\"Draugr Omenreader\"")
        DbCard.objects.create(magic_set=khm, scryfall_id="f3567bdc-450e-4481-9349-a80fe52fe431",
                              name="\"Frigid - Sea Traveler\"")
        DbCard.objects.create(magic_set=khm, scryfall_id="b2d40071-cadf-48de-a8ed-d55adbfab632",
                              name="\"Cyclone Summoner\"")
        DbCard.objects.create(magic_set=khm, scryfall_id="620ed5b7-8874-40d0-9245-98876bdec153",
                              name="Battle of Frost and Fire")
        DbCard.objects.create(magic_set=khm, scryfall_id="d6eb23c9-6061-4ad1-a8f3-2c791c49f352",
                              name="\"Breakneck Berserker \"")
        DbCard.objects.create(magic_set=khm, scryfall_id="71a659b6-c4a8-4c0a-8b2a-07b6c9e27dfc",
                              name="King Harald's Revenge")
        DbCard.objects.create(magic_set=khm, scryfall_id="5b5490b8-5652-40f5-8678-e1263ef69b5a", name="Duskwielder")
        DbCard.objects.create(magic_set=khm, scryfall_id="e4802e6c-6921-4dac-bf44-7e09d6942b71",
                              name="Cinderheart Giant")
        DbCard.objects.create(magic_set=khm, scryfall_id="b65c215d-562d-4c7c-bc9f-b1d741050158",
                              name="Search for Glory")
        DbCard.objects.create(magic_set=khm, scryfall_id="d5c1a271-2107-462a-9d4a-9c7fbcfa8d77", name="Rune of Flight")
        DbCard.objects.create(magic_set=khm, scryfall_id="e0b99299-bf84-4654-a331-e4406768b33c", name="Squash")
        DbCard.objects.create(magic_set=khm, scryfall_id="5e8bded3-46c3-474f-9d09-978df8705ad1",
                              name="\"Matantiga Mentor\"")
        DbCard.objects.create(magic_set=khm, scryfall_id="1a68615d-9808-479d-aa80-50651246954e",
                              name="\"Jasper Sentinel\"")
        DbCard.objects.create(magic_set=khm, scryfall_id="b32aea04-04f7-48a8-a8ab-8b38fa53da3b", name="Basalt Ravager")
        DbCard.objects.create(magic_set=khm, scryfall_id="276f8abd-4d39-4b50-876f-9c6713bc4ab5",
                              name="Frostpyre Arcanist")
        DbCard.objects.create(magic_set=khm, scryfall_id="0fc2478f-e624-46fb-85af-1254564cd4d2",
                              name="Weathered Runestone")
        DbCard.objects.create(magic_set=khm, scryfall_id="76ee3829-8dec-4c0f-a6c2-ad47a1c94cfc",
                              name="\"Ski Resort Bandit\"")
        DbCard.objects.create(magic_set=khm, scryfall_id="205eb029-68a0-4895-b142-2eb09987b5cb",
                              name="\"My Larger Pony\"")
        DbCard.objects.create(magic_set=khm, scryfall_id="ce33c84e-008c-48d8-a8e8-77cd19cc4f1f",
                              name="\"Shepherd of the Cosmos\"")
        DbCard.objects.create(magic_set=khm, scryfall_id="80340582-655b-4bf1-88fb-14bcbe17aa04",
                              name="\"Pyrefly Chomper\"")
        DbCard.objects.create(magic_set=khm, scryfall_id="875a20c2-1d17-46ea-b4d2-3e70bc05aae3", name="Crush the Weak")
        DbCard.objects.create(magic_set=khm, scryfall_id="ea660d42-a441-48d8-98c1-00933cde94a4",
                              name="Starnheim Unleased")
        DbCard.objects.create(magic_set=khm, scryfall_id="6ef580f8-efec-4d31-8dc3-2018dd48b6f4", name="Dual Strike")
        DbCard.objects.create(magic_set=khm, scryfall_id="5f856b0e-b413-49b0-9aa7-d935ad40ae53",
                              name="\"Demonic Lightning\"")
        DbCard.objects.create(magic_set=khm, scryfall_id="4d3b0c3b-896e-4d1e-b7fb-670718ba97d4",
                              name="Burning-Rune Demon")
        DbCard.objects.create(magic_set=khm, scryfall_id="44c8136f-2826-476c-a103-7094670506a6", name="Run Amok")
        DbCard.objects.create(magic_set=khm, scryfall_id="1316a74e-da55-4668-87f2-98389a90a2a4",
                              name="Codespell Cleric")
        DbCard.objects.create(magic_set=khm, scryfall_id="0e55041f-69a5-4bcf-899f-a4b44c208b4d", name="Mammoth Growth")
        DbCard.objects.create(magic_set=khm, scryfall_id="f572cbb1-49ee-4c95-90a3-82704cf92454",
                              name="\"Raiding Karve\"")
        DbCard.objects.create(magic_set=khm, scryfall_id="fc71d8ca-c613-4534-bc9d-bc1e13202a2c",
                              name="\"Big - Botty Ox\"")
        DbCard.objects.create(magic_set=khm, scryfall_id="7f3a6148-d005-49c1-a7fc-867c4e8251cd",
                              name="Elderfang Disciple")
        DbCard.objects.create(magic_set=khm, scryfall_id="99a1a75b-20cf-4db9-a244-cc54411446c4",
                              name="Feed the Serpent")
        DbCard.objects.create(magic_set=khm, scryfall_id="074d526a-1eef-4045-bd38-f6d68c4bc4b9",
                              name="\"Midas Touch't\"")
        DbCard.objects.create(magic_set=khm, scryfall_id="9dfdb73d-b001-4a59-b79e-8c8c1baea116",
                              name="Egon, God of Death // Throne of Death")
        DbCard.objects.create(magic_set=khm, scryfall_id="e7c5f681-0145-45e9-b943-ca9784cfdea0",
                              name="Harald Unites the Elves")
        DbCard.objects.create(magic_set=khm, scryfall_id="233e4774-e701-42d9-aa25-e7e06c14e43d",
                              name="Kardur's Vicious Return")
        DbCard.objects.create(magic_set=khm, scryfall_id="c697548f-925b-405e-970a-4e78067d5c8e",
                              name="Jorn, God of Winter // Kaldring, the Rimestaff")
        DbCard.objects.create(magic_set=khm, scryfall_id="734afb5b-3163-47fa-856f-8a85b9da22d3", name="Roots of Wisdom")
        DbCard.objects.create(magic_set=khm, scryfall_id="2411c341-a470-4484-9248-7c1d3ca12978", name="Axgard Cavalry")
        DbCard.objects.create(magic_set=khm, scryfall_id="597fe119-64a7-4499-8b69-738af5a71a20", name="Withercrown")
        DbCard.objects.create(magic_set=khm, scryfall_id="9eac78a2-599f-4dba-aec7-982c5ae3f75a",
                              name="Harald, Kind of Skemfar")
        DbCard.objects.create(magic_set=khm, scryfall_id="22a6a5f1-1405-4efb-af3e-e1f58d664e99",
                              name="Toralf, God of Fury // Toralf's Hammer")
        DbCard.objects.create(magic_set=khm, scryfall_id="696a8c12-4a1f-4b96-a921-538fa1a2de43", name="Divine Gambit")
        DbCard.objects.create(magic_set=khm, scryfall_id="2318d4f8-309e-4645-b6d1-46572edd6996",
                              name="Tormentor's Helm")
        DbCard.objects.create(magic_set=khm, scryfall_id="8d18008f-10d2-4cdf-b4b5-7675782a8b0d", name="Tyvar Kell")
        DbCard.objects.create(magic_set=khm, scryfall_id="dd921e27-3e08-438c-bec2-723226d35175",
                              name="Tibalt's Trickery")
        DbCard.objects.create(magic_set=khm, scryfall_id="d7de696a-49c2-421d-a86c-bcffd68870c6",
                              name="\"Jack and Jill Storm the Hill\"")
        DbCard.objects.create(magic_set=khm, scryfall_id="455ae615-20d7-4251-828d-72a3345d06f1", name="Boreal Outrider")
        DbCard.objects.create(magic_set=khm, scryfall_id="1a67c196-632c-4c7b-a132-de07d894e634",
                              name="\"Wake the Draugr\"")
        DbCard.objects.create(magic_set=khm, scryfall_id="60f6a159-b969-4767-802e-409f8bf286fe", name="Dogged Persuit")
        DbCard.objects.create(magic_set=khm, scryfall_id="9685e2a0-5573-41bc-a914-f40c3011459b",
                              name="\"Kadur, Doomscourge\"")
        DbCard.objects.create(magic_set=khm, scryfall_id="7eed5a2d-d7a4-4f64-a96b-04c5d4206c5a", name="Run Ashore")
        DbCard.objects.create(magic_set=khm, scryfall_id="417f71d2-d7da-4279-8847-d27c67e9ea9d", name="Tegrid's Shadow")
        DbCard.objects.create(magic_set=khm, scryfall_id="4e4023c8-8e7f-42b9-99e5-87e80fc3d6c8",
                              name="Open the Omenpaths")
        DbCard.objects.create(magic_set=khm, scryfall_id="a6308a53-de07-4ed9-80a1-3579843466c2",
                              name="\"Fabulous Berserker\"")
        DbCard.objects.create(magic_set=khm, scryfall_id="f9f2029f-ffda-4374-9a78-79866ac23fca",
                              name="\"Big - Axe Diplomat\"")
        DbCard.objects.create(magic_set=khm, scryfall_id="22fdbe71-abca-4e48-99b2-1cb6b35d930b",
                              name="Moritte of the Frost")
        DbCard.objects.create(magic_set=khm, scryfall_id="eb8a16f6-55c1-40eb-998f-592bf31916b1",
                              name="Bloodline Pretender")
        DbCard.objects.create(magic_set=khm, scryfall_id="c119f836-0707-49e2-b6d4-25f849d054a4",
                              name="Littjara Kinseekers")
        DbCard.objects.create(magic_set=khm, scryfall_id="587eed42-5111-4161-9af5-bf76556c542a",
                              name="Guardian Gladewalker")
        DbCard.objects.create(magic_set=khm, scryfall_id="c204130f-0483-49ed-8512-03a74894702e",
                              name="\"Forsworn Cleric\"")
        DbCard.objects.create(magic_set=khm, scryfall_id="d00edda3-ddbc-44ee-a14b-47a701445bb0",
                              name="Eradicator Valkyrie")
        DbCard.objects.create(magic_set=khm, scryfall_id="e692c208-c171-4964-9207-43c2cbc62845", name="Snakeskin Veil")
        DbCard.objects.create(magic_set=khm, scryfall_id="4b1d4a59-11a0-4a55-8ac0-07377a9e6dc8", name="Annul")
        DbCard.objects.create(magic_set=khm, scryfall_id="76d8e0ff-e720-41ca-af69-35585a2d7ae2",
                              name="Draugr Necromancer")
        DbCard.objects.create(magic_set=khm, scryfall_id="471d2aef-cfd4-4131-bbc7-62eeed9f3343", name="Maskwood Nexus")
        DbCard.objects.create(magic_set=khm, scryfall_id="d3b18cdb-bc17-42ae-bfb7-4eafce01cd39", name="Hagi Mob")
        DbCard.objects.create(magic_set=khm, scryfall_id="f28e151f-b61b-486f-b7f8-7abde207c442",
                              name="Kaya's Onslaught")
        DbCard.objects.create(magic_set=khm, scryfall_id="e3cd82e5-6072-4334-a493-01ca4ad6b4eb", name="Faceless Haven")
        DbCard.objects.create(magic_set=khm, scryfall_id="03595195-3be2-4d18-b5c0-43b2dcc1c0f5",
                              name="\"Unshared Triumph\"")
        DbCard.objects.create(magic_set=khm, scryfall_id="54340c59-03a9-4d9d-bd27-9aed337ce75a",
                              name="\"Draugr Scourge Lord\"")
        DbCard.objects.create(magic_set=khm, scryfall_id="9d3a1ec1-f362-494d-a23b-6a963ce44fdd",
                              name="\"Rise of the Marnhorde\"")
        DbCard.objects.create(magic_set=khm, scryfall_id="bd06b52f-f14d-48f1-9eb8-b17b2af4689e",
                              name="\"Search for Glory\"")
        DbCard.objects.create(magic_set=khm, scryfall_id="cf036489-ef9e-40ee-a1bb-24ee37c554f1",
                              name="\"Spirit Blade\"")
        DbCard.objects.create(magic_set=khm, scryfall_id="bdd68d9d-b0b9-4915-8a12-658eb0e3dd4a", name="Reckless Crew")
        DbCard.objects.create(magic_set=khm, scryfall_id="b079e285-8431-46aa-bb04-70cac586ed0b",
                              name="Replicating Ring")
        DbCard.objects.create(magic_set=khm, scryfall_id="6201f78e-ff45-4c59-ac85-c8447c14a496", name="Broken Wings")
        DbCard.objects.create(magic_set=khm, scryfall_id="220df551-3820-4910-a206-14501ba02e69",
                              name="Spirit of the Aldergard")
        DbCard.objects.create(magic_set=khm, scryfall_id="a87606cc-fbf0-4e2c-9798-f1c935d0573d", name="Esika's Chariot")
        DbCard.objects.create(magic_set=khm, scryfall_id="28fced7f-3078-4a54-8f76-0ef14c732e97",
                              name="Vega, the Watcher")
        DbCard.objects.create(magic_set=khm, scryfall_id="550c745b-64e8-4d20-9cf0-024248ddbd57",
                              name="Undersear Invader")
        DbCard.objects.create(magic_set=khm, scryfall_id="c5bbffb9-1f1c-40e5-97f4-29bf1fc68625", name="Quakebringer")
        DbCard.objects.create(magic_set=khm, scryfall_id="e7f22fe4-2390-4c3d-8b5e-0cf398d97f6a",
                              name="\"Dragon Dad uwu…\"")
        DbCard.objects.create(magic_set=khm, scryfall_id="e8e645c8-90ac-4865-b441-e64251d6c9a8",
                              name="Gods' Hall Guardian")
        DbCard.objects.create(magic_set=khm, scryfall_id="36016324-384c-4c68-8f73-8f39a244c879",
                              name="\"Trolls™️ Official Trailer\"")
        DbCard.objects.create(magic_set=khm, scryfall_id="2fb38f5b-a2c2-4b06-8c9c-9615475a43e7",
                              name="\"The Man Who Passes the Sentence Should Swing the Axe\"")
        DbCard.objects.create(magic_set=khm, scryfall_id="14dc88ee-bba9-4625-af0d-89f3762a0ead",
                              name="Tegrid, God of Fear // Tergrid's Lantern")
        DbCard.objects.create(magic_set=khm, scryfall_id="6318918f-34e4-4bbf-9816-8e88f21ae324",
                              name="\"Skyrim Bear Attack\"")
        DbCard.objects.create(magic_set=khm, scryfall_id="a70cb6d9-3955-4064-917b-11dec26440c5", name="The World Tree")
        DbCard.objects.create(magic_set=khm, scryfall_id="df87077c-85d8-499e-bce0-27697caada5a",
                              name="Firja, Judge of Valor")
        DbCard.objects.create(magic_set=khm, scryfall_id="6dae01c8-15bb-44ad-a2c6-9bcf7a9e8c17", name="Doomskar Oracle")
        DbCard.objects.create(magic_set=khm, scryfall_id="877a1bb9-5eae-453a-bec0-a9de20ea6815", name="Saw It Coming")
        DbCard.objects.create(magic_set=khm, scryfall_id="b3b7a69c-75d2-49a6-ab56-ef608d0b0208",
                              name="Seize the Spoils")
        DbCard.objects.create(magic_set=khm, scryfall_id="f6cd7465-9dd0-473c-ac5e-dd9e2f22f5f6",
                              name="Esika, God of the Tree // The Prismatic Bridge")
        DbCard.objects.create(magic_set=khm, scryfall_id="afd2730f-878e-47ee-ad2a-73f8fa4e0794",
                              name="Snow-Covered Plains")
        DbCard.objects.create(magic_set=khm, scryfall_id="2de25ea4-284a-4c16-b823-048ff00c6a03",
                              name="Koma, Cosmos Serpent")
        DbCard.objects.create(magic_set=khm, scryfall_id="6aa85af8-15f5-4620-8aea-0b45c28372ed",
                              name="Snow-Covered Swamp")
        DbCard.objects.create(magic_set=khm, scryfall_id="5474e67c-628f-41b0-aa31-3d85a267265a",
                              name="Snow-Covered Mountain")
        DbCard.objects.create(magic_set=khm, scryfall_id="ca17acea-f079-4e53-8176-a2f5c5c408a1",
                              name="Snow-Covered Forest")
        DbCard.objects.create(magic_set=khm, scryfall_id="9dab2ca2-0039-4eac-a7dc-68756362737d",
                              name="Sculptor of Winter")
        DbCard.objects.create(magic_set=khm, scryfall_id="4ec318c6-b718-436f-b9e8-e0c6154e5010", name="Cosmos Charger")
        DbCard.objects.create(magic_set=khm, scryfall_id="0fab9ee8-776a-48e5-b309-bcd381e67bf7", name="Village Rites")
        DbCard.objects.create(magic_set=khm, scryfall_id="af0f1a90-af64-4122-9c1a-954edf8fa240", name="Koma's Faithful")
        DbCard.objects.create(magic_set=khm, scryfall_id="606da75d-382a-47a8-9739-644438594700",
                              name="Path to the World Tree")
        DbCard.objects.create(magic_set=khm, scryfall_id="a19b35ee-03ba-43f0-8c57-29718c899719", name="Tyvar Kell")
        DbCard.objects.create(magic_set=khm, scryfall_id="b76bed98-30b1-4572-b36c-684ada06826c",
                              name="Kolvori, God of Kinship // The Ringheart Crest")
        DbCard.objects.create(magic_set=khm, scryfall_id="a5a272b3-aaab-4c98-86a8-85c67a5f3d4d",
                              name="Hailstorm Valkyrie")
        DbCard.objects.create(magic_set=khm, scryfall_id="2c2cfcd7-b43a-4dad-a033-e661f55ceecd", name="Ravenform")
        DbCard.objects.create(magic_set=khm, scryfall_id="4aa19a68-0d71-4123-a64d-8cb76f93cd74",
                              name="The Trickster-God's Heist")
        DbCard.objects.create(magic_set=khm, scryfall_id="24a0f2e2-cfd7-4374-a172-4357d5de47bb",
                              name="Bretagard Stronghold")
        DbCard.objects.create(magic_set=khm, scryfall_id="a15edad1-ff68-4f20-95f6-99fe549bea98", name="Calamity Bearer")
        DbCard.objects.create(magic_set=khm, scryfall_id="3ce46100-461d-424e-afa4-7a0bb7d0a822",
                              name="Forging the Tyrite Sword")
        DbCard.objects.create(magic_set=khm, scryfall_id="ab8b1ec2-9303-4722-8644-b3bc1a5c387f", name="Giant's Amulet")
        DbCard.objects.create(magic_set=khm, scryfall_id="9d914868-9000-4df2-a818-0ef8a7f636ae", name="Goldspan Dragon")
        DbCard.objects.create(magic_set=khm, scryfall_id="c60fbc33-6198-4661-967e-cc94f2788e4a",
                              name="\"Gatorade™ Ice Punch\"")
        DbCard.objects.create(magic_set=khm, scryfall_id="6fb78693-354a-49d0-a493-430a89c6e6f6",
                              name="Snow-Covered Plains")
        DbCard.objects.create(magic_set=khm, scryfall_id="9160baf7-5796-4815-8e9d-e804af70cb74",
                              name="Snow-Covered Swamp")
        DbCard.objects.create(magic_set=khm, scryfall_id="f54aa46b-4b7c-4846-bf19-a289ed36c172",
                              name="Snow-Covered Mountain")
        DbCard.objects.create(magic_set=khm, scryfall_id="fe241460-f7c1-4ba8-a156-6720b494ac97",
                              name="Snow-Covered Forest")
        DbCard.objects.create(magic_set=khm, scryfall_id="b20e3117-f1e4-4449-ae9d-0b66abfc717d", name="Arctic Treeline")
        DbCard.objects.create(magic_set=khm, scryfall_id="9de5fadd-4559-479f-b45d-abe792f0f6e5",
                              name="Glacial Floodplain")
        DbCard.objects.create(magic_set=khm, scryfall_id="8702d6b9-bb01-4841-a76d-4a576066c772", name="Alpine Meadow")
        DbCard.objects.create(magic_set=khm, scryfall_id="682eee5f-7986-45d3-910f-407303fdbcc4", name="Highland Forest")
        DbCard.objects.create(magic_set=khm, scryfall_id="8cff3ef0-4dfb-472e-aa1e-77613dd0f6d8", name="Ice Tunnel")
        DbCard.objects.create(magic_set=khm, scryfall_id="da1db084-f235-4e26-8867-5f0835a0d283", name="Rimewood Falls")
        DbCard.objects.create(magic_set=khm, scryfall_id="6611dc5e-6acc-48df-b8c4-4b327314578b",
                              name="Snowfield Sinkhole")
        DbCard.objects.create(magic_set=khm, scryfall_id="35ebe245-ebb5-493c-b9c1-56fbfda9bd66", name="Sulfurous Mine")
        DbCard.objects.create(magic_set=khm, scryfall_id="f2392fbb-d9c4-4688-b99c-4e7614c60c12", name="Volatile Fjord")
        DbCard.objects.create(magic_set=khm, scryfall_id="b2dd0b71-5a60-418c-82fc-f13d1b5075d0", name="Woodland Chasm")
        DbCard.objects.create(magic_set=khm, scryfall_id="eadee447-ce9a-4dea-a074-bfd04197548e",
                              name="Reflections of Littjara")
        DbCard.objects.create(magic_set=khm, scryfall_id="a9947cfd-91d6-479e-a7f6-2a2050f020f3", name="Augury Raven")
        DbCard.objects.create(magic_set=khm, scryfall_id="dc96ebe8-f4b3-4788-a6f5-2a50b6c0d935",
                              name="Glimpse the Cosmos")
        DbCard.objects.create(magic_set=khm, scryfall_id="27855a38-a682-4f97-ad22-ac625e86faec",
                              name="Behold the Multiverse")
        DbCard.objects.create(magic_set=khm, scryfall_id="6061113e-7dd8-4739-b4dd-55bb7f9e39a2",
                              name="Sarulf's Packmate")
        DbCard.objects.create(magic_set=khm, scryfall_id="c94fcb53-a7bd-4a80-a536-9fb0eb24261a",
                              name="Alrund's Epiphany")
        DbCard.objects.create(magic_set=khm, scryfall_id="92613468-205e-488b-930d-11908477e9f8",
                              name="Vorinclex, Monstrous Raider")
        DbCard.objects.create(magic_set=khm, scryfall_id="9423318a-c5a8-48d2-92f5-280d15a050a6", name="Frost Bite")
        DbCard.objects.create(magic_set=khm, scryfall_id="efa8dbf0-4e5a-452b-826f-5813e8cd9d85",
                              name="Varragoth, Bloodsky Sire")
        DbCard.objects.create(magic_set=khm, scryfall_id="d93ee644-d7d7-48d8-a04b-fb479b74edb0",
                              name="Binding of the Old Gods")
        DbCard.objects.create(magic_set=khm, scryfall_id="3bfa5ebc-5623-4eec-89ea-dc187489ee4a",
                              name="Snow-Covered Island")
        DbCard.objects.create(magic_set=khm, scryfall_id="5d131784-c1a3-463e-a37b-b720af67ab62",
                              name="Alrund, God of the Cosmos // Hakka, Whispering Raven")
        DbCard.objects.create(magic_set=khm, scryfall_id="58da074a-a776-4e3f-be04-9e7f18320ae1",
                              name="Elvish Warmaster")
        DbCard.objects.create(magic_set=khm, scryfall_id="b759b0f6-342c-4bba-89f1-8451835d8c45",
                              name="Old-Growth Troll")
        DbCard.objects.create(magic_set=khm, scryfall_id="f0a9c72a-e450-41e3-80e5-06f2f1171245", name="Masked Vandal")
        DbCard.objects.create(magic_set=khm, scryfall_id="aeec3c1e-e612-4700-888e-300912932552",
                              name="Sigrid, God-Favored")
        DbCard.objects.create(magic_set=khm, scryfall_id="22f68b53-0cf7-434d-9da5-1d18c0828a46",
                              name="Koll, the Forgemaster")
        DbCard.objects.create(magic_set=khm, scryfall_id="62a6f095-5beb-42a8-af8f-d40eef27150e", name="Inga Rune-Eyes")
        DbCard.objects.create(magic_set=khm, scryfall_id="ea7e4c65-b4c4-4795-9475-3cba71c50ea5",
                              name="Tibalt, Cosmic Impostor // Valki, God of Lies")
        DbCard.objects.create(magic_set=khm, scryfall_id="6c4e9cfe-e72e-46a1-a8d8-9fda5f2bae73", name="Niko Aris")
        DbCard.objects.create(magic_set=khm, scryfall_id="7f5075a0-c72a-474c-937c-95dc9205d14f",
                              name="Invasion of the Giants")
        DbCard.objects.create(magic_set=khm, scryfall_id="f9e79b59-94c8-4697-bf88-f0a0433170f5",
                              name="Toski, Bearer of Secrets")
        DbCard.objects.create(magic_set=khm, scryfall_id="bcecf9ba-36da-490a-9460-99ff87d99fbd",
                              name="Sarulf, Realm Eater")
        DbCard.objects.create(magic_set=khm, scryfall_id="45b31046-d84d-4afa-a207-bb6cccac4339",
                              name="Sarulf, Realm Eater")
        DbCard.objects.create(magic_set=khm, scryfall_id="97502411-5c93-434c-b77b-ceb2c32feae7",
                              name="Halvar, God of Battle // Sword of the Realms")
        DbCard.objects.create(magic_set=khm, scryfall_id="166c0bd1-b59d-4644-832f-888a4ca3a0aa",
                              name="Kaya the Inexorable")
        DbCard.objects.create(magic_set=khm, scryfall_id="079e6263-e54c-4899-a336-5315909b9322",
                              name="Magda, Brazen Outlaw")
        DbCard.objects.create(magic_set=khm, scryfall_id="c8212667-7e18-42a5-9f36-4f8a6ad12f83", name="Realmwalker")
        DbCard.objects.create(magic_set=khm, scryfall_id="a5675655-dc9f-45ad-9cd0-ce28fba1f972", name="Renegade Reaper")
        DbCard.objects.create(magic_set=khm, scryfall_id="544b6477-cefa-40e2-a96a-72794c7eb815",
                              name="Thornmantle Striker")
        DbCard.objects.create(magic_set=khm, scryfall_id="2381dbab-e968-4bbc-b3a7-a1e55b066039", name="Bearded Axe")
        DbCard.objects.create(magic_set=khm, scryfall_id="c7f05d49-dfc1-4dad-89e0-07174330d98e",
                              name="Fire Giant's Fury")
        DbCard.objects.create(magic_set=khm, scryfall_id="5274c2fa-eb0e-438b-8a48-d0b58829083a",
                              name="Gilded Assault Cart")
        DbCard.objects.create(magic_set=khm, scryfall_id="70479c44-da7c-48c7-8c6a-47210dc03277", name="Elven Ambush")
        DbCard.objects.create(magic_set=khm, scryfall_id="8053b888-a680-4318-88c3-0924e596e780",
                              name="Gladewalker Ritualist")
        DbCard.objects.create(magic_set=khm, scryfall_id="1e928b7c-ca30-4e2d-adf7-965f111c8bf1",
                              name="Rampage of the Valkyries")
        DbCard.objects.create(magic_set=khm, scryfall_id="74c92d48-504a-4320-b9f4-c1d2d06fa223", name="Giant's Grasp")
        DbCard.objects.create(magic_set=khm, scryfall_id="57348f93-8764-4b1a-b02e-4e7881337fa2",
                              name="Elderfang Ritualist")
        DbCard.objects.create(magic_set=khm, scryfall_id="ffe93b27-f8ae-4abf-8ade-90f503f132c2",
                              name="Youthful Valyrie")
        DbCard.objects.create(magic_set=khm, scryfall_id="aa1c6bcc-2d43-4ea9-a93f-019793616869", name="Absorb Identity")
        DbCard.objects.create(magic_set=khm, scryfall_id="edab83a9-35b5-4312-b8ee-1c042c02aa31",
                              name="Valkyrie Harbinger")
        DbCard.objects.create(magic_set=khm, scryfall_id="1c9e7fdc-676f-4901-83ff-bfea3a96d937",
                              name="Surtland Elementalist")
        DbCard.objects.create(magic_set=khm, scryfall_id="b59dadef-74e5-47c7-a3e0-51075ddb82b1", name="Cleaving Reaper")
        DbCard.objects.create(magic_set=khm, scryfall_id="4a628052-8175-495f-bfab-eeb3a0388e4e",
                              name="Surtland Flinger")
        DbCard.objects.create(magic_set=khm, scryfall_id="3eaf48c9-09bc-4d81-a3a5-432219a71754",
                              name="Canopy Tactician")
        DbCard.objects.create(magic_set=khm, scryfall_id="4f4c1253-7eba-454b-9269-3695ba746a7a",
                              name="Armed and Armored")
        DbCard.objects.create(magic_set=khm, scryfall_id="ea007a18-b31a-4881-92c4-86120dc5729b",
                              name="Starnhiem Aspirant")
        DbCard.objects.create(magic_set=khm, scryfall_id="f79c5e95-f6c6-4e2f-9c6c-d99addb757ac",
                              name="Warchanter Skald")
        DbCard.objects.create(magic_set=khm, scryfall_id="b6de14ae-0132-4261-af00-630bf15918cd",
                              name="Barkchannel Pathway // Tidechannel Pathway")
        DbCard.objects.create(magic_set=khm, scryfall_id="ae9a8e44-f5de-497d-be48-adf1bcbaec97", name="Pyre of Heroes")
        DbCard.objects.create(magic_set=khm, scryfall_id="87a4e5fe-161f-42da-9ca2-67c8e8970e94",
                              name="Darkbore Pathway // Slitherbore Pathway")
        DbCard.objects.create(magic_set=khm, scryfall_id="0ce39a19-f51d-4a35-ae80-5b82eb15fcff",
                              name="Blightstep Pathway // Searstep Pathway")
        DbCard.objects.create(magic_set=khm, scryfall_id="7ef37cb3-d803-47d7-8a01-9c803aa2eadc",
                              name="Hengegate Pathway // Mistgate Pathway")
        DbCard.objects.create(magic_set=khm, scryfall_id="3d9d840e-1f13-44e3-a4de-903cfa58a346",
                              name="Showdown of the Skalds")

        tkhm = DbSet.objects.create(scryfall_id='c3ee48f1-6f93-42d4-b05c-65a04d02a488',
                                    code='tkhm',
                                    name='Kaldheim Tokens',
                                    release_date='2021-02-05',
                                    watched=True,
                                    icon_svg_uri='foobar')

        DbCard.objects.create(magic_set=tkhm, scryfall_id="97873c66-6bff-4d79-850c-1e2663098ef4",
                              name="Valkyrie's Sword")
        DbCard.objects.create(magic_set=tkhm, scryfall_id="ea56de43-c0fd-4627-846d-41a962b95f17",
                              name="Ascendant Spirit")
        DbCard.objects.create(magic_set=tkhm, scryfall_id="fad2c6d4-03dd-4dab-861c-77c55bda0db7",
                              name="Skemfar Avenger")
        DbCard.objects.create(magic_set=tkhm, scryfall_id="29306305-cb71-4fef-bf86-f5deb4e7e561",
                              name="Strategic Planning")
        DbCard.objects.create(magic_set=tkhm, scryfall_id="fb02637f-1385-4d3d-8dc0-de513db7633a", name="Foretell")

    def test_card_created_in_wrong_set(self):
        khm = DbSet.objects.get(code='khm')

        self.assertEqual(228, khm.cards.count())

    def test_refreshing_with_conflicts(self):
        test_channel = TestClient()

        def clients(arg1):
            return [test_channel, ]

        patcher = mock.patch(target='announce.models.ChannelManager.clients', new=clients)
        patcher.start()

        service = SpoilersService()
        directory = os.path.dirname(__file__)
        with open(os.path.join(directory, 'test_data', 'khm_response.json')) as f:
            response_data = '\n'.join(f.readlines())
        with open(os.path.join(directory, 'test_data', 'tkhm_response.json')) as f:
            token_response_data = '\n'.join(f.readlines())
        with responses.RequestsMock() as rm:
            rm.add('GET', 'https://api.scryfall.com/cards/search?order=spoiled&q=e=khm&unique=card', body=response_data)
            rm.add('GET', 'https://api.scryfall.com/cards/search?order=spoiled&q=e=tkhm&unique=card',
                   body=token_response_data)
            service.update_cards()

        patcher.stop()

        self.assertEqual(0, len(test_channel.cards))
        self.assertEqual(0, len(test_channel.text))
        self.assertEqual(0, len(test_channel.errors))
        self.assertEqual(2, DbSet.objects.get(code='tkhm').cards.count())
