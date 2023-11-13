try:
    import typer
except ImportError as e:
    e.msg = "You need to install this package with nextcloud_news_filter[cli]"
    raise e

from pathlib import Path
from nextcloud_news_filter import filter_news

from nextcloud_news_filter.filter import FilterConfig


def cli(
    filter_file: Path,
):
    filter_config = FilterConfig.from_file(filter_file=filter_file)
    filter_news(filter_config)


def main():
    typer.run(cli)
