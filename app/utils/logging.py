import logging
import sys
from pathlib import Path
from app.config import settings

class CustomFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None):
        super().__init__(
            fmt or "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d]: %(message)s",
            datefmt=datefmt or "%Y-%m-%d %H:%M:%S"
        )

def setup_logging(
    name: str = "ai_job_search",
    log_level: str = None,
    log_to_file: bool = False,
    log_filename: str = None
) -> logging.Logger:
    logger = logging.getLogger(name)
    
    level_str = log_level or getattr(settings, "LOG_LEVEL", "INFO")
    level = getattr(logging, level_str.upper(), logging.INFO)
    logger.setLevel(level)

    formatter = CustomFormatter()

    if not logger.handlers:
        if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
            try:
                sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    if log_to_file and log_filename:
        log_path = Path(log_filename)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

def get_logger(name: str = None) -> logging.Logger:
    if not name:
        return setup_logging()
    if not name.startswith("ai_job_search.") and name != "ai_job_search":
        full_name = f"ai_job_search.{name}"
    else:
        full_name = name
    return setup_logging(full_name)

setup_logger = setup_logging
logger = setup_logging()
