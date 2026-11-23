#!/usr/bin/env python3
"""בדיקת תקינות קבצי הספרים ובניית books.json אוטומטית.
שימוש:  python scripts/build.py          (בודק ובונה)
         python scripts/build.py --check  (בודק בלבד; נכשל גם אם books.json לא מעודכן)
"""
import json, sys, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUIRED = {"title": str, "authors": list, "language": str}
OPTIONAL = {"id": str, "isbn": str, "publisher": str, "publication_year": int, "danacode": str, "subtitle": str, "translators": list, "pages": int,
            "genres": list, "summary": str, "cover_url": str,
            "series": str, "series_number": int, "original_title": str}
DANACODE = re.compile(r"^\d{3}-\d{4}$")
UUID = re.compile(r"^[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$")

def validate(path):
    errs = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return None, [f"JSON לא תקין: {e}"]
    for k, t in REQUIRED.items():
        if k not in data: errs.append(f"שדה חובה חסר: {k}")
        elif not isinstance(data[k], t): errs.append(f"סוג שגוי בשדה {k}")
    for k, t in OPTIONAL.items():
        if k in data and not isinstance(data[k], t): errs.append(f"סוג שגוי בשדה {k}")
    for k in data:
        if k not in REQUIRED and k not in OPTIONAL: errs.append(f"שדה לא מוכר: {k}")
    if not errs:
        identifier = data.get("id") or data.get("isbn")
        if not identifier: errs.append("שדה מזהה חסר: id")
        elif data.get("id") and not UUID.fullmatch(data["id"]): errs.append("מזהה id חייב להיות UUID")
        elif path.stem != identifier: errs.append("שם הקובץ חייב להתאים למזהה הספר")
        if not data["authors"]: errs.append("חייב מחבר אחד לפחות")
        if data.get("danacode") and not DANACODE.match(data["danacode"]): errs.append("דאנאקוד בפורמט NNN-NNNN")
        if "publication_year" in data and not 1400 <= data["publication_year"] <= 2100: errs.append("שנת הוצאה לא סבירה")
    return data, errs

def main():
    check = "--check" in sys.argv
    books, failed = [], False
    for p in sorted((ROOT / "books").glob("*.json")):
        data, errs = validate(p)
        for e in errs:
            print(f"❌ {p.name}: {e}"); failed = True
        if data and not errs:
            identifier = data.get("id") or data.get("isbn")
            books.append({
                "id": identifier, "title": data["title"], "authors": data["authors"],
                "publisher": data.get("publisher", ""), "publication_year": data.get("publication_year"),
                "language": data["language"], "genres": data.get("genres", []),
                "series": data.get("series", ""), "series_number": data.get("series_number"),
                "has_cover": (ROOT / "covers" / f"{identifier}.webp").exists(),
            })
    if failed: sys.exit(1)
    books.sort(key=lambda b: b["title"])
    out = json.dumps({"count": len(books), "books": books}, ensure_ascii=False, indent=2) + "\n"
    target = ROOT / "books.json"
    if check:
        if not target.exists() or target.read_text(encoding="utf-8") != out:
            print("❌ books.json לא מעודכן. הריצו: python scripts/build.py"); sys.exit(1)
    else:
        target.write_text(out, encoding="utf-8")
    print(f"✅ {len(books)} ספרים תקינים")

if __name__ == "__main__":
    main()