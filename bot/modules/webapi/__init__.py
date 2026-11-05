"""ماژول وب‌سرور داخلی و وب‌هوک پایان فصل."""

import asyncio
from ...core.registry import AppContext
from .server import start_webapi


def setup(ctx: AppContext) -> None:
    """راه‌اندازی سرور داخلی در پس‌زمینه تسک‌های رویدادی."""
    # ثبت وظیفه استارت وب‌سرور در صورت شروع چرخه رویداد
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(start_webapi())
    except Exception:
        pass
