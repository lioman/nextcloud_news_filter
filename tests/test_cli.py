from pathlib import Path

from nextcloud_news_filter.config import ConfigurationError
from nextcloud_news_filter.filter import FilterConfig
from pytest_mock import MockerFixture
from nextcloud_news_filter import cli


def test_main(mocker: MockerFixture):
    typer_mock = mocker.patch("nextcloud_news_filter.cli.typer.run")
    cli.main()
    typer_mock.assert_called_once()


class TestCli:
    def test_cli_with_working_config(
        self, filter_config: FilterConfig, mocker: MockerFixture
    ):
        filter_news_mock = mocker.patch("nextcloud_news_filter.cli.filter_news")
        filter_config_mock = mocker.patch.object(
            FilterConfig, "from_file", return_value=filter_config
        )
        fake_file = Path("This_does_not_exists.json")
        cli.cli(fake_file)
        filter_config_mock.assert_called_once_with(filter_file=fake_file)
        filter_news_mock.assert_called_once()

    def test_config_errounous_config(
        self, filter_config: FilterConfig, mocker: MockerFixture
    ):
        filter_news_mock = mocker.patch(
            "nextcloud_news_filter.cli.filter_news", side_effect=ConfigurationError()
        )
        filter_config_mock = mocker.patch.object(
            FilterConfig, "from_file", return_value=filter_config
        )
        print_mock = mocker.patch("builtins.print")
        fake_file = Path("This_does_not_exists.json")
        cli.cli(fake_file)
        filter_config_mock.assert_called_once_with(filter_file=fake_file)
        filter_news_mock.assert_called_once()
        assert "There is a configuration error" in print_mock.call_args[0][0]
