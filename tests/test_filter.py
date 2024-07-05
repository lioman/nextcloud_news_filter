import json
import logging
from pathlib import Path

import pytest
import responses
from nextcloud_news_filter.config import Config
from nextcloud_news_filter.filter import FilterConfig, filter_items, mark_as_read
from nextcloud_news_filter.model import FilterJson
from pytest_mock import MockerFixture

from tests.conftest import MockConfig


class TestFilterConfig:
    def test_from_dict(self, filter_json: FilterJson):
        conf = FilterConfig(filter_json=filter_json)
        assert len(conf.filter) == 3
        assert len(conf.feeds_to_skip) == 3

    def test_from_file(self, filter_json: dict, tmp_path: Path):
        tmp_file = tmp_path / "test.json"
        tmp_file.write_text(json.dumps(filter_json))
        conf = FilterConfig.from_file(tmp_file)
        assert conf is not None
        assert len(conf.filter) == 3
        assert len(conf.feeds_to_skip) == 3

    def test_from_non_existant_file(self, caplog: pytest.LogCaptureFixture):
        with pytest.raises(FileNotFoundError):
            file = "this_does_not_exist.json"
            FilterConfig.from_file(Path(file))
            assert file in caplog.text

    @pytest.mark.parametrize(
        "items,filter_sequence,call_count,expected",
        [
            (
                [{"id": 42, "unread": True}, {"id": 2, "unread": False}],
                [True],
                1,
                ([42], 1),
            ),
            (
                [{"id": 42, "unread": True}, {"id": 2, "unread": True}],
                [True, True],
                2,
                ([42, 2], 2),
            ),
            (
                [{"id": 42, "unread": True}, {"id": 2, "unread": True}],
                [False, True],
                2,
                ([2], 2),
            ),
        ],
    )
    def test_apply_filter_to_batch(
        self,
        mocker: MockerFixture,
        filter_config: FilterConfig,
        items: dict,
        filter_sequence: list[bool],
        call_count: int,
        expected: tuple[int, int],
    ):
        is_matching_mock = mocker.patch.object(
            filter_config,
            "is_filter_matching_item",
            side_effect=filter_sequence,
        )
        assert expected == filter_config.apply_filter_to_batch(items)  # type: ignore
        assert is_matching_mock.call_count == call_count

    class TestIsFilterMatchingItem:
        def test_no_filter_is_matching(
            self,
        ):
            filter_config = FilterConfig(
                filter_json={
                    "filter": [
                        {"name": "hoursAge > 20 Days", "feedId": 123, "hoursAge": 504}
                    ]
                }
            )
            assert filter_config.is_filter_matching_item({"feedId": 21}) is False  # type: ignore

        def test_skipped_item_returns_False(self, filter_config: FilterConfig):
            filter_config._feeds_to_skip = [21]
            assert filter_config.is_filter_matching_item({"feedId": 21}) is False  # type: ignore

        @pytest.mark.parametrize(
            "filter,item",
            [
                (
                    [{"name": "feed older > 20 Days", "feedId": 123, "hoursAge": 504}],
                    {"feedId": 123, "pubDate": 0, "id": 22, "title": "Hello"},
                ),
                (
                    [{"name": "every feed older > 1", "hoursAge": 24}],
                    {"feedId": 6363, "pubDate": 0, "id": 22, "title": "Hello"},
                ),
                (
                    [{"name": "title Regex starts with", "titleRegex": "Hello"}],
                    {"feedId": 6363, "pubDate": 0, "id": 22, "title": "Hello"},
                ),
                (
                    [{"name": "title Regex middle", "titleRegex": "World"}],
                    {
                        "feedId": 6363,
                        "pubDate": 0,
                        "id": 22,
                        "title": "Hello World, foo bar",
                    },
                ),
                (
                    [
                        {
                            "name": "title Regex is case incensitive",
                            "titleRegex": "World",
                        }
                    ],
                    {
                        "feedId": 6363,
                        "pubDate": 0,
                        "id": 22,
                        "title": "Hello world",
                    },
                ),
                (
                    [
                        {
                            "name": "body Regex is matches only body",
                            "bodyRegex": "World",
                        },
                        {
                            "name": "title Regex",
                            "titleRegex": "foo",
                        },
                    ],
                    {
                        "id": 22,
                        "feedId": 3434,
                        "title": "Hello",
                        "body": "<p>World</p>",
                    },
                ),
            ],
        )
        def test_matching_filters(
            self,
            caplog: pytest.LogCaptureFixture,
            filter,
            item,
        ):
            filter_config = FilterConfig(filter_json={"filter": filter})  # type: ignore
            caplog.set_level(logging.INFO)
            assert filter_config.is_filter_matching_item(item) is True
            assert str(item["id"]) in caplog.text
            assert item["title"] in caplog.text

        def test_matching_filters_only_one(
            self,
            caplog: pytest.LogCaptureFixture,
        ):
            filter = [
                {
                    "name": "title Regex matches",
                    "titleRegex": "Hello",
                },
                {
                    "name": "body Regex is not executed",
                    "bodyRegex": "World",
                },
            ]
            item = {
                "id": 22,
                "feedId": 3434,
                "title": "Hello",
                "body": "<p>World</p>",
            }

            filter_config = FilterConfig(filter_json={"filter": filter})  # type: ignore
            caplog.set_level(logging.INFO)
            assert filter_config.is_filter_matching_item(item) is True  # type: ignore
            assert str(item["id"]) in caplog.text
            assert item["title"] in caplog.text  # type: ignore
            assert filter[0]["name"] in caplog.text
            assert filter[1]["name"] not in caplog.text


