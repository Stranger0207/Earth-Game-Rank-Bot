"""
سیستم گذرگاه رویداد ناهمگام (Async Event Bus) برای هماهنگی بین ماژول‌ها بدون وابستگی مستقیم.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable, Coroutine, TypeVar

logger = logging.getLogger(__name__)

TEvent = TypeVar("TEvent")
HandlerCallable = Callable[[Any], Coroutine[Any, Any, None]]


@dataclass(frozen=True)
class RankChanged:
    """رویداد تغییر مقام یک عضو."""

    telegram_id: int
    old_level: int
    new_level: int
    source: str          # season / manual / setrank / join / bulk / import
    reason: str | None = None
    actor_id: int | None = None
    username: str | None = None
    full_name: str | None = None


@dataclass(frozen=True)
class SeasonApplied:
    """رویداد اعمال تغییرات فصلی برای بازیکنان."""

    event_id: str
    players_count: int
    promoted_count: int
    capped_count: int
    source: str


@dataclass(frozen=True)
class MemberJoined:
    """رویداد ورود یا مشاهده‌ی عضو جدید در گروه."""

    telegram_id: int
    username: str | None
    full_name: str
    rank_level: int
    is_restored: bool = False


@dataclass(frozen=True)
class TagSyncFailed:
    """رویداد شکست در اعمال یا همگام‌سازی تگ کاربر در گروه."""

    telegram_id: int
    tag: str
    error: str


class EventBus:
    """مدیریت ثبت شنوندگان و انتشار رویدادها."""

    def __init__(self) -> None:
        self._listeners: dict[type, list[HandlerCallable]] = defaultdict(list)

    def subscribe(self, event_type: type[TEvent], handler: HandlerCallable) -> None:
        """ثبت شنونده برای یک نوع رویداد مشخص."""
        if handler not in self._listeners[event_type]:
            self._listeners[event_type].append(handler)

    def unsubscribe(self, event_type: type[TEvent], handler: HandlerCallable) -> None:
        """لغو اشتراک شنونده."""
        if handler in self._listeners[event_type]:
            self._listeners[event_type].remove(handler)

    async def emit(self, event: Any) -> None:
        """انتشار رویداد به تمام شنوندگان ثبت‌شده به‌صورت همزمان و ایمن."""
        event_type = type(event)
        handlers = self._listeners.get(event_type, [])
        if not handlers:
            return

        tasks = []
        for h in handlers:
            try:
                res = h(event)
                if inspect.isawaitable(res):
                    tasks.append(res)
            except Exception as exc:
                logger.error("خطا هنگام آماده‌سازی شنونده رویداد %s: %s", event_type.__name__, exc)

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for r in results:
                if isinstance(r, Exception):
                    logger.error("خطا در اجرای شنونده رویداد %s: %s", event_type.__name__, r)


# نمونه‌ی سراسری EventBus
event_bus = EventBus()
