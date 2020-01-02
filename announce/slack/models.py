from dataclasses import dataclass, field
from typing import List, Optional

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class SlackMessage:
    text: str
    channel: str = None
    blocks: List[object] = field(default_factory=list)


@dataclass_json
@dataclass
class SectionText:
    text: str
    emoji: bool = True
    type: str = 'plain_text'


@dataclass_json
@dataclass
class ImageBlock:
    image_url: str
    alt_text: str
    title: SectionText = SectionText("Image")
    type: str = 'image'


@dataclass_json
@dataclass
class SectionBlock:
    text: SectionText
    type: str = 'section'

    @classmethod
    def of(cls, text) -> 'SectionBlock':
        return SectionBlock(SectionText(text))


@dataclass_json
@dataclass
class SectionWithImage:
    text: SectionText
    accessory: ImageBlock
    type: str = 'section'

    @classmethod
    def of(cls, text, image_url, alt_text) -> 'SectionWithImage':
        return SectionWithImage(
            SectionText(text),
            ImageBlock(image_url, alt_text)
        )
