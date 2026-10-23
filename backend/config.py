"""DentSloth – Central Configuration Loader."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # App
    app_env: str = "development"
    demo_mode: bool = True
    log_level: str = "INFO"

    # MongoDB
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db: str = "dentsloth"

    # LLM
    llm_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gemma3:4b"
    gemma_api_key: str = ""

    # TabPFN
    tabpfn_mode: str = "local"
    tabpfn_api_key: str = ""

    # Embedding
    embed_provider: str = "ollama"
    embed_model: str = "nomic-embed-text"

    # Upload
    max_upload_mb: int = 10

    # CORS
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def is_demo(self) -> bool:
        return self.demo_mode


@lru_cache
def get_settings() -> Settings:
    return Settings()
