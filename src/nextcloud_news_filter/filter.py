from datetime import datetime, timedelta
import json
import logging
from pathlib import Path
import re
from typing import Dict, List, Optional, Tuple
import requests

from nextcloud_news_filter import Config


class FilterConfig:
    def __init__(self, filter_json: Dict):
        self._filter = FilterConfig._build_filters(filter_json["filter"])
        if isinstance(feeds_to_skip := filter_json.get("skipFeeds", []), list):
            self._feeds_to_skip = feeds_to_skip

    @property
    def filter(self) -> List[Dict]:
        return self.filter

    @property
    def feeds_to_skip(self) -> List[int]:
        return self._feeds_to_skip

    @classmethod
    def from_file(cls, filter_file: Path) -> Optional["FilterConfig"]:
        try:
            with open(filter_file, "r") as f:
                filter_config = json.loads(f.read())
                return cls(filter_config)
        except FileNotFoundError:
            logging.error(
                f"Can not open file: {filter_file}. Please enter a valid path."
            )

    @staticmethod
    def _build_filters(filters: List[Dict]) -> List[Dict]:
        compiled_filters = []
        for feed_filter in filters:
            one_filter = {
                "name": feed_filter["name"],
                "feedId": feed_filter.get("feedId"),
                "titleRegex": re.compile(feed_filter["titleRegex"], re.IGNORECASE)
                if feed_filter.get("titleRegex")
                else None,
                "bodyRegex": re.compile(feed_filter["bodyRegex"], re.IGNORECASE)
                if feed_filter.get("bodyRegex")
                else None,
                "minPubDate": int(
                    (
                        datetime.now() - timedelta(hours=int(feed_filter["hoursAge"]))
                    ).timestamp()
                )
                if feed_filter.get("hoursAge")
                else None,
            }
            compiled_filters.append(one_filter)
        return compiled_filters


def _apply_filter_to_batch(
    items: Dict, filters_config: FilterConfig
) -> Tuple[List[int], int]:
    unread_item_count = 0
    matched_item_ids = []
    for item in items:
        if item["feedId"] in filters_config.feeds_to_skip:
            logging.debug(f'Skipped because {item["feedId"]}')
            continue
        if item["unread"]:
            unread_item_count = unread_item_count + 1
            for one_filter in filters_config.filter:
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
                        f"filter: '{one_filter['name']}' matched item {item['id']} with title {item['title']}",
                    )
                    matched_item_ids.append(item["id"])
    return matched_item_ids, unread_item_count


def filter_items(config: Config, filter_config: FilterConfig) -> Tuple[List[int], int]:
    batch_size = config.batch_size
    offset = 0
    matched_item_ids = []
    unread_item_count = 0
    feed_type = 3  # Feed: 0, Folder: 1, Starred: 2, All: 3
    while True:
        response = requests.get(
            url=f"{config.nextcloud_url}/index.php/apps/news/api/v1-3/items",
            headers=dict(Authorization=config.auth_header),
            json=dict(
                batchSize=batch_size,
                offset=offset,
                type=feed_type,
                id=0,  # 0 = all
                getRead="false",
            ),
        )
        if not response.ok:
            break
        items = response.json()["items"]

        if len(items) == 0:
            break

        matched, count = _apply_filter_to_batch(items, filter_config)
        matched_item_ids = matched_item_ids + matched
        unread_item_count += count
        offset = items[-1]["id"]
    return matched_item_ids, unread_item_count


def mark_as_read(matched_item_ids: List[int], config: Config):
    requests.post(
        url=f"{config.nextcloud_url}/index.php/apps/news/api/v1-3/items/read/multiple",
        headers=dict(Authorization=config.auth_header),
        json=dict(itemIds=matched_item_ids),
    )
