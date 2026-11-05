"""
آزمون‌های جامع پایان فصل: تضمین Idempotency، سقف خودکار ۱۷، بازیکنان جدید، و deduplication.
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
from bot.modules.season.service import SeasonService


async def main() -> None:
    print("🚀 اجرای آزمون‌های ماژول season...")
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    await init_db(custom_engine=engine)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        # ساخت اعضای اولیه برای تست حالات مختلف:
        # ۱. بازیکن سطح ۱۶ (باید بشود ۱۷ - سقف)
        m16 = Member(telegram_id=5001, full_name="سرهنگ دوم تست", rank_level=16, is_player=True)
        # ۲. بازیکن سطح ۱۷ (در سقف است و نباید تغییر کند)
        m17 = Member(telegram_id=5002, full_name="سرهنگ تست", rank_level=17, is_player=True)
        # ۳. بازیکن سطح ۲۰ (ژنرال، نباید تغییر کند)
        m20 = Member(telegram_id=5003, full_name="سپهبد تست", rank_level=20, is_player=True)

        session.add_all([m16, m17, m20])
        await session.commit()

        # لیست بازیکنان فصل شامل:
        # - ۵۰۰۱ (سطح ۱۶)
        # - ۵۰۰۲ (سطح ۱۷)
        # - ۵۰۰۳ (سطح ۲۰)
        # - ۵۰۰۴ (بازیکن کاملاً جدید که در دیتابیس نیست)
        # - ۵۰۰۱ تکراری (جهت تست deduplicate)
        players_payload = [
            {"telegram_id": 5001, "full_name": "سرهنگ دوم تست"},
            {"telegram_id": 5002, "full_name": "سرهنگ تست"},
            {"telegram_id": 5003, "full_name": "سپهبد تست"},
            {"telegram_id": 5004, "full_name": "بازیکن جدید"},
            {"telegram_id": 5001, "full_name": "سرهنگ دوم تست تکراری"},
        ]

        # تست اول: اجرای پیش‌نمایش
        preview = await SeasonService.preview_season(session, players_payload)
        assert preview["total_players"] == 4  # ۵ مورد با ۱ تکراری = ۴ نفر یکتا
        assert preview["promoted_count"] == 2  # ۵۰۰۱ (۱۶->۱۷) و ۵۰۰۴ (جدید ۱->۲)
        assert preview["capped_count"] == 2    # ۵۰۰۲ و ۵۰۰۳
        print("✅ پیش‌نمایش آماری فصل با موفقیت تأیید شد.")

        # تست دوم: اعمال واقعی فصل
        event_id = "test-season-event-1234"
        res1 = await SeasonService.process_season_ended(
            session=session,
            event_id=event_id,
            players=players_payload,
            source="test",
        )
        assert res1["status"] == "processed"
        assert res1["promoted"] == 2
        assert res1["capped"] == 2

        # بررسی وضعیت در دیتابیس
        async with session_factory() as verify_session:
            m16_updated = await verify_session.get(Member, 5001)
            assert m16_updated.rank_level == 17, "سطح ۱۶ باید به ۱۷ ارتقا یافته باشد"

            m17_updated = await verify_session.get(Member, 5002)
            assert m17_updated.rank_level == 17, "سطح ۱۷ باید در ۱۷ باقی بماند"

            m20_updated = await verify_session.get(Member, 5003)
            assert m20_updated.rank_level == 20, "سطح ۲۰ نباید خودکار ارتقا یابد"

            m_new = await verify_session.get(Member, 5004)
            assert m_new is not None
            assert m_new.rank_level == 2, "بازیکن جدید باید از ۱ به ۲ ارتقا یابد"
            assert m_new.seasons_participated == 1

        print("✅ اعمال تغییرات در سطوح، سقف ۱۷ و ثبت بازیکن جدید تأیید شد.")

        # تست سوم: تضمین Idempotency (ارسال دوباره همان event_id)
        res2 = await SeasonService.process_season_ended(
            session=session,
            event_id=event_id,
            players=players_payload,
            source="test",
        )
        assert res2["status"] == "already_processed"
        print("✅ تضمین Idempotency (عدم پردازش مجدد با event_id تکراری) تأیید شد.")

    print("🎉 تمامی آزمون‌های season.py سبز شدند!")


if __name__ == "__main__":
    asyncio.run(main())
