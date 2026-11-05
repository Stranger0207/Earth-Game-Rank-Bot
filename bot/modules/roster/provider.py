"""
رابط انتزاعی و پیاده‌سازی‌های تامین‌کننده روستر بازیکنان (RosterProvider).
"""

from __future__ import annotations

import abc
import json
import logging
import time
import aiohttp
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from ...core.config import get_settings
from ...core.security import generate_hmac_signature

logger = logging.getLogger(__name__)


class RosterProvider(abc.ABC):
    """رابط تامین فهرست بازیکنان فعال بازی The Earth Game."""

    @abc.abstractmethod
    async def fetch_roster(self) -> list[dict]:
        """دریافت فهرست بازیکنان. هر بازیکن شامل حداقل telegram_id، username و full_name است."""
        pass


class HttpRosterProvider(RosterProvider):
    """دریافت روستر از وب‌سرور داخلی ربات اصلی از طریق HTTP Pull با امضای HMAC."""

    async def fetch_roster(self) -> list[dict]:
        settings = get_settings()
        url = f"{settings.main_bot_api_url.rstrip('/')}/internal/v1/rank-roster"
        ts = int(time.time())
        sig = generate_hmac_signature(settings.rank_sync_secret, ts, raw_body="")

        headers = {
            "Content-Type": "application/json",
            "X-Rank-Timestamp": str(ts),
            "X-Rank-Signature": sig,
        }

        async with aiohttp.ClientSession() as client:
            async with client.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    text_resp = await resp.text()
                    raise RuntimeError(f"خطا در دریافت روستر از ربات اصلی (Status: {resp.status}): {text_resp}")
                data = await resp.json()
                return data.get("players", [])


class DbRosterProvider(RosterProvider):
    """
    دریافت مستقیم روستر با خواندن از پایگاه داده ربات اصلی (حالت فقط‌خواندنی).
    تعریف بازیکن: کاربرانی که در حال حاضر مالک یک کشور (owner_user_id) هستند.
    """

    async def fetch_roster(self) -> list[dict]:
        settings = get_settings()
        # کوئری جهت استخراج بازیکنان دارای کشور در بازی
        sql = """
            SELECT DISTINCT u.telegram_id, u.username, u.first_name, c.name_fa AS country_name
            FROM countries c
            JOIN users u ON c.owner_user_id = u.telegram_id
            WHERE c.owner_user_id IS NOT NULL AND c.is_claimed = TRUE;
        """
        temp_engine = create_async_engine(settings.database_url, echo=False)
        try:
            async with temp_engine.connect() as conn:
                res = await conn.execute(text(sql))
                rows = res.fetchall()
                players = []
                for row in rows:
                    players.append({
                        "telegram_id": row[0],
                        "username": row[1],
                        "full_name": row[2] or f"رهبر {row[3]}",
                        "country": row[3],
                    })
                return players
        finally:
            await temp_engine.dispose()


def get_roster_provider() -> RosterProvider:
    """کارخانه‌ی ساخت نمونه تامین‌کننده روستر بر اساس متغیر ROSTER_SOURCE."""
    settings = get_settings()
    if settings.roster_source.lower() == "db":
        return DbRosterProvider()
    return HttpRosterProvider()
