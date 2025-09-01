"""Tests for utils/logging.py module (pytest-mock, functions only)."""


def test_setup_logging_configuration(mocker):
    from app.utils.logging import setup_logging

    mock_logger = mocker.patch("app.utils.logging.logger")
    mock_path = mocker.patch("app.utils.logging.Path")
    mock_config = mocker.patch("app.utils.logging.config")

    mock_config.LOG_LEVEL = "INFO"
    mock_logs_dir = mocker.MagicMock()
    mock_path.return_value = mock_logs_dir

    setup_logging()

    mock_logger.remove.assert_called_once()
    mock_path.assert_called_with("logs")
    mock_logs_dir.mkdir.assert_called_once_with(exist_ok=True)
    assert mock_logger.add.call_count == 4
    mock_logger.info.assert_called_with("Logging configured with level: INFO")


def test_setup_logging_handlers(mocker):
    from app.utils.logging import setup_logging

    mock_logger = mocker.patch("app.utils.logging.logger")
    mock_path = mocker.patch("app.utils.logging.Path")
    mock_sys = mocker.patch("app.utils.logging.sys")
    mock_config = mocker.patch("app.utils.logging.config")

    mock_config.LOG_LEVEL = "DEBUG"
    mock_path.return_value = mocker.MagicMock()

    setup_logging()

    add_calls = mock_logger.add.call_args_list
    assert len(add_calls) == 4
    first_call = add_calls[0]
    assert first_call[0][0] == mock_sys.stdout
    assert first_call[1]["level"] == "DEBUG"
    assert first_call[1]["colorize"] is True
    for call in add_calls[1:]:
        assert hasattr(call[0][0], "__truediv__")


def test_get_logger_function(mocker):
    from app.utils.logging import get_logger

    mock_logger = mocker.patch("app.utils.logging.logger")
    mock_bound = mocker.MagicMock()
    mock_logger.bind.return_value = mock_bound

    result = get_logger("test_module")
    mock_logger.bind.assert_called_once_with(name="test_module")
    assert result == mock_bound


def test_get_logger_return_type():
    from app.utils.logging import get_logger

    assert callable(get_logger)
    assert get_logger("test") is not None


def test_setup_logging_file_paths(mocker):
    from app.utils.logging import setup_logging

    mocker.patch("app.utils.logging.logger")
    mock_path = mocker.patch("app.utils.logging.Path")
    mock_config = mocker.patch("app.utils.logging.config")

    mock_config.LOG_LEVEL = "INFO"
    mock_logs_dir = mocker.MagicMock()
    mock_path.return_value = mock_logs_dir

    setup_logging()

    expected_files = ["app.log", "errors.log", "structured.log"]
    for expected in expected_files:
        mock_logs_dir.__truediv__.assert_any_call(expected)


def test_setup_logging_levels(mocker):
    from app.utils.logging import setup_logging

    mock_logger = mocker.patch("app.utils.logging.logger")
    mock_path = mocker.patch("app.utils.logging.Path")
    mock_config = mocker.patch("app.utils.logging.config")

    mock_config.LOG_LEVEL = "WARNING"
    mock_path.return_value = mocker.MagicMock()

    setup_logging()

    add_calls = mock_logger.add.call_args_list
    assert add_calls[0][1]["level"] == "WARNING"
    assert add_calls[1][1]["level"] == "DEBUG"
    assert add_calls[2][1]["level"] == "ERROR"
    assert add_calls[3][1]["level"] == "INFO"


def test_setup_logging_formats(mocker):
    from app.utils.logging import setup_logging

    mock_logger = mocker.patch("app.utils.logging.logger")
    mock_path = mocker.patch("app.utils.logging.Path")
    mock_config = mocker.patch("app.utils.logging.config")

    mock_config.LOG_LEVEL = "INFO"
    mock_path.return_value = mocker.MagicMock()

    setup_logging()
    add_calls = mock_logger.add.call_args_list

    console_fmt = add_calls[0][1]["format"]
    assert "<green>" in console_fmt and "<level>" in console_fmt and "<cyan>" in console_fmt

    for file_call in add_calls[1:3]:
        file_fmt = file_call[1]["format"]
        assert "YYYY-MM-DD HH:mm:ss" in file_fmt
        assert "{level: <8}" in file_fmt
        assert "{name}:{function}:{line}" in file_fmt

    structured_fmt = add_calls[3][1]["format"]
    assert structured_fmt == "{message}"
    assert add_calls[3][1]["serialize"] is True


def test_setup_logging_rotation_and_retention(mocker):
    from app.utils.logging import setup_logging

    mock_logger = mocker.patch("app.utils.logging.logger")
    mock_path = mocker.patch("app.utils.logging.Path")
    mock_config = mocker.patch("app.utils.logging.config")

    mock_config.LOG_LEVEL = "INFO"
    mock_path.return_value = mocker.MagicMock()

    setup_logging()
    add_calls = mock_logger.add.call_args_list

    app_call = add_calls[1]
    assert app_call[1]["rotation"] == "10 MB"
    assert app_call[1]["retention"] == "7 days"
    assert app_call[1]["compression"] == "zip"

    error_call = add_calls[2]
    assert error_call[1]["rotation"] == "5 MB"
    assert error_call[1]["retention"] == "30 days"
    assert error_call[1]["compression"] == "zip"

    structured_call = add_calls[3]
    assert structured_call[1]["rotation"] == "20 MB"
    assert structured_call[1]["retention"] == "7 days"
    assert structured_call[1]["compression"] == "zip"


def test_logger_import():
    from app.utils.logging import logger

    assert logger is not None


def test_config_integration():
    from app.utils.logging import config

    assert config is not None
    assert hasattr(config, "LOG_LEVEL")


def test_pathlib_integration():
    from app.utils.logging import Path

    assert Path is not None
    assert isinstance(Path("test"), Path)


def test_sys_integration():
    from app.utils.logging import sys

    assert sys is not None
    assert hasattr(sys, "stdout")


def test_setup_logging_can_be_called(mocker):
    import app.utils.logging as logging_module

    spy = mocker.patch("app.utils.logging.setup_logging")
    assert callable(logging_module.setup_logging)
    logging_module.setup_logging()
    spy.assert_called_once()


def test_get_logger_with_different_names():
    from app.utils.logging import get_logger

    assert get_logger("app.main") is not None
    assert get_logger("__main__") is not None
    assert get_logger("test_module") is not None
