import os
from dataclasses import dataclass


@dataclass
class Config:
    bot_token: str
    db_path: str


def get_config() -> Config:
    bot_token = os.environ.get("BACHZTAB_BOT_TOKEN", "")
    raw_db_path = os.environ.get("BACHZTAB_DB_PATH", "bachztab.db")
    db_path = os.path.abspath(os.path.expanduser(raw_db_path))

    # If specified db_path parent directory is not writable (e.g. stale env var on another machine),
    # fallback to local 'bachztab.db' in the current working directory.
    parent = os.path.dirname(db_path)
    if parent:
        check_dir = parent
        while check_dir and check_dir != "/" and not os.path.exists(check_dir):
            check_dir = os.path.dirname(check_dir)
        if check_dir and not os.access(check_dir, os.W_OK):
            db_path = os.path.abspath("bachztab.db")

    return Config(bot_token=bot_token, db_path=db_path)
