"""
متون، جداول و قالب‌های نمایشی دستورهای عمومی اعضا.
"""

from __future__ import annotations

from ...core.utils.format import fa_number, format_datetime
from ...core.utils.html import bold, clean_html, code
from ...core.utils.ui import DIVIDER, header
from ...domain.ranks import RANKS, Rank, get_rank
from ..achievements.catalog import ACHIEVEMENT_CATALOG


def text_fallback_rank_card(member, rank: Rank, medals_count: int = 0) -> str:
    """متن جایگزین کارت مقام در صورت بروز خطای رندر تصویر."""
    return (
        f"{header('کارت خدمت نظامی', rank.insignia)}\n"
        f"👤 نام: {bold(clean_html(member.full_name or 'رزمنده'))}\n"
        f"🎖 مقام: {bold(rank.name_fa)} (سطح {fa_number(rank.level)})\n"
        f"🏅 رده: <b>{rank.tier}</b>\n"
        f"🏆 فصول خدمت: {bold(fa_number(member.seasons_participated))}\n"
        f"🎗 نشان‌های افتخار: {bold(fa_number(medals_count))}\n"
        f"📅 تاریخ آخرین ترفیع: {format_datetime(member.rank_reached_at)}\n"
        f"{DIVIDER}\n"
        f"{'🔒 در سقف ارتقای خودکار' if rank.level >= 17 else '▰▰▰▱▱ در مسیر پیشرفت'}"
    )


def top_leaderboard_text(top_members: list[tuple[any, Rank]]) -> str:
    """متن جدول افتخار و برترین رتبه‌های ارتش."""
    lines = [
        header("جدول افتخار — برترین فرماندهان ارتش زمین", "🏆"),
    ]
    for idx, (m, r) in enumerate(top_members, 1):
        medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"{fa_number(idx)}."
        name = clean_html(m.full_name or m.username or str(m.telegram_id))
        lines.append(f"{medal} <b>{name}</b> — {r.insignia} {r.name_fa} (سطح {fa_number(r.level)})")

    lines.append(DIVIDER)
    lines.append("🎖 ارشدیت بر اساس سطح مقام و تقدم در نیل به درجه محاسبه می‌گردد.")
    return "\n".join(lines)


def ranks_ladder_text(level_counts: dict[int, int], user_level: int) -> str:
    """نردبان ۲۱ مقام نظامی با هرم آماری دارندگان و مشخص کردن جایگاه کاربر."""
    lines = [
        header("نردبان و سلسله‌مراتب ۲۱ مقام ارتش زمین", "📜"),
    ]

    for r in reversed(RANKS):
        count = level_counts.get(r.level, 0)
        marker = "👉 " if r.level == user_level else "   "
        u_flag = " (مقام شما)" if r.level == user_level else ""
        lines.append(
            f"{marker}<b>{fa_number(r.level)}.</b> {r.insignia} {r.name_fa} — 👥 {bold(fa_number(count))} نفر{u_flag}"
        )

    lines.append(DIVIDER)
    lines.append("🔒 سقف ارتقای خودکار پایان هر فصل: سطح ۱۷ (سرهنگ)")
    return "\n".join(lines)


def history_timeline_text(full_name: str, histories: list[any]) -> str:
    """خط زمانی و تاریخچه ترفیعات و تغییرات مقام کاربر."""
    lines = [
        header(f"خط زمانی ترفیعات نظامی {clean_html(full_name)}", "📜"),
    ]

    if not histories:
        lines.append("هنوز هیچ سابقه‌ای از تغییر درجه برای شما ثبت نشده است.")
    else:
        for h in histories:
            direction = "🔺" if h.delta > 0 else "🔻"
            old_r = get_rank(h.old_level)
            new_r = get_rank(h.new_level)
            lines.append(
                f"{direction} <b>{old_r.name_fa} ➔ {new_r.name_fa}</b>\n"
                f"   📅 {format_datetime(h.created_at)} | منبع: {code(h.source)}"
                f"{(f' | دلیل: ' + clean_html(h.reason)) if h.reason else ''}"
            )

    return "\n".join(lines)


def medals_list_text(user_achievements: set[str]) -> str:
    """فهرست نشان‌های نظامی (کسب‌شده و قفل‌شده با شرایط)."""
    lines = [
        header("ویترین مدال‌ها و نشان‌های افتخار نظامی", "🏅"),
    ]

    for ach in ACHIEVEMENT_CATALOG:
        is_unlocked = ach.key in user_achievements
        icon = ach.badge if is_unlocked else "🔒"
        status = "✅ کسب‌شده" if is_unlocked else f"<i>شرط: {ach.hint}</i>"
        lines.append(f"{icon} <b>{ach.title}</b> — {status}\n   {ach.description}\n")

    return "\n".join(lines)
