import requests

from announce.slack.models import SlackMessage


class SlackClient:
    __webhook_url: str
    __channel: str

    def __init__(self, webhook_url: str, channel: str = None):
        self.__webhook_url = webhook_url
        self.__channel = channel

    def send(self, message: SlackMessage) -> bool:
        message.channel = self.__channel
        json = message.to_json()
        response = requests.post(self.__webhook_url, data=json)
        if response.status_code != 200:
            return False
        return True
