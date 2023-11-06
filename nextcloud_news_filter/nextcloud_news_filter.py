#!/usr/bin/env python3
#
# mark specific news items as read (so they don't show in the "unread" feed)
#
import base64
import json
import sys
import logging
from os import environ
import re
from _datetime import datetime, timedelta
import requests


def get_configuration() -> dict:
    config = {}

    if environ.get("NEXTCLOUD_ADDRESS") is None:
        logging.log(logging.ERROR, "NEXTCLOUD_ADDRESS is not set in environment")
        exit(1)
    config["address"] = environ.get("NEXTCLOUD_ADDRESS")

    if environ.get("NEXTCLOUD_USER") is None or environ.get("NEXTCLOUD_PASS") is None:
        logging.log(
            logging.ERROR,
            "NEXTCLOUD_USER and NEXTCLOUD_PASS need to be set in environment",
        )
        exit(1)

    config["auth"] = (
        base64.encodebytes(
            f'{environ["NEXTCLOUD_USER"]}:{environ["NEXTCLOUD_PASS"]}'.encode(
                encoding="UTF-8"
            )
        )
        .decode(encoding="UTF-8")
        .strip()
    )
    with open("./filter.json") as f:
        config["filters"] = json.loads(f.read())
    config["skip_feed"] = json.loads(environ.get("FEED_SKIP", "[]"))
    return config


def filter_news():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )
    logging.debug("starting run")

    config = get_configuration()
    filters = []
    for feed_filter in config["filters"]:
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
        filters.append(one_filter)

    response = requests.get(
        url=config["address"] + "/index.php/apps/news/api/v1-3/items",
        headers=dict(Authorization=f"Basic {config['auth']}"),
        json=dict(batchSize=-1, offset=0, type=3, id=0, getRead="false"),
    )
    data = response.json()

    unread_item_count = 0
    matched_item_ids = []
    for item in data["items"]:
        if item["feedId"] in config.get("skip_feed"):
            continue
        if item["unread"]:
            unread_item_count = unread_item_count + 1
            for one_filter in filters:
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
                        logging.DEBUG,
                        f"filter {one_filter['name']} matched item {item['id']} with title {item['title']}",
                    )
                    matched_item_ids.append(item["id"])

    if matched_item_ids:
        logging.log(
            logging.INFO,
            f"marking as read: {len(matched_item_ids)} of {unread_item_count} items",
        )
        requests.post(
            url=f'{config["address"]}/index.php/apps/news/api/v1-3/items/read/multiple',
            headers=dict(Authorization=f"Basic {config['auth']}"),
            json=dict(itemIds=matched_item_ids),
        )

    logging.debug("finished run")
