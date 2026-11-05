"""
هندلرهای دستورات پیش‌نمایش و اعمال دستی ارتقای فصلی (/season_preview و /season_apply).
"""

from __future__ import annotations

import uuid
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from ...core.db.base import get_session
from ...core.middlewares.owner_guard import OwnerOnlyMiddleware
from ...core.utils.format import fa_number
from ...core.utils.html import bold, clean_html
from ...core.utils.ui import DIVIDER, header
from ..owner_panel.keyboards import confirm_dialog_keyboard
from ..roster.service import RosterService
from .service import SeasonService

router = Router(name="season")
router.message.middleware(OwnerOnlyMiddleware())
router.callback_query.middleware(OwnerOnlyMiddleware())


@router.message(Command("season_preview"))
async def cmd_season_preview(message: Message) -> None:
    """پیش‌نمایش تغییرات و ترفیعات فصلی بدون اعمال روی دیتابیس."""
    status_msg = await message.reply("⏳ در حال دریافت آخرین روستر و شبیه‌سازی پایان فصل...")

    async for session in get_session():
        _, players = await RosterService.get_latest_snapshot(session)
        if not players:
            try:
                _, players = await RosterService.fetch_and_snapshot(session)
            except Exception as exc:
                await status_msg.edit_text(f"❌ امکان دریافت روستر وجود ندارد:\n<code>{clean_html(str(exc))}</code>")
                return

        preview = await SeasonService.preview_season(session, players)

        lines = [
            header("پیش‌نمایش ارتقای پایان فصل (Simulation)", "🔮"),
            f"👥 کل بازیکنان فعال: {bold(fa_number(preview['total_players']))}",
            f"📈 مشمول ترفیع درجه: {bold(fa_number(preview['promoted_count']))} نفر",
            f"🆕 بازیکنان تازه وارد: {bold(fa_number(preview['new_recruits_count']))} نفر",
            f"🔒 مانده در سقف خودکار (سرهنگ به بالا): {bold(fa_number(preview['capped_count']))} نفر",
            DIVIDER,
            "💡 هیچ تغییری در پایگاه داده اعمال نشد.",
        ]
        await status_msg.edit_text("\n".join(lines))


@router.message(Command("season_apply"))
async def cmd_season_apply(message: Message) -> None:
    """اعمال دستی ارتقای فصل از روی آخرین روستر (تأیید دو مرحله‌ای)."""
    async for session in get_session():
        _, players = await RosterService.get_latest_snapshot(session)
        if not players:
            await message.reply("❌ هیچ اسنپ‌شاتی از روستر بازیکنان یافت نشد. ابتدا /roster را اجرا کنید.")
            return

        text = (
            f"⚠️ <b>تأیید اعمال دستی ارتقای فصل</b>\n\n"
            f"تعداد بازیکنان در اسنپ‌شات: {bold(fa_number(len(players)))}\n"
            "این عملیات به تمام بازیکنان واجد شرایط یک درجه ترفیع اعطا خواهد کرد.\n\n"
            "آیا از اجرای ترفیع فصلی اطمینان دارید؟"
        )
        await message.reply(text, reply_markup=confirm_dialog_keyboard("apply_season_manual"))


@router.callback_query(F.data == "confirm_act:apply_season_manual")
async def on_confirm_season_apply(call: CallbackQuery) -> None:
    await call.message.edit_text("⏳ در حال اعمال ارتقای فصلی روی پایگاه داده...")
    event_id = f"manual-{uuid.uuid4()}"

    async for session in get_session():
        _, players = await RosterService.get_latest_snapshot(session)
        result = await SeasonService.process_season_ended(
            session=session,
            event_id=event_id,
            players=players,
            source="manual_cmd",
        )

        text = (
            f"🎉 <b>ارتقای فصلی با موفقیت اعمال شد</b>\n\n"
            f"📈 ترفیع‌یافتگان: {bold(fa_number(result['promoted']))}\n"
            f"🔒 در سقف مانده: {bold(fa_number(result['capped']))}\n"
            f"🆔 شناسه واقعه: <code>{event_id}</code>\n\n"
            "تگ‌های تلگرام در صف پس‌زمینه در حال اعمال هستند."
        )
        await call.message.edit_text(text)
