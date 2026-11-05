"""
رجیستری و بارگذاری ماژولار ماژول‌های ربات بر اساس تنظیمات ENABLED_MODULES.
"""

from __future__ import annotations

import importlib
import logging
from dataclasses import dataclass
from typing import Any

from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .config import Settings, get_settings
from .events import EventBus, event_bus
from .loader import bot, dp, scheduler

logger = logging.getLogger(__name__)

# فهرست پیش‌فرض تمامی ماژول‌های سیستم به ترتیب بارگذاری
ALL_MODULES: list[str] = [
    "members",
    "ranks",
    "tags",
    "achievements",
    "cards",
    "announce",
    "season",
    "roster",
    "owner_panel",
    "member_commands",
    "audit",
    "export",
    "webapi",
]


@dataclass
class AppContext:
    """کانتکست اشتراکی که به هر ماژول در متد setup تزریق می‌شود."""

    bot: Bot
    dp: Dispatcher
    scheduler: AsyncIOScheduler
    settings: Settings
    event_bus: EventBus


def load_modules(custom_modules: list[str] | None = None) -> list[str]:
    """
    بارگذاری و فعال‌سازی ماژول‌های مشخص‌شده در تنظیمات.
    هر ماژول با فراخوانی تابع setup(ctx) در ماژول مربوطه فعال می‌گردد.
    """
    settings = get_settings()
    target_modules = custom_modules if custom_modules is not None else settings.enabled_modules

    if not target_modules:
        target_modules = ALL_MODULES

    ctx = AppContext(
        bot=bot,
        dp=dp,
        scheduler=scheduler,
        settings=settings,
        event_bus=event_bus,
    )

    loaded: list[str] = []
    for mod_name in target_modules:
        full_path = f"bot.modules.{mod_name}"
        try:
            mod = importlib.import_module(full_path)
            if hasattr(mod, "setup"):
                mod.setup(ctx)
                loaded.append(mod_name)
                logger.info("ماژول '%s' با موفقیت بارگذاری شد.", mod_name)
            else:
                logger.warning("ماژول '%s' فاقد تابع setup است.", full_path)
        except Exception as exc:
            logger.exception("خطا در بارگذاری ماژول '%s': %s", full_path, exc)

    return loaded
