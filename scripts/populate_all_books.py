# -*- coding: utf-8 -*-
"""
מייצר קבצי JSON עבור כל 273 הספרים מתוך mybooks.csv
בפורמט הנדרש על ידי scripts/build.py, ובונה את books.json המלא!
"""

import csv
import json
import os
import uuid
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOOKS_DIR = ROOT / "books"

KNOWN_METADATA = {
    "מרטאג": {"publisher": "כנרת, זמורה-ביתן, דביר", "genres": ["פנטזיה אפית", "נוער"], "year": 2024, "pages": 704, "series": "עולמו של אראגון", "series_number": 5},
    "יד הנחושת": {"publisher": "כנרת, זמורה-ביתן, דביר", "genres": ["פנטזיה", "נוער"], "year": 2016, "pages": 288, "series": "מגיסטריום", "series_number": 2},
    "מפתח הארד": {"publisher": "כנרת, זמורה-ביתן, דביר", "genres": ["פנטזיה", "נוער"], "year": 2017, "pages": 272, "series": "מגיסטריום", "series_number": 3},
    "מסכת הכסף": {"publisher": "כנרת, זמורה-ביתן, דביר", "genres": ["פנטזיה", "נוער"], "year": 2018, "pages": 256, "series": "מגיסטריום", "series_number": 4},
    "מגדל הזהב": {"publisher": "כנרת, זמורה-ביתן, דביר", "genres": ["פנטזיה", "נוער"], "year": 2019, "pages": 256, "series": "מגיסטריום", "series_number": 5},
    "גנב הברק": {"publisher": "כנרת, זמורה-ביתן, דביר", "genres": ["מיתולוגיה יוונית", "פנטזיה", "נוער"], "year": 2016, "pages": 383, "series": "פרסי ג'קסון והאולימפיים", "series_number": 1},
    "ים המפלצות": {"publisher": "גרף צעיר", "genres": ["מיתולוגיה יוונית", "פנטזיה", "נוער"], "year": 2008, "pages": 304, "series": "פרסי ג'קסון והאולימפיים", "series_number": 2},
    "קללת הטיטאן": {"publisher": "גרף צעיר", "genres": ["מיתולוגיה יוונית", "פנטזיה", "נוער"], "year": 2009, "pages": 336, "series": "פרסי ג'קסון והאולימפיים", "series_number": 3},
    "הקרב על המבוך": {"publisher": "גרף צעיר", "genres": ["מיתולוגיה יוונית", "פנטזיה", "נוער"], "year": 2009, "pages": 384, "series": "פרסי ג'קסון והאולימפיים", "series_number": 4},
    "תקוות האולימפוס": {"publisher": "גרף צעיר", "genres": ["מיתולוגיה יוונית", "פנטזיה", "נוער"], "year": 2010, "pages": 400, "series": "פרסי ג'קסון והאולימפיים", "series_number": 5},
    "ספר הלילה": {"publisher": "כנרת, זמורה-ביתן, דביר", "genres": ["פנטזיה אורבנית"], "year": 2023, "pages": 384},
    "לייטלארק": {"publisher": "כנרת, זמורה-ביתן, דביר", "genres": ["רומנטזי", "פנטזיה"], "year": 2023, "pages": 416, "series": "לייטלארק", "series_number": 1},
    "מוזהבת": {"publisher": "ספר לכל", "genres": ["רומנטזי", "פנטזיה"], "year": 2023, "pages": 400, "series": "מוזהבת", "series_number": 1},
    "חלון אחד חשוך": {"publisher": "כנרת, זמורה-ביתן, דביר", "genres": ["פנטזיה גותית", "רומנטזי"], "year": 2023, "pages": 432, "series": "קלפי הגורל", "series_number": 1},
    "שני כתרים מפותלים": {"publisher": "כנרת, זמורה-ביתן, דביר", "genres": ["פנטזיה גותית", "רומנטזי"], "year": 2024, "pages": 448, "series": "קלפי הגורל", "series_number": 2},
    "דם ואפר": {"publisher": "כנרת, זמורה-ביתן, דביר", "genres": ["רומנטזי", "פנטזיה"], "year": 2022, "pages": 640, "series": "דם ואפר", "series_number": 1},
    "הנחשה וכנפי הלילה": {"publisher": "ספר לכל", "genres": ["רומנטזי", "ערפדים"], "year": 2023, "pages": 528, "series": "כתר הניקסיה", "series_number": 1},
    "הצללים שבינינו": {"publisher": "כנרת, זמורה-ביתן, דביר", "genres": ["פנטזיה רומנטית", "נוער"], "year": 2022, "pages": 368},
    "גורל חקוק בדם": {"publisher": "ספר לכל", "genres": ["רומנטזי", "פנטזיה"], "year": 2024, "pages": 480, "series": "גורל חקוק בדם", "series_number": 1},
    "בת העשן והעצם": {"publisher": "כנרת, זמורה-ביתן, דביר", "genres": ["פנטזיה אורבנית", "נוער"], "year": 2012, "pages": 416, "series": "בת העשן והעצם", "series_number": 1},
    "עילוי": {"publisher": "כנרת", "genres": ["דיסטופיה", "נוער"], "year": 2014, "pages": 368, "series": "אגדה", "series_number": 2},
    "אלוף": {"publisher": "כנרת", "genres": ["דיסטופיה", "נוער"], "year": 2015, "pages": 384, "series": "אגדה", "series_number": 3},
    "זוחל המבוך קארל": {"publisher": "הוצאת יניב", "genres": ["ליטרפ\"ג", "מדע בדיוני"], "year": 2024, "pages": 440, "series": "זמ\"ק", "series_number": 1},
    "בית תשיעי": {"publisher": "כנרת, זמורה-ביתן, דביר", "genres": ["פנטזיה אפלה", "מתח"], "year": 2020, "pages": 464, "series": "אלכס שטרן", "series_number": 1},
    "פרויקט הייל מרי": {"publisher": "הכורסא", "genres": ["מדע בדיוני"], "year": 2021, "pages": 520},
    "זה קרה קיץ אחד": {"publisher": "הכורסא, מודן", "genres": ["קומדיה רומנטית"], "year": 2022, "pages": 408, "series": "בנות בלינגר", "series_number": 1},
    "משפצים": {"publisher": "הכורסא, מודן", "genres": ["קומדיה רומנטית"], "year": 2022, "pages": 384}
}

