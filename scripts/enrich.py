#!/usr/bin/env python3
"""משלים פרטים (הוצאה, שנה, עמודים, ז'אנרים) לספרים שב-pending/pending.json
באמצעות Google Books API (חינמי, ללא מפתח לשימוש קל) ושומר מועמדים לבדיקה ידנית.

  python scripts/enrich.py                 # יוצר pending/candidates.json (לבדיקה ידנית)
  python scripts/enrich.py --write         # כותב ל-books/ רק התאמות ודאיות (כותרת זהה + שם משפחה של המחבר)
  python scripts/enrich.py --limit 10      # הרצת ניסיון על 10 הספרים הראשונים

חשוב: מעבירים אל books/ רק ספרים שהמהדורה העברית שלהם אומתה. לא מעתיקים תקצירים מהוצאות או מחנויות."""
import json, re, sys, time, urllib.parse, urllib.request, uuid
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent

def norm(s): return re.sub(r"[^\w]", "", s or "").lower()

def search(title, author):
    q = f'intitle:"{title}" inauthor:"{author}"'
    url = "https://www.googleapis.com/books/v1/volumes?" + urllib.parse.urlencode(
        {"q": q, "langRestrict": "he", "maxResults": 8, "printType": "books"})
    with urllib.request.urlopen(url, timeout=20) as r:
        return json.load(r).get("items", [])

def to_book(item, src):
    v = item["volumeInfo"]
    year = re.match(r"\d{4}", v.get("publishedDate", ""))
    b = {"id": str(uuid.uuid4()), "title": v.get("title", ""), "authors": v.get("authors", src["authors"]),
         "publisher": v.get("publisher", ""), "publication_year": int(year.group()) if year else 0,
         "language": v.get("language", "he")}
    if v.get("subtitle"): b["subtitle"] = v["subtitle"]
    if v.get("pageCount"): b["pages"] = v["pageCount"]
    if v.get("categories"): b["genres"] = v["categories"]
    for k in ("series", "series_number"):
        if k in src: b[k] = src[k]
    return b

def confident(b, src):
    last = {a.split()[-1] for a in src["authors"]}
    ok_author = any(norm(l) in norm(" ".join(b["authors"])) for l in last)
    return (norm(b["title"]) == norm(src["title"]) and ok_author
            and b["publisher"] and b["publication_year"] and b["language"] == "he")

def main():
    write = "--write" in sys.argv
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
    pending = json.loads((ROOT / "pending" / "pending.json").read_text(encoding="utf-8"))[:limit]
    cands, done = [], 0
    for src in pending:
        try:
            items = search(src["title"], src["authors"][0])
        except Exception as e:
            print(f"שורה {src['row']}: שגיאת רשת ({e})"); items = []
        found = [b for b in (to_book(i, src) for i in items) if b]
        sure = [b for b in found if confident(b, src)]
        cands.append({"row": src["row"], "title": src["title"], "confident": bool(sure),
                      "candidates": sure[:1] or found[:3]})
        if write and sure:
            (ROOT / "books" / f"{sure[0]['id']}.json").write_text(
                json.dumps(sure[0], ensure_ascii=False, indent=2) + "\n", encoding="utf-8"); done += 1
        time.sleep(0.4)
    (ROOT / "pending" / "candidates.json").write_text(json.dumps(cands, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"נבדקו {len(pending)}; התאמה ודאית: {sum(c['confident'] for c in cands)}; נכתבו ל-books/: {done}")

if __name__ == "__main__":
    main()
