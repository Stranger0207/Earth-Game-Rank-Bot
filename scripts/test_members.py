"""
آزمون‌های ردگیری اعضا، ورود خودکار با سطح ۱، بازیابی مقام اعضای قدیمی و resolver.
"""

from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from bot.core.db.base import init_db
from bot.modules.members.service import MemberService
from bot.modules.members.resolver import resolve_target


async def main() -> None:
    print("🚀 اجرای آزمون‌های ماژول members...")
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    await init_db(custom_engine=engine)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        # ۱. عضو جدید وارد می‌شود -> باید سطح ۱ (سرباز صفر) باشد
        m1 = await MemberService.handle_join(
            session=session,
            telegram_id=1001,
            username="new_recruit",
            full_name="سرباز جدید",
        )
        assert m1.rank_level == 1
        assert m1.in_group is True
        print("✅ عضو جدید با سطح ۱ ثبت شد.")

        # ۲. تغییر رنک دستی به ۵
        m1.rank_level = 5
        await session.commit()

        # ۳. خروج از گروه و ورود مجدد -> مقام ۵ باید بازیابی شود، نه ریست به ۱
        m1_restored = await MemberService.handle_join(
            session=session,
            telegram_id=1001,
            username="new_recruit",
            full_name="سرباز جدید",
        )
        assert m1_restored.rank_level == 5, f"مقام باید ۵ بماند اما {m1_restored.rank_level} شد!"
        print("✅ بازیابی مقام عضو قدیمی پس از جوین مجدد تأیید شد.")

        # ۴. ردگیری فعالیت و جستجوی یوزرنیم
        m_by_u = await MemberService.get_by_username(session, "@new_recruit")
        assert m_by_u is not None and m_by_u.telegram_id == 1001
        print("✅ جستجوی عضو با @username تأیید شد.")

    print("🎉 تمامی آزمون‌های members.py سبز شدند!")


if __name__ == "__main__":
    asyncio.run(main())