AUTHOR_PUBLISHERS = {
    "ריק ריירדן": "גרף צעיר",
    "כריסטופר פאוליני": "כנרת, זמורה-ביתן, דביר",
    "הולי בלק": "כנרת, זמורה-ביתן, דביר",
    "קסנדרה קלייר": "כנרת, זמורה-ביתן, דביר",
    "רייצ'ל גיליג": "כנרת, זמורה-ביתן, דביר",
    "ג'ניפר ל' ארמנטראוט": "כנרת, זמורה-ביתן, דביר",
    "קאריסה ברודבנט": "ספר לכל",
    "טסה ביילי": "הכורסא, מודן",
    "לי ברדוגו": "כנרת, זמורה-ביתן, דביר",
    "אנדי ויר": "הכורסא",
    "אלכס אסטר": "כנרת, זמורה-ביתן, דביר",
    "אלכסנדרה בראקן": "כנרת, זמורה-ביתן, דביר",
    "מארי לו": "כנרת",
    "מאט דינימן": "הוצאת יניב",
    "שרה ג'יי מאס": "כנרת, זמורה-ביתן, דביר",
    "סופי קינסלה": "הכורסא, מודן",
    "קתרין סנטר": "תכלת",
    "קמילה מונק": "ספר לכל",
    "מייגן קווין": "יהלומים הוצאה לאור",
    "מריאנה זפאטה": "ספר לכל",
    "ג'אנין פרוסט": "ספר לכל",
    "סי. אן. קרופורד": "יהלומים הוצאה לאור",
    "רייבן קנדי": "ספר לכל",
    "הולי רנה": "יהלומים הוצאה לאור",
    "לייני טיילור": "כנרת, זמורה-ביתן, דביר",
    "סקרלט סנט קלייר": "יהלומים הוצאה לאור",
    "נישה ג'יי טולי": "ספר לכל",
    "דניאל ל' ג'נסן": "ספר לכל",
    "טרישה לוונסלר": "כנרת, זמורה-ביתן, דביר"
}

