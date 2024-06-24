
import pytest
from nextcloud_news_filter.config import Config
from nextcloud_news_filter.filter import FilterConfig


@pytest.fixture()
def filter_json() -> dict:
    return {
        "filter": [
            {"name": "hoursAge > 20 Days", "feedId": 123, "hoursAge": 504},
            {"name": "title regex", "feedId": 1592, "titleRegex": "Advertisement"},
            {"name": "body regex", "feedId": 42, "bodyRegex": "dpa"},
        ],
        "skipFeeds": [1, 2, 3],
    }


@pytest.fixture()
def filter_config(filter_json) -> FilterConfig:
    return FilterConfig(filter_json)


class MockConfig(Config):
    def __init__(self):
        self._nextcloud_url = "https://example.com"
        self._auth_header = "Basic dXNlcjpwYXNz"
        self._batch_size = 50


@pytest.fixture
def config():
    return MockConfig()
