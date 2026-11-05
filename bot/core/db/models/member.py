"""مدل‌های دیتابیس اعضای گروه و کاربران."""

from __future__ import annotations

import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base, utcnow


class Member(Base):
    """عضو شناسایی‌شده در گروه یا بازی تلگرام."""

    __tablename__ = "members"

    # شناسه عددی تلگرام کاربر
    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    # نام کاربری بدون @
    username: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    # نام و نام خانوادگی تلگرام
    full_name: Mapped[str] = mapped_column(String(128), default="", nullable=False)

    # سطح مقام کاربر (۱ تا ۲۱) - پیش‌فرض ۱: سرباز صفر
    rank_level: Mapped[int] = mapped_column(Integer, default=1, nullable=False, index=True)

    # تعداد فصل‌های کامل بازی که کاربر در آن مشارکت داشته
    seasons_participated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # آیا کاربر در بازی اصلی کشور دارد/پلیر فعال است؟
    is_player: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # آیا کاربر هم‌اکنون در سوپرگروه حضور دارد؟
    in_group: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # وضعیت هماهنگی تگ تلگرام با مقام فعلی دیتابیس
    tag_synced: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # متن آخرین خطای همگام‌سازی تگ (مثلاً اگر کاربر ادمین باشد)
    tag_error: Mapped[str | None] = mapped_column(String(256), nullable=True)

    # تاریخ رسیدن به سطح مقام فعلی
    rank_reached_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    # تاریخ اولین مشاهده در سیستم
    first_seen_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    # تاریخ آخرین فعالیت یا مشاهده در گروه
    last_seen_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )
