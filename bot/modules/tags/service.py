"""
سرویس صف‌بندی، اعمال و همگام‌سازی تگ‌های اعضای گروه با تلگرام (TagService).
"""

from __future__ import annotations

import asyncio
import datetime
import logging
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.config import get_settings
from ...core.db.base import get_session, utcnow
from ...core.db.models.member import Member
from ...core.db.models.tag_queue import TagQueueItem
from ...core.events import MemberJoined, RankChanged, TagSyncFailed, event_bus
from ...domain.ranks import get_rank

logger = logging.getLogger(__name__)

# سمافور برای کنترل نرخ همزمانی درخواست‌های تلگرام جهت جلوگیری از فلود
_tag_semaphore = asyncio.Semaphore(2)


class TagService:
    """مدیریت اعمال تگ در تلگرام با صف پایدار و کنترل خطا."""

    @classmethod
    async def enqueue_tag(
        cls,
        session: AsyncSession,
        telegram_id: int,
        target_tag: str,
    ) -> TagQueueItem:
        """افزودن یا به‌روزرسانی درخواست اعمال تگ در صف پایدار."""
        stmt = (
            select(TagQueueItem)
            .where(TagQueueItem.telegram_id == telegram_id, TagQueueItem.status == "pending")
            .limit(1)
        )
        res = await session.execute(stmt)
        item = res.scalar_one_or_none()

        now = utcnow()
        if item:
            item.target_tag = target_tag
            item.next_try_at = now
            item.attempts = 0
            item.last_error = None
        else:
            item = TagQueueItem(
                telegram_id=telegram_id,
                target_tag=target_tag,
                attempts=0,
                next_try_at=now,
                status="pending",
            )
            session.add(item)

        await session.commit()
        return item

    @classmethod
    async def apply_tag_direct(
        cls,
        bot: Bot,
        chat_id: int,
        user_id: int,
        tag: str,
    ) -> tuple[bool, str | None]:
        """
        ارسال درخواست مستقیم setChatMemberTag به تلگرام همراه با سمافور و مدیریت استثناها.
        خروجی: (آیا موفق بود؟، پیام خطا در صورت شکست)
        """
        async with _tag_semaphore:
            # مکث کوتاه برای رعایت سقف درخواست‌های تلگرام
            await asyncio.sleep(0.08)
            try:
                # فراخوانی متد جدید aiogram 3.13+
                await bot.set_chat_member_tag(chat_id=chat_id, user_id=user_id, tag=tag)
                return True, None
            except TelegramRetryAfter as exc:
                wait_time = exc.retry_after
                logger.warning("محدودیت نرخ تلگرام (FloodWait): %s ثانیه", wait_time)
                await asyncio.sleep(wait_time)
                try:
                    await bot.set_chat_member_tag(chat_id=chat_id, user_id=user_id, tag=tag)
                    return True, None
                except Exception as retry_exc:
                    return False, f"FloodWait Retry Failed: {retry_exc}"
            except TelegramBadRequest as exc:
                err_text = str(exc).lower()
                # بررسی خطاهای شناخته‌شده: ادمین بودن کاربر یا عدم حضور در گروه
                if "user is an administrator" in err_text or "chat_admin_required" in err_text:
                    return False, "کاربر ادمین یا مالک گروه است (تگ روی ادمین‌ها قابل اعمال نیست)"
                if "user not found" in err_text or "participant_id_invalid" in err_text:
                    return False, "کاربر در گروه حاضر نیست (هنگام ورود اعمال خواهد شد)"
                if "not enough rights" in err_text or "can_manage_tags" in err_text:
                    return False, "ربات دسترسی can_manage_tags را ندارد"
                return False, f"TelegramBadRequest: {exc}"
            except TelegramForbiddenError as exc:
                return False, f"TelegramForbiddenError: {exc}"
            except Exception as exc:
                return False, f"خطای ناشناخته تلگرام: {exc}"

    @classmethod
    async def process_queue_batch(cls, bot: Bot, limit: int = 15) -> int:
        """
        پردازش دسته‌ای آیتم‌های موجود در صف تگ‌های معوقه.
        این متد توسط جاب زمان‌بندی‌شده (Scheduler) به صورت دوره‌ای اجرا می‌شود.
        """
        settings = get_settings()
        now = utcnow()
        processed_count = 0

        async for session in get_session():
            stmt = (
                select(TagQueueItem)
                .where(
                    TagQueueItem.status == "pending",
                    TagQueueItem.next_try_at <= now,
                )
                .order_by(TagQueueItem.id.asc())
                .limit(limit)
            )
            res = await session.execute(stmt)
            items = list(res.scalars().all())

            for item in items:
                success, err = await cls.apply_tag_direct(
                    bot=bot,
                    chat_id=settings.target_chat_id,
                    user_id=item.telegram_id,
                    tag=item.target_tag,
                )

                item.attempts += 1
                member_stmt = select(Member).where(Member.telegram_id == item.telegram_id)
                m_res = await session.execute(member_stmt)
                member = m_res.scalar_one_or_none()

                if success:
                    item.status = "success"
                    if member:
                        member.tag_synced = True
                        member.tag_error = None
                    processed_count += 1
                else:
                    item.last_error = err
                    if member:
                        member.tag_synced = False
                        member.tag_error = err

                    # اگر خطای قطعی است (مثل ادمین بودن) تلاش مجدد نکنیم
                    if err and ("ادمین" in err or "حاضر نیست" in err):
                        item.status = "failed"
                    else:
                        if item.attempts >= 5:
                            item.status = "failed"
                        else:
                            # Exponential backoff
                            backoff_sec = 2 ** item.attempts * 5
                            item.next_try_at = utcnow() + datetime.timedelta(seconds=backoff_sec)

                    await event_bus.emit(
                        TagSyncFailed(
                            telegram_id=item.telegram_id,
                            tag=item.target_tag,
                            error=err or "خطای نامشخص",
                        )
                    )

            await session.commit()

        return processed_count


# ==========================================
# شنوندگان رویدادهای گذرگاه جهت به‌روزرسانی تگ
# ==========================================

async def on_rank_changed_handler(event: RankChanged) -> None:
    """هنگام تغییر مقام، تگ جدید در صف قرار می‌گیرد."""
    rank = get_rank(event.new_level)
    async for session in get_session():
        await TagService.enqueue_tag(
            session=session,
            telegram_id=event.telegram_id,
            target_tag=rank.name_fa,
        )


async def on_member_joined_handler(event: MemberJoined) -> None:
    """هنگام ورود یا بازگشت عضو به گروه، تگ او در صف اعمال قرار می‌گیرد."""
    rank = get_rank(event.rank_level)
    async for session in get_session():
        await TagService.enqueue_tag(
            session=session,
            telegram_id=event.telegram_id,
            target_tag=rank.name_fa,
        )
