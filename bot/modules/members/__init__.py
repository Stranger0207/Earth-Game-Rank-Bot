"""ماژول مدیریت اعضای گروه."""

from ...core.registry import AppContext
from .router import router


def setup(ctx: AppContext) -> None:
    """ثبت روتر اعضا در دیسپچر."""
    if router.parent_router is None:
        ctx.dp.include_router(router)
