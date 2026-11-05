"""ماژول ممیزی تگ‌ها و تست سلامت سامانه."""

from ...core.registry import AppContext
from .router import router
from .service import AuditService


def setup(ctx: AppContext) -> None:
    """ثبت روتر و جاب دوره‌ای ممیزی شبانه."""
    if router.parent_router is None:
        ctx.dp.include_router(router)

    # جاب شبانه ساعت ۴:۰۰ صبح برای ممیزی تگ‌ها
    ctx.scheduler.add_job(
        AuditService.run_audit,
        trigger="cron",
        hour=4,
        minute=0,
        args=[ctx.bot],
        id="nightly_audit_job",
        replace_existing=True,
    )
