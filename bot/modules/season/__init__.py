"""ماژول مدیریت فصل‌های بازی."""

from ...core.registry import AppContext
from .router import router


def setup(ctx: AppContext) -> None:
    """ثبت روتر فصل در دیسپچر."""
    ctx.dp.include_router(router)
