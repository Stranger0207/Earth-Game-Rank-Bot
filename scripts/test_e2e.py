"""
آزمون انتها به انتها (End-to-End Simulation):
از دریافت وب‌هوک پایان فصل با امضای HMAC تا تراکنش دیتابیس، صف تگ تلگرام و اعطای نشان.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from bot.core.db.base import init_db
from bot.core.db.models.achievement import Achievement
from bot.core.db.models.member import Member
from bot.core.db.models.tag_queue import TagQueueItem
from bot.core.security import generate_hmac_signature, verify_hmac_request
from bot.modules.season.service import SeasonService
from bot.modules.tags.service import on_rank_changed_handler
from bot.modules.achievements.engine import on_rank_changed_achievement_listener
from bot.core.events import RankChanged, event_bus


async def main() -> None:
    print("🚀 آغاز آزمون یکپارچه انتها به انتها (E2E)...")
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    await init_db(custom_engine=engine)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    # اتصال شنوندگان رویداد تغییر رتبه
    event_bus.subscribe(RankChanged, on_rank_changed_handler)
    event_bus.subscribe(RankChanged, on_rank_changed_achievement_listener)

    # ۱. تولید داده‌های وب‌هوک و امضای HMAC
    secret = "e2e_secret_key_very_safe_1234567890_32bytes"
    payload_dict = {
        "event_id": "e2e-season-event-9999",
        "event_type": "season_ended",
        "players": [
            {"telegram_id": 8801, "username": "hero_one", "full_name": "قهرمان اول", "country": "ایران"},
            {"telegram_id": 8802, "username": "hero_two", "full_name": "قهرمان دوم", "country": "آلمان"},
        ],
    }
    raw_body = json.dumps(payload_dict, ensure_ascii=False)
    now_ts = int(time.time())
    sig = generate_hmac_signature(secret, now_ts, raw_body)

    # ۲. مرحله امنیت و اعتبارسنجی امضا
    auth = verify_hmac_request(
        received_signature=sig,
        received_timestamp=str(now_ts),
        raw_body=raw_body,
        custom_secret=secret,
    )
    assert auth.is_valid is True
    print("✅ مرحله ۱ (امنیت): اعتبارسنجی امضا و تایم‌استمپ درخواست تأیید شد.")

    # ۳. مرحله سرویس فصل و تراکنش پایگاه داده
    async with session_factory() as session:
        result = await SeasonService.process_season_ended(
            session=session,
            event_id=payload_dict["event_id"],
            players=payload_dict["players"],
            source="e2e_test",
            payload_raw=raw_body,
        )
        assert result["status"] == "processed"
        assert result["promoted"] == 2
        print("✅ مرحله ۲ (تراکنش DB): پردازش اتمام فصل و ارتقای اعضا با موفقیت انجام شد.")

    # ۴. بررسی پیامدهای رویدادها (صف تگ و نشان‌ها)
    async with session_factory() as session:
        m1 = await session.get(Member, 8801)
        assert m1 is not None
        assert m1.rank_level == 2  # از ۱ به ۲ ارتقا یافت
        assert m1.seasons_participated == 1

        # بررسی قرار گرفتن در صف تگ
        tags_in_queue = (await session.execute(
            TagQueueItem.__table__.select().where(TagQueueItem.telegram_id == 8801)
        )).fetchall()
        assert len(tags_in_queue) >= 1
        print("✅ مرحله ۳ (صف تگ): تگ جدید کاربر در صف پایدار تلگرام قرار گرفت.")

        # بررسی اعطای خودکار نشان
        achievements = (await session.execute(
            Achievement.__table__.select().where(Achievement.telegram_id == 8801)
        )).fetchall()
        assert len(achievements) >= 1  # نشان first_step باید اعطا شده باشد
        print("✅ مرحله ۴ (دستاوردها): نشان 'نخستین گام' با موفقیت به کاربر اعطا شد.")

    print("🎉 آزمون جامع انتها به انتها (E2E) با موفقیت کامل سبز شد!")


if __name__ == "__main__":
    asyncio.run(main())
