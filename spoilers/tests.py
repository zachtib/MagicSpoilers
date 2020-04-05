from django.test import TestCase

from .scryfall import ScryfallSet, ScryfallCard, ScryfallCardFace
from .scryfall.converters import convert_set, convert_card
from magic.models import MagicSet, MagicCard, CardFace


# Create your tests here.
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
