"""مدل نشان‌ها و دستاوردهای اعضا."""

from __future__ import annotations

import datetime
from sqlalchemy import BigInteger, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base, utcnow


class Achievement(Base):
    """مدال‌ها و افتخارات کسب‌شده توسط کاربران."""

    __tablename__ = "achievements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # شناسه تلگرام کاربر
    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)

    # کلید یکتای نشان (از کاتالوگ نشان‌ها)
    key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # زمان اعطای نشان
    awarded_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    __table_args__ = (
        UniqueConstraint("telegram_id", "key", name="uq_member_achievement"),
    )
