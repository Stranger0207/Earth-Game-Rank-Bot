"""
هندلرهای دستورات عمومی اعضا (/myrank, /top, /ranks, /history, /medals, /start).
"""

from __future__ import annotations

import logging
from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from sqlalchemy import func, select

from ...core.db.base import get_session
from ...core.db.models.achievement import Achievement
from ...core.db.models.history import RankHistory
from ...core.db.models.member import Member
from ...core.middlewares.throttling import ThrottlingMiddleware
from ...domain.ranks import DEFAULT_LEVEL, get_rank
from ..cards.generator import render_rank_card
from ..members.service import MemberService
from .texts import (
    history_timeline_text,
    medals_list_text,
    ranks_ladder_text,
    text_fallback_rank_card,
    top_leaderboard_text,
)

logger = logging.getLogger(__name__)

router = Router(name="member_commands")
router.message.middleware(ThrottlingMiddleware())
router.callback_query.middleware(ThrottlingMiddleware())


async def _send_rank_card_response(message: Message, user_id: int) -> None:
    """ارسال کارت گرافیکی مقام کاربر یا فال‌بک متنی در صورت بروز هرگونه خطا."""
    async for session in get_session():
        member = await MemberService.get_by_id(session, user_id)
        if not member:
            member = await MemberService.track_activity(
                session=session,
                telegram_id=user_id,
                username=message.from_user.username if message.from_user else None,
                full_name=message.from_user.full_name if message.from_user else "",
            )

        rank = get_rank(member.rank_level)
        medals_count = await session.scalar(
            select(func.count(Achievement.id)).where(Achievement.telegram_id == user_id)
        ) or 0

        name = member.full_name or member.username or f"کاربر {user_id}"

        # تلاش برای تولید و ارسال کارت تصویری PNG
        try:
            buf = render_rank_card(
                full_name=name,
                rank_name=rank.name_fa,
                level=rank.level,
                tier=rank.tier,
                insignia=rank.insignia,
                seasons_participated=member.seasons_participated,
                medals_count=medals_count,
            )
            photo = BufferedInputFile(buf.getvalue(), filename=f"card_{user_id}.png")
            await message.reply_photo(photo=photo)
            return
        except Exception as exc:
            logger.warning("تولید کارت تصویری شکست خورد، ارسال نسخه متنی fallback: %s", exc)

        # نسخه متنی Fallback
        text = text_fallback_rank_card(member, rank, medals_count)
        await message.reply(text)


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """دستور /start در چت خصوصی."""
    if not message.from_user:
        return
    await _send_rank_card_response(message, message.from_user.id)


@router.message(Command("myrank"))
@router.message(Command("rank"))
async def cmd_myrank(message: Message) -> None:
    """مشاهده کارت مقام خود کاربر."""
    if not message.from_user:
        return
    await _send_rank_card_response(message, message.from_user.id)


@router.message(Command("top"))
async def cmd_top(message: Message) -> None:
    """نمایش جدول افتخار و برترین رتبه‌ها."""
    async for session in get_session():
        stmt = (
            select(Member)
            .where(Member.in_group.is_(True))
            .order_by(Member.rank_level.desc(), Member.rank_reached_at.asc())
            .limit(10)
        )
        res = await session.execute(stmt)
        members = list(res.scalars().all())

        items = [(m, get_rank(m.rank_level)) for m in members]
        text = top_leaderboard_text(items)
        await message.reply(text)


@router.message(Command("ranks"))
async def cmd_ranks(message: Message) -> None:
    """نمایش نردبان ۲۱ مقام و جایگاه کاربر."""
    user_id = message.from_user.id if message.from_user else 0
    async for session in get_session():
        stmt = select(Member.rank_level, func.count(Member.telegram_id)).group_by(Member.rank_level)
        res = await session.execute(stmt)
        level_counts = dict(res.all())

        user_member = await MemberService.get_by_id(session, user_id)
        user_level = user_member.rank_level if user_member else DEFAULT_LEVEL

        text = ranks_ladder_text(level_counts, user_level)
        await message.reply(text)


@router.message(Command("history"))
async def cmd_history(message: Message) -> None:
    """مشاهده خط زمانی تغییرات مقام خود کاربر."""
    if not message.from_user:
        return
    user_id = message.from_user.id

    async for session in get_session():
        stmt = (
            select(RankHistory)
            .where(RankHistory.telegram_id == user_id)
            .order_by(RankHistory.created_at.desc())
            .limit(15)
        )
        res = await session.execute(stmt)
        histories = list(res.scalars().all())

        name = message.from_user.full_name or "شما"
        text = history_timeline_text(name, histories)
        await message.reply(text)


@router.message(Command("medals"))
async def cmd_medals(message: Message) -> None:
    """مشاهده نشان‌های کسب‌شده و قفل‌شده کاربر."""
    if not message.from_user:
        return
    user_id = message.from_user.id

    async for session in get_session():
        stmt = select(Achievement.key).where(Achievement.telegram_id == user_id)
        res = await session.execute(stmt)
        keys = set(res.scalars().all())

        text = medals_list_text(keys)
        await message.reply(text)


# کال‌بک‌های دکمه‌های زیر ابلاغیه
@router.callback_query(F.data == "member_cmd:myrank")
async def on_cb_myrank(call: CallbackQuery) -> None:
    await _send_rank_card_response(call.message, call.from_user.id)
    await call.answer()


@router.callback_query(F.data == "member_cmd:top")
async def on_cb_top(call: CallbackQuery) -> None:
    async for session in get_session():
        stmt = (
            select(Member)
            .where(Member.in_group.is_(True))
            .order_by(Member.rank_level.desc(), Member.rank_reached_at.asc())
            .limit(10)
        )
        res = await session.execute(stmt)
        members = list(res.scalars().all())
        items = [(m, get_rank(m.rank_level)) for m in members]
        text = top_leaderboard_text(items)
        await call.message.reply(text)
    await call.answer()


@router.callback_query(F.data == "member_cmd:ranks")
async def on_cb_ranks(call: CallbackQuery) -> None:
    user_id = call.from_user.id
    async for session in get_session():
        stmt = select(Member.rank_level, func.count(Member.telegram_id)).group_by(Member.rank_level)
        res = await session.execute(stmt)
        level_counts = dict(res.all())

        user_member = await MemberService.get_by_id(session, user_id)
        user_level = user_member.rank_level if user_member else DEFAULT_LEVEL

        text = ranks_ladder_text(level_counts, user_level)
        await call.message.reply(text)
    await call.answer()
