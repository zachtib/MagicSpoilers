import json
import uuid

import responses
from django.contrib.auth.models import User
from django.test import TestCase

# Create your tests here.
from announce.discord.discordclient import DiscordClient
from announce.emoji_formatters import HyphenatedManamojiFormatter, NonHyphenatedManamojiFormatter, NoopManamojiFormatter
from announce.models import Channel
from announce.slack import SlackClient
from magic.models import MagicCard, CardFace


class AnnounceTests(TestCase):

    def test_slackclient_send(self):
        pass


class ChannelTests(TestCase):

    def setUp(self) -> None:
        self.user = User.objects.create_user('user')

    def test_slack_channel_client_creation(self):
        channel = Channel(
            owner=self.user,
            name='Slack Channel',
            kind=Channel.Kind.SLACK,
            webhook_url='https://example.com/webhook',
            channel_name='spoilers',
            supports_manamoji=True,
            manamoji_style=Channel.EmojiStyle.HYPHENATED,
        )
        client = channel.client()
        self.assertIsInstance(client, SlackClient)
        self.assertIsInstance(client._SlackClient__manamoji_formatter, HyphenatedManamojiFormatter)

    def test_slack_channel_card_reporting(self):
        channel = Channel(
            owner=self.user,
            name='Slack Channel',
            kind=Channel.Kind.SLACK,
            webhook_url='https://example.com/webhook',
            channel_name='spoilers',
            supports_manamoji=True,
            manamoji_style=Channel.EmojiStyle.HYPHENATED,
        )
        client = channel.client()
        card = MagicCard(
            scryfall_id='',
            lang='en',
            oracle_id='',
            uri='https://',
            name='Llanowar Elves',
            mana_cost='{G}',
            scryfall_uri='https://',
            layout='normal',
            type_line='Creature - Elf',
            oracle_text='{T}: Add {G}',
            power='1',
            toughness='1',
        )
        with responses.RequestsMock() as rm:
            rm.add('POST', 'https://example.com/webhook', status=200)
            client.send_cards([card])

            request = rm.calls[0].request

            body = json.loads(request.body)
            self.assertEqual('Llanowar Elves', body['text'])
            self.assertEqual('spoilers', body['channel'])

            blocks = body['blocks']
            self.assertEqual(1, len(blocks))
            block_text = blocks[0]['text']['text']
            self.assertEqual('Llanowar Elves :mana-g:\nCreature - Elf\n:mana-t:: add :mana-g:\n1/1', block_text)

    def test_discord_channel_client_creation(self):
        channel = Channel(
            owner=self.user,
            name='Discord Channel',
            kind=Channel.Kind.DISCORD,
            webhook_url='https://example.com/webhook',
            channel_name='spoilers',
            supports_manamoji=True,
            manamoji_style=Channel.EmojiStyle.NON_HYPHENATED,
        )
        client = channel.client()
        self.assertIsInstance(client, DiscordClient)
        self.assertIsInstance(client._DiscordClient__manamoji_formatter, NonHyphenatedManamojiFormatter)

    def test_discord_channel_card_reporting(self):
        channel = Channel(
            owner=self.user,
            name='Discord Channel',
            kind=Channel.Kind.DISCORD,
            webhook_url='https://example.com/webhook',
            channel_name='spoilers',
            supports_manamoji=True,
            manamoji_style=Channel.EmojiStyle.NON_HYPHENATED,
        )
        client = channel.client()
        card = MagicCard(
            scryfall_id='',
            lang='en',
            oracle_id='',
            uri='https://',
            name='Llanowar Elves',
            mana_cost='{G}',
            scryfall_uri='https://',
            layout='normal',
            type_line='Creature - Elf',
            oracle_text='{T}: Add {G}',
            power='1',
            toughness='1',
        )
        with responses.RequestsMock() as rm:
            rm.add('POST', 'https://example.com/webhook', status=200)
            client.send_cards([card])

            request = rm.calls[0].request

            body = json.loads(request.body)
            self.assertEqual('Llanowar Elves :manag:\nCreature - Elf\n:manat:: add :manag:\n1/1', body['content'])


