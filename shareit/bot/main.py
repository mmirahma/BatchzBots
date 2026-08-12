"""BachzTab bot entry point."""

import logging
from datetime import time, timezone, timedelta

from telegram.ext import Application
from telegram.request import HTTPXRequest

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

# Vancouver timezone (UTC-7 PDT / UTC-8 PST)
# Using fixed UTC-7 for summer; for year-round accuracy use pytz/zoneinfo
try:
    from zoneinfo import ZoneInfo
    VANCOUVER_TZ = ZoneInfo("America/Vancouver")
except ImportError:
    # Python 3.9 without zoneinfo backport — use fixed UTC-7
    VANCOUVER_TZ = timezone(timedelta(hours=-7))


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

    # Configure robust network connection timeouts (30s) for high latency / network glitches
    request = HTTPXRequest(
        connect_timeout=30.0,
        read_timeout=30.0,
        write_timeout=30.0,
        pool_timeout=30.0,
    )

    app = Application.builder().token(config.bot_token).request(request).post_init(post_init).build()
    app.bot_data["db_path"] = config.db_path

    register_handlers(app)

    # Schedule daily reminder at 6pm Vancouver time
    app.job_queue.run_daily(
        send_daily_reminder,
        time=time(hour=18, minute=0, tzinfo=VANCOUVER_TZ),
        name="daily_reminder",
    )

    logger.info(f"Starting BachzTab bot v{__version__}...")
    app.run_polling(drop_pending_updates=True, bootstrap_retries=-1)


if __name__ == "__main__":
    main()
