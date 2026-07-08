import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"

# Create the instance directory if it doesn't exist
INSTANCE_DIR.mkdir(parents=True, exist_ok=True)


class Config:
    # Security
    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "change-this-secret-key-before-production"
    )

    # Database
    database_url = os.environ.get("DATABASE_URL")

    # Railway PostgreSQL compatibility
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace(
            "postgres://",
            "postgresql://",
            1
        )

    SQLALCHEMY_DATABASE_URI = (
        database_url
        or f"sqlite:///{INSTANCE_DIR / 'database.db'}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # CSRF Protection
    WTF_CSRF_ENABLED = True

    # Session Security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Enable only when using HTTPS
    SESSION_COOKIE_SECURE = os.environ.get("FLASK_ENV") == "production"

    # File Upload Limit (16 MB)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024