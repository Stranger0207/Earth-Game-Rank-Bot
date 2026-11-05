"""
موتور تولید کارت گرافیکی مقام در حافظه رم با استفاده از Pillow و فونت فارسی وزیرمتن.
"""

from __future__ import annotations

import io
import logging
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

from ...core.utils.format import fa_number
from ...domain.promotion import calculate_progress_ratio, is_at_auto_cap

logger = logging.getLogger(__name__)

# مسیر فونت‌های پروژه
_FONT_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "fonts"
_FONT_BOLD = _FONT_DIR / "Vazirmatn-Bold.ttf"
_FONT_REGULAR = _FONT_DIR / "Vazirmatn-Regular.ttf"


def _shape_persian(text: str) -> str:
    """اصلاح چیدمان حروف و جهت‌گیری راست‌به‌چپ متن فارسی."""
    if not text:
        return ""
    try:
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except Exception:
        return text


def _get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """دریافت فونت با اندازه مشخص با سیستم فال‌بک."""
    font_path = _FONT_BOLD if bold else _FONT_REGULAR
    if font_path.exists():
        try:
            return ImageFont.truetype(str(font_path), size)
        except Exception as exc:
            logger.warning("خطا در بارگذاری فونت محلی: %s", exc)

    # فال‌بک به فونت‌های سیستمی ویندوز
    sys_fonts = ["tahoma.ttf", "arial.ttf", "seguiemj.ttf"]
    for sf in sys_fonts:
        try:
            return ImageFont.truetype(sf, size)
        except Exception:
            continue

    return ImageFont.load_default()


def render_rank_card(
    full_name: str,
    rank_name: str,
    level: int,
    tier: str,
    insignia: str,
    seasons_participated: int,
    medals_count: int = 0,
) -> io.BytesIO:
    """
    رسم کارت مقام با طراحی مدرن، تیره و نظامی در حافظه رم:
    ابعاد: 800x450 پیکسل
    """
    width, height = 800, 450
    # پس‌زمینه گرادیان سرمه‌ای-تیره نظامی
    img = Image.new("RGB", (width, height), color=(18, 24, 38))
    draw = ImageDraw.Draw(img)

    # کادر حاشیه‌ای طلایی-نظامی
    draw.rounded_rectangle(
        [(15, 15), (width - 15, height - 15)],
        radius=20,
        outline=(212, 175, 55),
        width=3,
    )

    # هدر کارت
    font_header = _get_font(22, bold=True)
    header_text = _shape_persian("ارتش بازی زمین — کارنامه خدمت نظامی")
    draw.text((width // 2, 45), header_text, font=font_header, fill=(212, 175, 55), anchor="mm")

    # نام عضو
    font_name = _get_font(28, bold=True)
    name_display = _shape_persian(full_name[:24])
    draw.text((width // 2, 95), name_display, font=font_name, fill=(240, 245, 255), anchor="mm")

    # مستطیل نمایش درجه و سطح
    draw.rounded_rectangle(
        [(60, 140), (width - 60, 260)],
        radius=16,
        fill=(26, 36, 56),
        outline=(50, 70, 110),
        width=2,
    )

    # عنوان مقام و رده
    font_rank = _get_font(36, bold=True)
    rank_display = _shape_persian(f"{rank_name}")
    draw.text((width // 2, 185), rank_display, font=font_rank, fill=(255, 215, 0), anchor="mm")

    font_tier = _get_font(20, bold=False)
    tier_display = _shape_persian(f"رده: {tier} | سطح: {fa_number(level)} از ۲۱")
    draw.text((width // 2, 230), tier_display, font=font_tier, fill=(180, 200, 230), anchor="mm")

    # آمار و اطلاعات خدمت (فصل‌ها و مدال‌ها)
    font_stats = _get_font(19, bold=False)
    stats_text = _shape_persian(f"فصول خدمت: {fa_number(seasons_participated)}   |   نشان‌های افتخار: {fa_number(medals_count)}")
    draw.text((width // 2, 290), stats_text, font=font_stats, fill=(200, 215, 240), anchor="mm")

    # بخش نوار پیشرفت یا قفل سقف ارتقای خودکار
    bar_y = 350
    if is_at_auto_cap(level):
        # در سقف خودکار (سطح ۱۷ به بالا)
        font_cap = _get_font(18, bold=True)
        cap_msg = _shape_persian("🔒 در سقف ارتقای خودکار فصلی — ترفیع منحصراً با فرمان مالک")
        draw.text((width // 2, bar_y + 10), cap_msg, font=font_cap, fill=(255, 120, 120), anchor="mm")
    else:
        # نوار پیشرفت تا سطح بعدی
        ratio = calculate_progress_ratio(level)
        bar_w = 560
        bar_h = 24
        bar_x = (width - bar_w) // 2

        # پس‌زمینه خالی نوار
        draw.rounded_rectangle(
            [(bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h)],
            radius=12,
            fill=(40, 50, 70),
        )
        # بخش پر شده نوار
        fill_w = int(bar_w * ratio)
        if fill_w > 12:
            draw.rounded_rectangle(
                [(bar_x, bar_y), (bar_x + fill_w, bar_y + bar_h)],
                radius=12,
                fill=(46, 204, 113),
            )

        font_bar_lbl = _get_font(15, bold=False)
        bar_lbl = _shape_persian(f"پیشرفت در مسیر سرهنگی: {fa_number(int(ratio * 100))}٪")
        draw.text((width // 2, bar_y + bar_h + 18), bar_lbl, font=font_bar_lbl, fill=(160, 180, 210), anchor="mm")

    # ذخیره تصویر خروجی در یک بافر حافظه‌ای BytesIO
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf
