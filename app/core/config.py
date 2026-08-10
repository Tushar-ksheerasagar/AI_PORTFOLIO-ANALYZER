import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    PORT: int = 8000
    HOST: str = "127.0.0.1"
    
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/portfolio_db"
    
    JWT_SECRET_KEY: str = "supersecretjwtkeychangethisinproduction12345"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    MISTRAL_API_KEY: str = "your_mistral_api_key_here"
    MISTRAL_MODEL: str = "mistral-large-latest"

settings = Settings()
