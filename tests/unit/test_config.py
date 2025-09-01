"""Tests for app.config.Config validation and defaults."""

import pytest


def test_config_validate_missing_fields(mocker):
    import app.config as cfg

    # Ensure required fields are missing
    mocker.patch.object(cfg.Config, "TELEGRAM_API_ID", None)
    mocker.patch.object(cfg.Config, "TELEGRAM_API_HASH", None)
    mocker.patch.object(cfg.Config, "TELEGRAM_PHONE", None)

    with pytest.raises(ValueError) as ei:
        cfg.Config.validate()

    msg = str(ei.value)
    assert "TELEGRAM_API_ID" in msg and "TELEGRAM_API_HASH" in msg and "TELEGRAM_PHONE" in msg


def test_config_validate_success(mocker):
    # Reload module to ensure a clean state for class attributes
    import app.config as cfg

    mocker.patch.object(cfg.Config, "TELEGRAM_API_ID", "123")
    mocker.patch.object(cfg.Config, "TELEGRAM_API_HASH", "abc")
    mocker.patch.object(cfg.Config, "TELEGRAM_PHONE", "+1000")

    # Should not raise
    cfg.Config.validate()
