"""ماژول نشان‌ها و دستاوردهای اعضا."""

from ...core.events import RankChanged
from ...core.registry import AppContext
from .engine import on_rank_changed_achievement_listener


def setup(ctx: AppContext) -> None:
    """ثبت شنونده رویداد تغییر رنک جهت اعطای خودکار نشان‌ها."""
    ctx.event_bus.subscribe(RankChanged, on_rank_changed_achievement_listener)
