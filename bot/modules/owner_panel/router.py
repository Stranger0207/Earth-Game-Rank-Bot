"""
هندلرهای دستورات و پنل شیشه‌ای مالکان (Owner Panel Router).
"""

from __future__ import annotations

import logging
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy import func, select

from ...core.config import get_settings
from ...core.db.base import get_session
from ...core.db.models.achievement import Achievement
from ...core.db.models.history import RankHistory
from ...core.db.models.member import Member
from ...core.db.models.tag_queue import TagQueueItem
from ...core.middlewares.owner_guard import OwnerOnlyMiddleware
from ...core.utils.format import fa_number
from ...core.utils.html import bold, clean_html
from ...core.utils.ui import DIVIDER, header
from ...domain.ranks import find_rank, get_rank
from ..members.resolver import resolve_target
from ..members.service import MemberService
from ..ranks.service import RankService
from .keyboards import back_to_panel_keyboard, confirm_dialog_keyboard, panel_main_keyboard
from .texts import member_dossier_text, panel_welcome_text

logger = logging.getLogger(__name__)

router = Router(name="owner_panel")
router.message.middleware(OwnerOnlyMiddleware())
router.callback_query.middleware(OwnerOnlyMiddleware())


async def _log_to_channel(bot, text: str) -> None:
    """ارسال لاگ عملیات حساس به چت لاگ مالکان در صورت پیکربندی."""
    settings = get_settings()
    if settings.log_chat_id:
        try:
            await bot.send_message(chat_id=settings.log_chat_id, text=text)
        except Exception as exc:
            logger.error("خطا در ارسال پیام به کانال لاگ: %s", exc)


@router.message(Command("panel", "پنل"))
@router.message(F.text.in_({"پنل", "/panel", "/پنل"}))
async def cmd_panel(message: Message) -> None:
    """نمایش پنل اصلی فرماندهی با دکمه‌های شیشه‌ای."""
    async for session in get_session():
        m_count = await session.scalar(select(func.count(Member.telegram_id))) or 0
        s_count = await session.scalar(select(func.count(Member.telegram_id)).where(Member.tag_synced.is_(True))) or 0
        p_count = await session.scalar(select(func.count(TagQueueItem.id)).where(TagQueueItem.status == "pending")) or 0

        text = panel_welcome_text(m_count, s_count, p_count)
        await message.answer(text, reply_markup=panel_main_keyboard())


@router.message(Command("who"))
async def cmd_who(message: Message) -> None:
    """مشاهده پرونده کامل نظامی یک عضو."""
    args = (message.text or "").partition(" ")[2].strip()
    async for session in get_session():
        res = await resolve_target(message, session, args)
        if res.error_message:
            await message.reply(res.error_message)
            return

        member = res.member
        if not member:
            await message.reply("❌ عضو یافت نشد.")
            return

        rank = get_rank(member.rank_level)
        hist_count = await session.scalar(
            select(func.count(RankHistory.id)).where(RankHistory.telegram_id == member.telegram_id)
        ) or 0
        ach_count = await session.scalar(
            select(func.count(Achievement.id)).where(Achievement.telegram_id == member.telegram_id)
        ) or 0

        text = member_dossier_text(member, rank, hist_count, ach_count)
        await message.reply(text)


@router.message(Command("promote"))
async def cmd_promote(message: Message) -> None:
    """ارتقای دستی درجه کاربر: /promote [target] [n=1] [دلیل]"""
    args = (message.text or "").partition(" ")[2].strip()
    async for session in get_session():
        res = await resolve_target(message, session, args)
        if res.error_message:
            await message.reply(res.error_message)
            return

        rem = res.remaining_text.strip()
        delta = 1
        reason = None

        if rem:
            parts = rem.split(maxsplit=1)
            token = parts[0].translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))
            if token.isdigit():
                delta = max(1, int(token))
                reason = parts[1].strip() if len(parts) > 1 else None
            else:
                reason = rem

        member, old_lvl, new_lvl = await RankService.promote(
            session=session,
            telegram_id=res.telegram_id,
            delta=delta,
            reason=reason,
            actor_id=message.from_user.id,
            source="manual",
        )

        old_rank = get_rank(old_lvl)
        new_rank = get_rank(new_lvl)

        msg = (
            f"🎖 <b>حکم ترفیع درجه صادر شد</b>\n\n"
            f"👤 عضو: {bold(clean_html(member.full_name or str(member.telegram_id)))}\n"
            f"📉 از: {old_rank.name_fa} (سطح {fa_number(old_lvl)})\n"
            f"📈 به: {bold(new_rank.name_fa)} (سطح {fa_number(new_lvl)})\n"
        )
        if reason:
            msg += f"📜 دلیل: <i>{clean_html(reason)}</i>\n"

        await message.reply(msg)
        await _log_to_channel(
            message.bot,
            f"🎖 [ارتقای دستی] {member.telegram_id} توسط {message.from_user.id}: {old_lvl} -> {new_lvl} ({reason or 'بدون دلیل'})",
        )


