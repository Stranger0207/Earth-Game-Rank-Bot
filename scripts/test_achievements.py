"""
آزمون‌های سیستم نشان‌ها، بررسی شرایط احراز و پیشگیری از اعطای تکراری.
"""

from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from bot.core.db.base import init_db
from bot.core.db.models.member import Member
from bot.modules.achievements.engine import AchievementEngine


async def main() -> None:
    print("🚀 اجرای آزمون‌های ماژول achievements...")
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    await init_db(custom_engine=engine)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        member = Member(
            telegram_id=6001,
            full_name="رزمنده شایسته",
            rank_level=2,
            seasons_participated=3,
        )
        session.add(member)
        await session.commit()

        # ارزیابی عضو: باید نشان first_step و veteran_3 را دریافت کند
        awarded = await AchievementEngine.evaluate_member(session, member)
        assert "first_step" in awarded
        assert "veteran_3" in awarded
        print("✅ اعطای خودکار نشان‌های 'نخستین گام' و 'کهنه‌سرباز ۳ فصل' تأیید شد.")

        # ارزیابی مجدد: نباید نشان تکراری اعطا شود
        awarded_again = await AchievementEngine.evaluate_member(session, member)
        assert len(awarded_again) == 0
        print("✅ پیشگیری از اعطای تکراری نشان‌ها تأیید شد.")

        # ارتقا به سرهنگی و ارزیابی
        member.rank_level = 17
        awarded_colonel = await AchievementEngine.evaluate_member(session, member)
        assert "colonel_achieved" in awarded_colonel
        print("✅ اعطای نشان 'سرهنگ میدان' تأیید شد.")

        # ارتقای دستی با دلیل: نشان افتخار فرماندهی
        awarded_honor = await AchievementEngine.evaluate_member(
            session, member, recent_reason="شجاعت فوق‌العاده", recent_source="manual"
        )
        assert "commander_honor" in awarded_honor
        print("✅ اعطای نشان 'افتخار فرماندهی' تأیید شد.")

    print("🎉 تمامی آزمون‌های achievements.py سبز شدند!")


if __name__ == "__main__":
    asyncio.run(main())
