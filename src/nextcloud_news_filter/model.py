from enum import IntEnum
from typing import Required, TypedDict


class Item(TypedDict, total=False):
    id: Required[int]  # 3443,
    guid: Required[str]  # "http://grulja.wordpress.com/?p=76",
    guidHash: Required[str]  # "3059047a572cd9cd5d0bf645faffd077",
    url: Required[
        str
    ]  # "http://grulja.wordpress.com/2013/04/29/plasma-nm-after-the-solid-sprint/",
    title: Required[str]  # "Plasma-nm after the solid sprint",
    author: Required[str]  # "Jan Grulich (grulja)",
    pubDate: Required[int]  # 1367270544,
    body: Required[str]  # "<p>At first I have to say...</p>",
    enclosureMime: str  # null,
    enclosureLink: str  # null,
    mediaThumbnail: str  # null, // new in 14.1.4-rc1
    mediaDescription: str  # null, // new in 14.1.4-rc1
    feedId: Required[int]  # 67,
    unread: Required[bool]  # true,
    starred: Required[bool]  # false,
    rtl: bool  # false, // new in 6.0.2
    lastModified: Required[int]  # 1367273003,
    fingerprint: str  # "aeaae2123"  // new in 8.4.0 hash over title, enclosures, body and url. Same fingerprint means same item and it's advised to locally mark the other one read as well and filter out duplicates in folder and all articles view  # noqa: E501


class FeedType(IntEnum):
    Feed = 0
    Folder = 1
    Starred = 2
    All = 3


class Filter(TypedDict, total=False):
    name: Required[str]
    feedId: int
    hoursAge: int
    titleRegex: str
    bodyRegex: str


class FilterJson(TypedDict, total=False):
    filter: Required[list[Filter]]
    skipFeeds: list[int]
