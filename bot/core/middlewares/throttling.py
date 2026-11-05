"""
میان‌افزار ضد اسپم و کنترل نرخ (Throttling / Cooldown) برای دستورهای اعضا.
"""

from __future__ import annotations

import time
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from ..config import get_settings
from ..utils.format import fa_number


class ThrottlingMiddleware(BaseMiddleware):
    """اعمال محدودیت زمانی بین ارسال دستورات توسط کاربران عادی."""

    def __init__(self) -> None:
        self._user_last_call: dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        settings = get_settings()
        user_id = None

        if isinstance(event, Message) and event.from_user:
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery) and event.from_user:
            user_id = event.from_user.id

        if user_id is None:
            return await handler(event, data)

        # مالکان ربات مشمول محدودیت کول‌داون نمی‌شوند
        if settings.is_owner(user_id):
            return await handler(event, data)

        now = time.monotonic()
        cooldown = settings.member_cmd_cooldown_sec
        last_time = self._user_last_call.get(user_id, 0.0)

        if now - last_time < cooldown:
            remaining = int(cooldown - (now - last_time)) + 1
            msg = f"⏳ لطفاً کمی صبور باشید. امکان ارسال دستور مجدد تا {fa_number(remaining)} ثانیه‌ی دیگر."
            if isinstance(event, Message):
                await event.reply(msg)
            elif isinstance(event, CallbackQuery):
                await event.answer(msg, show_alert=True)
            return None

        self._user_last_call[user_id] = now
        return await handler(event, data)