@router.message(Command("demote"))
async def cmd_demote(message: Message) -> None:
    """تنزل درجه کاربر: /demote [target] [n=1] [دلیل]"""
    args = (message.text or "").partition(" ")[2].strip()
    async for session in get_session():
        res = await resolve_target(message, session, args)
        if res.error_message:
            await message.reply(res.error_message)
            return

        rem = res.remaining_text.strip()
        delta = 1
        reason = None

        if rem:
            parts = rem.split(maxsplit=1)
            token = parts[0].translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))
            if token.isdigit():
                delta = max(1, int(token))
                reason = parts[1].strip() if len(parts) > 1 else None
            else:
                reason = rem

        member, old_lvl, new_lvl = await RankService.demote(
            session=session,
            telegram_id=res.telegram_id,
            delta=delta,
            reason=reason,
            actor_id=message.from_user.id,
            source="manual",
        )

        old_rank = get_rank(old_lvl)
        new_rank = get_rank(new_lvl)

        msg = (
            f"🔻 <b>حکم تنزل درجه صادر شد</b>\n\n"
            f"👤 عضو: {bold(clean_html(member.full_name or str(member.telegram_id)))}\n"
            f"📈 از: {old_rank.name_fa} (سطح {fa_number(old_lvl)})\n"
            f"📉 به: {bold(new_rank.name_fa)} (سطح {fa_number(new_lvl)})\n"
        )
        if reason:
            msg += f"📜 دلیل: <i>{clean_html(reason)}</i>\n"

        await message.reply(msg)
        await _log_to_channel(
            message.bot,
            f"🔻 [تنزل دستی] {member.telegram_id} توسط {message.from_user.id}: {old_lvl} -> {new_lvl}",
        )


@router.message(Command("setrank"))
async def cmd_setrank(message: Message) -> None:
    """انتصاب مستقیم یک مقام: /setrank [target] [عدد یا نام مقام]"""
    args = (message.text or "").partition(" ")[2].strip()
    async for session in get_session():
        res = await resolve_target(message, session, args)
        if res.error_message:
            await message.reply(res.error_message)
            return

        target_rank_input = res.remaining_text.strip()
        if not target_rank_input:
            await message.reply("❌ لطفاً شماره سطح (۱ تا ۲۱) یا نام مقام را مشخص کنید.")
            return

        target_rank = find_rank(target_rank_input)
        if not target_rank:
            await message.reply(f"❌ مقامی با عنوان یا سطح «{clean_html(target_rank_input)}» یافت نشد.")
            return

        member, old_lvl, new_lvl = await RankService.set_rank(
            session=session,
            telegram_id=res.telegram_id,
            target_level=target_rank.level,
            actor_id=message.from_user.id,
            source="setrank",
        )

        msg = (
            f"🎖 <b>مقام با موفقیت انتصاب یافت</b>\n\n"
            f"👤 عضو: {bold(clean_html(member.full_name or str(member.telegram_id)))}\n"
            f"🏷 مقام جدید: {bold(target_rank.name_fa)} (سطح {fa_number(new_lvl)})\n"
        )
        await message.reply(msg)
        await _log_to_channel(
            message.bot,
            f"🎖 [SetRank] {member.telegram_id} توسط {message.from_user.id} -> سطح {new_lvl} ({target_rank.name_fa})",
        )


