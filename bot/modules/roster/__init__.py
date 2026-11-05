"""ماژول دریافت روستر بازیکنان."""

from ...core.registry import AppContext
from .router import router


def setup(ctx: AppContext) -> None:
    """ثبت روتر روستر در دیسپچر."""
    ctx.dp.include_router(router)
