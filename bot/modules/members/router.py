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
