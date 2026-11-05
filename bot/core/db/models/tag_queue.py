"""صف پایدار اعمال تگ تلگرام جهت رعایت محدودیت‌های نرخ و خطایابی."""

from __future__ import annotations

import datetime
from sqlalchemy import BigInteger, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base, utcnow


class TagQueueItem(Base):
    """آیتم موجود در صف اعمال تگ به عضو گروه."""

    __tablename__ = "tag_queue"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # شناسه کاربر
    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)

    # تگ متنی که باید اعمال شود (حداکثر ۱۶ کاراکتر)
    target_tag: Mapped[str] = mapped_column(String(64), nullable=False)

    # تعداد دفعات تلاش انجام‌شده
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # زمان مجاز برای تلاش بعدی (جهت مدیریت backoff و RetryAfter)
    next_try_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False, index=True
    )

    # متن آخرین خطا
    last_error: Mapped[str | None] = mapped_column(String(256), nullable=True)

    # وضعیت: pending / success / failed
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False, index=True)
