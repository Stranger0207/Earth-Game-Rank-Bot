"""
ماژول امنیت و اعتبارسنجی امضای رمزنگاری HMAC-SHA256 بین دو ربات.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import NamedTuple

from .config import get_settings


class AuthResult(NamedTuple):
    """نتیجه‌ی اعتبارسنجی امضا و امنیت درخواست."""

    is_valid: bool
    status_code: int
    error_message: str | None = None


def generate_hmac_signature(secret: str, timestamp: int | str, raw_body: str = "") -> str:
    """
    تولید امضای HMAC-SHA256 بر اساس کلید محرمانه، تایم‌استمپ و متن بدنه:
    hex(HMAC_SHA256(secret, f"{timestamp}.{raw_body}"))
    """
    message = f"{timestamp}.{raw_body}".encode("utf-8")
    secret_bytes = secret.encode("utf-8")
    return hmac.new(secret_bytes, message, hashlib.sha256).hexdigest()


def verify_hmac_request(
    received_signature: str | None,
    received_timestamp: str | None,
    raw_body: str = "",
    max_drift_seconds: int = 300,
    custom_secret: str | None = None,
) -> AuthResult:
    """
    اعتبارسنجی کامل درخواست‌های داخلی دریافتی:
    - بررسی وجود هدرها
    - بررسی انحراف زمانی (حداکثر ۳۰۰ ثانیه)
    - مقایسه‌ی ایمن با hmac.compare_digest
    """
    settings = get_settings()
    secret = custom_secret or settings.rank_sync_secret

    if not secret:
        return AuthResult(False, 500, "Secret is not configured on rank-bot.")

    if not received_signature or not received_timestamp:
        return AuthResult(False, 401, "Missing required security headers (X-Rank-Signature, X-Rank-Timestamp).")

    # اعتبارسنجی تایم‌استمپ عددی
    try:
        ts = int(received_timestamp)
    except (ValueError, TypeError):
        return AuthResult(False, 401, "Invalid timestamp format.")

    now = int(time.time())
    if abs(now - ts) > max_drift_seconds:
        return AuthResult(False, 401, f"Timestamp drift too large ({abs(now - ts)}s > {max_drift_seconds}s).")

    expected_signature = generate_hmac_signature(secret, ts, raw_body)
    if not hmac.compare_digest(expected_signature.lower(), received_signature.lower()):
        return AuthResult(False, 401, "Invalid HMAC signature.")

    return AuthResult(True, 200, None)
