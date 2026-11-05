"""کیبوردهای شیشه‌ای پنل مدیریت و پنجره‌های تأیید دومرحله‌ای."""

from aiogram.types import InlineKeyboardMarkup
from ...core.utils.ui import STYLE_MAIN, STYLE_NO, STYLE_OK, styled_btn


def panel_main_keyboard() -> InlineKeyboardMarkup:
    """منوی شیشه‌ای اصلی /panel."""
    buttons = [
        [
            styled_btn("📋 روستر بازیکنان", "panel_action:roster", STYLE_MAIN),
            styled_btn("🔮 پیش‌نمایش فصل", "panel_action:season_preview", STYLE_MAIN),
        ],
        [
            styled_btn("🔄 ممیزی تگ‌ها (/audit)", "panel_action:audit", STYLE_MAIN),
            styled_btn("🩺 تست سلامت (/selftest)", "panel_action:selftest", STYLE_MAIN),
        ],
        [
            styled_btn("🎖 ترفیع همه بازیکنان (+۱)", "panel_confirm:promote_players:1", STYLE_OK),
            styled_btn("🌐 ترفیع تمام اعضا (+۱)", "panel_confirm:promote_all:1", STYLE_OK),
        ],
        [
            styled_btn("📊 خروجی اکسل/CSV", "panel_action:export", STYLE_MAIN),
            styled_btn("⚙️ تنظیمات", "panel_action:settings", STYLE_MAIN),
        ],
        [
            styled_btn("❌ بستن منو", "panel_action:close", STYLE_NO),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirm_dialog_keyboard(action_key: str, payload: str = "") -> InlineKeyboardMarkup:
    """کیبورد تأیید دومرحله‌ای عملیات حساس."""
    data_confirm = f"confirm_act:{action_key}:{payload}".rstrip(":")
    data_cancel = f"cancel_act:{action_key}"

    buttons = [
        [
            styled_btn("✅ تأیید و اجرا", data_confirm, STYLE_OK),
            styled_btn("❌ انصراف", data_cancel, STYLE_NO),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
