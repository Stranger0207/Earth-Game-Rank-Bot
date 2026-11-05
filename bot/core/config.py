"""
تنظیمات و پیکربندی ربات با استفاده از pydantic-settings.
تمامی مقادیر از محیط یا فایل .env خوانده می‌شوند و هیچ سکرتی هاردکد نمی‌شود.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """مدل اعتبارسنجی و نگهداری تنظیمات برنامه."""

    # توکن ربات تلگرام
    bot_token: str = ""

    # شناسه‌های عددی مالکان مجاز
    owner_ids: list[int] | str = []

    # گروه تلگرامی اصلی (Supergroup) که تگ‌ها در آن مدیریت می‌شوند
    target_chat_id: int = -1002641478967

    # کانال یا گروه برای ارسال لاگ تغییرات و گزارش‌های سیستمی (اختیاری)
    log_chat_id: int | None = None

    # آدرس اتصال به پایگاه داده (PostgreSQL در پروداکشن، SQLite در تست‌ها)
    database_url: str = "sqlite+aiosqlite:///:memory:"

    # کلید محرمانه مشترک برای امضای HMAC بین ربات اصلی و ربات مقام
    rank_sync_secret: str = ""

    # تنظیمات وب‌سرور داخلی ربات مقام
    rank_bot_api_host: str = "127.0.0.1"
    rank_bot_api_port: int = 8091

    # آدرس وب‌سرور داخلی ربات اصلی
    main_bot_api_url: str = "http://127.0.0.1:8090"

    # منبع دریافت فهرست بازیکنان (http یا db)
    roster_source: str = "http"

    # فهرست ماژول‌های فعال (اگر خالی باشد همه فعال خواهند بود)
    enabled_modules: list[str] | str = []

    # خروج خودکار از گروه‌هایی که گروه هدف نیستند
    auto_leave_unauthorized_groups: bool = True

    # مدت کول‌داون برای دستورهای اعضا جهت پیشگیری از اسپم (ثانیه)
    member_cmd_cooldown_sec: int = 20

    # منطقه‌ی زمانی پیش‌فرض
    tz: str = "Asia/Tehran"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @field_validator("log_chat_id", mode="before")
    @classmethod
    def parse_log_chat_id(cls, v: Any) -> int | None:
        """پارس کردن شناسه چت لاگ (تبدیل رشته‌های خالی به None)."""
        if v is None or v == "":
            return None
        if isinstance(v, str):
            cleaned = v.strip()
            if not cleaned or cleaned.lower() in ("none", "null"):
                return None
            return int(cleaned)
        return int(v)

    @field_validator("target_chat_id", mode="before")
    @classmethod
    def parse_target_chat_id(cls, v: Any) -> int:
        """پارس کردن شناسه چت هدف با حفظ پیش‌فرض در صورت خالی بودن."""
        if v is None or v == "":
            return -1002641478967
        return int(v)

    @field_validator("member_cmd_cooldown_sec", "rank_bot_api_port", mode="before")
    @classmethod
    def parse_ints_with_defaults(cls, v: Any, info) -> int:
        """پارس کردن پورت و کول‌داون با حفظ پیش‌فرض در صورت خالی بودن در env."""
        if v is None or v == "":
            if info.field_name == "rank_bot_api_port":
                return 8091
            if info.field_name == "member_cmd_cooldown_sec":
                return 20
        return int(v)

    @field_validator("owner_ids", mode="before")
    @classmethod
    def parse_owner_ids(cls, v: Any) -> list[int]:
        """پارس کردن شناسه‌های مالکان از رشته‌های حاوی کاما یا لیست مستقیم."""
        if isinstance(v, str):
            cleaned = v.strip()
            if not cleaned:
                return []
            return [int(x.strip()) for x in cleaned.split(",") if x.strip()]
        if isinstance(v, (list, tuple)):
            return [int(x) for x in v]
        return []

    @field_validator("enabled_modules", mode="before")
    @classmethod
    def parse_enabled_modules(cls, v: Any) -> list[str]:
        """پارس کردن فهرست ماژول‌های فعال از رشته یا لیست."""
        if isinstance(v, str):
            cleaned = v.strip()
            if not cleaned:
                return []
            return [x.strip() for x in cleaned.split(",") if x.strip()]
        if isinstance(v, (list, tuple)):
            return [str(x).strip() for x in v if str(x).strip()]
        return []

    def is_owner(self, user_id: int) -> bool:
        """آیا کاربر جزء مالکان مجاز سیستم است؟"""
        if isinstance(self.owner_ids, (list, tuple, set)):
            return user_id in self.owner_ids
        return False


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """دریافت نمونه‌ی سراسری و کش‌شده‌ی تنظیمات."""
    return Settings()