class TestFilterItems:
    @responses.activate
    def test_items_api_called(self, config: Config):
        rsp = responses.add(
            responses.GET,
            url=f"{config.nextcloud_url}/index.php/apps/news/api/v1-3/items",
            json={"items": []},
            status=502,  # The rest of the code will not be executed
        )
        filter_conf = FilterConfig(filter_json={"filter": [{"name": "test"}]})
        filter_items(config=config, filter_config=filter_conf)
        assert rsp.call_count == 1
        assert json.loads(rsp.calls[0].request.body) == {  # type: ignore
            "batchSize": 50,
            "offset": 0,
            "type": 3,  # Type: all
            "id": 0,  # Get all entries
            "getRead": "false",  # ignore read entries
        }

    @responses.activate
    def test_filter_is_skipped_no_items(
        self, config: Config, filter_config: FilterConfig, mocker: MockerFixture
    ):
        rsp = responses.add(
            responses.GET,
            url=f"{config.nextcloud_url}/index.php/apps/news/api/v1-3/items",
            json={"items": []},
            status=200,
        )
        apply_filter_mock = mocker.patch.object(filter_config, "apply_filter_to_batch")
        filter_items(config=config, filter_config=filter_config)

        assert rsp.call_count == 1
        apply_filter_mock.assert_not_called()

    @responses.activate
    def test_filter_are_applied_to_batch(
        self, config: Config, filter_config: FilterConfig, mocker: MockerFixture
    ):
        rsp1 = responses.add(
            responses.GET,
            url=f"{config.nextcloud_url}/index.php/apps/news/api/v1-3/items",
            json={"items": [{"id": 42}]},
            status=200,
        )
        rsp2 = responses.add(
            responses.GET,
            url=f"{config.nextcloud_url}/index.php/apps/news/api/v1-3/items",
            json={"items": [{"id": 48}]},
            status=200,
        )
        rsp3 = responses.add(
            responses.GET,
            url=f"{config.nextcloud_url}/index.php/apps/news/api/v1-3/items",
            json={"items": []},
            status=200,
        )
        apply_filter_mock = mocker.patch.object(
            filter_config,
            "apply_filter_to_batch",
            side_effect=[([1, 2, 3], 12), ([43], 12)],
        )
        assert filter_items(config=config, filter_config=filter_config) == (
            [1, 2, 3, 43],
            24,
        )

        assert rsp1.call_count == 1
        assert json.loads(rsp1.calls[0].request.body)["offset"] == 0  # type: ignore
        assert rsp2.call_count == 1
        assert json.loads(rsp2.calls[0].request.body)["offset"] == 42  # type: ignore
        assert rsp3.call_count == 1
        assert json.loads(rsp3.calls[0].request.body)["offset"] == 48  # type: ignore
        assert apply_filter_mock.call_count == 2


@responses.activate
def test_mark_as_read(config: MockConfig):
    rsp = responses.add(
        responses.POST,
        url=f"{config.nextcloud_url}/index.php/apps/news/api/v1-3/items/read/multiple",
        status=200,
    )
    mark_as_read([1, 2, 6], config=config)
    assert rsp.call_count == 1
    assert json.loads(rsp.calls[0].request.body) == {"itemIds": [1, 2, 6]}  # type: ignore