class EmojiFormattersTests(TestCase):

    def setUp(self) -> None:
        self.mana = '{2}{2/W}{W/B}{U}{G/P}'
        self.card = MagicCard(
            scryfall_id='1ec65f89-b87c-48c5-a525-fcd4fae81a95',
            lang='en',
            oracle_id='a9ded2b8-65f8-4dbb-9935-f61a07870986',
            uri='https://example.com/card',
            name='This Magic Card',
            scryfall_uri='https://scryfall.com/card',
            layout='normal',
            type_line='Magic - Card',
            mana_cost='{2}{G}{G}',
            oracle_text='{T}: Add {G}',
        )

        self.dfc = MagicCard(
            scryfall_id='1ec65f89-b87c-48c5-a525-fcd4fae81a95',
            lang='en',
            oracle_id='a9ded2b8-65f8-4dbb-9935-f61a07870986',
            uri='https://example.com/card',
            name='This Magic Card',
            scryfall_uri='https://scryfall.com/card',
            layout='dfc',
            type_line='Magic - Card',
            card_faces=[
                CardFace(
                    name='Side A',
                    type_line='Card',
                    mana_cost='{G}',
                    oracle_text='{T}: Add {G}',
                ),
                CardFace(
                    name='Side B',
                    type_line='Card',
                    mana_cost='{B}',
                    oracle_text='Pay 1 life: Add {B}',
                ),
            ]
        )

    def test_hypenated_formatter(self):
        formatter = HyphenatedManamojiFormatter()

        result = formatter.format_manamoji(self.mana)
        self.assertEqual(result, ':mana-2::mana-2w::mana-wb::mana-u::mana-gp:')

    def test_non_hypenated_formatter(self):
        formatter = NonHyphenatedManamojiFormatter()

        result = formatter.format_manamoji(self.mana)
        self.assertEqual(result, ':mana2::mana2w::manawb::manau::managp:')

    def test_hypenated_formatter_on_card(self):
        formatter = HyphenatedManamojiFormatter()

        result = formatter.format_card(self.card)
        self.assertEqual(result.mana_cost, ':mana-2::mana-g::mana-g:')
        self.assertEqual(result.oracle_text, ':mana-t:: add :mana-g:')

    def test_non_hypenated_formatter_on_card(self):
        formatter = NonHyphenatedManamojiFormatter()

        result = formatter.format_card(self.card)
        self.assertEqual(result.mana_cost, ':mana2::manag::manag:')
        self.assertEqual(result.oracle_text, ':manat:: add :manag:')

    def test_hypenated_formatter_on_dfc(self):
        formatter = HyphenatedManamojiFormatter()

        result = formatter.format_card(self.dfc)

        self.assertIsNone(result.mana_cost)
        self.assertIsNone(result.oracle_text)

        self.assertEqual(result.card_faces[0].mana_cost, ':mana-g:')
        self.assertEqual(result.card_faces[0].oracle_text, ':mana-t:: add :mana-g:')

        self.assertEqual(result.card_faces[1].mana_cost, ':mana-b:')
        self.assertEqual(result.card_faces[1].oracle_text, 'pay 1 life: add :mana-b:')

    def test_non_hypenated_formatter_on_dfc(self):
        formatter = NonHyphenatedManamojiFormatter()

        result = formatter.format_card(self.dfc)

        self.assertIsNone(result.mana_cost)
        self.assertIsNone(result.oracle_text)

        self.assertEqual(result.card_faces[0].mana_cost, ':manag:')
        self.assertEqual(result.card_faces[0].oracle_text, ':manat:: add :manag:')

        self.assertEqual(result.card_faces[1].mana_cost, ':manab:')
        self.assertEqual(result.card_faces[1].oracle_text, 'pay 1 life: add :manab:')

    def test_noop_formatter_does_nothing(self):
        formatter = NoopManamojiFormatter()

        self.assertEqual('{G}', formatter.format_manamoji('{G}'))
        self.assertEqual('{2}', formatter.format_manamoji('{2}'))
        self.assertEqual('{W/B}', formatter.format_manamoji('{W/B}'))
