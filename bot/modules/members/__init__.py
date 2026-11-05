"""ماژول مدیریت اعضای گروه."""

from ...core.registry import AppContext
from .middleware import MemberTrackingMiddleware
from .router import router


def setup(ctx: AppContext) -> None:
    """ثبت روتر و میان‌افزار اعضا در دیسپچر."""
    ctx.dp.message.outer_middleware(MemberTrackingMiddleware())
    if router.parent_router is None:
        ctx.dp.include_router(router)
