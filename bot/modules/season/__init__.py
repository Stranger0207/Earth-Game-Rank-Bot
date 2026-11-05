"""ماژول مدیریت فصل‌های بازی."""

from ...core.registry import AppContext
from .router import router


def setup(ctx: AppContext) -> None:
    """ثبت روتر فصل در دیسپچر."""
    if router.parent_router is None:
        ctx.dp.include_router(router)
