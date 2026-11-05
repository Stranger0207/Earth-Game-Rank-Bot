"""
آزمون‌های جامع جدول ۲۱ مقام نظامی، رده‌ها، محدودیت‌ها و نرمال‌سازی فارسی.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from bot.domain.ranks import (
    DEFAULT_LEVEL,
    MAX_LEVEL,
    RANKS,
    find_rank,
    get_rank,
    normalize_persian_text,
)


def test_ranks_structure() -> None:
    assert len(RANKS) == 21
    assert [r.level for r in RANKS] == list(range(1, 22))
    assert DEFAULT_LEVEL == 1
    assert MAX_LEVEL == 21

    # بررسی یکتایی نام‌ها و رده‌ها
    names = [r.name_fa for r in RANKS]
    assert len(set(names)) == 21

    # بررسی طول مجاز برای تگ تلگرام (<= 16 کاراکتر)
    for r in RANKS:
        assert len(r.name_fa) <= 16, f"نام '{r.name_fa}' بیش از ۱۶ کاراکتر است!"
        assert not any(ord(c) > 0x1F000 for c in r.name_fa), f"نام '{r.name_fa}' نباید ایموجی داشته باشد!"
        assert r.insignia, f"نشان مقام '{r.name_fa}' نباید خالی باشد!"

    print("✅ ساختار ۲۱ مقام و محدودیت ۱۶ کاراکتری تگ‌ها تأیید شد.")


def test_find_rank() -> None:
    # جستجو با عدد انگلیسی
    r1 = find_rank(1)
    assert r1 is not None and r1.name_fa == "سرباز صفر"

    r17 = find_rank("17")
    assert r17 is not None and r17.name_fa == "سرهنگ"

    # جستجو با عدد فارسی
    r21 = find_rank("۲۱")
    assert r21 is not None and r21.name_fa == "ارتشبد"

    # جستجو با نام فارسی دقیق
    r_major = find_rank("سرگرد")
    assert r_major is not None and r_major.level == 15

    # جستجو با حروف عربی (ي/ك)
    r_ar = find_rank("سرباز يكم")  # با ي و ك عربی
    assert r_ar is not None and r_ar.level == 2

    r_ar2 = find_rank("سرتيپ")  # با ي عربی
    assert r_ar2 is not None and r_ar2.level == 18

    # جستجو با فاصله و نیم‌فاصله
    r_sarhang2 = find_rank("سرهنگ\u200cدوم")  # با نیم‌فاصله
    assert r_sarhang2 is not None and r_sarhang2.level == 16

    # مقادیر خارج از محدوده
    assert find_rank(0) is None
    assert find_rank(25) is None
    assert find_rank("ناشناس_کاملاً_بی‌ربط") is None

    print("✅ جستجوی هوشمند مقام‌ها با اعداد، نام‌ها و املای عربی/نیم‌فاصله تأیید شد.")


if __name__ == "__main__":
    print("🚀 اجرای آزمون‌های جدول مقام‌ها...")
    test_ranks_structure()
    test_find_rank()
    print("🎉 تمامی آزمون‌های ranks.py سبز شدند!")
