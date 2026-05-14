from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Gemini
    gemini_api_key: str

    # Phoenix
    phoenix_api_key: str = ""
    phoenix_collector_endpoint: str = "https://app.phoenix.arize.com"

    # GitHub
    github_token: str
    github_test_repo: str

    # App config
    app_env: str = "development"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
