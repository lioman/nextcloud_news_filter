import json
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path

import httpx

from nextcloud_news_filter import Config
from nextcloud_news_filter.model import FeedType, Filter, FilterJson, Item


class FilterConfig:
    def __init__(self, filter_json: FilterJson):
        self._filter = FilterConfig._build_filters(filter_json["filter"])
        if isinstance(feeds_to_skip := filter_json.get("skipFeeds", []), list):
            self._feeds_to_skip = feeds_to_skip

    @property
    def filter(self) -> list[dict]:
        return self._filter

    @property
    def feeds_to_skip(self) -> list[int]:
        return self._feeds_to_skip

    @classmethod
    def from_file(cls, filter_file: Path) -> "FilterConfig | None":
        try:
            with open(filter_file) as f:
                filter_config = json.loads(f.read())
                return cls(filter_config)
        except FileNotFoundError as e:
            logging.error(
                f"Can not open file: {filter_file}. Please enter a valid path."
            )
            raise e

    @staticmethod
    def _build_filters(filters: list[Filter]) -> list[dict]:
        def _compile(regex: str | None) -> re.Pattern | None:
            if isinstance(regex, str):
                return re.compile(regex, re.IGNORECASE)
            return None

        compiled_filters = []
        for feed_filter in filters:
            one_filter = {
                "name": feed_filter["name"],
                "feedId": feed_filter.get("feedId"),
                "titleRegex": _compile(feed_filter.get("titleRegex")),
                "bodyRegex": _compile(feed_filter.get("bodyRegex")),
                "minPubDate": None,
            }
            if hours := feed_filter.get("hoursAge"):
                one_filter["minPubDate"] = int(
                    (datetime.now() - timedelta(hours=hours)).timestamp()
                )

            compiled_filters.append(one_filter)
        return compiled_filters

    def is_filter_matching_item(self, item: Item) -> bool:
        if item["feedId"] in self.feeds_to_skip:
            logging.debug(f'Skipped because {item["feedId"]}')
            return False
        for one_filter in self.filter:
            if (
                (
                    "feedId" not in one_filter
                    or one_filter["feedId"] is None
                    or one_filter["feedId"] == item["feedId"]
                )
                and (
                    "titleRegex" not in one_filter
                    or one_filter["titleRegex"] is None
                    or one_filter["titleRegex"].search(item["title"])
                )
                and (
                    "bodyRegex" not in one_filter
                    or one_filter["bodyRegex"] is None
                    or one_filter["bodyRegex"].search(item["body"])
                )
                and (
                    "minPubDate" not in one_filter
                    or one_filter["minPubDate"] is None
                    or item["pubDate"] < one_filter["minPubDate"]
                )
            ):
                logging.log(
                    logging.INFO,
                    f"filter: '{one_filter['name']}' matched item {item['id']} "
                    f"with title {item['title']}",
                )
                return True
        return False

    def apply_filter_to_batch(self, items: list[Item]) -> tuple[list[int], int]:
        unread_item_count = 0
        matched_item_ids = []
        for item in items:
            if item["unread"]:
                unread_item_count = unread_item_count + 1
                if self.is_filter_matching_item(item):
                    matched_item_ids.append(item["id"])
        return matched_item_ids, unread_item_count


def filter_items(config: Config, filter_config: FilterConfig) -> tuple[list[int], int]:
    batch_size = config.batch_size
    offset = 0
    matched_item_ids: list[int] = []
    unread_item_count = 0
    feed_type = FeedType.All
    with httpx.Client(http2=True) as client:
        while True:
            response = client.get(
                url=f"{config.nextcloud_url}/index.php/apps/news/api/v1-3/items",
                headers=dict(Authorization=config.auth_header),
                params=dict(
                    batchSize=batch_size,
                    offset=offset,
                    type=feed_type,
                    id=0,  # 0 = all
                    getRead="false",
                ),
            )
            if response.status_code != httpx.codes.OK:
                break
            items = response.json()["items"]

            if len(items) == 0:
                break

            matched, count = filter_config.apply_filter_to_batch(items)
            matched_item_ids = matched_item_ids + matched
            unread_item_count += count
            offset = items[-1]["id"]
    return matched_item_ids, unread_item_count


def mark_as_read(matched_item_ids: list[int], config: Config):
    url = f"{config.nextcloud_url}/index.php/apps/news/api/v1-3/items/read/multiple"
    httpx.post(
        url=url,
        headers=dict(Authorization=config.auth_header),
        json=dict(itemIds=matched_item_ids),
    )
