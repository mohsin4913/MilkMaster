import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class Config:
    # Security
    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "change-this-secret-key-before-production"
    )

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'instance' / 'database.db'}",
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # CSRF Protection
    WTF_CSRF_ENABLED = True

    # Session Security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # These should only be enabled when using HTTPS
    SESSION_COOKIE_SECURE = os.environ.get("FLASK_ENV") == "production"

    # File Upload Limits (16 MB)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024