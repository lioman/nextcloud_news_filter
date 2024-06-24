import base64
import logging
from os import environ


class ConfigurationError(Exception):
    pass


class Config:
    def __init__(self):
        if environ.get("NEXTCLOUD_URL") is None:
            msg = "NEXTCLOUD_URL is not set in environment"
            logging.log(logging.ERROR, msg)
            raise ConfigurationError(msg)
        self._nextcloud_url = environ["NEXTCLOUD_URL"].rstrip("/")

        if (
            environ.get("NEXTCLOUD_USER") is None
            or environ.get("NEXTCLOUD_PASS") is None
        ):
            msg = "NEXTCLOUD_USER and NEXTCLOUD_PASS need to be set in environment"
            logging.log(
                logging.ERROR,
                msg,
            )
            raise ConfigurationError(msg)
        self._auth_header = f"Basic {self._basic_auth()}"

        self._batch_size = int(environ.get("BATCH_SIZE", 500))

    @property
    def nextcloud_url(self) -> str:
        return self._nextcloud_url

    @property
    def auth_header(self) -> str:
        return self._auth_header

    @property
    def batch_size(self) -> int:
        return self._batch_size

    def _basic_auth(self) -> str:
        return (
            base64.encodebytes(
                f'{environ["NEXTCLOUD_USER"]}:{environ["NEXTCLOUD_PASS"]}'.encode()
            )
            .decode(encoding="UTF-8")
            .strip()
        )
