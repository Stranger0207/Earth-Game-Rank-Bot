"""
سرویس مدیریت، ردگیری و شناسایی اعضای گروه (MemberService).
"""

from __future__ import annotations

import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.db.base import utcnow
from ...core.db.models.member import Member
from ...core.events import MemberJoined, event_bus
from ...domain.ranks import DEFAULT_LEVEL

logger = logging.getLogger(__name__)


class MemberService:
    """سرویس عملیات مربوط به اعضای گروه."""

    @staticmethod
    async def get_by_id(session: AsyncSession, telegram_id: int) -> Member | None:
        """یافتن عضو بر اساس شناسه عددی تلگرام."""
        stmt = select(Member).where(Member.telegram_id == telegram_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_username(session: AsyncSession, username: str) -> Member | None:
        """یافتن عضو بر اساس نام کاربری (بدون @)."""
        clean_user = username.lstrip("@").lower().strip()
        stmt = select(Member).where(Member.username.ilike(clean_user))
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def track_activity(
        cls,
        session: AsyncSession,
        telegram_id: int,
        username: str | None = None,
        full_name: str = "",
        is_in_group: bool = True,
    ) -> Member:
        """
        ثبت یا به‌روزرسانی آخرین زمان مشاهده و اطلاعات هویتی کاربر در گروه.
        اگر کاربر در سیستم ثبت نباشد، با سطح پیش‌فرض ۱ (سرباز صفر) ثبت می‌شود.
        """
        clean_user = username.lstrip("@").strip() if username else None
        member = await cls.get_by_id(session, telegram_id)
        now = utcnow()

        if member is None:
            # کاربر برای بار اول در سیستم مشاهده شده است
            member = Member(
                telegram_id=telegram_id,
                username=clean_user,
                full_name=full_name,
                rank_level=DEFAULT_LEVEL,
                seasons_participated=0,
                is_player=False,
                in_group=is_in_group,
                tag_synced=False,
                rank_reached_at=now,
                first_seen_at=now,
                last_seen_at=now,
            )
            session.add(member)
            await session.commit()

            # انتشار رویداد ورود عضو جدید
            await event_bus.emit(
                MemberJoined(
                    telegram_id=telegram_id,
                    username=clean_user,
                    full_name=full_name,
                    rank_level=DEFAULT_LEVEL,
                    is_restored=False,
                )
            )
            logger.info("عضو جدید با سطح پیش‌فرض ۱ ثبت شد: %s (%s)", full_name, telegram_id)
        else:
            # به‌روزرسانی نام و آخرین زمان مشاهده
            changed = False
            if clean_user and member.username != clean_user:
                member.username = clean_user
                changed = True
            if full_name and member.full_name != full_name:
                member.full_name = full_name
                changed = True
            if member.in_group != is_in_group:
                member.in_group = is_in_group
                changed = True
            member.last_seen_at = now

            if changed:
                await session.commit()

        return member

    @classmethod
    async def handle_join(
        cls,
        session: AsyncSession,
        telegram_id: int,
        username: str | None,
        full_name: str,
    ) -> Member:
        """
        مدیریت ورود کاربر به گروه:
        - اگر قبلاً عضو بوده و مقام داشته: بازگردانی مقام و وضعیت in_group=True
        - اگر بار اول است: انتصاب سطح ۱ (سرباز صفر)
        """
        clean_user = username.lstrip("@").strip() if username else None
        member = await cls.get_by_id(session, telegram_id)
        now = utcnow()

        if member is None:
            member = Member(
                telegram_id=telegram_id,
                username=clean_user,
                full_name=full_name,
                rank_level=DEFAULT_LEVEL,
                seasons_participated=0,
                is_player=False,
                in_group=True,
                tag_synced=False,
                rank_reached_at=now,
                first_seen_at=now,
                last_seen_at=now,
            )
            session.add(member)
            await session.commit()

            await event_bus.emit(
                MemberJoined(
                    telegram_id=telegram_id,
                    username=clean_user,
                    full_name=full_name,
                    rank_level=DEFAULT_LEVEL,
                    is_restored=False,
                )
            )
            logger.info("ورود عضو جدید به گروه با سطح ۱: %s (%s)", full_name, telegram_id)
        else:
            member.in_group = True
            member.last_seen_at = now
            if clean_user:
                member.username = clean_user
            if full_name:
                member.full_name = full_name
            await session.commit()

            # انتشار رویداد بازگشت عضو به گروه با حفظ مقام ذخیره‌شده
            await event_bus.emit(
                MemberJoined(
                    telegram_id=telegram_id,
                    username=clean_user,
                    full_name=full_name,
                    rank_level=member.rank_level,
                    is_restored=True,
                )
            )
            logger.info(
                "بازگشت عضو قدیمی به گروه با حفظ سطح %s: %s (%s)",
                member.rank_level,
                full_name,
                telegram_id,
            )

        return member