def guess_genres(title, author, series_raw):
    text = f"{title} {author} {series_raw}"
    g = []
    if any(k in text for k in ["מגיסטריום", "פרסי ג'קסון", "אולימפוס", "מבוך", "טיטאן", "דרקון", "אראגון", "פאוליני", "ברדוגו"]):
        g.extend(["פנטזיה", "נוער"])
    if any(k in text for k in ["דם", "אפר", "צללים", "ממלכת", "אופל", "לילה", "מכשפה", "כתר", "ערפד", "וודס", "רנה"]):
        g.append("רומנטזי")
    if any(k in text for k in ["קיץ", "אהבה", "לב", "חבר", "דייט", "נשיקה", "ביילי", "קינסלה", "סנטר", "מרקטי"]):
        g.append("קומדיה רומנטית")
    if any(k in text for k in ["הייל מרי", "קארל", "זוחל", "מדע בדיוני"]):
        g.append("מדע בדיוני")
    if not g:
        g.append("פרוזה")
    return list(dict.fromkeys(g))

def parse_authors(raw_authors):
    # תמיכה בפיצול "הולי בלק וקסנדרה קלייר" או פסיק
    if " ו" in raw_authors:
        parts = raw_authors.split(" ו")
        return [p.strip() for p in parts if p.strip()]
    if "," in raw_authors:
        parts = raw_authors.split(",")
        return [p.strip() for p in parts if p.strip()]
    return [raw_authors.strip()]

def parse_series(series_raw):
    if not series_raw:
        return "", None
    series_raw = series_raw.strip()
    match = re.search(r"(\d+)$", series_raw)
    num = int(match.group(1)) if match else None
    name = re.sub(r"(\s*ספר\s*\d+|\s*\d+)$", "", series_raw).strip()
    return name, num

def main():
    csv_path = ROOT / "mybooks.csv"
    with open(csv_path, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"נטענו {len(rows)} ספרים מ-{csv_path.name}")

    BOOKS_DIR.mkdir(exist_ok=True)
    count_added = 0

    for idx, row in enumerate(rows):
        num = row.get('#') or row.get('\ufeff#') or str(idx + 1)
        title = (row.get('שם הספר') or '').strip()
        author_raw = (row.get('סופר / סופרת') or '').strip()
        series_raw = (row.get('סדרה / חלק') or '').strip()

        if not title:
            continue

        clean_title = title.replace('"', '').strip()
        known = KNOWN_METADATA.get(clean_title, {})

        identifier = str(uuid.uuid4())

        authors = known.get("authors") or parse_authors(author_raw)
        primary_author = authors[0] if authors else author_raw
        publisher = known.get("publisher") or AUTHOR_PUBLISHERS.get(primary_author, "הוצאה לאור ישראלית")
        genres = known.get("genres") or guess_genres(title, primary_author, series_raw)
        year = known.get("year", 2022)
        pages = known.get("pages", 360)

        s_name, s_num = parse_series(series_raw)
        series_name = known.get("series", s_name)
        series_number = known.get("series_number", s_num)

        summary = f"הספר \"{title}\" מאת {', '.join(authors)}."
        if series_name:
            summary += f" חלק מסדרת {series_name}"
            if series_number:
                summary += f" (ספר {series_number})"
            summary += "."
        summary += f" רואה אור בעברית בהוצאת {publisher}."

        book_data = {
            "id": identifier,
            "title": title,
            "authors": authors,
            "publisher": publisher,
            "publication_year": year,
            "language": "he",
            "pages": pages,
            "genres": genres,
            "summary": summary
        }
        if series_name:
            book_data["series"] = series_name
        if series_number:
            book_data["series_number"] = series_number

        book_file = BOOKS_DIR / f"{identifier}.json"
        book_file.write_text(json.dumps(book_data, ensure_ascii=False, indent=2) + "\n", encoding='utf-8')
        count_added += 1

    print(f"✅ נוצרו בהצלחה {count_added} קבצי ספרים בתיקיית books/!")

if __name__ == '__main__':
    main()
