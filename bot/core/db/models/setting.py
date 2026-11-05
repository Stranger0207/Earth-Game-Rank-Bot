"""تنظیمات پویا و پایدار ربات."""

from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class DynamicSetting(Base):
    """تنظیمات پویای ربات که از طریق دستور /settings قابل تغییر هستند."""

    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(String(256), nullable=True)
