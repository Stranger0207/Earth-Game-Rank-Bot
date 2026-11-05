"""
توابع کمکی قالب‌بندی متون، تبدیل ارقام به فارسی و تقسیم پیام‌های بلند.
"""

from __future__ import annotations

import datetime

_FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
_EN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")


def fa_number(val: int | float | str) -> str:
    """تبدیل اعداد انگلیسی یا رشته‌ای به ارقام فارسی."""
    return str(val).translate(_FA_DIGITS)


def en_number(val: str) -> str:
    """تبدیل ارقام فارسی یا عربی به اعداد انگلیسی."""
    return str(val).translate(_EN_DIGITS)


def format_datetime(dt: datetime.datetime | None) -> str:
    """نمایش خوانا و کوتاه زمان به صورت فارسی/UTC."""
    if not dt:
        return "ثبت نشده"
    # نمایش تاریخ به صورت YYYY-MM-DD HH:MM
    formatted = dt.strftime("%Y-%m-%d %H:%M")
    return fa_number(formatted)


def split_text(text: str, max_length: int = 4000) -> list[str]:
    """
    تقسیم یک متن طولانی به بخش‌های کوچکتر از حداکثر سقف مشخص‌شده تلگرام.
    سعی می‌کند بر اساس خطوط جدید یا فاصله متن را برش دهد.
    """
    if len(text) <= max_length:
        return [text]

    chunks: list[str] = []
    lines = text.split("\n")
    current_chunk: list[str] = []
    current_len = 0

    for line in lines:
        line_len = len(line) + 1  # احتساب کاراکتر \n
        if current_len + line_len > max_length:
            if current_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = []
                current_len = 0

            # اگر خود یک خط از حداکثر سقف بیشتر باشد، مستقیماً برش داده شود
            if line_len > max_length:
                for i in range(0, len(line), max_length):
                    chunks.append(line[i : i + max_length])
            else:
                current_chunk.append(line)
                current_len = line_len
        else:
            current_chunk.append(line)
            current_len += line_len

    if current_chunk:
        chunks.append("\n".join(current_chunk))

    return chunks
