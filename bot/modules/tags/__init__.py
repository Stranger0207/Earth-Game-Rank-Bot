"""ماژول مدیریت تگ‌ها و صف همگام‌سازی."""

from ...core.events import MemberJoined, RankChanged
from ...core.registry import AppContext
from .service import (
    TagService,
    on_member_joined_handler,
    on_rank_changed_handler,
)


def setup(ctx: AppContext) -> None:
    """راه‌اندازی ماژول تگ‌ها و اتصال رویدادها و جاب‌های پس‌زمینه."""
    # ثبت شنوندگان رویداد در گذرگاه
    ctx.event_bus.subscribe(RankChanged, on_rank_changed_handler)
    ctx.event_bus.subscribe(MemberJoined, on_member_joined_handler)

    # ثبت جاب پردازش صف تگ‌ها هر ۵ ثانیه
    ctx.scheduler.add_job(
        TagService.process_queue_batch,
        trigger="interval",
        seconds=5,
        args=[ctx.bot],
        id="tag_queue_worker",
        replace_existing=True,
    )