@router.message(Command("promote_players"))
async def cmd_promote_players(message: Message) -> None:
    """درخواست ارتقای گروهی بازیکنان (تأیید دو مرحله‌ای)."""
    args = (message.text or "").partition(" ")[2].strip()
    delta = 1
    if args.isdigit():
        delta = max(1, int(args))

    async for session in get_session():
        count = await session.scalar(
            select(func.count(Member.telegram_id)).where(Member.is_player.is_(True))
        ) or 0

        text = (
            f"⚠️ <b>تأیید عملیات ارتقای گروهی بازیکنان</b>\n\n"
            f"تعداد بازیکنان شناسایی‌شده: {bold(fa_number(count))}\n"
            f"میزان ارتقا: {bold(fa_number(delta))} درجه\n\n"
            "آیا از اجرای این حکم اطمینان دارید؟"
        )
        await message.reply(text, reply_markup=confirm_dialog_keyboard("promote_players", str(delta)))


@router.message(Command("promote_all"))
async def cmd_promote_all(message: Message) -> None:
    """درخواست ارتقای تمام اعضای گروه (تأیید دو مرحله‌ای)."""
    args = (message.text or "").partition(" ")[2].strip()
    delta = 1
    if args.isdigit():
        delta = max(1, int(args))

    async for session in get_session():
        count = await session.scalar(select(func.count(Member.telegram_id))) or 0

        text = (
            f"⚠️ <b>تأیید عملیات سراسری ارتقای تمامی اعضا</b>\n\n"
            f"تعداد کل اعضا: {bold(fa_number(count))}\n"
            f"میزان ارتقا: {bold(fa_number(delta))} درجه\n\n"
            "آیا از اجرای این حکم گسترده اطمینان دارید؟"
        )
        await message.reply(text, reply_markup=confirm_dialog_keyboard("promote_all", str(delta)))


# کال‌بک‌های بازگشت و ناوبری
@router.callback_query(F.data == "panel_action:main_menu")
async def on_panel_main_menu(call: CallbackQuery) -> None:
    """بازگشت به صفحه اصلی پنل فرماندهی."""
    await call.answer()
    async for session in get_session():
        m_count = await session.scalar(select(func.count(Member.telegram_id))) or 0
        s_count = await session.scalar(select(func.count(Member.telegram_id)).where(Member.tag_synced.is_(True))) or 0
        p_count = await session.scalar(select(func.count(TagQueueItem.id)).where(TagQueueItem.status == "pending")) or 0

        text = panel_welcome_text(m_count, s_count, p_count)
        await call.message.edit_text(text, reply_markup=panel_main_keyboard())
        break


# کال‌بک‌های تأیید و انصراف دومرحله‌ای
@router.callback_query(F.data.startswith("confirm_act:"))
async def on_confirm_action(call: CallbackQuery) -> None:
    parts = call.data.split(":")
    action = parts[1]
    param = parts[2] if len(parts) > 2 else "1"
    delta = int(param) if param.isdigit() else 1

    await call.message.edit_text("⏳ در حال پردازش و اعمال احکام... لطفاً شکیبا باشید.")

    try:
        async for session in get_session():
            if action == "promote_players":
                stmt = select(Member).where(Member.is_player.is_(True))
                res = await session.execute(stmt)
                members = list(res.scalars().all())
                for m in members:
                    await RankService.promote(
                        session=session,
                        telegram_id=m.telegram_id,
                        delta=delta,
                        actor_id=call.from_user.id,
                        source="bulk_players",
                    )
                await call.message.edit_text(
                    f"✅ ارتقای گروهی {fa_number(len(members))} بازیکن با موفقیت اعمال شد.",
                    reply_markup=back_to_panel_keyboard(),
                )
                break

            elif action == "promote_all":
                stmt = select(Member)
                res = await session.execute(stmt)
                members = list(res.scalars().all())
                for m in members:
                    await RankService.promote(
                        session=session,
                        telegram_id=m.telegram_id,
                        delta=delta,
                        actor_id=call.from_user.id,
                        source="bulk_all",
                    )
                await call.message.edit_text(
                    f"✅ ارتقای سراسری {fa_number(len(members))} عضو با موفقیت اعمال شد.",
                    reply_markup=back_to_panel_keyboard(),
                )
                break
    except Exception as exc:
        logger.exception("خطا در تایید عملیات پنل: %s", exc)
        await call.message.edit_text(
            f"❌ خطا در اعمال عملیات:\n<code>{clean_html(str(exc))}</code>",
            reply_markup=back_to_panel_keyboard(),
        )


