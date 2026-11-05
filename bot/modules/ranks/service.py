"""
سرویس تخصصی مدیریت مقام‌ها، ارتقا، تنزل، ثبت تاریخچه و انتشار رویدادها.
"""

from __future__ import annotations

import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.db.base import utcnow
from ...core.db.models.history import RankHistory
from ...core.db.models.member import Member
from ...core.events import RankChanged, event_bus
from ...domain.promotion import (
    clamp,
    demote_manual,
    promote_manual,
)
from ...domain.ranks import Rank, get_rank

logger = logging.getLogger(__name__)


class RankService:
    """عملیات ارتقا، تنزل و تغییر مقام اعضا."""

    @classmethod
    async def get_rank_info(
        cls, session: AsyncSession, telegram_id: int
    ) -> tuple[Member | None, Rank | None]:
        """دریافت رکورد عضو و شیء مقام فعلی او."""
        stmt = select(Member).where(Member.telegram_id == telegram_id)
        res = await session.execute(stmt)
        member = res.scalar_one_or_none()
        if not member:
            return None, None
        return member, get_rank(member.rank_level)

    @classmethod
    async def promote(
        cls,
        session: AsyncSession,
        telegram_id: int,
        delta: int = 1,
        reason: str | None = None,
        actor_id: int | None = None,
        source: str = "manual",
    ) -> tuple[Member, int, int]:
        """
        ارتقای مقام عضو به تعداد delta درجه.
        خروجی: (عضو به‌روزرسانی‌شده، سطح قبلی، سطح جدید)
        """
        stmt = select(Member).where(Member.telegram_id == telegram_id).with_for_update()
        res = await session.execute(stmt)
        member = res.scalar_one_or_none()

        if not member:
            now = utcnow()
            member = Member(
                telegram_id=telegram_id,
                rank_level=1,
                rank_reached_at=now,
                first_seen_at=now,
                last_seen_at=now,
            )
            session.add(member)

        old_level = member.rank_level
        new_level, act_delta = promote_manual(old_level, delta)

        if act_delta > 0:
            member.rank_level = new_level
            member.tag_synced = False
            member.rank_reached_at = utcnow()

            # ثبت تاریخچه‌ی تغییر مقام
            history = RankHistory(
                telegram_id=telegram_id,
                old_level=old_level,
                new_level=new_level,
                delta=act_delta,
                source=source,
                reason=reason,
                actor_id=actor_id,
            )
            session.add(history)
            await session.commit()

            # انتشار رویداد جهت اعمال تگ و ارسال اعلانات
            await event_bus.emit(
                RankChanged(
                    telegram_id=telegram_id,
                    old_level=old_level,
                    new_level=new_level,
                    source=source,
                    reason=reason,
                    actor_id=actor_id,
                    username=member.username,
                    full_name=member.full_name,
                )
            )
            logger.info("ارتقای عضو %s: %s -> %s (منبع: %s)", telegram_id, old_level, new_level, source)

        return member, old_level, new_level

    @classmethod
    async def demote(
        cls,
        session: AsyncSession,
        telegram_id: int,
        delta: int = 1,
        reason: str | None = None,
        actor_id: int | None = None,
        source: str = "manual",
    ) -> tuple[Member, int, int]:
        """
        تنزل مقام عضو به میزان delta درجه.
        خروجی: (عضو، سطح قبلی، سطح جدید)
        """
        stmt = select(Member).where(Member.telegram_id == telegram_id).with_for_update()
        res = await session.execute(stmt)
        member = res.scalar_one_or_none()

        if not member:
            now = utcnow()
            member = Member(
                telegram_id=telegram_id,
                rank_level=1,
                rank_reached_at=now,
                first_seen_at=now,
                last_seen_at=now,
            )
            session.add(member)

        old_level = member.rank_level
        new_level, act_delta = demote_manual(old_level, delta)

        if act_delta > 0:
            member.rank_level = new_level
            member.tag_synced = False
            member.rank_reached_at = utcnow()

            history = RankHistory(
                telegram_id=telegram_id,
                old_level=old_level,
                new_level=new_level,
                delta=-act_delta,
                source=source,
                reason=reason,
                actor_id=actor_id,
            )
            session.add(history)
            await session.commit()

            await event_bus.emit(
                RankChanged(
                    telegram_id=telegram_id,
                    old_level=old_level,
                    new_level=new_level,
                    source=source,
                    reason=reason,
                    actor_id=actor_id,
                    username=member.username,
                    full_name=member.full_name,
                )
            )
            logger.info("تنزل عضو %s: %s -> %s", telegram_id, old_level, new_level)

        return member, old_level, new_level

    @classmethod
    async def set_rank(
        cls,
        session: AsyncSession,
        telegram_id: int,
        target_level: int,
        reason: str | None = None,
        actor_id: int | None = None,
        source: str = "setrank",
    ) -> tuple[Member, int, int]:
        """انتصاب مستقیم یک مقام مشخص به عضو."""
        target_lvl = clamp(target_level)

        stmt = select(Member).where(Member.telegram_id == telegram_id).with_for_update()
        res = await session.execute(stmt)
        member = res.scalar_one_or_none()

        if not member:
            now = utcnow()
            member = Member(
                telegram_id=telegram_id,
                rank_level=1,
                rank_reached_at=now,
                first_seen_at=now,
                last_seen_at=now,
            )
            session.add(member)

        old_level = member.rank_level
        if old_level != target_lvl:
            member.rank_level = target_lvl
            member.tag_synced = False
            member.rank_reached_at = utcnow()

            history = RankHistory(
                telegram_id=telegram_id,
                old_level=old_level,
                new_level=target_lvl,
                delta=target_lvl - old_level,
                source=source,
                reason=reason,
                actor_id=actor_id,
            )
            session.add(history)
            await session.commit()

            await event_bus.emit(
                RankChanged(
                    telegram_id=telegram_id,
                    old_level=old_level,
                    new_level=target_lvl,
                    source=source,
                    reason=reason,
                    actor_id=actor_id,
                    username=member.username,
                    full_name=member.full_name,
                )
            )
            logger.info("انتصاب مقام عضو %s به سطح %s", telegram_id, target_lvl)

        return member, old_level, target_lvl
