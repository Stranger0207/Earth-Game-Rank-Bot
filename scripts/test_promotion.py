"""
آزمون‌های جدول‌محور قوانین ارتقا، تنزل، سقف خودکار ۱۷ و سقف مطلق ۲۱.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from bot.domain.promotion import (
    calculate_progress_ratio,
    demote_manual,
    is_at_auto_cap,
    promote_auto,
    promote_manual,
)


def test_auto_promotion_table() -> None:
    # موارد آزمون ارتقای خودکار: (سطح ورودی, سطح خروجی مورد انتظار, آیا ارتقا یافت؟)
    cases = [
        (1, 2, True),
        (2, 3, True),
        (15, 16, True),
        (16, 17, True),       # رسیدن به سقف خودکار
        (17, 17, False),      # ماندن در سقف خودکار سرهنگ
        (18, 18, False),      # ژنرال‌ها خودکار تغییر نمی‌کنند
        (20, 20, False),
        (21, 21, False),
    ]

    for curr, expected_lvl, expected_promoted in cases:
        lvl, promoted = promote_auto(curr)
        assert lvl == expected_lvl, f"خطا در سطح خودکار: {curr} -> {lvl} != {expected_lvl}"
        assert promoted == expected_promoted, f"خطا در پرچم ارتقا: {curr}"

    print("✅ ارتقای خودکار فصلی و سقف ۱۷ با موفقیت تأیید شد.")


def test_manual_promotion_table() -> None:
    # ارتقای دستی بدون سقف ۱۷، تا سقف مطلق ۲۱
    cases = [
        (15, 2, 17, 2),       # ارتقای ۲ درجه از ۱۵ به ۱۷
        (17, 1, 18, 1),       # عبور دستی از سقف خودکار
        (20, 3, 21, 1),       # سقف مطلق ۲۱ (تنها ۱ درجه امکان ارتقا داشت)
        (21, 5, 21, 0),       # در سقف مطلق ۲۱ دیگر افزایش نمی‌یابد
        (10, 0, 10, 0),       # دلتای صفر
    ]

    for curr, delta, expected_lvl, expected_delta in cases:
        new_lvl, act_delta = promote_manual(curr, delta)
        assert new_lvl == expected_lvl, f"دستی: {curr}+{delta} -> {new_lvl} != {expected_lvl}"
        assert act_delta == expected_delta, f"دلتای دستی اشتباه: {act_delta} != {expected_delta}"

    print("✅ ارتقای دستی مالک و سقف مطلق ۲۱ با موفقیت تأیید شد.")


def test_manual_demotion_table() -> None:
    # تنزل دستی تا حداقل سطح ۱
    cases = [
        (1, 1, 1, 0),         # حداقل سطح ۱ است و کمتر نمی‌شود
        (5, 2, 3, 2),         # تنزل ۲ درجه
        (3, 10, 1, 2),        # کاهش بیش از حد -> کلمپ روی ۱
        (18, 1, 17, 1),
    ]

    for curr, delta, expected_lvl, expected_delta in cases:
        new_lvl, act_delta = demote_manual(curr, delta)
        assert new_lvl == expected_lvl, f"تنزل: {curr}-{delta} -> {new_lvl} != {expected_lvl}"
        assert act_delta == expected_delta, f"دلتای تنزل اشتباه: {act_delta} != {expected_delta}"

    print("✅ تنزل درجه و حداقل سطح ۱ با موفقیت تأیید شد.")


def test_progress_and_cap() -> None:
    assert is_at_auto_cap(16) is False
    assert is_at_auto_cap(17) is True
    assert is_at_auto_cap(20) is True

    # پیشرفت سطح ۱ برابر 0.0 است
    assert calculate_progress_ratio(1) == 0.0
    # پیشرفت سطح ۱۷ و بالاتر برابر 1.0 است
    assert calculate_progress_ratio(17) == 1.0
    assert calculate_progress_ratio(21) == 1.0

    print("✅ محاسبات سقف خودکار و پیشرفت رده تأیید شد.")


if __name__ == "__main__":
    print("🚀 اجرای آزمون‌های قوانین ارتقا...")
    test_auto_promotion_table()
    test_manual_promotion_table()
    test_manual_demotion_table()
    test_progress_and_cap()
    print("🎉 تمامی آزمون‌های promotion.py سبز شدند!")
