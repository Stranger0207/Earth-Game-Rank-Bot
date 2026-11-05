"""مدل‌های ثبت وقایع فصلی و اسنپ‌شات‌های روستر بازیکنان."""

from __future__ import annotations

import datetime
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base, utcnow


class SeasonEvent(Base):
    """ثبت واقعه‌ی اتمام فصل جهت تضمین Idempotency و گزارش‌گیری."""

    __tablename__ = "season_events"

    # شناسه یکتای رویداد (تولید شده در ربات اصلی یا دستور دستی)
    event_id: Mapped[str] = mapped_column(String(64), primary_key=True)

    # منبع فراخوانی: webhook یا manual
    source: Mapped[str] = mapped_column(String(32), default="webhook", nullable=False)

    # تعداد کل بازیکنان حاضر در پیلود
    players_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # تعداد ارتقایافته‌ها
    promoted_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # تعداد کسانی که در سقف ارتقای خودکار (سطح ۱۷) مانده‌اند
    capped_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # تعداد کاربرانی که در صف اعمال تگ یا با خطای تگ مواجه شده‌اند
    tag_failed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # وضعیت پردازش: processed / failed
    status: Mapped[str] = mapped_column(String(32), default="processed", nullable=False)

    # ذخیره خام پیلود دریافتی جهت ممیزی و بازبینی
    payload_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)

    # زمان شروع و پایان پردازش
    started_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    finished_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class RosterSnapshot(Base):
    """عکس لحظه‌ای (Snapshot) از فهرست بازیکنان دریافت شده از ربات اصلی."""

    __tablename__ = "roster_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # تاریخ دریافت
    fetched_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    # محتوای JSON لیست بازیکنان
    players_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)

    # منبع دریافت: http یا db
    source: Mapped[str] = mapped_column(String(32), default="http", nullable=False)
