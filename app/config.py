from functools import lru_cache
from pydantic import BaseModel
from dotenv import load_dotenv, find_dotenv
from pathlib import Path
import os

root_env = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=root_env if root_env.exists() else find_dotenv())

class Settings(BaseModel):
    APP_ENV: str = os.getenv("APP_ENV", "dev")

    # Local LLM (Ollama)
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "phi")

    # OpenAI (kept for future switch)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")  # empty string, not None
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


@lru_cache
def get_settings() -> Settings:
    return Settings()