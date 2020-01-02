from django.test import TestCase


# Create your tests here.
class CliTestCase(TestCase):
    def test_updatecards(self):
        from .management.commands.updatecards import Command
        command = Command()
        command.handle()
