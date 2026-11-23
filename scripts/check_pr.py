#!/usr/bin/env python3
"""בדיקות בטיחות ל-PR של ספר חדש. עובר = אפשר למזג אוטומטית. נכשל = נשאר לבדיקה ידנית."""
import json, os, re, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build

BASE = os.environ.get("BASE_REF", "origin/main")
def fail(msg): print(f"❌ {msg}"); sys.exit(1)

diff = subprocess.check_output(["git", "diff", "--name-status", f"{BASE}...HEAD"], text=True).splitlines()
rows = [l.split("\t") for l in diff if l]
if not rows: fail("אין שינויים ב-PR")
if len(rows) > 2: fail("יותר משני קבצים ב-PR")
status = {r[-1]: r[0] for r in rows}
paths = list(status)
jsons = [p for p in paths if re.fullmatch(r"books/\d{13}\.json", p)]
covers = [p for p in paths if re.fullmatch(r"covers/\d{13}\.webp", p)]
if len(jsons) != 1 or len(jsons) + len(covers) != len(paths): fail("הקבצים ב-PR לא תואמים לתבנית של ספר חדש")
isbn = Path(jsons[0]).stem
if covers and Path(covers[0]).stem != isbn: fail("שם קובץ הכריכה לא תואם ל-ISBN")

if any(status[c] != "A" for c in covers): fail("אסור להחליף או למחוק כריכה קיימת")
if status[jsons[0]] not in ("A", "M"): fail("סוג שינוי לא מותר בקובץ הספר")
data, errs = build.validate(build.ROOT / jsons[0])
if errs: fail("; ".join(errs))
old = {}
if status[jsons[0]] == "M":   # השלמת פרטים: מותר רק להוסיף. שדה מלא לא משתנה (חוץ מהוספת ז'אנרים)
    old = json.loads(subprocess.check_output(["git", "show", f"{BASE}:{jsons[0]}"], text=True))
    for k, v in old.items():
        if v in ("", None, [], 0): continue
        nv = data.get(k)
        ok = (isinstance(nv, list) and all(x in nv for x in v)) if k == "genres" else nv == v
        if not ok: fail(f"שינוי בשדה שכבר מלא: {k}")

def strings(v):
    if isinstance(v, str): yield v
    elif isinstance(v, list):
        for x in v: yield from strings(x)
for k, v in data.items():
    if k == "cover_url": continue
    for s in strings(v):
        if re.search(r"https?:|www\.|@|[<>]", s, re.I): fail(f"קישור או תו חשוד בשדה {k}")
        if len(s) > 800: fail(f"טקסט ארוך מדי בשדה {k}")
if "cover_url" in data and (status[jsons[0]] == "A" or data["cover_url"] != old.get("cover_url")):
    if not covers: fail("יש cover_url בלי קובץ כריכה")
    if not re.fullmatch(rf"https://[\w.-]+\.github\.io/[\w.-]+/covers/{isbn}\.webp", data["cover_url"]):
        fail("cover_url לא מצביע על GitHub Pages של המאגר")

if covers:
    from PIL import Image
    f = build.ROOT / covers[0]
    if f.stat().st_size > 100_000: fail("הכריכה גדולה מ-100KB")
    try:
        with Image.open(f) as im:
            if im.format != "WEBP": fail("הכריכה אינה WebP")
            if im.width > 900 or im.height > 1200: fail("מידות הכריכה גדולות מדי")
    except Exception: fail("קובץ הכריכה לא נפתח")
print(f"✅ {isbn} עבר את כל הבדיקות")
