import os
from dataclasses import dataclass


@dataclass
class Config:
    bot_token: str
    db_path: str


def get_config() -> Config:
    bot_token = os.environ.get("BACHZTAB_BOT_TOKEN", "")
    db_path = os.environ.get("BACHZTAB_DB_PATH", "bachztab.db")
    return Config(bot_token=bot_token, db_path=db_path)
