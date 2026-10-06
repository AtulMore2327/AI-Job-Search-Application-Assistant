"""
Tests for logging module.
"""

import logging
from pathlib import Path
from app.utils.logging import setup_logging, get_logger, CustomFormatter

def test_custom_formatter():
    formatter = CustomFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Test log message",
        args=(),
        exc_info=None
    )
    formatted = formatter.format(record)
    assert "INFO" in formatted
    assert "test_logger:10" in formatted
    assert "Test log message" in formatted

def test_setup_logging(tmp_path):
    log_file = tmp_path / "test.log"
    logger = setup_logging(log_level="DEBUG", log_to_file=True, log_filename=str(log_file))
    
    assert logger.level == logging.DEBUG
    assert len(logger.handlers) >= 1
    
    logger.info("Sample test output")
    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8")
    assert "Sample test output" in content

def test_get_logger():
    logger = get_logger("my_component")
    assert logger.name == "ai_job_search.my_component"