@router.callback_query(F.data.startswith("cancel_act:"))
async def on_cancel_action(call: CallbackQuery) -> None:
    await call.message.edit_text("❌ عملیات با موفقیت لغو شد.", reply_markup=back_to_panel_keyboard())


@router.callback_query(F.data == "panel_action:close")
async def on_panel_close(call: CallbackQuery) -> None:
    await call.message.delete()


@router.callback_query(F.data == "panel_action:roster")
async def on_panel_roster(call: CallbackQuery) -> None:
    await call.answer()
    await call.message.edit_text("⏳ در حال ارتباط با ربات اصلی و دریافت روستر بازیکنان...")
    try:
        from ..roster.service import RosterService
        from ...core.utils.format import split_text

        async for session in get_session():
            try:
                snapshot, players = await RosterService.fetch_and_snapshot(session)
            except Exception as exc:
                logger.warning("خطا در دریافت زنده روستر، بررسی اسنپ‌شات قبلی: %s", exc)
                snapshot, players = await RosterService.get_latest_snapshot(session)
                if not players:
                    await call.message.edit_text(
                        f"❌ خطا در دریافت روستر و عدم وجود اسنپ‌شات قبلی:\n<code>{clean_html(str(exc))}</code>",
                        reply_markup=back_to_panel_keyboard(),
                    )
                    return

            lines = [
                header("فهرست بازیکنان فعال فصل (Roster Snapshot)", "📋"),
                f"👥 تعداد کل بازیکنان: {bold(fa_number(len(players)))}",
                f"📅 شناسه اسنپ‌شات: <code>{snapshot.id if snapshot else 'نامشخص'}</code>",
                DIVIDER,
            ]

            for i, p in enumerate(players[:50], 1):
                name = clean_html(p.get("full_name") or p.get("username") or str(p.get("telegram_id")))
                country = f" ({clean_html(p.get('country'))})" if p.get("country") else ""
                lines.append(f"{fa_number(i)}. {name}{country} — <code>{p.get('telegram_id')}</code>")

            if len(players) > 50:
                lines.append(f"\n... و {fa_number(len(players) - 50)} بازیکن دیگر")

            chunks = split_text("\n".join(lines), max_length=4000)
            await call.message.edit_text(chunks[0], reply_markup=back_to_panel_keyboard())
            break
    except Exception as exc:
        logger.exception("خطا در دریافت روستر از پنل: %s", exc)
        await call.message.edit_text(
            f"❌ خطا در ارتباط با ربات اصلی یا بارگذاری روستر:\n<code>{clean_html(str(exc))}</code>",
            reply_markup=back_to_panel_keyboard(),
        )


@router.callback_query(F.data == "panel_action:season_preview")
async def on_panel_season_preview(call: CallbackQuery) -> None:
    await call.answer()
    await call.message.edit_text("⏳ در حال محاسبه پیش‌نمایش ترفیعات فصلی...")
    try:
        from ..roster.service import RosterService
        from ..season.service import SeasonService

        async for session in get_session():
            _, players = await RosterService.get_latest_snapshot(session)
            if not players:
                try:
                    _, players = await RosterService.fetch_and_snapshot(session)
                except Exception as exc:
                    await call.message.edit_text(
                        f"❌ امکان دریافت روستر وجود ندارد:\n<code>{clean_html(str(exc))}</code>",
                        reply_markup=back_to_panel_keyboard(),
                    )
                    return

            preview = await SeasonService.preview_season(session, players)
            lines = [
                header("پیش‌نمایش ارتقای پایان فصل (Simulation)", "🔮"),
                f"👥 کل بازیکنان فعال: {bold(fa_number(preview['total_players']))}",
                f"📈 مشمول ترفیع درجه: {bold(fa_number(preview['promoted_count']))} نفر",
                f"🆕 بازیکنان تازه وارد: {bold(fa_number(preview['new_recruits_count']))} نفر",
                f"🔒 مانده در سقف خودکار (سرهنگ به بالا): {bold(fa_number(preview['capped_count']))} نفر",
                DIVIDER,
                "💡 هیچ تغییری در پایگاه داده اعمال نشد.",
            ]
            await call.message.edit_text("\n".join(lines), reply_markup=back_to_panel_keyboard())
            break
    except Exception as exc:
        logger.exception("خطا در پیش‌نمایش فصل از پنل: %s", exc)
        await call.message.edit_text(
            f"❌ خطا در محاسبه پیش‌نمایش فصل:\n<code>{clean_html(str(exc))}</code>",
            reply_markup=back_to_panel_keyboard(),
        )


