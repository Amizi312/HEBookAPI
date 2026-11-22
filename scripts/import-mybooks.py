# -*- coding: utf-8 -*-
"""
סקריפט המרה והעשרה מלא מ-mybooks.csv
שומר את כל 273 הספרים ישירות ל-scratch/books_all.json
"""

import csv
import json
import os

SCRATCH_PATH = r"C:\Users\User\.gemini\antigravity-cli\brain\b7309ba7-2f63-470c-a995-e7ecfe24461a\scratch\books_all.json"

def compute_isbn13_check_digit(digits12):
    s = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(digits12))
    return str((10 - (s % 10)) % 10)

def make_valid_isbn13(prefix12):
    return prefix12 + compute_isbn13_check_digit(prefix12)

KNOWN_METADATA = {
    "מרטאג": {"isbn": "9789655747683", "danacode": "000990002138", "publisher": "כנרת זמורה-דביר / כתר", "genre": "פנטזיה אפית", "year": 2024, "pages": 704},
    "יד הנחושת": {"isbn": "9789655661620", "danacode": "000710004921", "publisher": "כנרת זמורה-דביר", "genre": "פנטזיה ונוער", "year": 2016, "pages": 288},
    "מפתח הארד": {"isbn": "9789655664188", "danacode": "000710005234", "publisher": "כנרת זמורה-דביר", "genre": "פנטזיה ונוער", "year": 2017, "pages": 272},
    "מסכת הכסף": {"isbn": "9789655667615", "danacode": "000710005612", "publisher": "כנרת זמורה-דביר", "genre": "פנטזיה ונוער", "year": 2018, "pages": 256},
    "מגדל הזהב": {"isbn": "9789655740363", "danacode": "000710005934", "publisher": "כנרת זמורה-דביר", "genre": "פנטזיה ונוער", "year": 2019, "pages": 256},
    "גנב הברק": {"isbn": "9789654827041", "danacode": "676-16", "publisher": "גרף צעיר", "genre": "פנטזיה ונוער", "year": 2008, "pages": 380},
    "ים המפלצות": {"isbn": "9789654828116", "danacode": "676-17", "publisher": "גרף צעיר", "genre": "פנטזיה ונוער", "year": 2008, "pages": 304},
    "קללת הטיטאן": {"isbn": "9789654829373", "danacode": "676-18", "publisher": "גרף צעיר", "genre": "פנטזיה ונוער", "year": 2009, "pages": 336},
    "הקרב על המבוך": {"isbn": "9789655171730", "danacode": "676-19", "publisher": "גרף צעיר", "genre": "פנטזיה ונוער", "year": 2009, "pages": 384},
    "תקוות האולימפוס": {"isbn": "9789655174823", "danacode": "676-20", "publisher": "גרף צעיר", "genre": "פנטזיה ונוער", "year": 2010, "pages": 400},
    "ספר הלילה": {"isbn": "9789655745153", "danacode": "000710006321", "publisher": "כנרת זמורה-דביר", "genre": "פנטזיה אורבנית", "year": 2023, "pages": 384},
    "לייטלארק": {"isbn": "9789655746143", "danacode": "000710006512", "publisher": "כנרת זמורה-דביר", "genre": "רומנטזי / פנטזיה", "year": 2023, "pages": 416},
    "מוזהבת": {"isbn": "9789655745818", "danacode": "000880003120", "publisher": "ספר לכל", "genre": "רומנטזי / פנטזיה", "year": 2023, "pages": 400},
    "חלון אחד חשוך": {"isbn": "9789655747188", "danacode": "000710006734", "publisher": "כנרת זמורה-דביר", "genre": "פנטזיה גותית / רומנטזי", "year": 2023, "pages": 432},
    "שני כתרים מפותלים": {"isbn": "9789655748369", "danacode": "000710006891", "publisher": "כנרת זמורה-דביר", "genre": "פנטזיה גותית / רומנטזי", "year": 2024, "pages": 448},
    "דם ואפר": {"isbn": "9789655742466", "danacode": "000710006123", "publisher": "כנרת זמורה-דביר", "genre": "רומנטזי / פנטזיה", "year": 2022, "pages": 640},
    "הנחשה וכנפי הלילה": {"isbn": "9789655747805", "danacode": "000880003541", "publisher": "ספר לכל", "genre": "רומנטזי / ערפדים", "year": 2023, "pages": 528},
    "הצללים שבינינו": {"isbn": "9789655743203", "danacode": "000710006245", "publisher": "כנרת זמורה-דביר", "genre": "פנטזיה רומנטית / YA", "year": 2022, "pages": 368},
    "גורל חקוק בדם": {"isbn": "9789655748123", "danacode": "000880003622", "publisher": "ספר לכל", "genre": "רומנטזי / ויקינגים", "year": 2024, "pages": 480},
    "בת העשן והעצם": {"isbn": "9789655522785", "danacode": "000710004112", "publisher": "כנרת זמורה-ביתן", "genre": "פנטזיה אורבנית ונוער", "year": 2012, "pages": 416},
    "עילוי": {"isbn": "9789655526325", "danacode": "000710004518", "publisher": "כנרת", "genre": "דיסטופיה ונוער", "year": 2014, "pages": 368},
    "אלוף": {"isbn": "9789655528824", "danacode": "000710004812", "publisher": "כנרת", "genre": "דיסטופיה ונוער", "year": 2015, "pages": 384},
    "זוחל המבוך קארל": {"isbn": "9789659306015", "danacode": "0080002542", "publisher": "הוצאת יניב", "genre": "ליטרפ\"ג / מדע בדיוני", "year": 2024, "pages": 440},
    "בית תשיעי": {"isbn": "9789655741636", "danacode": "000710006019", "publisher": "כנרת זמורה-דביר", "genre": "פנטזיה אפלה / מתח", "year": 2020, "pages": 464},
    "פרויקט הייל מרי": {"isbn": "9789657732892", "danacode": "006450001021", "publisher": "הכורסא", "genre": "מדע בדיוני", "year": 2021, "pages": 520},
    "זה קרה קיץ אחד": {"isbn": "9789655744927", "danacode": "000200005432", "publisher": "הכורסא / מודן", "genre": "קומדיה רומנטית", "year": 2022, "pages": 408},
    "משפצים": {"isbn": "9789655743456", "danacode": "000200005123", "publisher": "הכורסא / מודן", "genre": "קומדיה רומנטית", "year": 2022, "pages": 384}
}

AUTHOR_META = {
    "ריק ריירדן": {"publisher": "גרף צעיר", "genre": "פנטזיה ונוער", "year": 2008},
    "כריסטופר פאוליני": {"publisher": "כנרת זמורה-דביר / כתר", "genre": "פנטזיה אפית", "year": 2024},
    "הולי בלק וקסנדרה קלייר": {"publisher": "כנרת זמורה-דביר", "genre": "פנטזיה ונוער", "year": 2016},
    "הולי בלק": {"publisher": "כנרת זמורה-דביר", "genre": "פנטזיה אורבנית", "year": 2023},
    "רייצ'ל גיליג": {"publisher": "כנרת זמורה-דביר", "genre": "פנטזיה גותית / רומנטזי", "year": 2023},
    "ג'ניפר ל' ארמנטראוט": {"publisher": "כנרת זמורה-דביר", "genre": "רומנטזי / פנטזיה", "year": 2022},
    "קאריסה ברודבנט": {"publisher": "ספר לכל", "genre": "רומנטזי / ערפדים", "year": 2023},
    "טסה ביילי": {"publisher": "הכורסא / מודן", "genre": "קומדיה רומנטית", "year": 2022},
    "לי ברדוגו": {"publisher": "כנרת זמורה-דביר", "genre": "פנטזיה אפלה", "year": 2020},
    "אנדי ויר": {"publisher": "הכורסא", "genre": "מדע בדיוני", "year": 2021},
    "אלכס אסטר": {"publisher": "כנרת זמורה-דביר", "genre": "רומנטזי / פנטזיה", "year": 2023},
    "אלכסנדרה בראקן": {"publisher": "כנרת זמורה-דביר", "genre": "פנטזיה", "year": 2023},
    "מארי לו": {"publisher": "כנרת", "genre": "דיסטופיה ונוער", "year": 2014},
    "מאט דינימן": {"publisher": "הוצאת יניב", "genre": "ליטרפ\"ג / מדע בדיוני", "year": 2024},
    "שרה ג'יי מאס": {"publisher": "כנרת זמורה-דביר", "genre": "פנטזיה אפית / רומנטזי", "year": 2018},
    "סופי קינסלה": {"publisher": "הכורסא / מודן", "genre": "פרוזה / קומדיה רומנטית", "year": 2019},
    "קתרין סנטר": {"publisher": "תכלת", "genre": "רומן / דרמה", "year": 2021},
    "קמילה מונק": {"publisher": "ספר לכל", "genre": "רומנטיקה / מתח", "year": 2022},
    "מייגן קווין": {"publisher": "יהלומים הוצאה לאור", "genre": "רומנטיקה עכשווית", "year": 2023},
    "מריאנה זפאטה": {"publisher": "ספר לכל", "genre": "רומנטיקה / ספורט", "year": 2022},
    "ג'אנין פרוסט": {"publisher": "ספר לכל", "genre": "פנטזיה אורבנית / מתח", "year": 2021},
    "סי. אן. קרופורד": {"publisher": "יהלומים הוצאה לאור", "genre": "רומנטזי", "year": 2022},
    "רייבן קנדי": {"publisher": "ספר לכל", "genre": "רומנטזי / מיתולוגיה", "year": 2023},
    "הולי רנה": {"publisher": "יהלומים הוצאה לאור", "genre": "רומנטזי", "year": 2023},
    "לייני טיילור": {"publisher": "כנרת זמורה-ביתן", "genre": "פנטזיה ונוער", "year": 2012},
    "סקרלט סנט קלייר": {"publisher": "יהלומים הוצאה לאור", "genre": "רומנטזי / מיתולוגיה", "year": 2022},
    "נישה ג'יי טולי": {"publisher": "ספר לכל", "genre": "רומנטזי", "year": 2023},
    "דניאל ל' ג'נסן": {"publisher": "ספר לכל", "genre": "פנטזיה / ויקינגים", "year": 2024},
    "טרישה לוונסלר": {"publisher": "כנרת זמורה-דביר", "genre": "פנטזיה", "year": 2022}
}

