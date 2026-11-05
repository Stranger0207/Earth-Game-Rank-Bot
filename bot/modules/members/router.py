"""
هندلرهای مربوط به رویدادهای ورود، خروج و فعالیت اعضا در سوپرگروه.
"""

from __future__ import annotations

import logging
from aiogram import F, Router
from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.types import ChatMemberUpdated, Message

from ...core.db.base import get_session
from .service import MemberService

logger = logging.getLogger(__name__)

router = Router(name="members")


@router.chat_member()
async def on_chat_member_updated(event: ChatMemberUpdated) -> None:
    """ردگیری تغییرات عضویت کاربران در گروه (جوین، لفت، کیک)."""
    user = event.new_chat_member.user
    if user.is_bot:
        return

    old_status = event.old_chat_member.status
    new_status = event.new_chat_member.status

    # اگر کاربر عضو گروه شده است
    if new_status in (
        ChatMemberStatus.MEMBER,
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.CREATOR,
        ChatMemberStatus.RESTRICTED,
    ):
        if old_status in (ChatMemberStatus.LEFT, ChatMemberStatus.KICKED):
            async for session in get_session():
                await MemberService.handle_join(
                    session=session,
                    telegram_id=user.id,
                    username=user.username,
                    full_name=user.full_name,
                )
    elif new_status in (ChatMemberStatus.LEFT, ChatMemberStatus.KICKED):
        # کاربر از گروه خارج یا اخراج شده است
        async for session in get_session():
            member = await MemberService.get_by_id(session, user.id)
            if member:
                member.in_group = False
                await session.commit()
                logger.info("عضو از گروه خارج شد: %s (%s)", user.full_name, user.id)


@router.message(F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))
async def on_group_message(message: Message) -> None:
    """ردگیری پیام‌ها در گروه برای به‌روزرسانی جدول اعضای شناخته‌شده."""
    if not message.from_user or message.from_user.is_bot:
        return

    # پردازش در صورت پیام‌های سرویسی ورود
    if message.new_chat_members:
        for new_user in message.new_chat_members:
            if not new_user.is_bot:
                async for session in get_session():
                    await MemberService.handle_join(
                        session=session,
                        telegram_id=new_user.id,
                        username=new_user.username,
                        full_name=new_user.full_name,
                    )
        return

    # پیام معمولی کاربر: به‌روزرسانی مشخصات هویتی و آخرین مشاهده
    async for session in get_session():
        await MemberService.track_activity(
            session=session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            full_name=message.from_user.full_name,
            is_in_group=True,
        )
