from nextcloud_news_filter import Event, handler
from pytest_mock import MockerFixture


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
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
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
            "body": '{"filter":[{"feedId":1592,"name":"test","titleRegex":"test"}],"skipFeeds":[1678,1683]}',
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
