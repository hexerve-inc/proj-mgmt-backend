from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Project Management API"
    DATABASE_URL: str

    # ── SMTP / Email settings ────────────────────────────────────
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = True
    SMTP_FROM_EMAIL: str = "noreply@pmtool.io"
    SMTP_FROM_NAME: str = "PMTool"

    # Master kill-switch: set to True to enable actual email delivery
    EMAIL_ENABLED: bool = False

    # Frontend URL used for building links inside email templates
    FRONTEND_URL: str = "http://localhost:3000"

    # ── Cloudinary settings ──────────────────────────────────────
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
