import json
from pathlib import Path

import pytest
import responses
from nextcloud_news_filter.config import Config
from nextcloud_news_filter.filter import FilterConfig, filter_items, mark_as_read
from pytest_mock import MockerFixture


class TestFilterConfig:
    def test_from_dict(self, filter_json):
        conf = FilterConfig(filter_json=filter_json)
        assert len(conf.filter) == 3
        assert len(conf.feeds_to_skip) == 3

    def test_from_file(self, filter_json, tmp_path: Path):
        tmp_file = tmp_path / "test.json"
        tmp_file.write_text(json.dumps(filter_json))
        conf = FilterConfig.from_file(tmp_file)
        assert conf is not None
        assert len(conf.filter) == 3
        assert len(conf.feeds_to_skip) == 3

    def test_from_non_existant_file(self, caplog):
        with pytest.raises(FileNotFoundError):
            file = "this_does_not_exist.json"
            FilterConfig.from_file(Path(file))
            assert file in caplog.text

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
    def test_stop_on_no_items(self, config: Config, mocker: MockerFixture):
        rsp = responses.add(
            responses.GET,
            url=f"{config.nextcloud_url}/index.php/apps/news/api/v1-3/items",
            json={"items": []},
            status=200,
        )
        apply_filter_mock = mocker.patch(
            "nextcloud_news_filter.filter.apply_filter_to_batch"
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
        apply_filter_mock.assert_not_called()

    @responses.activate
    def test_mark_matched_items_as_read(self, config: Config, mocker: MockerFixture):
        rsp = responses.add(
            responses.GET,
            url=f"{config.nextcloud_url}/index.php/apps/news/api/v1-3/items",
            json={"items": []},
            status=200,
        )
        apply_filter_mock = mocker.patch(
            "nextcloud_news_filter.filter.apply_filter_to_batch"
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
        apply_filter_mock.assert_not_called()


@responses.activate
def test_mark_as_read(config):
    rsp = responses.add(
        responses.POST,
        url=f"{config.nextcloud_url}/index.php/apps/news/api/v1-3/items/read/multiple",
        status=200,
    )
    mark_as_read([1, 2, 6], config=config)
    assert rsp.call_count == 1
    assert json.loads(rsp.calls[0].request.body) == {"itemIds": [1, 2, 6]}  # type: ignore
