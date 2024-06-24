try:
    import typer
except ImportError as e:
    e.msg = "You need to install this package with nextcloud_news_filter[cli]"
    raise e

import logging
from pathlib import Path
from typing import Annotated

from nextcloud_news_filter import filter_news
from nextcloud_news_filter.config import ConfigurationError
from nextcloud_news_filter.filter import FilterConfig


def cli(
    filter_file: Path,
    debug: Annotated[bool, typer.Option(help="Enable debug output")] = False,
):
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(format="%(levelname)s: %(message)s", level=log_level)
    logging.debug("Start filtering news…")
    filter_config = FilterConfig.from_file(filter_file=filter_file)
    if filter_config:
        try:
            filter_news(filter_config)
        except ConfigurationError:
            print(
                "There is a configuration error."
                "Fix the ones, that are mentioned above!"
            )


def main():
    typer.run(cli)


if __name__ == "__main__":
    main()
