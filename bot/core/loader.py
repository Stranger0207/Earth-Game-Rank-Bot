"""
بارگذاری و مقداردهی اشیای اصلی: Bot، Dispatcher و APScheduler.
"""

from __future__ import annotations

import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# توکن ربات (در صورت خالی بودن توکن تست قرار می‌گیرد تا ساخت اولیه اشیا در تست‌ها کرش نکند)
_token = settings.bot_token or "123456789:AAG_DUMMY_TOKEN_FOR_TESTS_ONLY_xyz"

bot = Bot(
    token=_token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)

storage = MemoryStorage()
dp = Dispatcher(storage=storage)

scheduler = AsyncIOScheduler(timezone=settings.tz)
