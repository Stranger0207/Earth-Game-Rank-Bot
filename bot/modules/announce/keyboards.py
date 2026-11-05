"""کیبوردهای شیشه‌ای رنگی برای ابلاغیه‌ها و پیام‌های ارتقا."""

from aiogram.types import InlineKeyboardMarkup
from ...core.utils.ui import STYLE_MAIN, STYLE_OK, styled_btn


def announcement_action_keyboard() -> InlineKeyboardMarkup:
    """دکمه‌های تعاملی زیر پیام ابلاغیه ارتقا و خلاصه فصل."""
    buttons = [
        [
            styled_btn("🎖 کارت من", "member_cmd:myrank", STYLE_MAIN),
            styled_btn("🏆 جدول افتخار", "member_cmd:top", STYLE_OK),
        ],
        [
            styled_btn("📜 نردبان ۲۱ مقام", "member_cmd:ranks", STYLE_MAIN),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
