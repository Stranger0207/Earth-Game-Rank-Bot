"""
آزمون‌های صف تگ‌ها، مدیریت خطاهای تلگرام، خطای ادمین و عدم کرش سامانه.
"""

from __future__ import annotations

import asyncio
import os
import sys
from unittest.mock import AsyncMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from aiogram.exceptions import TelegramBadRequest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from bot.core.db.base import init_db
from bot.modules.tags.service import TagService


async def main() -> None:
    print("🚀 اجرای آزمون‌های ماژول tags...")
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    await init_db(custom_engine=engine)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        # ۱. تست افزودن به صف تگ
        item = await TagService.enqueue_tag(
            session=session,
            telegram_id=3001,
            target_tag="سرهنگ",
        )
        assert item.target_tag == "سرهنگ"
        assert item.status == "pending"
        print("✅ صف‌بندی اولیه تگ با موفقیت انجام شد.")

    # ۲. شبیه‌سازی متد set_chat_member_tag با Mock Bot
    mock_bot = AsyncMock()

    # حالت الف: موفقیت
    mock_bot.set_chat_member_tag.return_value = True
    ok, err = await TagService.apply_tag_direct(
        bot=mock_bot,
        chat_id=-100123456,
        user_id=3001,
        tag="سرهنگ",
    )
    assert ok is True
    assert err is None
    print("✅ ارسال موفقیت‌آمیز تگ به تلگرام تأیید شد.")

    # حالت ب: خطای ادمین بودن کاربر در گروه
    mock_bot.set_chat_member_tag.side_effect = TelegramBadRequest(
        method="setChatMemberTag",
        message="Bad Request: user is an administrator of the chat",
    )
    ok_admin, err_admin = await TagService.apply_tag_direct(
        bot=mock_bot,
        chat_id=-100123456,
        user_id=3001,
        tag="سرهنگ",
    )
    assert ok_admin is False
    assert "ادمین" in err_admin
    print("✅ مدیریت خطای کاربر ادمین بدون کرش کردن سامانه تأیید شد.")

    print("🎉 تمامی آزمون‌های tags.py سبز شدند!")


if __name__ == "__main__":
    asyncio.run(main())
