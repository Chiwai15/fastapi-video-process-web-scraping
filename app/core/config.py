import os
from functools import lru_cache
from typing import Dict
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # API settings
    API_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Video Processing Service"
    DEBUG: bool = True

    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    CACHE_TTL: int = 600  # in seconds

    # Concurrency settings
    MAX_WORKERS: int = Field(        
        default_factory=lambda: min(
            16,                     # Upper bound
            max(4, os.cpu_count())  # Lower bound of 4, but scale with CPU count
        )
    )

    # Media settings
    MEDIA_DIR: str = "app/media"
    OUTPUT_DIR: str = "app/media/output"
    FONT_PATH: str = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" 
    DEFAULT_BG_IMAGE: str = "app/media/default_bg.jpg"

    # Scraper settings
    SCIENCE_NEWS_URL: str = "https://www.sciencenews.org/"

    # .env 
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    def get_redis_uri(self) -> str:
        """Return a full Redis URI."""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    def get_media_paths(self) -> Dict[str, str]:
        """Return all relevant media file paths."""
        return {
            "media_dir": self.MEDIA_DIR,
            "output_dir": self.OUTPUT_DIR,
            "font_path": "/usr/share/fonts/truetype/" + self.FONT_PATH,
            "default_bg": self.DEFAULT_BG_IMAGE,
        }


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings object."""
    return Settings()
