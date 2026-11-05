"""
موتور بررسی شروط و اعطای خودکار نشان‌ها و مدال‌ها (Achievement Engine).
"""

from __future__ import annotations

import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.db.base import get_session, utcnow
from ...core.db.models.achievement import Achievement
from ...core.db.models.member import Member
from ...core.events import RankChanged
from .catalog import get_achievement_def

logger = logging.getLogger(__name__)


class AchievementEngine:
    """بررسی و اعطای نشان‌ها بر اساس سوابق و رویدادها."""

    @classmethod
    async def get_member_achievements(
        cls, session: AsyncSession, telegram_id: int
    ) -> list[Achievement]:
        """دریافت لیست نشان‌های کسب‌شده توسط یک عضو."""
        stmt = select(Achievement).where(Achievement.telegram_id == telegram_id)
        res = await session.execute(stmt)
        return list(res.scalars().all())

    @classmethod
    async def award_achievement(
        cls, session: AsyncSession, telegram_id: int, key: str
    ) -> bool:
        """اعطای یک نشان در صورت عدم وجود قبلی."""
        stmt = select(Achievement).where(
            Achievement.telegram_id == telegram_id,
            Achievement.key == key,
        )
        res = await session.execute(stmt)
        if res.scalar_one_or_none():
            return False

        ach = Achievement(
            telegram_id=telegram_id,
            key=key,
            awarded_at=utcnow(),
        )
        session.add(ach)
        await session.commit()
        logger.info("نشان '%s' به کاربر %s اعطا شد.", key, telegram_id)
        return True

    @classmethod
    async def evaluate_member(
        cls,
        session: AsyncSession,
        member: Member,
        recent_reason: str | None = None,
        recent_source: str | None = None,
    ) -> list[str]:
        """ارزیابی جامع شرایط عضو و اعطای نشان‌های واجد شرایط."""
        awarded_keys = []

        # ۱. نخستین گام (سطح >= ۲)
        if member.rank_level >= 2:
            if await cls.award_achievement(session, member.telegram_id, "first_step"):
                awarded_keys.append("first_step")

        # ۲. فصول خدمت (۳، ۵، ۱۰)
        if member.seasons_participated >= 3:
            if await cls.award_achievement(session, member.telegram_id, "veteran_3"):
                awarded_keys.append("veteran_3")
        if member.seasons_participated >= 5:
            if await cls.award_achievement(session, member.telegram_id, "veteran_5"):
                awarded_keys.append("veteran_5")
        if member.seasons_participated >= 10:
            if await cls.award_achievement(session, member.telegram_id, "veteran_10"):
                awarded_keys.append("veteran_10")

        # ۳. سرهنگ میدان (سطح >= ۱۷)
        if member.rank_level >= 17:
            if await cls.award_achievement(session, member.telegram_id, "colonel_achieved"):
                awarded_keys.append("colonel_achieved")

        # ۴. ستاره ژنرال (سطح >= ۱۸)
        if member.rank_level >= 18:
            if await cls.award_achievement(session, member.telegram_id, "general_star"):
                awarded_keys.append("general_star")

        # ۵. نشان عالی ارتشبد (سطح ۲۱)
        if member.rank_level >= 21:
            if await cls.award_achievement(session, member.telegram_id, "supreme_marshal"):
                awarded_keys.append("supreme_marshal")

        # ۶. افتخار فرماندهی (ارتقای دستی همراه با دلیل ثبت‌شده)
        if recent_source == "manual" and recent_reason:
            if await cls.award_achievement(session, member.telegram_id, "commander_honor"):
                awarded_keys.append("commander_honor")

        return awarded_keys


async def on_rank_changed_achievement_listener(event: RankChanged) -> None:
    """هنگام هر تغییر رنک، نشان‌های احتمالی کاربر ارزیابی می‌شوند."""
    async for session in get_session():
        m_stmt = select(Member).where(Member.telegram_id == event.telegram_id)
        m_res = await session.execute(m_stmt)
        member = m_res.scalar_one_or_none()
        if member:
            await AchievementEngine.evaluate_member(
                session=session,
                member=member,
                recent_reason=event.reason,
                recent_source=event.source,
            )
