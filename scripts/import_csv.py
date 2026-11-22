#!/usr/bin/env python3
"""ייבוא רשימת ספרים מ-CSV (עמודות: #, שם הספר, סופר / סופרת, סדרה / חלק) אל pending/pending.json.
ספרים בלי ISBN לא יכולים להיכנס ל-books/, ולכן הם נשמרים כאן עד שיושלמו (ראו enrich.py)."""
import csv, json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
src = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "pending" / "mybooks.csv"

def split_authors(s):
    parts = re.split(r"\s+ו(?=\S)", s.strip())      # "א ו-ב" / "א וב"
    return parts if len(parts) > 1 and all(len(p.split()) >= 2 for p in parts) else [s.strip()]

def parse_series(s):
    s = s.strip()
    if not s: return None, None
    m = re.match(r'^(.*?)\s*(?:ספר\s*)?(\d+)$', s)
    if not m: return s, None
    name = re.sub(r'\s*ספר$', '', m.group(1)).strip()
    return (name or None), int(m.group(2))

out, seen = [], {}
with open(src, encoding="utf-8-sig", newline="") as f:
    for row in csv.reader(f):
        if not row or not row[0].strip().isdigit(): continue
        row += [""] * (4 - len(row))
        title, author, series = (c.strip() for c in row[1:4])
        sname, snum = parse_series(series)
        b = {"row": int(row[0]), "title": title, "authors": split_authors(author)}
        if sname: b["series"] = sname
        if snum: b["series_number"] = snum
        out.append(b); seen.setdefault(title, []).append(b["row"])
(ROOT / "pending" / "pending.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(f"{len(out)} ספרים נשמרו ב-pending/pending.json")
print("כותרות כפולות:", {t: r for t, r in seen.items() if len(r) > 1} or "אין")
print("שורות עם כמה מחברים:", [(b["row"], b["authors"]) for b in out if len(b["authors"]) > 1])
print("שורות בלי מחבר:", [b["row"] for b in out if not b["authors"][0]] or "אין")
