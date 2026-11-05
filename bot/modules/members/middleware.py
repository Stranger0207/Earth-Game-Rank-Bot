"""
میان‌افزار ردگیری فعالیت و مشخصات اعضای گروه (بدون متوقف کردن پیام‌ها).
"""

from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.enums import ChatType
from aiogram.types import Message, TelegramObject

from ...core.db.base import get_session
from .service import MemberService

logger = logging.getLogger(__name__)


class MemberTrackingMiddleware(BaseMiddleware):
    """به‌روزرسانی خودکار هویت و زمان حضور اعضا هنگام ارسال هر پیام در گروه."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Message) and event.from_user and not event.from_user.is_bot:
            # اگر پیام سرویسی عضو جدید بود
            if event.new_chat_members:
                for new_u in event.new_chat_members:
                    if not new_u.is_bot:
                        async for session in get_session():
                            await MemberService.handle_join(
                                session=session,
                                telegram_id=new_u.id,
                                username=new_u.username,
                                full_name=new_u.full_name,
                            )
            elif event.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
                # پیام معمولی در گروه
                async for session in get_session():
                    await MemberService.track_activity(
                        session=session,
                        telegram_id=event.from_user.id,
                        username=event.from_user.username,
                        full_name=event.from_user.full_name,
                        is_in_group=True,
                    )

        # ارسال پیام به هندلرهای بعدی تا هیچ دستوری بلاک نشود
        return await handler(event, data)
