"""
پالایش امن و فرار از کاراکترهای خاص HTML برای تلگرام.
"""

from __future__ import annotations

import html


def clean_html(text: str | None) -> str:
    """ایمن‌سازی متن با تبدیل کاراکترهای <>& و غیره به موجودیت‌های امن HTML."""
    if text is None:
        return ""
    return html.escape(str(text))


def bold(text: str) -> str:
    """ساخت تگ bold با ایمن‌سازی محتوا."""
    return f"<b>{clean_html(text)}</b>"


def code(text: str) -> str:
    """ساخت تگ code با ایمن‌سازی محتوا."""
    return f"<code>{clean_html(text)}</code>"


def user_link(telegram_id: int, name: str) -> str:
    """ایجاد لینک تلگرامی امن به پروفایل کاربر."""
    return f'<a href="tg://user?id={telegram_id}">{clean_html(name)}</a>'
