import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
load_dotenv(BASE_DIR / ".env")

class Settings:
    PROJECT_NAME: str = "10X AI Job Search & Application Assistant"
    VERSION: str = "1.0.0"
    
    # API Keys
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
    
    # SMTP Email Configuration
    SMTP_SENDER_EMAIL: str = os.getenv("SMTP_SENDER_EMAIL", "")
    SMTP_SENDER_PASSWORD: str = os.getenv("SMTP_SENDER_PASSWORD", "")
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))

    # Demo Mode
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "false").lower() in ("true", "1", "t")
    
    # Storage Paths
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = BASE_DIR / "data"
    EXPORTS_DIR: Path = BASE_DIR / "exports"
    DATABASE_PATH: Path = BASE_DIR / os.getenv("DATABASE_PATH", "data/job_search.db")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Server configuration
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))

    @classmethod
    def ensure_directories(cls):
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

settings = Settings()
settings.ensure_directories()

def get_settings() -> Settings:
    return settings

reload_settings = get_settings
