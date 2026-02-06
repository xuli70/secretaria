import os


class Settings:
    # MINIMAX AI
    MINIMAX_API_KEY: str = os.getenv("MINIMAX_API_KEY", "")
    MINIMAX_API_URL: str = os.getenv("MINIMAX_API_URL", "https://api.minimax.io/v1")
    MINIMAX_MODEL: str = os.getenv("MINIMAX_MODEL", "MiniMax-M2")

    # Perplexity
    PERPLEXITY_API_KEY: str = os.getenv("PERPLEXITY_API_KEY", "")
    PERPLEXITY_API_URL: str = os.getenv("PERPLEXITY_API_URL", "https://api.perplexity.ai")
    PERPLEXITY_MODEL: str = os.getenv("PERPLEXITY_MODEL", "sonar")

    # Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

    # Auth
    JWT_SECRET: str = os.getenv("JWT_SECRET", "change-me-to-a-random-secret")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

    # App
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
    DATA_DIR: str = os.getenv("DATA_DIR", "/data")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:////data/secretaria.db")

    # Upload
    MAX_UPLOAD_SIZE: int = 20 * 1024 * 1024  # 20 MB

    ALLOWED_EXTENSIONS: set[str] = {
        ".pdf", ".docx", ".xlsx", ".txt",
        ".jpg", ".jpeg", ".png", ".webp",
    }

    DOCUMENT_EXTENSIONS: set[str] = {".pdf", ".docx", ".xlsx", ".txt"}
    IMAGE_EXTENSIONS: set[str] = {".jpg", ".jpeg", ".png", ".webp"}

    MIME_TYPES: dict[str, str] = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".txt": "text/plain",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }


settings = Settings()
