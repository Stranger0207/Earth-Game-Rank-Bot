"""
آزمون‌های پنل شیشه‌ای مدیریت، کیبوردها با استایل رنگی و تاییدهای دومرحله‌ای.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from bot.modules.owner_panel.keyboards import (
    confirm_dialog_keyboard,
    panel_main_keyboard,
)
from bot.modules.owner_panel.texts import member_dossier_text, panel_welcome_text
from bot.domain.ranks import get_rank


def test_keyboards() -> None:
    kb = panel_main_keyboard()
    assert kb.inline_keyboard is not None
    # بررسی وجود دکمه‌های شیشه‌ای
    buttons = [btn for row in kb.inline_keyboard for btn in row]
    assert any("روستر" in btn.text for btn in buttons)
    assert any("تست سلامت" in btn.text for btn in buttons)

    # تست کیبورد تایید دو مرحله‌ای
    confirm_kb = confirm_dialog_keyboard("promote_all", "1")
    c_btns = [btn for row in confirm_kb.inline_keyboard for btn in row]
    assert any("تأیید" in btn.text for btn in c_btns)
    assert any("انصراف" in btn.text for btn in c_btns)
    print("✅ ساخت کیبوردهای شیشه‌ای و تاییدهای دومرحله‌ای با موفقیت تأیید شد.")


def test_texts() -> None:
    text = panel_welcome_text(100, 80, 5)
    assert "۱۰۰" in text
    assert "۸۰" in text

    class DummyMember:
        telegram_id = 98765
        username = "commander"
        full_name = "فرمانده تست"
        rank_level = 17
        tag_synced = True
        tag_error = None
        is_player = True
        seasons_participated = 4
        rank_reached_at = None
        last_seen_at = None

    rank17 = get_rank(17)
    dossier = member_dossier_text(DummyMember(), rank17, history_count=5, medals_count=3)
    assert "سرهنگ" in dossier
    assert "بازیکن فعال" in dossier
    print("✅ متون اداری و پرونده نظامی با موفقیت تأیید شد.")


if __name__ == "__main__":
    print("🚀 اجرای آزمون‌های owner_panel...")
    test_keyboards()
    test_texts()
    print("🎉 تمامی آزمون‌های owner_panel سبز شدند!")
