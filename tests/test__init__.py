import logging

import pytest
from nextcloud_news_filter import Event, filter_news, handler, setup_scaleway
from nextcloud_news_filter.filter import FilterConfig
from pytest import LogCaptureFixture
from pytest_mock import MockerFixture

from tests.conftest import MockConfig


class TestHandler:
    def test_handler_call(self, mocker: MockerFixture):
        call_args: Event = {
            "path": "/",
            "httpMethod": "POST",
            "headers": {
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "en-US,en;q=0.8,en-GB;q=0.6,de-DE;q=0.4,de;q=0.2",
                "Content-Length": "920",
                "Content-Type": "text/plain;charset=UTF-8",
                "Dnt": "1",
                "Forwarded": "for=84.150.218.51;proto=https, for=100.64.7.161",
                "K-Proxy-Request": "activator",
                "Origin": "https://console.scaleway.com",
                "Referer": "https://console.scaleway.com/",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "cross-site",
                "Sec-Gpc": "1",
                "Te": "trailers",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",  # noqa: E501
                "X-Envoy-External-Address": "84.150.218.51",
                "X-Forwarded-For": "84.150.218.51, 100.64.7.161, 100.64.0.57",
                "X-Forwarded-Proto": "https",
                "X-Request-Id": "5bbf123a-f99e-4978-ba2a-82d683d6f8a5",
            },
            "multiValueHeaders": None,
            "queryStringParameters": {},
            "multiValueQueryStringParameters": None,
            "pathParameters": None,
            "stageVariable": {},
            "requestContext": {
                "accountId": "",
                "resourceId": "",
                "stage": "",
                "requestId": "",
                "resourcePath": "",
                "authorizer": None,
                "httpMethod": "POST",
                "apiId": "",
            },
            "body": '{"filter":[{"feedId":1592,"name":"test","titleRegex":"test"}],"skipFeeds":[1678,1683]}',  # noqa: E501
        }

        filter_news_mock = mocker.patch("nextcloud_news_filter.filter_news")
        json_loads_mock = mocker.patch("nextcloud_news_filter.json.loads")

        handler(
            call_args,
            {"memoryLimitInMb": 123, "functionName": "test", "functionVersion": "test"},
        )
        filter_news_mock.assert_called_once()
        json_loads_mock.assert_called_once_with(
            '{"filter":[{"feedId":1592,"name":"test","titleRegex":"test"}],"skipFeeds":[1678,1683]}'
        )


@pytest.mark.parametrize("matched_items,mark_call_count", [([1, 2], 1), ([], 0)])
def test_filter_news(
    filter_config: FilterConfig,
    caplog: LogCaptureFixture,
    mocker: MockerFixture,
    matched_items,
    mark_call_count,
):
    filter_items_mock = mocker.patch(
        "nextcloud_news_filter.filter_items", return_value=(matched_items, 300)
    )
    mark_as_read_mock = mocker.patch("nextcloud_news_filter.mark_as_read")
    mocker.patch("nextcloud_news_filter.Config", side_effect=MockConfig)
    caplog.set_level(logging.INFO)

    filter_news(filter_config)
    filter_items_mock.assert_called_once()
    assert mark_as_read_mock.call_count == mark_call_count
    if len(matched_items) > 0:
        assert "Marking as read" in caplog.text


def test_scaleway_setup(mocker: MockerFixture):
    local_mock = mocker.patch("scaleway_functions_python.local.serve_handler")
    handler_mock = mocker.patch("nextcloud_news_filter.handler")
    setup_scaleway()
    local_mock.assert_called_once_with(handler_mock, port=8080)
