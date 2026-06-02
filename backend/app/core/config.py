from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str
    app_version: str
    api_host: str
    api_port: int

    groq_api_key: str
    llm_model: str = "llama-3.3-70b-versatile"

    # Docker/Qdrant
    qdrant_host: str = "qdrant"
    qdrant_port: int = 6333

    # Demo auth
    demo_username: str = "admin"
    demo_password: str = "techsolve_secure_2026"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()