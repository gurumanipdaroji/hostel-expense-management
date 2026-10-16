import os
import sys
from pathlib import Path
from typing import List
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve backend directory and project root directory
BACKEND_DIR = Path(__file__).resolve().parent.parent  # .../backend
ROOT_DIR = BACKEND_DIR.parent                          # .../hostelexpensemanagament

# Ensure backend directory is in sys.path so 'import app...' works from any working directory
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Locate .env file (check backend/.env first, then root .env)
env_file_paths = []
if (BACKEND_DIR / ".env").exists():
    env_file_paths.append(BACKEND_DIR / ".env")
if (ROOT_DIR / ".env").exists():
    env_file_paths.append(ROOT_DIR / ".env")

# Preload discovered .env files into os.environ
for env_path in env_file_paths:
    load_dotenv(dotenv_path=env_path, override=True)


class Settings(BaseSettings):
    """
    Application configuration settings.
    Prioritizes environment variables, then .env file, then safe local defaults.
    """
    APP_NAME: str = "Hostel Expense Management System"
    
    # Database URL from environment or .env; defaults to SQLite for local development
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./hostel_management.db"
    )
    
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", 
        "dev_super_secret_hostel_expense_key_change_in_production"
    )
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    
    # Comma-separated list of origins for CORS
    CORS_ORIGINS: str = os.getenv(
        "CORS_ORIGINS", 
        "http://localhost:5500,http://127.0.0.1:5500,http://localhost:8000,http://127.0.0.1:8000,http://localhost:3000"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        if not self.CORS_ORIGINS:
            return ["http://localhost:5500", "http://127.0.0.1:5500", "http://127.0.0.1:8000"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip() and origin.strip() != "*"]

    @property
    def resolved_database_url(self) -> str:
        """
        Resolves relative SQLite paths against BACKEND_DIR so that the database file
        is always consistently located, whether running from the repository root or backend/.
        MySQL and in-memory URLs are preserved unchanged.
        """
        url = self.DATABASE_URL.strip()
        if url.startswith("sqlite:///") and not url.startswith("sqlite:////") and url != "sqlite:///:memory:":
            raw_path = url[len("sqlite:///"):]
            if raw_path.startswith("./") or raw_path.startswith(".\\"):
                raw_path = raw_path[2:]
            resolved_db = (BACKEND_DIR / raw_path).resolve()
            return f"sqlite:///{resolved_db.as_posix()}"
        return url

    model_config = SettingsConfigDict(
        env_file=[str(p) for p in env_file_paths] if env_file_paths else ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
