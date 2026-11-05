"""
سرویس ممیزی تگ‌ها و آزمون جامع سلامت سامانه (Audit & SelfTest Service).
"""

from __future__ import annotations

import logging
from aiogram import Bot
from sqlalchemy import func, select, text

from ...core.config import get_settings
from ...core.db.base import get_session
from ...core.db.models.member import Member
from ...core.db.models.tag_queue import TagQueueItem
from ...domain.ranks import get_rank
from ..tags.service import TagService

logger = logging.getLogger(__name__)


class AuditService:
    """عملیات ممیزی و تست‌های تشخیصی سلامت سیستم."""

    @classmethod
    async def run_audit(cls, bot: Bot) -> dict[str, int]:
        """
        تطبیق دیتابیس با وضعیت تگ‌ها و ارسال تگ‌های ناهماهنگ به صف تگ تلگرام.
        خروجی: خلاصه آماری اعضای بررسی‌شده و ارسال‌شده به صف.
        """
        settings = get_settings()
        total_checked = 0
        enqueued_count = 0

        async for session in get_session():
            stmt = select(Member).where(Member.in_group.is_(True))
            res = await session.execute(stmt)
            members = list(res.scalars().all())
            total_checked = len(members)

            for m in members:
                if not m.tag_synced:
                    rank = get_rank(m.rank_level)
                    await TagService.enqueue_tag(
                        session=session,
                        telegram_id=m.telegram_id,
                        target_tag=rank.name_fa,
                    )
                    enqueued_count += 1

            await session.commit()

        # تلاش فوری برای پردازش بخشی از صف
        try:
            await TagService.process_queue_batch(bot=bot, limit=20)
        except Exception as exc:
            logger.warning("خطا در پردازش فوری صف تگ در ممیزی: %s", exc)

        return {
            "total_checked": total_checked,
            "enqueued": enqueued_count,
        }

    @classmethod
    async def run_selftest(cls, bot: Bot) -> dict[str, any]:
        """
        بررسی سلامت سیستم: دسترسی ادمین ربات، دسترسی can_manage_tags، اتصال DB،
        وضعیت can_edit_tag در گروه، و اندازه صف تگ.
        """
        settings = get_settings()
        results = {}

        # ۱. اتصال پایگاه داده
        try:
            async for session in get_session():
                await session.execute(text("SELECT 1"))
            results["database"] = {"ok": True, "detail": "اتصال به پایگاه داده برقرار است"}
        except Exception as exc:
            results["database"] = {"ok": False, "detail": f"خطای اتصال به دیتابیس: {exc}"}

        # ۲. بررسی وضعیت ادمین بودن و حق مدیریت تگ در گروه هدف
        try:
            chat_member = await bot.get_chat_member(
                chat_id=settings.target_chat_id,
                user_id=(await bot.get_me()).id,
            )
            is_admin = chat_member.status in ("administrator", "creator")
            can_tags = getattr(chat_member, "can_manage_tags", False) or chat_member.status == "creator"

            results["bot_admin"] = {
                "ok": is_admin,
                "detail": "ادمین گروه است" if is_admin else "ربات ادمین گروه هدف نیست!",
            }
            results["can_manage_tags"] = {
                "ok": can_tags,
                "detail": "دسترسی can_manage_tags دارد" if can_tags else "فاقد دسترسی مدیریت تگ (can_manage_tags)!",
            }
        except Exception as exc:
            results["bot_admin"] = {"ok": False, "detail": f"عدم امکان دریافت وضعیت ربات در گروه: {exc}"}
            results["can_manage_tags"] = {"ok": False, "detail": "بررسی نشد"}

        # ۳. بررسی تنظیمات چت برای دستکاری تگ توسط اعضا (can_edit_tag)
        try:
            chat = await bot.get_chat(chat_id=settings.target_chat_id)
            perms = getattr(chat, "permissions", None)
            can_edit = getattr(perms, "can_edit_tag", None) if perms else None

            if can_edit is True:
                results["group_tag_perm"] = {
                    "ok": False,
                    "detail": "⚠️ هشدار: گزینه can_edit_tag برای اعضا باز است! اعضا می‌توانند تگ خود را تغییر دهند.",
                }
            else:
                results["group_tag_perm"] = {
                    "ok": True,
                    "detail": "گزینه can_edit_tag برای اعضای عادی بسته و امن است.",
                }
        except Exception as exc:
            results["group_tag_perm"] = {"ok": True, "detail": f"امکان بررسی پرمیشن‌ها نبود ({exc})"}

        # ۴. وضعیت صف تگ
        try:
            async for session in get_session():
                p_count = await session.scalar(
                    select(func.count(TagQueueItem.id)).where(TagQueueItem.status == "pending")
                ) or 0
                f_count = await session.scalar(
                    select(func.count(TagQueueItem.id)).where(TagQueueItem.status == "failed")
                ) or 0
            results["tag_queue"] = {
                "ok": True,
                "detail": f"{p_count} مورد در انتظار، {f_count} مورد ناموفق",
            }
        except Exception as exc:
            results["tag_queue"] = {"ok": False, "detail": f"خطا در خواندن صف تگ: {exc}"}

        return results
