"""
آزمون‌های سرویس مقام‌ها: ارتقا، تنزل، ثبت در تاریخچه و صدور رویداد RankChanged.
"""

from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from bot.core.db.base import init_db
from bot.core.events import RankChanged, event_bus
from bot.modules.ranks.service import RankService


async def main() -> None:
    print("🚀 اجرای آزمون‌های ماژول ranks...")
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    await init_db(custom_engine=engine)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    events_received: list[RankChanged] = []

    async def on_rank_changed(event: RankChanged) -> None:
        events_received.append(event)

    event_bus.subscribe(RankChanged, on_rank_changed)

    async with session_factory() as session:
        # ۱. ارتقای عضو از سطح پیش‌فرض به ۲
        m, old_lvl, new_lvl = await RankService.promote(
            session=session,
            telegram_id=2001,
            delta=2,
            reason="شجاعت در خط مقدم",
            actor_id=999,
        )
        assert old_lvl == 1
        assert new_lvl == 3
        assert len(events_received) == 1
        assert events_received[-1].new_level == 3
        print("✅ ارتقای دستی و انتشار رویداد با موفقیت تأیید شد.")

        # ۲. انتصاب مستقیم مقام (set_rank)
        m2, old_lvl2, new_lvl2 = await RankService.set_rank(
            session=session,
            telegram_id=2001,
            target_level=18,  # سرتیپ
            reason="فرمان مستقیم مالک",
        )
        assert old_lvl2 == 3
        assert new_lvl2 == 18
        print("✅ انتصاب مستقیم مقام به ۱۸ (سرتیپ) تأیید شد.")

        # ۳. تنزل مقام
        m3, old_lvl3, new_lvl3 = await RankService.demote(
            session=session,
            telegram_id=2001,
            delta=1,
            reason="تخلف انضباطی",
        )
        assert old_lvl3 == 18
        assert new_lvl3 == 17
        print("✅ تنزل مقام به ۱۷ تأیید شد.")

    print("🎉 تمامی آزمون‌های ranks_service.py سبز شدند!")


if __name__ == "__main__":
    asyncio.run(main())
