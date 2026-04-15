from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

class Settings(BaseModel):
    """Application settings."""
    app_name: str = "AutoCoder"
    version: str = "1.0.0"
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    
    # Database
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "autocoder"
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Security
    secret_key: str = Field(default="change-me-in-production", min_length=32)
    jwt_expiry_hours: int = 24
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()