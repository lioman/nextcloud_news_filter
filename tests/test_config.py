import pytest
from random import randint
from nextcloud_news_filter.config import Config, ConfigurationError


class TestGetConfig:
    def test_address_missing(self, monkeypatch):
        monkeypatch.delenv("NEXTCLOUD_URL", raising=False)
        monkeypatch.setenv("NEXTCLOUD_PASS", "BAR")
        monkeypatch.setenv("NEXTCLOUD_USER", "FOO")
        with pytest.raises(ConfigurationError) as exc_info:
            Config()
        assert "NEXTCLOUD_URL" in exc_info.value.args[0]

    def test_user_is_missing(self, monkeypatch):
        test_url = "https://example.com/"
        monkeypatch.setenv("NEXTCLOUD_URL", test_url)
        monkeypatch.setenv("NEXTCLOUD_PASS", "BAR")
        monkeypatch.delenv("NEXTCLOUD_USER", raising=False)
        with pytest.raises(ConfigurationError) as exc_info:
            Config()
        assert "NEXTCLOUD_USER" in exc_info.value.args[0]

    def test_pass_is_missing(self, monkeypatch):
        test_url = "https://example.com/"
        monkeypatch.setenv("NEXTCLOUD_URL", test_url)
        monkeypatch.setenv("NEXTCLOUD_USER", "BAR")
        monkeypatch.delenv("NEXTCLOUD_PASS", raising=False)
        with pytest.raises(ConfigurationError) as exc_info:
            Config()
        assert "NEXTCLOUD_PASS" in exc_info.value.args[0]

    def test_NEXTCLOUD_URL(self, monkeypatch):
        test_url = "https://example.com/"
        monkeypatch.setenv("NEXTCLOUD_URL", test_url)
        monkeypatch.setenv("NEXTCLOUD_USER", "FOO")
        monkeypatch.setenv("NEXTCLOUD_PASS", "BAR")
        config = Config()
        assert config.nextcloud_url == "https://example.com"

    def test_auth_is_set(self, monkeypatch):
        test_url = "https://example.com/"
        monkeypatch.setenv("NEXTCLOUD_URL", test_url)
        monkeypatch.setenv("NEXTCLOUD_USER", "user")
        monkeypatch.setenv("NEXTCLOUD_PASS", "pass")
        config = Config()
        assert config.auth_header == "Basic dXNlcjpwYXNz"

    def test_default_batchsize_is_set(self, monkeypatch):
        test_url = "https://example.com/"
        monkeypatch.setenv("NEXTCLOUD_URL", test_url)
        monkeypatch.setenv("NEXTCLOUD_USER", "user")
        monkeypatch.setenv("NEXTCLOUD_PASS", "pass")
        config = Config()
        assert config.batch_size == 500

    def test_default_is_overridden(self, monkeypatch):
        test_url = "https://example.com/"
        monkeypatch.setenv("NEXTCLOUD_URL", test_url)
        monkeypatch.setenv("NEXTCLOUD_USER", "user")
        monkeypatch.setenv("NEXTCLOUD_PASS", "pass")
        test_batch_size = randint(0, 300)
        monkeypatch.setenv("BATCH_SIZE", test_batch_size)
        config = Config()
        assert config.batch_size == test_batch_size
