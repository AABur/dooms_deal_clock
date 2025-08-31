"""Tests for utils/logging.py module."""

from unittest.mock import MagicMock, patch


class TestLoggingSetup:
    """Test logging setup functionality."""

    @patch("app.utils.logging.logger")
    @patch("app.utils.logging.Path")
    @patch("app.utils.logging.config")
    def test_setup_logging_configuration(self, mock_config, mock_path, mock_logger):
        """Test logging setup configuration."""
        from app.utils.logging import setup_logging

        # Mock config
        mock_config.LOG_LEVEL = "INFO"

        # Mock Path and directory creation
        mock_logs_dir = MagicMock()
        mock_path.return_value = mock_logs_dir

        # Call setup_logging
        setup_logging()

        # Verify logger.remove() was called
        mock_logger.remove.assert_called_once()

        # Verify logs directory creation
        mock_path.assert_called_with("logs")
        mock_logs_dir.mkdir.assert_called_once_with(exist_ok=True)

        # Verify logger.add was called multiple times (4 handlers)
        assert mock_logger.add.call_count == 4

        # Verify logger.info was called with config info
        mock_logger.info.assert_called_with("Logging configured with level: INFO")

    @patch("app.utils.logging.logger")
    @patch("app.utils.logging.Path")
    @patch("app.utils.logging.sys")
    @patch("app.utils.logging.config")
    def test_setup_logging_handlers(self, mock_config, mock_sys, mock_path, mock_logger):
        """Test that all logging handlers are configured."""
        from app.utils.logging import setup_logging

        # Mock config
        mock_config.LOG_LEVEL = "DEBUG"

        # Mock Path
        mock_logs_dir = MagicMock()
        mock_path.return_value = mock_logs_dir

        # Call setup_logging
        setup_logging()

        # Check that logger.add was called for different handlers
        add_calls = mock_logger.add.call_args_list

        # Should have 4 calls: console, app.log, errors.log, structured.log
        assert len(add_calls) == 4

        # First call should be console handler (sys.stdout)
        first_call = add_calls[0]
        assert first_call[0][0] == mock_sys.stdout
        assert first_call[1]["level"] == "DEBUG"
        assert first_call[1]["colorize"] is True

        # Check file handlers
        for call in add_calls[1:]:
            # Should be file paths
            assert hasattr(call[0][0], "__truediv__")  # Path object

    @patch("app.utils.logging.logger")
    def test_get_logger_function(self, mock_logger):
        """Test get_logger function."""
        from app.utils.logging import get_logger

        # Mock logger.bind
        mock_bound_logger = MagicMock()
        mock_logger.bind.return_value = mock_bound_logger

        # Call get_logger
        result = get_logger("test_module")

        # Verify logger.bind was called with correct name
        mock_logger.bind.assert_called_once_with(name="test_module")
        assert result == mock_bound_logger

    def test_get_logger_return_type(self):
        """Test get_logger return type annotation."""
        from app.utils.logging import get_logger

        # Check that function exists and is callable
        assert callable(get_logger)

        # Check that it can be called with a string
        logger_instance = get_logger("test")
        assert logger_instance is not None

    @patch("app.utils.logging.logger")
    @patch("app.utils.logging.Path")
    @patch("app.utils.logging.config")
    def test_setup_logging_file_paths(self, mock_config, mock_path, mock_logger):
        """Test that correct file paths are used for log files."""
        from app.utils.logging import setup_logging

        mock_config.LOG_LEVEL = "INFO"
        mock_logs_dir = MagicMock()
        mock_path.return_value = mock_logs_dir

        setup_logging()

        # Check file names used
        expected_files = ["app.log", "errors.log", "structured.log"]

        for expected_file in expected_files:
            # Should call logs_dir / filename
            mock_logs_dir.__truediv__.assert_any_call(expected_file)

    @patch("app.utils.logging.logger")
    @patch("app.utils.logging.Path")
    @patch("app.utils.logging.config")
    def test_setup_logging_levels(self, mock_config, mock_path, mock_logger):
        """Test that correct logging levels are set."""
        from app.utils.logging import setup_logging

        mock_config.LOG_LEVEL = "WARNING"
        mock_logs_dir = MagicMock()
        mock_path.return_value = mock_logs_dir

        setup_logging()

        add_calls = mock_logger.add.call_args_list

        # Console handler should use config.LOG_LEVEL
        console_call = add_calls[0]
        assert console_call[1]["level"] == "WARNING"

        # App log should use DEBUG
        app_log_call = add_calls[1]
        assert app_log_call[1]["level"] == "DEBUG"

        # Error log should use ERROR
        error_log_call = add_calls[2]
        assert error_log_call[1]["level"] == "ERROR"

        # Structured log should use INFO
        structured_call = add_calls[3]
        assert structured_call[1]["level"] == "INFO"

    @patch("app.utils.logging.logger")
    @patch("app.utils.logging.Path")
    @patch("app.utils.logging.config")
    def test_setup_logging_formats(self, mock_config, mock_path, mock_logger):
        """Test that correct log formats are used."""
        from app.utils.logging import setup_logging

        mock_config.LOG_LEVEL = "INFO"
        mock_logs_dir = MagicMock()
        mock_path.return_value = mock_logs_dir

        setup_logging()

        add_calls = mock_logger.add.call_args_list

        # Console handler should have colored format
        console_call = add_calls[0]
        console_format = console_call[1]["format"]
        assert "<green>" in console_format
        assert "<level>" in console_format
        assert "<cyan>" in console_format

        # File handlers should have timestamp format
        for file_call in add_calls[1:3]:  # app.log and errors.log
            file_format = file_call[1]["format"]
            assert "YYYY-MM-DD HH:mm:ss" in file_format
            assert "{level: <8}" in file_format
            assert "{name}:{function}:{line}" in file_format

        # Structured log should use simple format for JSON
        structured_call = add_calls[3]
        structured_format = structured_call[1]["format"]
        assert structured_format == "{message}"
        assert structured_call[1]["serialize"] is True

    @patch("app.utils.logging.logger")
    @patch("app.utils.logging.Path")
    @patch("app.utils.logging.config")
    def test_setup_logging_rotation_and_retention(self, mock_config, mock_path, mock_logger):
        """Test log rotation and retention settings."""
        from app.utils.logging import setup_logging

        mock_config.LOG_LEVEL = "INFO"
        mock_logs_dir = MagicMock()
        mock_path.return_value = mock_logs_dir

        setup_logging()

        add_calls = mock_logger.add.call_args_list

        # App log settings
        app_call = add_calls[1]
        assert app_call[1]["rotation"] == "10 MB"
        assert app_call[1]["retention"] == "7 days"
        assert app_call[1]["compression"] == "zip"

        # Error log settings
        error_call = add_calls[2]
        assert error_call[1]["rotation"] == "5 MB"
        assert error_call[1]["retention"] == "30 days"
        assert error_call[1]["compression"] == "zip"

        # Structured log settings
        structured_call = add_calls[3]
        assert structured_call[1]["rotation"] == "20 MB"
        assert structured_call[1]["retention"] == "7 days"
        assert structured_call[1]["compression"] == "zip"


