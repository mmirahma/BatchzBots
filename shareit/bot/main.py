"""BachzTab bot entry point."""

import logging
from datetime import time

from telegram.ext import Application

from config import get_config
from bot import __version__
from bot.db import init_db
from bot.handlers import register_handlers
from bot.reminder import send_daily_reminder

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def post_init(application: Application) -> None:
    """Initialize database after bot starts."""
    db_path = application.bot_data["db_path"]
    await init_db(db_path)
    logger.info(f"Database initialized at {db_path}")


def main() -> None:
    """Start the bot."""
    config = get_config()

    if not config.bot_token:
        logger.error("BACHZTAB_BOT_TOKEN environment variable not set!")
        return

    app = Application.builder().token(config.bot_token).post_init(post_init).build()
    app.bot_data["db_path"] = config.db_path

    register_handlers(app)

    # Schedule daily reminder at 18:00 local time
    app.job_queue.run_daily(
        send_daily_reminder,
        time=time(hour=18, minute=0),
        name="daily_reminder",
    )

    logger.info(f"Starting BachzTab bot v{__version__}...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
