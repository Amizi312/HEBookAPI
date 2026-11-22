"""שירות קבלת ספרים: מקבל טופס + תמונת כריכה, מאמת, דוחס ל-WebP ופותח Pull Request ב-GitHub.
שום מידע לא נשמר ב-Render. הכל נשמר ב-GitHub ומוגש מ-GitHub Pages."""
import base64, io, json, os, sys, tempfile, time
from collections import defaultdict, deque
from pathlib import Path
import httpx
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import build  # אותה בדיקת תקינות כמו ב-CI

TOKEN = os.environ.get("GITHUB_TOKEN", "")
REPO = os.environ.get("GITHUB_REPO", "")
BASE = os.environ.get("BASE_BRANCH", "main")
ORIGIN = os.environ.get("ALLOWED_ORIGIN", "")
PAGES = os.environ.get("PAGES_URL", "").rstrip("/")
MAX_UPLOAD = 6 * 1024 * 1024
MAX_COVER_BYTES = 100_000
RATE, WINDOW = 5, 3600
GH = "https://api.github.com"
Image.MAX_IMAGE_PIXELS = 25_000_000

app = FastAPI(title="Israeli Open Books submit")
app.add_middleware(CORSMiddleware, allow_origins=[ORIGIN] if ORIGIN else [],
                   allow_methods=["POST", "GET"], allow_headers=["*"])
hits = defaultdict(deque)

def rate_limit(request: Request):
    ip = (request.headers.get("x-forwarded-for") or request.client.host or "?").split(",")[0].strip()
    q, now = hits[ip], time.time()
    while q and now - q[0] > WINDOW: q.popleft()
    if len(q) >= RATE: raise HTTPException(429, "יותר מדי שליחות. נסו שוב בעוד שעה.")
    q.append(now)

def process_cover(raw: bytes) -> bytes:
    try:
        Image.open(io.BytesIO(raw)).verify()
        img = Image.open(io.BytesIO(raw))
        if img.format not in ("JPEG", "PNG", "WEBP"): raise ValueError
        img = img.convert("RGBA")
        bg = Image.new("RGB", img.size, "white"); bg.paste(img, mask=img.split()[3]); img = bg
    except Exception:
        raise HTTPException(422, "קובץ התמונה לא תקין. יש להעלות JPG, PNG או WebP.")
    for box in ((600, 900), (450, 675), (300, 450)):   # אם עדיין גדול, מקטינים עוד
        small = img.copy(); small.thumbnail(box)
        for quality in (85, 75, 65, 55, 45):           # מסיר גם מטא-דאטה (EXIF, מיקום)
            buf = io.BytesIO(); small.save(buf, "WEBP", quality=quality, method=6)
            if buf.tell() <= MAX_COVER_BYTES: return buf.getvalue()
    raise HTTPException(422, "התמונה מורכבת מדי. נסו תמונה אחרת.")

async def open_pr(isbn: str, book: dict, webp: bytes | None) -> str:
    h = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json",
         "X-GitHub-Api-Version": "2022-11-28"}
    b64 = lambda b: base64.b64encode(b).decode()
    branch = f"web-book-{isbn}"
    async with httpx.AsyncClient(timeout=30, headers=h, base_url=f"{GH}/repos/{REPO}") as c:
        if (await c.get(f"/contents/books/{isbn}.json", params={"ref": BASE})).status_code == 200:
            raise HTTPException(409, "הספר כבר קיים במאגר.")
        r = await c.get(f"/git/ref/heads/{BASE}"); r.raise_for_status()
        r = await c.post("/git/refs", json={"ref": f"refs/heads/{branch}", "sha": r.json()["object"]["sha"]})
        if r.status_code == 422: raise HTTPException(409, "הספר הזה כבר נשלח וממתין לבדיקה.")
        r.raise_for_status()
        try:
            files = [(f"books/{isbn}.json", (json.dumps(book, ensure_ascii=False, indent=2) + "\n").encode())]
            if webp: files.append((f"covers/{isbn}.webp", webp))
            for path, content in files:
                (await c.put(f"/contents/{path}", json={"message": f"feat: הוספת {path} מהטופס",
                                                        "content": b64(content), "branch": branch})).raise_for_status()
            title = " ".join(book["title"].split())[:100]
            body = ("נשלח דרך טופס האתר.\n\nלפני המיזוג כדאי לוודא את הפרטים מול הספר או מקור ביבליוגרפי."
                    + ("\n\nצורפה תמונת כריכה. המגיש/ה אישר/ה שיש לו/לה זכות להעלות אותה." if webp else ""))
            r = await c.post("/pulls", json={"title": f"ספר חדש: {title} ({isbn})", "head": branch,
                                             "base": BASE, "body": body})
            r.raise_for_status(); return r.json()["html_url"]
        except Exception:
            await c.delete(f"/git/refs/heads/{branch}"); raise

@app.get("/health")
def health(): return {"ok": True}

@app.post("/submit")
async def submit(request: Request, data: str = Form(...), cover_rights: str = Form("false"),
                 website: str = Form(""), cover: UploadFile | None = File(None)):
    if website: return {"ok": True}                       # בוט: מתעלמים בשקט
    if int(request.headers.get("content-length") or 0) > MAX_UPLOAD + 100_000:
        raise HTTPException(413, "הקובץ גדול מדי.")
    rate_limit(request)
    if not (TOKEN and REPO): raise HTTPException(503, "השירות לא הוגדר.")
    try:
        book = json.loads(data) if len(data) <= 20_000 else None
        assert isinstance(book, dict)
    except Exception:
        raise HTTPException(422, "נתוני הספר לא תקינים.")
    allowed = set(build.REQUIRED) | set(build.OPTIONAL)
    book = {k: v for k, v in book.items() if k in allowed and k != "cover_url"}
    isbn = str(book.get("isbn", ""))
    if not build.isbn13_ok(isbn): raise HTTPException(422, "ISBN-13 לא תקין.")
    webp = None
    if cover is not None and cover.filename:
        if cover_rights != "true": raise HTTPException(422, "יש לאשר שיש לך זכות להעלות את התמונה.")
        raw = await cover.read(MAX_UPLOAD + 1)
        if len(raw) > MAX_UPLOAD: raise HTTPException(413, "הקובץ גדול מדי.")
        webp = process_cover(raw)
        if PAGES: book["cover_url"] = f"{PAGES}/covers/{isbn}.webp"
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / f"{isbn}.json"; p.write_text(json.dumps(book, ensure_ascii=False), encoding="utf-8")
        _, errs = build.validate(p)
    if errs: raise HTTPException(422, "; ".join(errs))
    try:
        return {"ok": True, "pr": await open_pr(isbn, book, webp)}
    except HTTPException: raise
    except httpx.HTTPError:
        raise HTTPException(502, "לא הצלחנו לשמור את הספר כרגע. נסו שוב מאוחר יותר.")
