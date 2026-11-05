"""
آزمون‌های جامع امنیت وب‌هوک و اعتبارسنجی امضای HMAC-SHA256.
"""

from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from bot.core.security import generate_hmac_signature, verify_hmac_request


def test_hmac_security() -> None:
    secret = "test_super_secret_key_32_bytes_long_12345"
    now_ts = int(time.time())
    payload = '{"event_id": "test-uuid-1", "players": []}'

    # ۱. امضای معتبر
    valid_sig = generate_hmac_signature(secret, now_ts, payload)
    auth = verify_hmac_request(
        received_signature=valid_sig,
        received_timestamp=str(now_ts),
        raw_body=payload,
        custom_secret=secret,
    )
    assert auth.is_valid is True
    assert auth.status_code == 200
    print("✅ اعتبارسنجی امضای صحیح HMAC تأیید شد.")

    # ۲. امضای نامعتبر یا تغییر در بدنه
    tampered_sig = valid_sig[:-2] + "ff"
    auth_tampered = verify_hmac_request(
        received_signature=tampered_sig,
        received_timestamp=str(now_ts),
        raw_body=payload,
        custom_secret=secret,
    )
    assert auth_tampered.is_valid is False
    assert auth_tampered.status_code == 401
    print("✅ رد امضای دستکاری‌شده یا نامعتبر تأیید شد.")

    # ۳. انحراف زمانی قدیمی (Replay Attack) بیش از ۳۰۰ ثانیه
    old_ts = now_ts - 400
    old_sig = generate_hmac_signature(secret, old_ts, payload)
    auth_old = verify_hmac_request(
        received_signature=old_sig,
        received_timestamp=str(old_ts),
        raw_body=payload,
        custom_secret=secret,
    )
    assert auth_old.is_valid is False
    assert "drift" in auth_old.error_message.lower()
    print("✅ رد درخواست‌های قدیمی (بیش از ۳۰۰ ثانیه) تأیید شد.")

    # ۴. فقدان هدرها
    auth_missing = verify_hmac_request(
        received_signature=None,
        received_timestamp=str(now_ts),
        raw_body=payload,
        custom_secret=secret,
    )
    assert auth_missing.is_valid is False
    assert auth_missing.status_code == 401
    print("✅ مدیریت هدرهای مفقود با موفقیت تأیید شد.")


if __name__ == "__main__":
    print("🚀 اجرای آزمون‌های امنیت API...")
    test_hmac_security()
    print("🎉 تمامی آزمون‌های security.py سبز شدند!")
