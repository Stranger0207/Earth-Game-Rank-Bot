"""
اجراکننده‌ی سراسری و تجمیعی تمامی آزمون‌های ربات مقام (Rank Bot Test Suite).
"""

from __future__ import annotations

import os
import subprocess
import sys
import time

TEST_SCRIPTS: list[str] = [
    "test_phase0.py",
    "test_ranks.py",
    "test_promotion.py",
    "test_members.py",
    "test_ranks_service.py",
    "test_tags.py",
    "test_owner_panel.py",
    "test_audit.py",
    "test_security.py",
    "test_season.py",
    "test_cards.py",
    "test_achievements.py",
    "test_member_commands.py",
    "test_modular.py",
    "test_e2e.py",
]


def main() -> None:
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(scripts_dir)
    os.chdir(project_dir)

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONPATH"] = project_dir

    print("=" * 65)
    print("🎖 سامانه آزمون‌های یکپارچه ربات مقام — The Earth Game Rank Bot")
    print("=" * 65)

    passed_count = 0
    failed_count = 0
    start_total = time.time()

    for script in TEST_SCRIPTS:
        script_path = os.path.join(scripts_dir, script)
        print(f"\n▶️ در حال اجرای آزمون: {script} ...")
        t0 = time.time()
        res = subprocess.run(
            [sys.executable, script_path],
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        elapsed = time.time() - t0

        if res.returncode == 0:
            print(f"✅ {script} با موفقیت پاس شد ({elapsed:.2f} ثانیه)")
            passed_count += 1
        else:
            print(f"❌ {script} با خطا مواجه شد:")
            print(res.stdout)
            print(res.stderr)
            failed_count += 1

    total_time = time.time() - start_total
    print("\n" + "=" * 65)
    print("📊 نتیجه تجمیعی آزمون‌های پروژه:")
    print(f"   کل آزمون‌ها: {len(TEST_SCRIPTS)}")
    print(f"   موفق (سبز):  {passed_count}")
    print(f"   ناموفق:      {failed_count}")
    print(f"   مدت زمان کل: {total_time:.2f} ثانیه")
    print("=" * 65)

    if failed_count > 0:
        print("❌ متأسفانه برخی آزمون‌ها شکست خوردند. لطفاً خطاهای فوق را بررسی فرمایید.")
        sys.exit(1)
    else:
        print("🎉 تبریک! تمامی آزمون‌های سامانه با موفقیت ۱۰۰٪ سبز شدند! 🫡")
        sys.exit(0)


if __name__ == "__main__":
    main()
