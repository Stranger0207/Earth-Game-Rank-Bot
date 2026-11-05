"""
آزمون‌های متون و منطق دستورات عمومی اعضا (لیدربورد، نردبان و تاریخچه).
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from bot.domain.ranks import get_rank
from bot.modules.member_commands.texts import (
    history_timeline_text,
    ranks_ladder_text,
    text_fallback_rank_card,
    top_leaderboard_text,
)


def test_member_texts() -> None:
    class DummyMember:
        telegram_id = 7001
        username = "warrior"
        full_name = "مبارز کهنه‌کار"
        rank_level = 14
        seasons_participated = 4
        rank_reached_at = None

    r14 = get_rank(14)

    # تست فال‌بک کارت
    card_txt = text_fallback_rank_card(DummyMember(), r14, medals_count=2)
    assert "سروان" in card_txt
    assert "مبارز کهنه‌کار" in card_txt

    # تست جدول برترین‌ها
    top_txt = top_leaderboard_text([(DummyMember(), r14)])
    assert "سروان" in top_txt
    assert "جدول افتخار" in top_txt

    # تست نردبان ۲۱ مقام
    ladder_txt = ranks_ladder_text({14: 3, 1: 50}, user_level=14)
    assert "نردبان" in ladder_txt
    assert "(مقام شما)" in ladder_txt

    print("✅ صحت متون لیدربورد، نردبان و کارت متنی با موفقیت تأیید شد.")


if __name__ == "__main__":
    print("🚀 اجرای آزمون‌های member_commands texts...")
    test_member_texts()
    print("🎉 تمامی آزمون‌های member_commands سبز شدند!")
