"""ماژول ابلاغیه‌ها و پیام‌های تبریک."""

from ...core.events import RankChanged, SeasonApplied
from ...core.registry import AppContext
from .service import (
    on_rank_changed_announcement_handler,
    on_season_applied_announcement_handler,
)


def setup(ctx: AppContext) -> None:
    """ثبت شنوندگان اعلانات ارتقا و خلاصه فصل."""
    ctx.event_bus.subscribe(RankChanged, on_rank_changed_announcement_handler)
    ctx.event_bus.subscribe(SeasonApplied, on_season_applied_announcement_handler)
