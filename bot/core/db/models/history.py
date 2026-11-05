"""تاریخچه‌ی ارتقا، تنزل و تغییرات مقام اعضا."""

from __future__ import annotations

import datetime
from sqlalchemy import BigInteger, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base, utcnow


class RankHistory(Base):
    """ثبت لاگ هر تغییر مقام جهت پیگیری، نمایش سوابق و جلوگیری از خطا."""

    __tablename__ = "rank_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # شناسه تلگرام کاربری که مقامش تغییر یافته
    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)

    # سطح قبلی
    old_level: Mapped[int] = mapped_column(Integer, nullable=False)

    # سطح جدید
    new_level: Mapped[int] = mapped_column(Integer, nullable=False)

    # میزان تغییر (مثبت برای ارتقا، منفی برای تنزل)
    delta: Mapped[int] = mapped_column(Integer, nullable=False)

    # منبع تغییر: season / manual / setrank / join / bulk / import
    source: Mapped[str] = mapped_column(String(32), nullable=False)

    # دلیل ذکر شده توسط مالک (اختیاری)
    reason: Mapped[str | None] = mapped_column(String(256), nullable=True)

    # شناسه کاربری فرد تغییردهنده (برای دستورهای مالک)
    actor_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # شناسه رویداد فصل (در صورت ناشی شدن از پایان فصل)
    season_event_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    # زمان ثبت رویداد
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False, index=True
    )
