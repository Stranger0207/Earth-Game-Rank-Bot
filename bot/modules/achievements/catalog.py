"""
کاتالوگ نشان‌ها، مدال‌ها و افتخارات نظامی اعضا (Achievement Catalog).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AchievementDef:
    """تعریف مشخصات یک نشان نظامی."""

    key: str
    title: str
    description: str
    badge: str
    hint: str


ACHIEVEMENT_CATALOG: tuple[AchievementDef, ...] = (
    AchievementDef(
        key="first_step",
        title="نخستین گام",
        description="کسب اولین ترفیع درجه در خدمت نظامی.",
        badge="🥉",
        hint="رسیدن به سطح ۲ (سرباز یکم)",
    ),
    AchievementDef(
        key="veteran_3",
        title="کهنه‌سرباز برنزی",
        description="حضور فعال و پایدار در ۳ فصل متوالی بازی زمین.",
        badge="🎗",
        hint="تکمیل ۳ فصل خدمت",
    ),
    AchievementDef(
        key="veteran_5",
        title="کهنه‌سرباز نقره‌ای",
        description="حضور درخشان در ۵ فصل بازی زمین.",
        badge="🥈",
        hint="تکمیل ۵ فصل خدمت",
    ),
    AchievementDef(
        key="veteran_10",
        title="اسطوره خدمت طلایی",
        description="خدمت وفادارانه و شجاعانه در ۱۰ فصل بازی زمین.",
        badge="🥇",
        hint="تکمیل ۱۰ فصل خدمت",
    ),
    AchievementDef(
        key="colonel_achieved",
        title="سرهنگ میدان",
        description="رسیدن به سقف ارتقای خودکار نظامی (سطح ۱۷).",
        badge="🦅",
        hint="رسیدن به درجه سرهنگ",
    ),
    AchievementDef(
        key="general_star",
        title="ستاره ژنرال",
        description="ورود به شورای ژنرال‌ها و امرای ارتش (سطح ۱۸ یا بالاتر).",
        badge="⚡",
        hint="رسیدن به درجه سرتیپ یا بالاتر با حکم فرماندهی",
    ),
    AchievementDef(
        key="supreme_marshal",
        title="نشان عالی ارتشبد",
        description="دستیابی به بالاترین مقام در سلسله‌مراتب ارتش زمین (سطح ۲۱).",
        badge="💎",
        hint="رسیدن به درجه ارتشبد",
    ),
    AchievementDef(
        key="commander_honor",
        title="افتخار فرماندهی",
        description="کسب ترفیع ویژه تشویقی همراه با ثبت تقدیرنامه و دلیل توسط مالک.",
        badge="⚜️",
        hint="ترفیع دستی با ذکر دلیل شایستگی",
    ),
)

_CATALOG_MAP: dict[str, AchievementDef] = {a.key: a for a in ACHIEVEMENT_CATALOG}


def get_achievement_def(key: str) -> AchievementDef | None:
    """یافتن تعریف نشان بر اساس کلید."""
    return _CATALOG_MAP.get(key)
