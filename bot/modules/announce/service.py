"""
سرویس انتشار ابلاغیه‌های گروهی، گزارش‌های فصلی و پیام‌های خصوصی به بازیکنان.
"""

from __future__ import annotations

import logging
from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError
from aiogram.types import BufferedInputFile
from sqlalchemy import func, select

from ...core.config import get_settings
from ...core.db.base import get_session
from ...core.db.models.member import Member
from ...core.events import RankChanged, SeasonApplied
from ...core.utils.format import fa_number
from ...core.utils.html import bold
from ...domain.ranks import Rank, get_rank
from ..cards.generator import render_rank_card
from .keyboards import announcement_action_keyboard
from .texts import promotion_announcement_text, season_summary_text

logger = logging.getLogger(__name__)

# مقام‌های مایلستون که ورود به آن‌ها در گروه جشن گرفته می‌شود
MILESTONE_LEVELS = {15, 17, 18, 19, 20, 21}


class AnnounceService:
    """مدیریت ارسال پیام‌های گروهی و شخصی."""

    @classmethod
    async def announce_promotion(cls, bot: Bot, event: RankChanged) -> None:
        """
        ارسال ابلاغیه ترفیع به گروه در صورت ارتقای دستی مالک یا دستیابی به یک مایلستون.
        """
        old_rank = get_rank(event.old_level)
        new_rank = get_rank(event.new_level)

        is_manual = event.source == "manual" or event.actor_id is not None
        is_milestone = event.new_level in MILESTONE_LEVELS

        if not (is_manual or is_milestone):
            return

        settings = get_settings()
        name = event.full_name or event.username or f"کاربر {event.telegram_id}"
        text = promotion_announcement_text(
            full_name=name,
            telegram_id=event.telegram_id,
            old_rank=old_rank,
            new_rank=new_rank,
            reason=event.reason,
            is_legendary=(event.new_level >= 20),
        )

        try:
            await bot.send_message(
                chat_id=settings.target_chat_id,
                text=text,
                reply_markup=announcement_action_keyboard(),
            )
            logger.info("ابلاغیه ارتقای کاربر %s به گروه ارسال شد.", event.telegram_id)
        except Exception as exc:
            logger.error("خطا در ارسال ابلاغیه ارتقا به گروه: %s", exc)

    @classmethod
    async def send_dm_to_player(cls, bot: Bot, event: RankChanged) -> None:
        """ارسال پیام خصوصی به کاربر همراه با کارت مقام در صورت امکان."""
        try:
            rank = get_rank(event.new_level)
            name = event.full_name or event.username or "رزمنده گرامی"

            card_buf = render_rank_card(
                full_name=name,
                rank_name=rank.name_fa,
                level=rank.level,
                tier=rank.tier,
                insignia=rank.insignia,
                seasons_participated=1,
            )

            photo = BufferedInputFile(card_buf.getvalue(), filename=f"rank_{event.telegram_id}.png")
            caption = (
                f"🎖 <b>ترفیع درجه شما به ثبت رسید!</b>\n\n"
                f"مقام جدید: {bold(rank.name_fa)} ({rank.insignia})\n"
                f"رده نظامی: {bold(rank.tier)}\n\n"
                "🫡 با افتخار به خدمت ادامه دهید!"
            )
            await bot.send_photo(chat_id=event.telegram_id, photo=photo, caption=caption)
            logger.info("کارت مقام در پیوی به %s ارسال شد.", event.telegram_id)
        except TelegramForbiddenError:
            # کاربر ربات را استارت نکرده یا بلاک کرده است؛ با سکوت نادیده گرفته می‌شود
            pass
        except Exception as exc:
            logger.debug("ارسال پیام خصوصی به %s ناموفق بود: %s", event.telegram_id, exc)

    @classmethod
    async def announce_season_summary(cls, bot: Bot, event: SeasonApplied) -> None:
        """ارسال خلاصه پایان فصل در یک پست جامع بدون صدا (disable_notification=True)."""
        settings = get_settings()

        tier_counts = {
            "سرباز": 0,
            "درجه‌دار": 0,
            "استوار": 0,
            "افسریار": 0,
            "افسر جوان": 0,
            "افسر ارشد": 0,
            "ژنرال": 0,
            "فرماندهی عالی": 0,
        }

        async for session in get_session():
            stmt = select(Member.rank_level)
            res = await session.execute(stmt)
            levels = res.scalars().all()
            for lvl in levels:
                r = get_rank(lvl)
                if r.tier in tier_counts:
                    tier_counts[r.tier] += 1

        text = season_summary_text(
            promoted_count=event.promoted_count,
            capped_count=event.capped_count,
            total_players=event.players_count,
            tier_counts=tier_counts,
        )

        try:
            await bot.send_message(
                chat_id=settings.target_chat_id,
                text=text,
                disable_notification=True,
                reply_markup=announcement_action_keyboard(),
            )
            logger.info("خلاصه پایان فصل با موفقیت در گروه منتشر شد.")
        except Exception as exc:
            logger.error("خطا در ارسال خلاصه پایان فصل به گروه: %s", exc)


async def on_rank_changed_announcement_handler(event: RankChanged) -> None:
    from ...core.loader import bot
    await AnnounceService.announce_promotion(bot, event)
    await AnnounceService.send_dm_to_player(bot, event)


async def on_season_applied_announcement_handler(event: SeasonApplied) -> None:
    from ...core.loader import bot
    await AnnounceService.announce_season_summary(bot, event)
