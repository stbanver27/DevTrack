from datetime import timedelta

class Settings:
    APP_NAME: str = "DevTrack"
    APP_VERSION: str = "1.0.0"
    SECRET_KEY: str = "devtrack-super-secret-key-change-in-production-2024"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 hours
    DATABASE_URL: str = "sqlite:///./devtrack.db"
    ADMIN_EMAIL: str = "admin@devtrack.io"
    ADMIN_PASSWORD: str = "Admin2024!"

settings = Settings()
