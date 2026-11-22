# 📚 מאגר הספרים הישראלי הפתוח (Israeli Open Books API)

מאגר נתונים פתוח (Open Data) וחינמי המרכז מידע ביבליוגרפי על ספרים שיצאו לאור בישראל (בעברית ובשפות נוספות). הפרויקט מיועד למפתחים, חוקרים ואוהבי ספרים המעוניינים לבנות אפליקציות, אתרים וכלים מבוססי מידע אמין, עשיר ונגיש.

האתר עצמו (`index.html`) כולל חיפוש חי במאגר, סורק ברקוד, כפתורי ייצוא נתונים, מצב לילה ותיעוד מלא של ה-API, ומוגש ישירות מ-GitHub Pages ללא עלות שרת.

---

## 🎯 תכונות ויכולות

* **⚡ נגישות מלאה ללא שרת:** API סטטי וחינמי המבוסס על GitHub Pages ללא צורך במפתחות (API Keys) או הרשמה.
* **📚 מאגר ראשוני עשיר:** כולל מעל **270 ספרים** מובנים עם מספרי ISBN-13, הוצאות, סדרות ותקצירים.
* **📷 סורק ברקוד מהמצלמה:** בטופס הוספת הספר (`add.html`), ניתן להפעיל מצלמה ולסרוק ברקוד בגב הספר לסריקה ומילוי מיידי.
* **🔍 משיכת פרטים אוטומטית (Auto-lookup):** השלמה אוטומטית של פרטי הספר ממאגרים ציבוריים בלחיצת כפתור לפי ISBN.
* **🔎 חיפוש עברי חכם (Fuzzy & Normalized):** חיפוש סלחני לגרשיים, כתיב מלא/חסר, הוצאה, סדרה ודאנאקוד.
* **🌓 מצב לילה / יום (Dark/Light Mode):** שמירת העדפה מקומית בדפדפן.
* **📊 ייצוא נתונים:** הורדת כל המאגר המעודכן כ-JSON מלא או כקובץ CSV בלחיצה אחת.
* **🤝 קהילתיות:** תרומת ספרים דרך טופס Web שמייצר Issue/PR ב-GitHub ומאומת אוטומטית.

---

## 🗂️ מבנה המאגר

```text
/
├── index.html              # אתר החיפוש, התיעוד וייצוא הנתונים
├── add.html                # טופס הוספת ספר + סורק ברקוד ומשיכה אוטומטית
├── books.json              # אינדקס ראשי מאוחד (נבנה אוטומטית ע"י scripts/build.py)
├── books/                  # קובץ JSON נפרד לכל ספר (לפי ISBN)
│   └── 9789655747683.json
├── covers/                 # תמונות כריכה (לפי ISBN)
├── scripts/
│   ├── build.py            # בדיקת תקינות ובניית books.json
│   └── populate_all_books.py # יצירת קבצי הספרים מ-mybooks.csv
├── .github/workflows/      # בדיקות תקינות ובנייה אוטומטית ב-GitHub Actions
├── CONTRIBUTING.md         # מדריך תרומה
└── LICENSE                 # CC BY 4.0
```

---

## 📄 מבנה קובץ ספר (`books/[ISBN].json`)

שדות חובה: `isbn`, `title`, `authors`, `publisher`, `publication_year`, `language`.  
שאר השדות (`danacode`, `subtitle`, `translators`, `pages`, `genres`, `summary`, `series`, `series_number`) אופציונליים.

---

## 🚀 איך משתמשים ב-API?

לאחר הפעלת GitHub Pages:

1. **רשימת כל הספרים:**  
   `https://amizi312.github.io/HEBookAPI/books.json`
2. **ספר בודד לפי ISBN:**  
   `https://amizi312.github.io/HEBookAPI/books/9789655747683.json`
3. **תמונת כריכה:**  
   `https://amizi312.github.io/HEBookAPI/covers/9789655747683.webp` (או קישור OpenLibrary)

---

## 🧪 הרצה מקומית

```bash
# בדיקה ובנייה של האינדקס המאוחד
python scripts/build.py

# הפעלת שרת מקומי לצפייה באתר
python -m http.server 8000
```
ופתחו בדפדפן: [http://localhost:8000](http://localhost:8000)

---

## 📄 רישיון

הנתונים מופצים תחת רישיון **Creative Commons Attribution 4.0 International (CC BY 4.0)**.