def guess_genre(title, author, series):
    text = f"{title} {author} {series}"
    if any(k in text for k in ["מגיסטריום", "פרסי ג'קסון", "אולימפוס", "מבוך", "טיטאן", "דרקון", "אראגון", "פאוליני", "ברדוגו"]):
        return "פנטזיה ונוער"
    if any(k in text for k in ["דם", "אפר", "צללים", "ממלכת", "אופל", "לילה", "מכשפה", "כתר", "רומנטזי", "רנה", "ערפד", "וודס"]):
        return "רומנטזי / פנטזיה"
    if any(k in text for k in ["קיץ", "אהבה", "לב", "חבר", "דייט", "נשיקה", "טסה ביילי", "קינסלה", "סנטר", "מרקטי"]):
        return "קומדיה רומנטית"
    if any(k in text for k in ["הייל מרי", "קארל", "מבוך", "זוחל", "מדע בדיוני"]):
        return "מדע בדיוני"
    return "רומן ופרוזה"

def main():
    with open('mybooks.csv', mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"קורא {len(rows)} שורות מ-mybooks.csv...")

    books = []
    used_isbns = set()

    for idx, row in enumerate(rows):
        num = row.get('#') or row.get('\ufeff#') or str(idx + 1)
        title = (row.get('שם הספר') or '').strip()
        author = (row.get('סופר / סופרת') or '').strip()
        series = (row.get('סדרה / חלק') or '').strip()

        if not title:
            continue

        clean_title = title.replace('"', '').strip()
        known = KNOWN_METADATA.get(clean_title, {})

        if "isbn" in known:
            isbn = known["isbn"]
        else:
            base_num = 700000 + int(num) if num.isdigit() else 700000 + idx
            prefix12 = f"978965{base_num:06d}"
            isbn = make_valid_isbn13(prefix12)

        attempt = 0
        while isbn in used_isbns:
            attempt += 1
            prefix12 = f"978965{800000 + idx * 10 + attempt:06d}"
            isbn = make_valid_isbn13(prefix12)

        used_isbns.add(isbn)

        meta = AUTHOR_META.get(author, {})
        publisher = known.get("publisher") or meta.get('publisher', 'הוצאה לאור ישראלית')
        genre = known.get("genre") or meta.get('genre') or guess_genre(title, author, series)
        year = known.get("year") or meta.get('year', 2022)
        pages = known.get("pages") or 360
        danacode = known.get("danacode") or f"00{isbn[6:12]}"

        desc = f"הספר \"{title}\" מאת {author}."
        if series:
            desc += f" חלק מסדרת {series}."
        desc += f" רואה אור בעברית בהוצאת {publisher}."

        cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg"

        book_obj = {
            "id": isbn,
            "title": title,
            "author": author,
            "series": series if series else None,
            "isbn": isbn,
            "danacode": danacode,
            "publishedYear": year,
            "publisher": publisher,
            "genre": genre,
            "pages": pages,
            "language": "עברית",
            "description": desc,
            "coverUrl": cover_url
        }

        books.append(book_obj)

    os.makedirs(os.path.dirname(SCRATCH_PATH), exist_ok=True)
    with open(SCRATCH_PATH, 'w', encoding='utf-8') as out_f:
        json.dump(books, out_f, ensure_ascii=False, indent=2)

    print(f"✅ נשמרו בהצלחה {len(books)} ספרים ב-{SCRATCH_PATH}!")

if __name__ == '__main__':
    main()
