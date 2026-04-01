from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Evidence Adjudicator"
    env: str = "dev"
    database_url: str = "sqlite:///./evidence_adjudicator.db"
    log_level: str = "INFO"

    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"

    pubmed_email: str = "demo@example.com"
    pubmed_tool: str = "evidence-adjudicator"
    pubmed_api_key: str | None = None
    pubmed_max_results: int = 3

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
