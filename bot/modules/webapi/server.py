"""
وب‌سرور سبک داخلی aiohttp جهت دریافت وب‌هوک‌های امن و گزارش سلامت سیستم.
"""

from __future__ import annotations

import json
import logging
from aiohttp import web

from ...core.config import get_settings
from ...core.db.base import get_session
from ...core.security import verify_hmac_request
from ..season.service import SeasonService

logger = logging.getLogger(__name__)


async def handle_health(request: web.Request) -> web.Response:
    """مسیر سلامت‌سنجی سامانه (Health Check)."""
    return web.json_response({
        "ok": True,
        "status": "running",
        "service": "rank-bot",
    })


async def handle_season_ended(request: web.Request) -> web.Response:
    """
    دریافت رویداد پایان فصل بازی از ربات اصلی:
    POST /internal/v1/season-ended
    """
    raw_body = await request.text()
    sig = request.headers.get("X-Rank-Signature")
    ts = request.headers.get("X-Rank-Timestamp")

    # ۱. اعتبارسنجی امنیتی امضای HMAC و انحراف زمانی
    auth = verify_hmac_request(
        received_signature=sig,
        received_timestamp=ts,
        raw_body=raw_body,
    )
    if not auth.is_valid:
        logger.warning("درخواست غیرمجاز به season-ended: %s", auth.error_message)
        return web.json_response({"ok": False, "error": auth.error_message}, status=auth.status_code)

    # ۲. اعتبارسنجی محتوای JSON
    try:
        data = json.loads(raw_body)
    except Exception:
        return web.json_response({"ok": False, "error": "Invalid JSON body."}, status=422)

    event_id = data.get("event_id")
    players = data.get("players")

    if not event_id or not isinstance(players, list):
        return web.json_response({"ok": False, "error": "Missing event_id or players list."}, status=422)

    # ۳. پردازش ارتقای فصل
    try:
        async for session in get_session():
            result = await SeasonService.process_season_ended(
                session=session,
                event_id=event_id,
                players=players,
                source="webhook",
                payload_raw=raw_body,
            )
            return web.json_response(result, status=200)
    except Exception as exc:
        logger.exception("خطای غیرمنتظره در پردازش season-ended: %s", exc)
        return web.json_response({"ok": False, "error": str(exc)}, status=500)


def create_web_app() -> web.Application:
    """ساخت اپلیکیشن وب aiohttp."""
    app = web.Application()
    app.router.add_get("/health", handle_health)
    app.router.add_post("/internal/v1/season-ended", handle_season_ended)
    return app


async def start_webapi() -> web.AppRunner:
    """راه‌اندازی سرور وب داخلی روی لوکال‌هاست."""
    settings = get_settings()
    app = create_web_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=settings.rank_bot_api_host, port=settings.rank_bot_api_port)
    await site.start()
    logger.info("وب‌سرور داخلی ربات مقام روی http://%s:%s فعال شد.", settings.rank_bot_api_host, settings.rank_bot_api_port)
    return runner
