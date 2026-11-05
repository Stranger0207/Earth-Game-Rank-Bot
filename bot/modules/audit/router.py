"""
هندلرهای دستورات ممیزی و تست تشخیصی سلامت ربات.
"""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from ...core.middlewares.owner_guard import OwnerOnlyMiddleware
from ...core.utils.format import fa_number
from ...core.utils.html import bold
from ...core.utils.ui import DIVIDER, header
from .service import AuditService

router = Router(name="audit")
router.message.middleware(OwnerOnlyMiddleware())


@router.message(Command("audit"))
async def cmd_audit(message: Message) -> None:
    """تطبیق دیتابیس با وضعیت تگ‌ها در گروه و اصلاح عدم‌تطابق‌ها."""
    status_msg = await message.reply("⏳ در حال ممیزی اعضا و بررسی تگ‌های تلگرام...")
    stats = await AuditService.run_audit(bot=message.bot)

    text = (
        f"{header('گزارش ممیزی تگ‌ها', '📋')}\n"
        f"👥 اعضای بررسی‌شده: {bold(fa_number(stats['total_checked']))}\n"
        f"🏷 ارسال‌شده به صف اصلاح تگ: {bold(fa_number(stats['enqueued']))}\n"
        f"{DIVIDER}\n"
        "✅ فرآیند با موفقیت آغاز شد و تگ‌ها در پس‌زمینه اصلاح خواهند شد."
    )
    await status_msg.edit_text(text)


@router.message(Command("selftest"))
async def cmd_selftest(message: Message) -> None:
    """اجرای آزمون سلامت خودکار سامانه و دسترسی‌ها."""
    status_msg = await message.reply("🩺 در حال اجرای آزمون‌های تشخیصی سلامت سامانه...")
    report = await AuditService.run_selftest(bot=message.bot)

    lines = [header("نتایج تست سلامت سامانه (Self-Test)", "🩺")]

    for key, data in report.items():
        icon = "✅" if data["ok"] else "❌"
        lines.append(f"{icon} <b>{key}</b>: {data['detail']}")

    lines.append(DIVIDER)
    overall_ok = all(d["ok"] for d in report.values())
    if overall_ok:
        lines.append("🎉 وضعیت کلی سیستم: <b>کاملاً سالم و عملیاتی</b>")
    else:
        lines.append("⚠️ وضعیت کلی: <b>برخی موارد نیاز به توجه دارند</b>")

    await status_msg.edit_text("\n".join(lines))
