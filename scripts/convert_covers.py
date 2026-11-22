#!/usr/bin/env python3
"""ממיר כריכות JPG/PNG שנוספו מהטופס ל-WebP קטן (עד 100KB) ומוחק את קובץ המקור.
רץ ב-CI לפני scripts/build.py. דורש: pip install pillow"""
import io
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
MAX_BYTES = 100_000

def to_webp(path: Path) -> bytes | None:
    img = Image.open(path).convert("RGBA")
    bg = Image.new("RGB", img.size, "white"); bg.paste(img, mask=img.split()[3]); img = bg
    for box in ((600, 900), (450, 675), (300, 450)):
        small = img.copy(); small.thumbnail(box)
        for quality in (85, 75, 65, 55, 45):      # שומר רק את הפיקסלים (בלי EXIF/מיקום)
            buf = io.BytesIO(); small.save(buf, "WEBP", quality=quality, method=6)
            if buf.tell() <= MAX_BYTES: return buf.getvalue()
    return None

def main():
    for ext in ("jpg", "jpeg", "png"):
        for p in sorted((ROOT / "covers").glob(f"*.{ext}")):
            target = p.with_suffix(".webp")
            try:
                data = to_webp(p)
            except Exception as e:
                data = None; print(f"⚠️ {p.name}: {e}")
            if data:
                target.write_bytes(data); print(f"🖼️ {p.name} -> {target.name} ({len(data)//1024}KB)")
            else:
                print(f"⚠️ לא הצלחנו להמיר את {p.name}; הכריכה לא נשמרה")
            p.unlink()

if __name__ == "__main__":
    main()