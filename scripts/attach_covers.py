# -*- coding: utf-8 -*-
"""
סקריפט שממיר ומחבר את תמונות הכריכה מתיקיית covers לקבצי הספרים ול-books.json
- מזהה כל תמונה לפי שם הספר
- ממיר את התמונה לפורמט covers/{isbn}.webp אופטימלי
- מעדכן את books/{isbn}.json ואת books.json עם has_cover = True
"""

import os
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
COVERS_DIR = ROOT / "covers"
BOOKS_DIR = ROOT / "books"

# מיפוי שמות מיוחדים או הבדלי איות
TITLE_ALIASES = {
    "ממכלת הדם והבגידה": "ממלכת הדם והבגידה",
    "שילטונו של מלך האורורה": "שלטונו של מלך האורורה",
    "עיר החרמש": "בית הדם והאדמה",
    "תאה אותי, תעקוב אחרי": "תראה אותי"
}

def normalize_title(t):
    return t.replace('"', '').replace("'", '').replace("״", "").replace("׳", "").strip()

def main():
    # טעינת כל הספרים מתיקיית books/
    books_by_title = {}
    for p in BOOKS_DIR.glob("*.json"):
        try:
            data = json.loads(p.read_text(encoding='utf-8'))
            title = data.get('title', '').strip()
            norm = normalize_title(title)
            books_by_title[norm] = (p, data)
        except Exception as e:
            print(f"שגיאה בקריאת {p.name}: {e}")

    cover_files = [f for f in os.listdir(COVERS_DIR) if not f.startswith('.') and not f.endswith('.webp')]
    print(f"נמצאו {len(cover_files)} תמונות כריכה לעיבוד...")

    matched_count = 0
    unmatched = []

    for cf in cover_files:
        stem = os.path.splitext(cf)[0].strip()
        stem_mapped = TITLE_ALIASES.get(stem, stem)
        norm_stem = normalize_title(stem_mapped)

        # חיפוש התאמה ישירה או חלקית
        match = books_by_title.get(norm_stem)
        if not match:
            for b_norm, (bp, bdata) in books_by_title.items():
                if norm_stem == b_norm or (len(norm_stem) > 4 and (norm_stem in b_norm or b_norm in norm_stem)):
                    match = (bp, bdata)
                    break

        if match:
            book_path, book_data = match
            isbn = book_data["isbn"]
            input_path = COVERS_DIR / cf
            output_webp_path = COVERS_DIR / f"{isbn}.webp"

            try:
                # פתיחה והמרה ל-WebP אופטימלי
                with Image.open(input_path) as img:
                    img = img.convert("RGB")
                    # שינוי גודל פרופורציונלי אם התמונה גדולה מ-800 פיקסלים
                    img.thumbnail((600, 900), Image.Resampling.LANCZOS)
                    img.save(output_webp_path, "WEBP", quality=85, method=6)

                # עדכון קובץ הספר עם cover_url
                book_data["cover_url"] = f"covers/{isbn}.webp"
                book_path.write_text(json.dumps(book_data, ensure_ascii=False, indent=2) + "\n", encoding='utf-8')

                matched_count += 1
                print(f"✓ הותאמה כריכה: {cf} -> {book_data['title']} ({isbn}.webp)")
            except Exception as e:
                print(f"✗ שגיאה בעיבוד {cf}: {e}")
        else:
            unmatched.append(cf)

    print(f"\nסיכום: {matched_count} כריכות חוברו בהצלחה!")
    if unmatched:
        print("תמונות שלא נמצאה להן התאמה:", unmatched)

if __name__ == '__main__':
    main()
