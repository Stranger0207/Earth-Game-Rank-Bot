"""
هندلر دستور /export جهت تولید و ارسال خروجی CSV سازگار با اکسل برای مالکان.
"""

from __future__ import annotations

import csv
import io
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message
from sqlalchemy import select

from ...core.db.base import get_session, utcnow
from ...core.db.models.member import Member
from ...core.middlewares.owner_guard import OwnerOnlyMiddleware
from ...core.utils.format import fa_number
from ...domain.ranks import get_rank

router = Router(name="export")
router.message.middleware(OwnerOnlyMiddleware())


@router.message(Command("export"))
async def cmd_export(message: Message) -> None:
    """خروجی CSV از وضعیت تمام اعضا و مقام‌ها با انکودینگ UTF-8-SIG (سازگار با اکسل)."""
    status_msg = await message.reply("⏳ در حال استخراج داده‌ها و تولید فایل اکسل/CSV...")

    async for session in get_session():
        stmt = select(Member).order_by(Member.rank_level.desc(), Member.rank_reached_at.asc())
        res = await session.execute(stmt)
        members = list(res.scalars().all())

        output = io.StringIO()
        writer = csv.writer(output)

        # سرستون‌های فایل CSV
        writer.writerow([
            "Telegram ID",
            "Username",
            "Full Name",
            "Rank Level",
            "Rank Title",
            "Tier",
            "Seasons Participated",
            "Is Player",
            "In Group",
            "Tag Synced",
            "Rank Reached At",
            "First Seen At",
        ])

        for m in members:
            r = get_rank(m.rank_level)
            writer.writerow([
                m.telegram_id,
                f"@{m.username}" if m.username else "",
                m.full_name,
                m.rank_level,
                r.name_fa,
                r.tier,
                m.seasons_participated,
                "بله" if m.is_player else "خیر",
                "بله" if m.in_group else "خیر",
                "همگام" if m.tag_synced else "ناهماهنگ",
                m.rank_reached_at.isoformat() if m.rank_reached_at else "",
                m.first_seen_at.isoformat() if m.first_seen_at else "",
            ])

        # تبدیل به بایت با UTF-8 BOM جهت نمایش صحیح فارسی در اکسل
        csv_bytes = output.getvalue().encode("utf-8-sig")
        now_str = utcnow().strftime("%Y%m%d_%H%M%S")
        doc = BufferedInputFile(csv_bytes, filename=f"ranks_export_{now_str}.csv")

        caption = f"📊 خروجی سوابق و رتبه‌بندی اعضا شامل {fa_number(len(members))} رکورد."
        await message.reply_document(document=doc, caption=caption)
        await status_msg.delete()
