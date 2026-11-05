"""
اسکریپت خط فرمان جهت اجرای آزمون‌های تشخیصی سلامت سامانه (Self-Test).
"""

from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from bot.core.loader import bot
from bot.modules.audit.service import AuditService


async def main() -> None:
    print("🩺 در حال اجرای تست‌های تشخیصی سلامت ربات مقام...")
    report = await AuditService.run_selftest(bot=bot)

    print("\n" + "=" * 50)
    for key, data in report.items():
        icon = "✅" if data["ok"] else "❌"
        print(f"{icon} [{key}]: {data['detail']}")
    print("=" * 50)

    overall_ok = all(d["ok"] for d in report.values())
    if overall_ok:
        print("🎉 وضعیت کلی: تمامی بخش‌ها سالم و آماده بهره‌برداری هستند.")
    else:
        print("⚠️ توجه: برخی موارد نیازمند بررسی یا اصلاح پیکربندی هستند.")

    await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
