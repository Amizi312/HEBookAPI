# איך מוסיפים ספר

1. צרו קובץ `books/<UUID>.json` לפי המבנה ב-README. המזהה ושם הקובץ נוצרים אוטומטית.
2. (אופציונלי) הוסיפו כריכה דחוסה בפורמט WebP בשם `covers/<UUID>.webp`, עד 100KB. העלו רק כריכות שיש לכם זכות להפיץ.
3. הריצו מקומית `python scripts/build.py` לבדיקה.
4. פתחו Pull Request. הבדיקה האוטומטית תוודא שהקובץ תקין. אין צורך לערוך את `books.json` ידנית.

שדות חובה: `title`, `authors`, `language`. המערכת מוסיפה `id` מסוג UUID.
שדות אופציונליים: `danacode` (NNN-NNNN), `subtitle`, `translators`, `pages`, `genres`, `summary`, `cover_url`.
תקצירים: כתבו במילים שלכם, בלי להעתיק מהוצאות או מאתרי מכירה.

## ייבוא רשימה גדולה
`python scripts/import_csv.py mylist.csv` שומר את הרשימה ב-`pending/pending.json`. `python scripts/enrich.py` מציע מועמדים, ואותם יש לאמת לפני מיזוג.

## הוספה דרך הטופס (בלי לכתוב JSON)
באתר יש עמוד `add.html`. הוא בודק את הנתונים, פותח Issue מוכן ב-GitHub, ו-Action ממיר אותו ל-Pull Request לבדיקה. הגדרה חד-פעמית: Settings → Actions → General → סימון "Allow GitHub Actions to create and approve pull requests".

## כריכה והעלאה בלי חשבון GitHub
כשמגדירים את שירות Render (ראו `server/README.md`), הטופס מאפשר להעלות תמונת כריכה ולשלוח בלי חשבון GitHub. התמונה נדחסת אוטומטית ל-WebP ונפתח Pull Request לבדיקה.
