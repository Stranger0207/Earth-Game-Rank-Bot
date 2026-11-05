"""
آزمون‌های سرویس ممیزی تگ‌ها و تست سلامت سامانه (Self-Test).
"""

from __future__ import annotations

import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from bot.core.db.base import init_db, set_engine
from bot.core.db.models.member import Member
from bot.modules.audit.service import AuditService


async def main() -> None:
    print("🚀 اجرای آزمون‌های ماژول audit...")
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    await init_db(custom_engine=engine)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        # ساخت یک عضو ناهماهنگ (tag_synced=False)
        m = Member(
            telegram_id=4001,
            username="unsynced_soldier",
            full_name="سرباز ناهماهنگ",
            rank_level=3,
            in_group=True,
            tag_synced=False,
        )
        session.add(m)
        await session.commit()

    mock_bot = AsyncMock()
    mock_bot.set_chat_member_tag.return_value = True

    # اجرای ممیزی
    audit_stats = await AuditService.run_audit(mock_bot)
    assert audit_stats["total_checked"] >= 1
    assert audit_stats["enqueued"] >= 1
    print("✅ ممیزی تگ‌ها و افزودن اعضای ناهماهنگ به صف با موفقیت تأیید شد.")

    # اجرای سلف‌تست سلامت
    mock_me = MagicMock()
    mock_me.id = 99999
    mock_bot.get_me.return_value = mock_me

    mock_chat_member = MagicMock()
    mock_chat_member.status = "administrator"
    mock_chat_member.can_manage_tags = True
    mock_bot.get_chat_member.return_value = mock_chat_member

    mock_chat = MagicMock()
    mock_perms = MagicMock()
    mock_perms.can_edit_tag = False
    mock_chat.permissions = mock_perms
    mock_bot.get_chat.return_value = mock_chat

    report = await AuditService.run_selftest(mock_bot)
    assert report["database"]["ok"] is True
    assert report["bot_admin"]["ok"] is True
    assert report["can_manage_tags"]["ok"] is True
    assert report["group_tag_perm"]["ok"] is True
    print("✅ آزمون سلامت سامانه (Self-Test) با موفقیت تأیید شد.")

    print("🎉 تمامی آزمون‌های audit سبز شدند!")


if __name__ == "__main__":
    asyncio.run(main())
