from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env")

    db_user: str = "user"
    db_pass: str = "pass"
    db_name: str = "futures"
    db_host: str = "localhost"
    threshold: float = 0.01
    window_minutes: int = 60

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_pass}@{self.db_host}:5432/{self.db_name}"


settings = Settings()