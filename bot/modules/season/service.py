"""
سرویس مدیریت رویداد پایان فصل (SeasonService)، تضمین Idempotency و پیش‌نمایش ترفیعات فصلی.
"""

from __future__ import annotations

import json
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.db.base import utcnow
from ...core.db.models.history import RankHistory
from ...core.db.models.member import Member
from ...core.db.models.season import SeasonEvent
from ...core.events import RankChanged, SeasonApplied, event_bus
from ...domain.promotion import AUTO_PROMOTION_CAP_LEVEL, promote_auto
from ...domain.ranks import DEFAULT_LEVEL
from ..tags.service import TagService

logger = logging.getLogger(__name__)


class SeasonService:
    """عملیات ارتقای فصلی هماهنگ با ربات اصلی."""

    @classmethod
    async def process_season_ended(
        cls,
        session: AsyncSession,
        event_id: str,
        players: list[dict],
        source: str = "webhook",
        payload_raw: str = "{}",
    ) -> dict[str, any]:
        """
        پردازش اتمام فصل با تضمین قطعی Idempotency.
        اگر رویدادی با این event_id قبلاً پردازش شده باشد، بلافاصله بازمی‌گردد بدون تغییر مجدد.
        """
        # ۱. بررسی تکراری نبودن رویداد (Idempotency Check)
        stmt = select(SeasonEvent).where(SeasonEvent.event_id == event_id)
        res = await session.execute(stmt)
        existing_event = res.scalar_one_or_none()

        if existing_event and existing_event.status == "processed":
            logger.info("رویداد فصل %s قبلاً پردازش شده است (Already Processed).", event_id)
            return {
                "ok": True,
                "status": "already_processed",
                "promoted": existing_event.promoted_count,
                "capped": existing_event.capped_count,
                "tag_pending": existing_event.tag_failed_count,
            }

        now = utcnow()
        season_event = existing_event or SeasonEvent(
            event_id=event_id,
            source=source,
            payload_json=payload_raw,
            started_at=now,
            status="processing",
        )
        if not existing_event:
            session.add(season_event)

        # ۲. حذف موارد تکراری در پیلود بازیکنان (Deduplicate)
        unique_players: dict[int, dict] = {}
        for p in players:
            uid = p.get("telegram_id")
            if uid:
                unique_players[int(uid)] = p

        promoted_count = 0
        capped_count = 0
        tag_pending_count = 0
        rank_changes_to_emit: list[RankChanged] = []

        # ۳. پردازش تمامی بازیکنان در یک تراکنش یکپارچه پایگاه داده
        for uid, p_data in unique_players.items():
            member_stmt = select(Member).where(Member.telegram_id == uid).with_for_update()
            m_res = await session.execute(member_stmt)
            member = m_res.scalar_one_or_none()

            username = p_data.get("username")
            full_name = p_data.get("full_name") or f"بازیکن {uid}"

            if not member:
                # بازیکن جدید: ابتدا با سطح ۱ ساخته می‌شود و سپس ارتقا می‌یابد (می‌شود سطح ۲)
                old_lvl = DEFAULT_LEVEL
                new_lvl = DEFAULT_LEVEL + 1
                member = Member(
                    telegram_id=uid,
                    username=username.lstrip("@") if username else None,
                    full_name=full_name,
                    rank_level=new_lvl,
                    seasons_participated=1,
                    is_player=True,
                    in_group=False,  # ممکن است هنوز وارد گروه نشده باشد
                    tag_synced=False,
                    rank_reached_at=now,
                    first_seen_at=now,
                    last_seen_at=now,
                )
                session.add(member)
                promoted_count += 1
                tag_pending_count += 1

                history = RankHistory(
                    telegram_id=uid,
                    old_level=old_lvl,
                    new_level=new_lvl,
                    delta=1,
                    source="season",
                    reason="پایان فصل (اولین مشارکت)",
                    season_event_id=event_id,
                )
                session.add(history)

                rank_changes_to_emit.append(
                    RankChanged(
                        telegram_id=uid,
                        old_level=old_lvl,
                        new_level=new_lvl,
                        source="season",
                        reason="ارتقای فصلی",
                        username=member.username,
                        full_name=member.full_name,
                    )
                )
            else:
                old_lvl = member.rank_level
                member.seasons_participated += 1
                member.is_player = True
                if username:
                    member.username = username.lstrip("@")
                if full_name:
                    member.full_name = full_name

                new_lvl, did_promote = promote_auto(old_lvl)

                if did_promote:
                    member.rank_level = new_lvl
                    member.tag_synced = False
                    member.rank_reached_at = now
                    promoted_count += 1
                    tag_pending_count += 1

                    history = RankHistory(
                        telegram_id=uid,
                        old_level=old_lvl,
                        new_level=new_lvl,
                        delta=1,
                        source="season",
                        reason="پایان فصل",
                        season_event_id=event_id,
                    )
                    session.add(history)

                    rank_changes_to_emit.append(
                        RankChanged(
                            telegram_id=uid,
                            old_level=old_lvl,
                            new_level=new_lvl,
                            source="season",
                            reason="ارتقای فصلی",
                            username=member.username,
                            full_name=member.full_name,
                        )
                    )
                else:
                    capped_count += 1

        season_event.players_count = len(unique_players)
        season_event.promoted_count = promoted_count
        season_event.capped_count = capped_count
        season_event.tag_failed_count = tag_pending_count
        season_event.status = "processed"
        season_event.finished_at = utcnow()

        # ثبت قطعی در دیتابیس (Commit)
        await session.commit()
        logger.info(
            "فصل %s با موفقیت اعمال شد: %s ارتقا، %s در سقف، %s کل پلیرها",
            event_id,
            promoted_count,
            capped_count,
            len(unique_players),
        )

        # ۴. انتشار رویدادها خارج از تراکنش DB
        for ch in rank_changes_to_emit:
            await event_bus.emit(ch)

        await event_bus.emit(
            SeasonApplied(
                event_id=event_id,
                players_count=len(unique_players),
                promoted_count=promoted_count,
                capped_count=capped_count,
                source=source,
            )
        )

        return {
            "ok": True,
            "status": "processed",
            "promoted": promoted_count,
            "capped": capped_count,
            "tag_pending": tag_pending_count,
        }

    @classmethod
    async def preview_season(cls, session: AsyncSession, players: list[dict]) -> dict[str, any]:
        """
        پیش‌نمایش ارتقای فصل بدون اعمال هیچ تغییری در دیتابیس.
        نشان می‌دهد در صورت اتمام فصل، چند نفر ارتقا می‌یابند و چند نفر در سقف مانده‌اند.
        """
        unique_players = {int(p["telegram_id"]): p for p in players if p.get("telegram_id")}
        promoted_list = []
        capped_list = []
        new_recruits = []

        for uid, p in unique_players.items():
            member_stmt = select(Member).where(Member.telegram_id == uid)
            m_res = await session.execute(member_stmt)
            member = m_res.scalar_one_or_none()

            name = p.get("full_name") or p.get("username") or str(uid)
            if not member:
                new_recruits.append({"id": uid, "name": name, "new_level": 2})
                promoted_list.append({"id": uid, "name": name, "old": 1, "new": 2})
            else:
                if member.rank_level < AUTO_PROMOTION_CAP_LEVEL:
                    promoted_list.append({
                        "id": uid,
                        "name": name,
                        "old": member.rank_level,
                        "new": member.rank_level + 1,
                    })
                else:
                    capped_list.append({
                        "id": uid,
                        "name": name,
                        "level": member.rank_level,
                    })

        return {
            "total_players": len(unique_players),
            "promoted_count": len(promoted_list),
            "capped_count": len(capped_list),
            "new_recruits_count": len(new_recruits),
            "capped_players": capped_list[:10],
        }
