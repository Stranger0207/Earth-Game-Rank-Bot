"""
جدول ۲۱ مقام نظامی، رده‌ها، نشان‌ها و توابع اعتبارسنجی و نرمال‌سازی.
این ماژول سورس حقیقت (Source of Truth) تمام رتبه‌ها در سامانه است.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

DEFAULT_LEVEL: int = 1
MAX_LEVEL: int = 21
AUTO_PROMOTION_CAP_LEVEL: int = 17


@dataclass(frozen=True)
class Rank:
    """اطلاعات یک مقام نظامی."""

    level: int
    name_fa: str
    tier: str
    insignia: str  # فقط برای استفاده در متون پیام و دکمه‌های بات (نه در تگ تلگرام)


# فهرست ترتیبی ۲۱ مقام نظامی
RANKS: tuple[Rank, ...] = (
    Rank(level=1, name_fa="سرباز صفر", tier="سرباز", insignia="🪖"),
    Rank(level=2, name_fa="سرباز یکم", tier="سرباز", insignia="🎖"),
    Rank(level=3, name_fa="سرجوخه", tier="درجه‌دار", insignia="🎗"),
    Rank(level=4, name_fa="گروهبان سوم", tier="درجه‌دار", insignia="🥉"),
    Rank(level=5, name_fa="گروهبان دوم", tier="درجه‌دار", insignia="🥈"),
    Rank(level=6, name_fa="گروهبان یکم", tier="درجه‌دار", insignia="🥇"),
    Rank(level=7, name_fa="استوار دوم", tier="استوار", insignia="⚔️"),
    Rank(level=8, name_fa="استوار یکم", tier="استوار", insignia="🗡"),
    Rank(level=9, name_fa="افسریار دوم", tier="افسریار", insignia="🛡"),
    Rank(level=10, name_fa="افسریار یکم", tier="افسریار", insignia="⚜️"),
    Rank(level=11, name_fa="ستوان سوم", tier="افسر جوان", insignia="🔹"),
    Rank(level=12, name_fa="ستوان دوم", tier="افسر جوان", insignia="🔷"),
    Rank(level=13, name_fa="ستوان یکم", tier="افسر جوان", insignia="💠"),
    Rank(level=14, name_fa="سروان", tier="افسر ارشد", insignia="🌟"),
    Rank(level=15, name_fa="سرگرد", tier="افسر ارشد", insignia="⭐"),
    Rank(level=16, name_fa="سرهنگ دوم", tier="افسر ارشد", insignia="💫"),
    Rank(level=17, name_fa="سرهنگ", tier="افسر ارشد", insignia="🦅"),
    Rank(level=18, name_fa="سرتیپ", tier="ژنرال", insignia="⚡"),
    Rank(level=19, name_fa="سرلشکر", tier="ژنرال", insignia="🔥"),
    Rank(level=20, name_fa="سپهبد", tier="ژنرال", insignia="👑"),
    Rank(level=21, name_fa="ارتشبد", tier="فرماندهی عالی", insignia="💎"),
)

# نگاشت سریع بر اساس سطح
_LEVEL_TO_RANK: dict[int, Rank] = {r.level: r for r in RANKS}


def normalize_persian_text(text: str) -> str:
    """
    نرمال‌سازی متون فارسی: یکسان‌سازی ی/ي و ک/ك، حذف تنوین و اعراب، یکپارچه‌سازی فواصل و نیم‌فاصله‌ها.
    """
    if not text:
        return ""
    res = text.strip()
    res = res.replace("ي", "ی").replace("ك", "ک")
    res = res.replace("\u200c", " ")  # تبدیل نیم‌فاصله به فاصله جهت انطباق روان
    res = re.sub(r"[\u064B-\u065F\u0670]", "", res)  # حذف اعراب عربی
    res = re.sub(r"\s+", " ", res).strip()  # فشرده‌سازی فاصله‌های متوالی
    return res.lower()


# نگاشت نام نرمال‌شده به مقام
_NAME_TO_RANK: dict[str, Rank] = {
    normalize_persian_text(r.name_fa): r for r in RANKS
}


def clamp(level: int) -> int:
    """محدود کردن سطح به بازه مجاز [DEFAULT_LEVEL .. MAX_LEVEL]."""
    return max(DEFAULT_LEVEL, min(MAX_LEVEL, int(level)))


def get_rank(level: int) -> Rank:
    """دریافت اطلاعات مقام بر اساس سطح عددی."""
    clamped = clamp(level)
    return _LEVEL_TO_RANK[clamped]


def find_rank(query: str | int) -> Rank | None:
    """
    جستجوی هوشمند مقام بر اساس شماره سطح یا نام فارسی.
    از نرمال‌سازی کلمات، اصلاح حروف عربی و نادیده‌گیری فاصله‌ها پشتیبانی می‌کند.
    """
    if isinstance(query, int):
        if DEFAULT_LEVEL <= query <= MAX_LEVEL:
            return _LEVEL_TO_RANK[query]
        return None

    query_str = str(query).strip()
    if not query_str:
        return None

    # بررسی اگر ورودی عدد باشد (فارسی یا انگلیسی)
    persian_to_english = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
    ascii_num = query_str.translate(persian_to_english)
    if ascii_num.isdigit():
        lvl = int(ascii_num)
        if DEFAULT_LEVEL <= lvl <= MAX_LEVEL:
            return _LEVEL_TO_RANK[lvl]
        return None

    # جستجو بر اساس نام نرمال‌شده
    norm = normalize_persian_text(query_str)
    if norm in _NAME_TO_RANK:
        return _NAME_TO_RANK[norm]

    # جستجوی زیررشته‌ای در صورتی که تطابق کامل نیافت
    for norm_name, rank in _NAME_TO_RANK.items():
        if norm == norm_name or norm in norm_name:
            return rank

    return None


# ==========================================
# اعتبارسنجی‌های سخت‌گیرانه هنگام بارگذاری (Import)
# ==========================================

assert len(RANKS) == 21, f"تعداد مقام‌ها باید دقیقاً ۲۱ باشد، اما {len(RANKS)} مقام تعریف شده است!"

_levels = [r.level for r in RANKS]
assert _levels == list(range(1, 22)), f"سطوح مقام‌ها باید پیوسته از ۱ تا ۲۱ باشد! مقدار فعلی: {_levels}"

_names = [r.name_fa for r in RANKS]
assert len(set(_names)) == len(_names), "نام‌های مقام‌ها باید کاملاً یکتا باشند!"

for r in RANKS:
    assert len(r.name_fa) <= 16, (
        f"نام مقام '{r.name_fa}' با طول {len(r.name_fa)} بیش از محدودیت ۱۶ کاراکتری تگ تلگرام است!"
    )
    # بررسی عدم وجود کاراکترهای ایموجی یا علائم غیرمتنی در نام تگ
    assert not any(ord(char) > 0x1F000 for char in r.name_fa), (
        f"نام مقام '{r.name_fa}' نباید حاوی ایموجی باشد!"
    )
