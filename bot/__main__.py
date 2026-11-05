"""
نقطه ورود و اجرای اصلی ربات مقام (Rank Bot).
"""

from __future__ import annotations

import asyncio
import logging
import sys

from aiogram.enums import UpdateType

from .core.config import get_settings
from .core.db.base import init_db
from .core.loader import bot, dp, scheduler
from .core.middlewares.group_access import GroupAccessMiddleware
from .core.registry import load_modules

# پیکربندی استاندارد لاگ‌ها
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s : %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("rank_bot")


async def main() -> None:
    """راه‌اندازی چرخه حیات ربات."""
    settings = get_settings()
    logger.info("در حال آغاز به کار ربات مقام (Rank Bot v1.0.0)...")

    # ۱. راه‌اندازی و بررسی جداول پایگاه داده
    logger.info("در حال بررسی و آماده‌سازی پایگاه داده...")
    await init_db()
    logger.info("پایگاه داده با موفقیت متصل و راه‌اندازی شد.")

    # ۲. ثبت میان‌افزارهای سراسری
    dp.message.middleware(GroupAccessMiddleware())
    dp.callback_query.middleware(GroupAccessMiddleware())

    # ۳. بارگذاری ماژولار ماژول‌ها
    loaded = load_modules()
    logger.info("ماژول‌های فعال بارگذاری شدند: %s", ", ".join(loaded))

    # ۴. شروع زمان‌بند کارها (Scheduler)
    scheduler.start()
    logger.info("زمان‌بند APScheduler فعال گردید.")

    # ۵. اجرای Polling با نظارت بر آپدیت‌های عضویت گروه و پیام‌ها
    allowed_updates = [
        UpdateType.MESSAGE,
        UpdateType.CALLBACK_QUERY,
        UpdateType.CHAT_MEMBER,
        UpdateType.MY_CHAT_MEMBER,
    ]

    try:
        logger.info("ربات آماده دریافت پیام‌ها در گروه %s می‌باشد.", settings.target_chat_id)
        # حذف وب‌هوک‌های قبلی در صورت وجود
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=allowed_updates)
    finally:
        logger.info("در حال متوقف‌سازی ربات و بستن کانکشن‌ها...")
        scheduler.shutdown(wait=False)
        await bot.session.close()
        logger.info("ربات با موفقیت خاموش شد.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("اجرای برنامه توسط کاربر متوقف شد.")
