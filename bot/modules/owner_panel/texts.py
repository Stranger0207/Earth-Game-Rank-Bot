"""متون و پیام‌های اختصاصی پنل مدیریت مالک."""

from ...core.utils.format import fa_number, format_datetime
from ...core.utils.html import bold, clean_html, code
from ...core.utils.ui import DIVIDER, header
from ...domain.ranks import Rank


def panel_welcome_text(members_count: int, synced_count: int, pending_tags: int) -> str:
    """متن صفحه اصلی پنل شیشه‌ای مدیریت."""
    head = header("ستاد فرماندهی و مدیریت مقام‌ها", "🎖")
    body = (
        f"{head}\n"
        f"👥 کل اعضای شناسایی‌شده: {bold(fa_number(members_count))}\n"
        f"🏷 تگ‌های همگام تلگرام: {bold(fa_number(synced_count))}\n"
        f"⏳ در صف تگ: {bold(fa_number(pending_tags))}\n"
        f"{DIVIDER}\n"
        "یکی از عملیات‌های زیر را انتخاب کنید:"
    )
    return body


def member_dossier_text(member, rank: Rank, history_count: int, medals_count: int) -> str:
    """متن پرونده و کارنامه کامل عضو (/who)."""
    tag_status = "✅ همگام" if member.tag_synced else f"⚠️ عدم تطابق ({clean_html(member.tag_error or 'در صف')})"
    player_status = "👑 بازیکن فعال (دارای کشور)" if member.is_player else "عضو عادی گروه"

    lines = [
        header("پرونده نظامی عضو", rank.insignia),
        f"👤 نام: {bold(clean_html(member.full_name))}",
        f"🆔 شناسه تلگرام: {code(member.telegram_id)}",
        f"🔹 نام کاربری: {('@' + clean_html(member.username)) if member.username else 'ندارد'}",
        f"🎖 مقام فعلی: {bold(rank.name_fa)} (سطح {fa_number(rank.level)} - رده {rank.tier})",
        f"🏷 وضعیت تگ تلگرام: {tag_status}",
        f"🎮 وضعیت در بازی: {player_status}",
        f"🏆 فصول خدمت: {bold(fa_number(member.seasons_participated))}",
        f"🏅 مدال‌ها و افتخارات: {bold(fa_number(medals_count))}",
        f"📜 دفعات تغییر مقام: {bold(fa_number(history_count))}",
        f"📅 تاریخ آخرین ترفیع: {format_datetime(member.rank_reached_at)}",
        f"👁 آخرین مشاهده در گروه: {format_datetime(member.last_seen_at)}",
    ]
    return "\n".join(lines)
