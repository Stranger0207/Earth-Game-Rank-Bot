"""
آزمون‌های تولید کارت گرافیکی مقام نظامی با Pillow، فونت فارسی و اعتبارسنجی بافر خروجی.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from bot.modules.cards.generator import render_rank_card


def test_card_generation() -> None:
    # ۱. تولید کارت سطح معمولی
    buf1 = render_rank_card(
        full_name="علی رضایی مقدم",
        rank_name="گروهبان یکم",
        level=6,
        tier="درجه‌دار",
        insignia="🥇",
        seasons_participated=2,
        medals_count=1,
    )
    data1 = buf1.getvalue()
    assert len(data1) > 5000, "حجم فایل کارت تولیدشده باید معقول باشد"
    assert data1[:8] == b"\x89PNG\r\n\x1a\n", "هدر فایل باید فرمت معتبر PNG باشد"
    print("✅ تولید کارت مقام برای سطح معمولی با موفقیت انجام شد.")

    # ۲. تولید کارت برای سطح در سقف خودکار (سطح ۱۷ - سرهنگ)
    buf2 = render_rank_card(
        full_name="فرمانده ارشد با نام طولانی و حروف پیچیده فارسی",
        rank_name="سرهنگ",
        level=17,
        tier="افسر ارشد",
        insignia="🦅",
        seasons_participated=5,
        medals_count=4,
    )
    data2 = buf2.getvalue()
    assert len(data2) > 5000
    assert data2[:8] == b"\x89PNG\r\n\x1a\n"
    print("✅ تولید کارت مقام در سقف خودکار (سطح ۱۷) با موفقیت انجام شد.")

    # ۳. تولید کارت برای بالاترین سطح (ارتشبد)
    buf3 = render_rank_card(
        full_name="ارتشبد کل قوا",
        rank_name="ارتشبد",
        level=21,
        tier="فرماندهی عالی",
        insignia="💎",
        seasons_participated=12,
        medals_count=7,
    )
    data3 = buf3.getvalue()
    assert len(data3) > 5000
    print("✅ تولید کارت مقام عالی ارتشبد با موفقیت انجام شد.")


if __name__ == "__main__":
    print("🚀 اجرای آزمون‌های ماژول cards...")
    test_card_generation()
    print("🎉 تمامی آزمون‌های cards.py سبز شدند!")
