"""
ماژول شناسایی کاربر هدف (Target Resolver) برای دستورات مدیریتی و کاربری.
روش‌ها: ریپلای، آی‌دی عددی، منشن (@username)، text_mention و پیام فورواردشده در پیوی.
"""

from __future__ import annotations

from typing import NamedTuple
from aiogram.enums import MessageEntityType
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.db.models.member import Member
from .service import MemberService


class TargetResolution(NamedTuple):
    """نتیجه‌ی تحلیل و یافتن کاربر هدف."""

    member: Member | None
    telegram_id: int | None
    error_message: str | None = None
    remaining_text: str = ""


async def resolve_target(
    message: Message,
    session: AsyncSession,
    text_args: str | None = None,
) -> TargetResolution:
    """
    تشخیص هوشمند کاربر هدف از روی پیام و آرگومان‌های ارسالی.
    """
    raw_args = (text_args or "").strip()

    # ۱. بررسی ریپلای روی پیام یک کاربر در گروه
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user = message.reply_to_message.from_user
        if target_user.is_bot:
            return TargetResolution(
                member=None,
                telegram_id=None,
                error_message="⚠️ ربات‌ها نمی‌توانند دارای مقام نظامی باشند.",
            )

        member = await MemberService.track_activity(
            session=session,
            telegram_id=target_user.id,
            username=target_user.username,
            full_name=target_user.full_name,
        )
        return TargetResolution(
            member=member,
            telegram_id=target_user.id,
            remaining_text=raw_args,
        )

    # ۲. بررسی فوروارد پیام از کاربر در چت خصوصی
    if message.forward_from:
        target_user = message.forward_from
        if target_user.is_bot:
            return TargetResolution(
                member=None,
                telegram_id=None,
                error_message="⚠️ ربات‌ها نمی‌توانند دارای مقام نظامی باشند.",
            )

        member = await MemberService.track_activity(
            session=session,
            telegram_id=target_user.id,
            username=target_user.username,
            full_name=target_user.full_name,
        )
        return TargetResolution(
            member=member,
            telegram_id=target_user.id,
            remaining_text=raw_args,
        )

    # ۳. بررسی منشن مستقیم در متن (text_mention)
    if message.entities:
        for ent in message.entities:
            if ent.type == MessageEntityType.TEXT_MENTION and ent.user:
                target_user = ent.user
                if target_user.is_bot:
                    return TargetResolution(
                        member=None,
                        telegram_id=None,
                        error_message="⚠️ ربات‌ها نمی‌توانند دارای مقام نظامی باشند.",
                    )
                member = await MemberService.track_activity(
                    session=session,
                    telegram_id=target_user.id,
                    username=target_user.username,
                    full_name=target_user.full_name,
                )
                # حذف منشن از متن آرگومان
                return TargetResolution(
                    member=member,
                    telegram_id=target_user.id,
                    remaining_text=raw_args,
                )

    # ۴. بررسی آرگومان متنی (شناسه عددی یا @username)
    if not raw_args:
        return TargetResolution(
            member=None,
            telegram_id=None,
            error_message="❌ لطفاً روی پیام کاربر ریپلای کنید یا شناسه عددی / @نام‌کاربری او را وارد نمایید.",
        )

    parts = raw_args.split(maxsplit=1)
    first_token = parts[0].strip()
    rem_text = parts[1].strip() if len(parts) > 1 else ""

    # بررسی اگر شناسه عددی باشد
    ascii_token = first_token.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))
    if ascii_token.isdigit() or (ascii_token.startswith("-") and ascii_token[1:].isdigit()):
        uid = int(ascii_token)
        member = await MemberService.get_by_id(session, uid)
        if not member:
            # عضو تا کنون در گروه پیامی نداده است اما با شناسه ثبت اولیه می‌شود
            member = await MemberService.track_activity(
                session=session,
                telegram_id=uid,
                full_name=f"کاربر {uid}",
                is_in_group=False,
            )
        return TargetResolution(member=member, telegram_id=uid, remaining_text=rem_text)

    # بررسی اگر با @ یا به صورت نام کاربری باشد
    if first_token.startswith("@") or first_token.isalnum():
        clean_user = first_token.lstrip("@")
        member = await MemberService.get_by_username(session, clean_user)
        if member:
            return TargetResolution(
                member=member,
                telegram_id=member.telegram_id,
                remaining_text=rem_text,
            )
        return TargetResolution(
            member=None,
            telegram_id=None,
            error_message=(
                f"❌ کاربری با نام کاربری @{clean_user} در حافظه‌ی اعضای شناخته‌شده یافت نشد.\n"
                "💡 راهنما: کاربر باید حداقل یک بار در گروه پیامی فرستاده باشد، یا می‌توانید از شناسه عددی/ریپلای استفاده نمایید."
            ),
        )

    return TargetResolution(
        member=None,
        telegram_id=None,
        error_message="❌ هدف نامعتبر است. لطفاً روی پیام کاربر ریپلای کنید یا شناسه/یوزرنیم معتبر وارد نمایید.",
    )
