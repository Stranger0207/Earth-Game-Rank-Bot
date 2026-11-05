"""
سرویس ذخیره‌سازی، خواندن و اسنپ‌شات‌گیری از فهرست بازیکنان فعال (RosterService).
"""

from __future__ import annotations

import json
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.db.base import utcnow
from ...core.db.models.season import RosterSnapshot
from .provider import get_roster_provider

logger = logging.getLogger(__name__)


class RosterService:
    """عملیات دریافت و مدیریت اسنپ‌شات‌های روستر بازیکنان."""

    @classmethod
    async def fetch_and_snapshot(cls, session: AsyncSession) -> tuple[RosterSnapshot, list[dict]]:
        """
        دریافت زنده فهرست بازیکنان از ربات اصلی و ذخیره اسنپ‌شات پایدار در پایگاه داده.
        این متد هیچ ارتقای مقامی انجام نمی‌دهد و تنها عکس لحظه‌ای از بازیکنان ثبت می‌کند.
        """
        provider = get_roster_provider()
        players = await provider.fetch_roster()

        snapshot = RosterSnapshot(
            fetched_at=utcnow(),
            players_json=json.dumps(players, ensure_ascii=False),
            source=provider.__class__.__name__,
        )
        session.add(snapshot)
        await session.commit()
        logger.info("اسنپ‌شات جدید روستر شامل %s بازیکن با موفقیت ثبت شد.", len(players))
        return snapshot, players

    @classmethod
    async def get_latest_snapshot(cls, session: AsyncSession) -> tuple[RosterSnapshot | None, list[dict]]:
        """دریافت آخرین اسنپ‌شات ذخیره‌شده روستر از دیتابیس."""
        stmt = select(RosterSnapshot).order_by(RosterSnapshot.id.desc()).limit(1)
        res = await session.execute(stmt)
        snapshot = res.scalar_one_or_none()
        if not snapshot:
            return None, []
        try:
            players = json.loads(snapshot.players_json)
        except Exception:
            players = []
        return snapshot, players
