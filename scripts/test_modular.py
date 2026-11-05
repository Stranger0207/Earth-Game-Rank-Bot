"""
آزمون استقلال ماژولار: بارگذاری سیستم با فهرست انتخابی ماژول‌ها بدون بروز خطای ایمپورت.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from bot.core.registry import load_modules


def test_modular_loading() -> None:
    # ۱. بارگذاری فقط ماژول‌های پایه و حیاتی
    core_subset = ["members", "ranks", "tags"]
    loaded = load_modules(custom_modules=core_subset)
    assert set(loaded) == set(core_subset)
    print("✅ بارگذاری زیرمجموعه سبک ماژول‌ها با موفقیت تأیید شد.")

    # ۲. بارگذاری مجدد با تمام ماژول‌ها
    all_modules = [
        "members", "ranks", "tags", "achievements", "cards",
        "announce", "season", "roster", "owner_panel",
        "member_commands", "audit", "export", "webapi"
    ]
    loaded_all = load_modules(custom_modules=all_modules)
    assert len(loaded_all) == len(all_modules)
    print("✅ بارگذاری بدون تداخل تمام ۱۳ ماژول پروژه با موفقیت تأیید شد.")


if __name__ == "__main__":
    print("🚀 اجرای آزمون ماژولاریتی...")
    test_modular_loading()
    print("🎉 آزمون استقلال ماژولار سبز شد!")
