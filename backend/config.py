import os


class Settings:
    # MINIMAX AI
    MINIMAX_API_KEY: str = os.getenv("MINIMAX_API_KEY", "")
    MINIMAX_API_URL: str = os.getenv("MINIMAX_API_URL", "https://api.minimax.io/v1")
    MINIMAX_MODEL: str = os.getenv("MINIMAX_MODEL", "MiniMax-M2")

    # Perplexity
    PERPLEXITY_API_KEY: str = os.getenv("PERPLEXITY_API_KEY", "")
    PERPLEXITY_API_URL: str = os.getenv("PERPLEXITY_API_URL", "https://api.perplexity.ai")

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


settings = Settings()
