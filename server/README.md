# שירות קליטת ספרים (Render)

מה הוא עושה: מקבל מהטופס נתוני ספר ותמונת כריכה, בודק, דוחס את הכריכה ל-WebP (עד 100KB, בלי EXIF), ופותח Pull Request ב-GitHub. ב-Render לא נשמר דבר. הכל נשמר ב-GitHub ומוגש מ-GitHub Pages.

## הגדרה
1. ב-GitHub: Settings → Developer settings → Fine-grained tokens. מגבילים למאגר הזה בלבד, עם הרשאות Contents ו-Pull requests ברמת Read and write.
2. ב-Render: New → Blueprint → בוחרים את המאגר (קורא את `render.yaml`).
3. מגדירים משתני סביבה: `GITHUB_TOKEN`, `GITHUB_REPO` (owner/repo), `ALLOWED_ORIGIN` (https://USER.github.io), `PAGES_URL` (https://USER.github.io/REPO).
4. מעתיקים את כתובת השירות, בתוספת `/submit`, אל `SUBMIT_URL` בראש הסקריפט ב-`add.html`.

הערות: בתוכנית החינמית השירות נרדם אחרי חוסר פעילות, ושליחה ראשונה יכולה להמתין כדקה. מגבלת קצב: 5 שליחות לשעה לכל כתובת IP.
