import os


class Settings:
    def __init__(self) -> None:
        self.database_url = os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://postgres:postgres@db:5432/transactions",
        )
        self.redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        self.upload_dir = os.getenv("UPLOAD_DIR", "/app/uploads")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        self.allowed_categories = [
            "Food",
            "Shopping",
            "Travel",
            "Transport",
            "Utilities",
            "Cash Withdrawal",
            "Entertainment",
            "Other",
        ]
        self.domestic_usd_merchants = {"SWIGGY", "OLA", "IRCTC"}


settings = Settings()
