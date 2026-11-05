"""
میان‌افزار کنترل دسترسی گروه (Group Access Guard).
اطمینان از اینکه ربات تنها در سوپرگروه مجاز (TARGET_CHAT_ID) یا چت خصوصی فعالیت می‌کند.
"""

from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.enums import ChatType
from aiogram.types import CallbackQuery, Message, TelegramObject

from ..config import get_settings

logger = logging.getLogger(__name__)


class GroupAccessMiddleware(BaseMiddleware):
    """جلوگیری از فعالیت ربات در گروه‌های غیرمجاز و خروج خودکار در صورت نیاز."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        settings = get_settings()
        chat = None

        if isinstance(event, Message):
            chat = event.chat
        elif isinstance(event, CallbackQuery) and event.message:
            chat = event.message.chat

        if chat and chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
            if chat.id != settings.target_chat_id:
                logger.warning(
                    "پیام در گروه غیرمجاز دریاف شد: id=%s, title=%s", chat.id, chat.title
                )
                if settings.auto_leave_unauthorized_groups:
                    try:
                        bot = data.get("bot")
                        if bot:
                            await bot.leave_chat(chat.id)
                            logger.info("ربات از گروه غیرمجاز %s خارج شد.", chat.id)
                    except Exception as exc:
                        logger.error("خطا در خروج از گروه غیرمجاز %s: %s", chat.id, exc)
                return None

        return await handler(event, data)
