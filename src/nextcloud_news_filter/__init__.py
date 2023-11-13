import sys
import logging
from os import environ
from nextcloud_news_filter.config import Config

from nextcloud_news_filter.filter import FilterConfig, filter_items, mark_as_read


def handler(*args, **kwargs) -> None:
    logging.basicConfig(
        level=environ.get("LOG_LEVEL", logging.DEBUG),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )
    logging.debug(f"Handler called with: {args}")
    filter_config = FilterConfig(args[0]["body"])
    filter_news(filter_config)


def filter_news(filter_config: FilterConfig) -> None:
    logging.debug("starting run")

    config = Config()
    matched_item_ids, unread_item_count = filter_items(config, filter_config)
    if len(matched_item_ids) > 0:
        logging.log(
            logging.INFO,
            f"Marking as read: {len(matched_item_ids)} of {unread_item_count} items.",
        )
        mark_as_read(
            matched_item_ids=matched_item_ids,
            config=config,
        )
    logging.debug("finished run")
