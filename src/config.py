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
    jwt_secret_key: str = "super-secret-key-change-me"
    telegram_token: str = ""
    telegram_chat_id: str = ""

    @property
    def database_url(self) -> str:
        return f"sqlite+aiosqlite:///./marketpulse.db"


settings = Settings()