@router.callback_query(F.data == "panel_action:audit")
async def on_panel_audit(call: CallbackQuery) -> None:
    await call.answer()
    await call.message.edit_text("⏳ در حال ممیزی اعضا و بررسی تگ‌های تلگرام...")
    try:
        from ..audit.service import AuditService

        stats = await AuditService.run_audit(bot=call.bot)
        text = (
            f"{header('گزارش ممیزی تگ‌ها', '📋')}\n"
            f"👥 اعضای بررسی‌شده: {bold(fa_number(stats['total_checked']))}\n"
            f"🏷 ارسال‌شده به صف اصلاح تگ: {bold(fa_number(stats['enqueued']))}\n"
            f"{DIVIDER}\n"
            "✅ فرآیند با موفقیت آغاز شد و تگ‌ها در پس‌زمینه اصلاح خواهند شد."
        )
        await call.message.edit_text(text, reply_markup=back_to_panel_keyboard())
    except Exception as exc:
        logger.exception("خطا در ممیزی تگ‌ها از پنل: %s", exc)
        await call.message.edit_text(
            f"❌ خطا در اجرای ممیزی تگ‌ها:\n<code>{clean_html(str(exc))}</code>",
            reply_markup=back_to_panel_keyboard(),
        )


@router.callback_query(F.data == "panel_action:selftest")
async def on_panel_selftest(call: CallbackQuery) -> None:
    await call.answer()
    await call.message.edit_text("🩺 در حال اجرای تست‌های تشخیصی سلامت سامانه...")
    try:
        from ..audit.service import AuditService

        report = await AuditService.run_selftest(bot=call.bot)
        lines = [header("نتایج تست سلامت سامانه (Self-Test)", "🩺")]

        for key, data in report.items():
            icon = "✅" if data["ok"] else "❌"
            lines.append(f"{icon} <b>{key}</b>: {data['detail']}")

        lines.append(DIVIDER)
        overall_ok = all(d["ok"] for d in report.values())
        if overall_ok:
            lines.append("🎉 وضعیت کلی سیستم: <b>کاملاً سالم و عملیاتی</b>")
        else:
            lines.append("⚠️ وضعیت کلی: <b>برخی موارد نیاز به توجه دارند</b>")

        await call.message.edit_text("\n".join(lines), reply_markup=back_to_panel_keyboard())
    except Exception as exc:
        logger.exception("خطا در تست سلامت از پنل: %s", exc)
        await call.message.edit_text(
            f"❌ خطا در اجرای تست‌های تشخیصی سلامت:\n<code>{clean_html(str(exc))}</code>",
            reply_markup=back_to_panel_keyboard(),
        )


