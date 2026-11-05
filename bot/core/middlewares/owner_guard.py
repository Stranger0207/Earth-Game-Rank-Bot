"""
میان‌افزار محافظت از دستورهای مالک (Owner Guard).
دستورهای حساس مالکان را اعتبارسنجی کرده و درخواست‌های افراد غیرمجاز را بی‌صدا نادیده می‌گیرد.
"""

from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from ..config import get_settings

logger = logging.getLogger(__name__)


class OwnerOnlyMiddleware(BaseMiddleware):
    """رد کردن بی‌صدای پیام‌ها و کال‌بک‌های ارسالی از کاربران غیرمالک."""

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

        if user_id is None or not settings.is_owner(user_id):
            logger.info("درخواست دستور مالک توسط کاربر غیرمجاز %s رد شد.", user_id)
            if isinstance(event, Message):
                if event.chat.type == "private":
                    await event.reply(
                        f"⛔️ <b>دسترسی غیرمجاز</b>\n\n"
                        f"شناسه تلگرام شما: <code>{user_id}</code>\n"
                        f"این شناسه در متغیر <code>OWNER_IDS</code> فایل <code>.env</code> ثبت نشده است."
                    )
            elif isinstance(event, CallbackQuery):
                await event.answer("⛔️ شما مجاز به انجام این عملیات نیستید.", show_alert=True)
            return None

        return await handler(event, data)
