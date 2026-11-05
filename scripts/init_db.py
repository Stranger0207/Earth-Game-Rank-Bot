"""
اسکریپت خط فرمان جهت راه‌اندازی اولیه‌ی جداول پایگاه داده و مهاجرت ستون‌ها.
"""

from __future__ import annotations

import asyncio
import os
import sys

# افزودن مسیر ریشه پروژه به پایتون‌پث
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from bot.core.db.base import init_db


async def main() -> None:
    print("⏳ در حال ساخت جداول و اجرای مهاجرت‌های پایگاه داده...")
    await init_db()
    print("✅ تمامی جداول با موفقیت ساخته شدند و پایگاه داده آماده است.")


if __name__ == "__main__":
    asyncio.run(main())