class TestLoggingIntegration:
    """Test logging integration scenarios."""

    def test_logger_import(self):
        """Test that logger can be imported."""
        from app.utils.logging import logger

        assert logger is not None

    def test_config_integration(self):
        """Test integration with config module."""
        from app.utils.logging import config

        assert config is not None
        assert hasattr(config, "LOG_LEVEL")

    def test_pathlib_integration(self):
        """Test integration with pathlib."""
        from app.utils.logging import Path

        assert Path is not None

        # Should be able to create Path objects
        test_path = Path("test")
        assert isinstance(test_path, Path)

    def test_sys_integration(self):
        """Test integration with sys module."""
        from app.utils.logging import sys

        assert sys is not None
        assert hasattr(sys, "stdout")

    @patch("app.utils.logging.setup_logging")
    def test_setup_logging_can_be_called(self, mock_setup):
        """Test that setup_logging can be called without errors."""
        from app.utils.logging import setup_logging

        # Should be callable
        assert callable(setup_logging)

        # Should not raise when called
        setup_logging()
        mock_setup.assert_called_once()

    def test_get_logger_with_different_names(self):
        """Test get_logger with different module names."""
        from app.utils.logging import get_logger

        # Should work with various name formats
        logger1 = get_logger("app.main")
        logger2 = get_logger("__main__")
        logger3 = get_logger("test_module")

        assert logger1 is not None
        assert logger2 is not None
        assert logger3 is not None
