"""ماژول دستورات عمومی اعضا."""

from ...core.registry import AppContext
from .router import router


def setup(ctx: AppContext) -> None:
    """ثبت روتر دستورات اعضا در دیسپچر."""
    ctx.dp.include_router(router)
