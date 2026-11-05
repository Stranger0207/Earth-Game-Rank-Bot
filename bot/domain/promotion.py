"""
قوانین ترفیع، تنزل و محاسبات پیشرفت درجه (Pure Functions).
توابع این ماژول مستقل از دیتابیس و فریمورک تلگرام بوده و کاملاً Unit-Testable هستند.
"""

from __future__ import annotations

from .ranks import (
    AUTO_PROMOTION_CAP_LEVEL,
    DEFAULT_LEVEL,
    MAX_LEVEL,
    clamp,
)


def promote_auto(current_level: int) -> tuple[int, bool]:
    """
    اعمال ارتقای خودکار پایان فصل.
    - سطوح کمتر از ۱۷ (سرهنگ) یک درجه ارتقا می‌یابند.
    - سطوح ۱۷ و بالاتر بدون تغییر باقی می‌مانند (منحصراً با ارتقای دستی مالک).
    خروجی: (سطح جدید، آیا ارتقا یافت یا در سقف ماند)
    """
    lvl = clamp(current_level)
    if lvl < AUTO_PROMOTION_CAP_LEVEL:
        return lvl + 1, True
    return lvl, False


def promote_manual(current_level: int, delta: int = 1) -> tuple[int, int]:
    """
    ارتقای دستی توسط مالک (بدون محدودیت سقف ۱۷، تا سقف مطلق ۲۱).
    خروجی: (سطح جدید، میزان واقعی ارتقا)
    """
    if delta <= 0:
        return clamp(current_level), 0

    lvl = clamp(current_level)
    new_lvl = min(MAX_LEVEL, lvl + delta)
    actual_delta = new_lvl - lvl
    return new_lvl, actual_delta


def demote_manual(current_level: int, delta: int = 1) -> tuple[int, int]:
    """
    تنزل دستی توسط مالک (حداقل سطح ۱: سرباز صفر).
    خروجی: (سطح جدید، میزان واقعی کاهش)
    """
    if delta <= 0:
        return clamp(current_level), 0

    lvl = clamp(current_level)
    new_lvl = max(DEFAULT_LEVEL, lvl - delta)
    actual_delta = lvl - new_lvl
    return new_lvl, actual_delta


def is_at_auto_cap(level: int) -> bool:
    """آیا کاربر به سقف ارتقای خودکار فصلی رسیده یا فراتر رفته است؟"""
    return level >= AUTO_PROMOTION_CAP_LEVEL


def calculate_progress_ratio(level: int) -> float:
    """
    محاسبه‌ی درصد پیشرفت نسبت به سقف خودکار (سطح ۱۷).
    سطح ۱ = 0.0، سطح ۱۷ = 1.0.
    """
    lvl = clamp(level)
    if lvl >= AUTO_PROMOTION_CAP_LEVEL:
        return 1.0
    return float(lvl - DEFAULT_LEVEL) / float(AUTO_PROMOTION_CAP_LEVEL - DEFAULT_LEVEL)
