"""
هندلر دستور /roster جهت دریافت و نمایش فهرست بازیکنان فعلی فصل از ربات اصلی.
"""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from ...core.db.base import get_session
from ...core.middlewares.owner_guard import OwnerOnlyMiddleware
from ...core.utils.format import fa_number, split_text
from ...core.utils.html import bold, clean_html, code
from ...core.utils.ui import DIVIDER, header
from .service import RosterService

router = Router(name="roster")
router.message.middleware(OwnerOnlyMiddleware())


@router.message(Command("roster"))
async def cmd_roster(message: Message) -> None:
    """دریافت زنده و ذخیره اسنپ‌شات بازیکنان فعلی فصل از ربات اصلی."""
    status_msg = await message.reply("⏳ در حال ارتباط با ربات اصلی و دریافت روستر بازیکنان...")

    async for session in get_session():
        try:
            snapshot, players = await RosterService.fetch_and_snapshot(session)
        except Exception as exc:
            # در صورت عدم امکان دریافت زنده، آخرین اسنپ‌شات را بررسی می‌کنیم
            snapshot, players = await RosterService.get_latest_snapshot(session)
            if not players:
                await status_msg.edit_text(f"❌ خطا در دریافت روستر و عدم وجود اسنپ‌شات قبلی:\n<code>{clean_html(str(exc))}</code>")
                return

        lines = [
            header("فهرست بازیکنان فعال فصل (Roster Snapshot)", "📋"),
            f"👥 تعداد کل بازیکنان: {bold(fa_number(len(players)))}",
            f"📅 شناسه اسنپ‌شات: {code(snapshot.id)}",
            DIVIDER,
        ]

        for i, p in enumerate(players[:50], 1):
            name = clean_html(p.get("full_name") or p.get("username") or str(p.get("telegram_id")))
            country = f" ({clean_html(p.get('country'))})" if p.get("country") else ""
            lines.append(f"{fa_number(i)}. {name}{country} — {code(p.get('telegram_id'))}")

        if len(players) > 50:
            lines.append(f"\n... و {fa_number(len(players) - 50)} بازیکن دیگر")

        full_text = "\n".join(lines)
        chunks = split_text(full_text, max_length=4000)
        await status_msg.edit_text(chunks[0])
        for chunk in chunks[1:]:
            await message.answer(chunk)
