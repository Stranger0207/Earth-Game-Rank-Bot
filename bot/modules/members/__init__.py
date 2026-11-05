"""ماژول مدیریت اعضای گروه."""

from ...core.registry import AppContext
from .router import router


def setup(ctx: AppContext) -> None:
    """ثبت روتر اعضا در دیسپچر."""
    ctx.dp.include_router(router)
