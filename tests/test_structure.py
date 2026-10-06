"""
Tests verifying folder structure, required files, and module importability.
"""

from pathlib import Path
import importlib

BASE_DIR = Path(__file__).resolve().parent.parent

def test_required_files_exist():
    required_files = [
        "requirements.txt",
        ".env.example",
        "README.md",
        "run.py",
        "app/__init__.py",
        "app/main.py",
        "app/config.py",
        "app/api/__init__.py",
        "app/models/__init__.py",
        "app/services/__init__.py",
        "app/platforms/__init__.py",
        "app/database/__init__.py",
        "app/utils/__init__.py",
        "app/utils/logging.py",
        "app/utils/text.py",
        "app/utils/urls.py",
        "app/utils/retry.py",
        "tests/__init__.py"
    ]
    for rel_path in required_files:
        path = BASE_DIR / rel_path
        assert path.exists(), f"Missing required file: {rel_path}"

def test_module_imports():
    modules = [
        "app.config",
        "app.main",
        "app.utils.logging",
        "app.utils.text",
        "app.utils.urls",
        "app.utils.retry",
        "app.api",
        "app.models",
        "app.services",
        "app.platforms",
        "app.database"
    ]
    for mod in modules:
        m = importlib.import_module(mod)
        assert m is not None