@router.callback_query(F.data.startswith("panel_confirm:"))
async def on_panel_confirm_prompt(call: CallbackQuery) -> None:
    await call.answer()
    parts = call.data.split(":")
    action = parts[1]
    param = parts[2] if len(parts) > 2 else "1"
    delta = int(param) if param.isdigit() else 1

    async for session in get_session():
        if action == "promote_players":
            count = await session.scalar(
                select(func.count(Member.telegram_id)).where(Member.is_player.is_(True))
            ) or 0
            text = (
                f"⚠️ <b>تأیید عملیات ارتقای گروهی بازیکنان</b>\n\n"
                f"تعداد بازیکنان شناسایی‌شده: {bold(fa_number(count))}\n"
                f"میزان ارتقا: {bold(fa_number(delta))} درجه\n\n"
                "آیا از اجرای این حکم اطمینان دارید؟"
            )
            await call.message.edit_text(text, reply_markup=confirm_dialog_keyboard("promote_players", str(delta)))
            break
        elif action == "promote_all":
            count = await session.scalar(select(func.count(Member.telegram_id))) or 0
            text = (
                f"⚠️ <b>تأیید عملیات سراسری ارتقای تمامی اعضا</b>\n\n"
                f"تعداد کل اعضا: {bold(fa_number(count))}\n"
                f"میزان ارتقا: {bold(fa_number(delta))} درجه\n\n"
                "آیا از اجرای این حکم گسترده اطمینان دارید؟"
            )
            await call.message.edit_text(text, reply_markup=confirm_dialog_keyboard("promote_all", str(delta)))
            break


@router.callback_query(F.data == "panel_action:export")
async def on_panel_export(call: CallbackQuery) -> None:
    await call.answer()
    status_msg = await call.message.answer("⏳ در حال استخراج داده‌ها و تولید فایل اکسل/CSV...")
    try:
        import csv, io
        from ...core.db.models.member import Member
        from ...domain.ranks import get_rank
        from ...core.db.base import utcnow
        from aiogram.types import BufferedInputFile

        async for session in get_session():
            stmt = select(Member).order_by(Member.rank_level.desc(), Member.rank_reached_at.asc())
            res = await session.execute(stmt)
            members = list(res.scalars().all())

            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow([
                "Telegram ID", "Username", "Full Name", "Rank Level", "Rank Title",
                "Tier", "Seasons Participated", "Is Player", "In Group", "Tag Synced", "Rank Reached At"
            ])

            for m in members:
                r = get_rank(m.rank_level)
                writer.writerow([
                    m.telegram_id, f"@{m.username}" if m.username else "", m.full_name,
                    m.rank_level, r.name_fa, r.tier, m.seasons_participated,
                    "بله" if m.is_player else "خیر", "بله" if m.in_group else "خیر",
                    "همگام" if m.tag_synced else "ناهماهنگ",
                    m.rank_reached_at.isoformat() if m.rank_reached_at else ""
                ])

            csv_bytes = output.getvalue().encode("utf-8-sig")
            now_str = utcnow().strftime("%Y%m%d_%H%M%S")
            doc = BufferedInputFile(csv_bytes, filename=f"ranks_export_{now_str}.csv")
            await call.message.answer_document(document=doc, caption=f"📊 خروجی سوابق اعضا شامل {fa_number(len(members))} رکورد.")
            await status_msg.delete()
            break
    except Exception as exc:
        logger.exception("خطا در خروجی داده‌ها از پنل: %s", exc)
        await status_msg.edit_text(f"❌ خطا در تولید خروجی فایل:\n<code>{clean_html(str(exc))}</code>")


@router.callback_query(F.data == "panel_action:settings")
async def on_panel_settings(call: CallbackQuery) -> None:
    await call.answer()
    try:
        settings = get_settings()
        text = (
            f"{header('تنظیمات فعلی سامانه', '⚙️')}\n"
            f"🎯 شناسه گروه هدف: <code>{settings.target_chat_id}</code>\n"
            f"👑 مالکان: <code>{settings.owner_ids}</code>\n"
            f"⏱ کول‌داون کاربران: {fa_number(settings.member_cmd_cooldown_sec)} ثانیه\n"
            f"🌐 منبع روستر: <code>{settings.roster_source}</code>\n"
            f"🚪 خروج از گروه‌های غیرمجاز: {'فعال' if settings.auto_leave_unauthorized_groups else 'غیرفعال'}\n"
            f"🕒 منطقه زمانی: {settings.tz}\n"
        )
        await call.message.edit_text(text, reply_markup=back_to_panel_keyboard())
    except Exception as exc:
        logger.exception("خطا در نمایش تنظیمات پنل: %s", exc)
        await call.message.edit_text(
            f"❌ خطا در دریافت تنظیمات:\n<code>{clean_html(str(exc))}</code>",
            reply_markup=back_to_panel_keyboard(),
        )

