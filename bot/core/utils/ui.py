"""
کمک‌کننده‌های رابط کاربری (UI): استایل دکمه‌های شیشه‌ای (Bot API 9.4+)، خطوط جداکننده و نوار پیشرفت.
"""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton

# استایل‌های دکمه‌های اینلاین طبق تلگرام
STYLE_OK = "success"      # سبز: تأیید، پذیرش، انتخاب
STYLE_NO = "danger"       # قرمز: لغو، تنزل، حذف، عملیات خطرناک
STYLE_MAIN = "primary"    # آبی: دکمه‌های اصلی و هدایت‌کننده

# نشانگرهای انتخاب
PICK_ON = "🟢"
PICK_OFF = "⚪️"

# خط جداکننده‌ی استاندارد
DIVIDER = "➖➖➖➖➖➖➖➖➖➖"


def header(title: str, emoji: str = "") -> str:
    """سربرگ یکپارچه با خط جداکننده."""
    prefix = f"{emoji} " if emoji else ""
    return f"{prefix}<b>{title}</b>\n{DIVIDER}"


def render_progress_bar(ratio: float, length: int = 8) -> str:
    """رسم نوار پیشرفت متنی با کاراکترهای ▰ و ▱."""
    clamped = max(0.0, min(1.0, float(ratio)))
    filled = int(round(clamped * length))
    filled = max(0, min(length, filled))
    return "▰" * filled + "▱" * (length - filled)


def styled_btn(text: str, callback_data: str, style: str | None = None) -> InlineKeyboardButton:
    """ساخت دکمه‌ی شیشه‌ای با پشتیبانی از style بدون شکست در نسخه‌های مختلف."""
    kwargs = {"text": text, "callback_data": callback_data}
    if style:
        kwargs["style"] = style
    return InlineKeyboardButton(**kwargs)
