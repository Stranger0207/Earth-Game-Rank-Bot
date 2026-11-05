"""
آزمون‌های فاز ۰: بررسی بارگذاری تنظیمات، اتصال دیتابیس، EventBus و کمکی‌های متنی و UI.
"""

from __future__ import annotations

import asyncio
import os
import sys

# اطمینان از قرار داشتن ریشه پروژه در پایتون‌پث
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.ext.asyncio import create_async_engine
from bot.core.config import Settings
from bot.core.db.base import init_db, Base
from bot.core.db.models import Member, RankHistory, SeasonEvent
from bot.core.events import EventBus, RankChanged
from bot.core.utils.format import fa_number, split_text
from bot.core.utils.html import clean_html, bold
from bot.core.utils.ui import header, render_progress_bar


async def test_config() -> None:
    settings = Settings(
        bot_token="test_token",
        owner_ids="111, 222, 333",
        target_chat_id=-100123456789,
    )
    assert settings.owner_ids == [111, 222, 333]
    assert settings.is_owner(222) is True
    assert settings.is_owner(999) is False
    print("✅ تست تنظیمات با موفقیت پاس شد.")


async def test_db_init() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    await init_db(custom_engine=engine)
    assert "members" in Base.metadata.tables
    assert "rank_history" in Base.metadata.tables
    assert "season_events" in Base.metadata.tables
    print("✅ تست ساخت دیتابیس و جداول با موفقیت پاس شد.")


async def test_event_bus() -> None:
    bus = EventBus()
    received = []

    async def on_rank_changed(event: RankChanged) -> None:
        received.append(event)

    bus.subscribe(RankChanged, on_rank_changed)
    evt = RankChanged(
        telegram_id=123456,
        old_level=1,
        new_level=2,
        source="season",
        reason="ارتقای فصلی",
    )
    await bus.emit(evt)
    assert len(received) == 1
    assert received[0].telegram_id == 123456
    assert received[0].new_level == 2
    print("✅ تست گذرگاه رویداد (EventBus) با موفقیت پاس شد.")


def test_utils() -> None:
    assert fa_number(12345) == "۱۲۳۴۵"
    assert clean_html("<script>alert('xss')</script>") == "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"
    assert bold("عنوان") == "<b>عنوان</b>"
    
    prog = render_progress_bar(0.5, length=4)
    assert prog == "▰▰▱▱"
    
    long_text = "خط اول\n" * 1000
    chunks = split_text(long_text, max_length=100)
    for c in chunks:
        assert len(c) <= 100
    print("✅ تست کمکی‌های متنی و UI با موفقیت پاس شد.")


async def main() -> None:
    print("🚀 شروع آزمون‌های فاز ۰...")
    await test_config()
    await test_db_init()
    await test_event_bus()
    test_utils()
    print("🎉 تمام آزمون‌های فاز ۰ سبز شدند!")


if __name__ == "__main__":
    asyncio.run(main())
