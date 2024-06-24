import json
import logging
import sys
from os import environ
from typing import Literal, NotRequired, TypedDict

from nextcloud_news_filter.config import Config
from nextcloud_news_filter.filter import (
    FilterConfig,
    filter_items,
    mark_as_read,
)


class RequestContext(TypedDict):
    """Request context that is sent in the http event."""

    accountId: str
    resourceId: str
    stage: str
    requestId: str
    resourcePath: str
    authorizer: Literal[None]
    httpMethod: str
    apiId: str


class Event(TypedDict):
    """Event dictionnary passed to the function."""

    path: str
    httpMethod: str
    headers: dict[str, str]
    multiValueHeaders: Literal[None]
    queryStringParameters: dict[str, str]
    multiValueQueryStringParameters: Literal[None]
    pathParameters: Literal[None]
    stageVariable: dict[str, str]
    requestContext: RequestContext
    body: str
    isBase64Encoded: NotRequired[Literal[True]]


class Context(TypedDict):
    """Context dictionnary passed to the function."""

    memoryLimitInMb: int
    functionName: str
    functionVersion: str


def handler(event: Event, context: Context):
    logging.basicConfig(
        level=environ.get("LOG_LEVEL", logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )
    logging.debug(f"Handler called with: {event}")
    filter_json = event["body"]
    filter_config = FilterConfig(json.loads(filter_json))

    filter_news(filter_config)
    return "Handler finished"


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


def setup_scaleway():
    # The import is conditional so that you do not need
    # to package the library when deploying on Scaleway Functions.
    from scaleway_functions_python import local

    local.serve_handler(handler, port=8080)


if __name__ == "__main__":
    setup_scaleway()
