# 🔗 قرارداد اتصال ربات اصلی (The Earth Game) به ربات مقام (Rank Bot)

این سند نحوه ارتباط امن دو ربات مستقل را که روی یک VPS مشترک میزبانی می‌شوند تشریح می‌کند.

---

## ۱. اصول معماری و امنیت
- هر دو ربات روی آدرس لوکال `127.0.0.1` با یکدیگر تبادل داده دارند (در معرض اینترنت عمومی نیست).
- تمامی درخواست‌ها با الگوریتم **HMAC-SHA256** و کلید محرمانه مشترک `RANK_SYNC_SECRET` امضا می‌شوند.
- هدرهای امنیتی الزامی در تمام درخواست‌ها:
  - `Content-Type: application/json`
  - `X-Rank-Timestamp`: زمان یونیکس بر حسب ثانیه (مثلاً `1762340000`).
  - `X-Rank-Signature`: امضای هگزادسیمال به صورت `hex(HMAC_SHA256(secret, f"{timestamp}.{raw_body}"))`.
- انحراف زمانی مجاز: حداکثر ۳۰۰ ثانیه (جهت دفع حملات Replay).
- شناسه یکتای `event_id` در پایان فصل ضامن اجرای دقیقاً یکباره (Idempotency) است.

---

## ۲. سناریو ۱: ارسال رویداد پایان فصل (Push)
هنگامی که مالک در ربات اصلی دستور `/endseason` را تایید می‌کند (`cb_season_confirm` یا انتهای تابع `reset_season`):

- **متد:** `POST`
- **آدرس:** `http://127.0.0.1:8091/internal/v1/season-ended`
- **نمونه بدنه ارسالی (JSON):**
```json
{
  "event_id": "c7a8b412-8815-4fa9-b8ea-123456789abc",
  "event_type": "season_ended",
  "season_label": "فصل دهم",
  "occurred_at": "2026-11-05T12:00:00Z",
  "players": [
    {
      "telegram_id": 123456789,
      "username": "ali_leader",
      "full_name": "علی رضایی",
      "country": "ایران",
      "is_staff": false
    },
    {
      "telegram_id": 987654321,
      "username": "sarah_p",
      "full_name": "سارا",
      "country": "فرانسه",
      "is_staff": false
    }
  ]
}
```

- **پاسخ مورد انتظار از ربات مقام (Status 200):**
```json
{
  "ok": true,
  "status": "processed",
  "promoted": 2,
  "capped": 0,
  "tag_pending": 2
}
```

---

## ۳. سناریو ۲: دریافت روستر بازیکنان فعال (Pull)
هنگامی که مالک در ربات مقام دستور `/roster` یا `/season_preview` را اجرا می‌کند:

- **متد:** `GET`
- **آدرس:** `http://127.0.0.1:8090/internal/v1/rank-roster`
- **هدرها:** همان هدرهای HMAC (با `raw_body=""`).
- **پاسخ مورد انتظار از ربات اصلی (Status 200):**
```json
{
  "generated_at": "2026-11-05T12:00:00Z",
  "players": [
    {
      "telegram_id": 123456789,
      "username": "ali_leader",
      "full_name": "علی رضایی",
      "country": "ایران"
    }
  ]
}
```

---

## ۴. نمونه کد آماده جهت افزودن به ربات اصلی (The Earth Game)

### الف) تابع ارسال وب‌هوک پایان فصل به ربات مقام:
```python
import hashlib
import hmac
import json
import time
import uuid
import aiohttp
from bot.config import get_settings

async def notify_rank_bot_season_ended(players: list[dict], season_label: str = "") -> dict:
    settings = get_settings()
    url = "http://127.0.0.1:8091/internal/v1/season-ended"
    secret = getattr(settings, "rank_sync_secret", "YOUR_SHARED_SECRET")
    
    payload = {
        "event_id": str(uuid.uuid4()),
        "event_type": "season_ended",
        "season_label": season_label,
        "occurred_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "players": players,
    }
    raw_body = json.dumps(payload, ensure_ascii=False)
    ts = int(time.time())
    sig = hmac.new(
        secret.encode("utf-8"),
        f"{ts}.{raw_body}".encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    
    headers = {
        "Content-Type": "application/json",
        "X-Rank-Timestamp": str(ts),
        "X-Rank-Signature": sig,
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=raw_body.encode("utf-8"), headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            return await resp.json()
```

### ب) محل فراخوانی در ربات اصلی:
در فایل `bot/handlers/admin.py` در هندلر تایید ریست فصل (`cb_season_confirm`):
```python
# قبل یا بعد از reset_season(session):
# استخراج پلیرهای دارای کشور:
stmt = select(User.telegram_id, User.username, User.first_name, Country.name_fa).join(Country, Country.owner_user_id == User.telegram_id).where(Country.is_claimed == True)
rows = (await session.execute(stmt)).all()
players = [{"telegram_id": r[0], "username": r[1], "full_name": r[2], "country": r[3]} for r in rows]

# فراخوانی ناهمگام در پس‌زمینه بدون ایجاد وقفه در ریست:
asyncio.create_task(notify_rank_bot_season_ended(players))
```
