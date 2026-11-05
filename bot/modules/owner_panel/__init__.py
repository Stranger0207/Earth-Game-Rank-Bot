"""ماژول پنل فرماندهی مالکان."""

from ...core.registry import AppContext
from .router import router


def setup(ctx: AppContext) -> None:
    """ثبت روتر پنل مالک در دیسپچر."""
    ctx.dp.include_router(router)
