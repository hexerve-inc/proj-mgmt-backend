from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Project Management API"
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/proj_mgmt_db"
    
    class Config:
        env_file = ".env"

settings = Settings()
