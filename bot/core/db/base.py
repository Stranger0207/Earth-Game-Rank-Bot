"""
زیرساخت دیتابیس: ساخت موتور ناهمگام (Async Engine)، کارخانه‌ی سشن و مکانیزم مهاجرت خودکار ستون‌ها.
"""

from __future__ import annotations

import datetime
from collections.abc import AsyncIterator

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from ..config import get_settings


class Base(DeclarativeBase):
    """کلاس پایه‌ی تمامی مدل‌های دیتابیس."""


# متغیرهای سراسری موتور و کارخانه‌ی سشن
_engine = None
_session_factory = None


def get_engine():
    """دریافت یا ساخت موتور دیتابیس به صورت lazy بر اساس تنظیمات جاری."""
    global _engine
    if _engine is None:
        settings = get_settings()
        kwargs = {}
        if not settings.database_url.startswith("sqlite"):
            kwargs["pool_pre_ping"] = True
        _engine = create_async_engine(settings.database_url, echo=False, **kwargs)
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """دریافت یا ساخت سشن‌میکر ناهمگام."""
    global _session_factory
    if _session_factory is None:
        engine = get_engine()
        _session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


async def get_session() -> AsyncIterator[AsyncSession]:
    """تولید یک سشن مستقل و بستن خودکار آن پس از اتمام کار."""
    factory = get_session_factory()
    async with factory() as session:
        yield session


# ستون‌هایی که در آپدیت‌ها ممکن است به جدول‌های موجود اضافه شوند: (جدول، نام ستون، تعریف ستون در SQL)
_COLUMN_MIGRATIONS: list[tuple[str, str, str]] = [
    ("members", "rank_reached_at", "TIMESTAMP WITH TIME ZONE"),
    ("members", "tag_error", "VARCHAR(256)"),
    ("rank_history", "season_event_id", "VARCHAR(64)"),
    ("season_events", "tag_failed_count", "INTEGER NOT NULL DEFAULT 0"),
]


def _apply_column_migrations(sync_conn) -> None:
    """
    اعمال ستون‌های جدید روی دیتابیس بدون نیاز به ابزارهای سنگین.
    در هر اجرا بررسی می‌کند که ستون وجود داشته باشد؛ در غیر این صورت آن را می‌سازد.
    """
    inspector = inspect(sync_conn)
    existing_tables = set(inspector.get_table_names())
    for table, column, ddl in _COLUMN_MIGRATIONS:
        if table not in existing_tables:
            continue
        existing_cols = {c["name"] for c in inspector.get_columns(table)}
        if column not in existing_cols:
            sync_conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))


async def init_db(custom_engine=None) -> None:
    """
    راه‌اندازی اولیه‌ی جداول دیتابیس و اجرای مهاجرت‌های سبک ستون‌ها.
    """
    # وارد کردن مدل‌ها تا متادیتای Base پر شود
    from . import models  # noqa: F401

    engine = custom_engine or get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # فقط در صورتی که دیتابیس از نوع حافظه‌ای sqlite خالی نباشد مهاجرت را چک می‌کنیم
        await conn.run_sync(_apply_column_migrations)


def utcnow() -> datetime.datetime:
    """زمان فعلی آگاه از منطقه زمانی UTC."""
    return datetime.datetime.now(datetime.timezone.utc)
