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
REVIEW_REPO = os.environ.get("REVIEW_REPO", "")   # מאגר פרטי לבדיקות. אם ריק, נפתח Issue במאגר הראשי (ציבורי)
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

EMPTY = (None, "", [], 0)
def merge_book(old: dict, new: dict):
    """ממזג הצעה לספר קיים. ממלא רק שדות ריקים, מאחד ז'אנרים, ושדה מלא שונה הוא התנגשות."""
    merged, added, conflicts = dict(old), [], []
    for k, v in new.items():
        if k == "isbn" or v in EMPTY: continue
        cur = old.get(k)
        if cur in EMPTY: merged[k] = v; added.append(k)
        elif cur == v: continue
        elif k == "genres" and isinstance(cur, list) and isinstance(v, list):
            extra = [x for x in v if x not in cur]
            if extra: merged[k] = cur + extra; added.append(k)
        else: conflicts.append({"field": k, "current": cur, "proposed": v})
    return merged, added, conflicts

HEADERS = lambda: {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json",
                   "X-GitHub-Api-Version": "2022-11-28"}
b64 = lambda b: base64.b64encode(b).decode()

async def create_pr(c, branch, isbn, book, webp, sha, kind, note=""):
    r = await c.get(f"/git/ref/heads/{BASE}"); r.raise_for_status()
    r2 = await c.post("/git/refs", json={"ref": f"refs/heads/{branch}", "sha": r.json()["object"]["sha"]})
    if r2.status_code == 422: raise HTTPException(409, "הספר הזה כבר נשלח וממתין לבדיקה.")
    r2.raise_for_status()
    try:
        files = [(f"books/{isbn}.json", (json.dumps(book, ensure_ascii=False, indent=2) + "\n").encode(), sha)]
        if webp: files.append((f"covers/{isbn}.webp", webp, None))
        for path, content, file_sha in files:
            payload = {"message": f"feat: {kind} {path} מהטופס", "content": b64(content), "branch": branch}
            if file_sha: payload["sha"] = file_sha
            (await c.put(f"/contents/{path}", json=payload)).raise_for_status()
        title = " ".join(book["title"].split())[:100]
        body = (f"{kind}. נשלח דרך טופס האתר.{note}"
                + ("\n\nצורפה תמונת כריכה. המגיש/ה אישר/ה שיש לו/לה זכות להעלות אותה." if webp else ""))
        r3 = await c.post("/pulls", json={"title": f"{kind}: {title} ({isbn})", "head": branch, "base": BASE, "body": body})
        r3.raise_for_status(); return r3.json()["html_url"]
    except Exception:
        await c.delete(f"/git/refs/heads/{branch}"); raise

async def open_review(c, isbn, title, conflicts, proposal):
    body = (f"התנגשות בספר {isbn} ({title}). השדות הבאים כבר מלאים במאגר ושונים ממה שנשלח.\n\n"
            f"````json\n{json.dumps(conflicts, ensure_ascii=False, indent=2)}\n````\n\nההצעה המלאה:\n\n"
            f"````json\n{json.dumps(proposal, ensure_ascii=False, indent=2)}\n````\n")
    (await c.post(f"{GH}/repos/{REVIEW_REPO or REPO}/issues",
                  json={"title": f"[התנגשות] {isbn}", "body": body})).raise_for_status()

async def process(isbn, book, webp):
    async with httpx.AsyncClient(timeout=30, headers=HEADERS(), base_url=f"{GH}/repos/{REPO}") as c:
        r = await c.get(f"/contents/books/{isbn}.json", params={"ref": BASE})
        if r.status_code == 404:
            return {"result": "created", "pr": await create_pr(c, f"web-book-{isbn}", isbn, book, webp, None, "ספר חדש")}
        r.raise_for_status()
        old, sha = json.loads(base64.b64decode(r.json()["content"]).decode("utf-8")), r.json()["sha"]
        conflicts = []
        if webp and (await c.get(f"/contents/covers/{isbn}.webp", params={"ref": BASE})).status_code == 200:
            conflicts.append({"field": "cover", "current": "כבר קיימת כריכה", "proposed": "כריכה חדשה"}); webp = None
        if not webp: book.pop("cover_url", None)
        merged, added, c2 = merge_book(old, book)
        conflicts += c2
        pr, result = None, "nochange"
        if added or webp:
            note = f"\n\nשדות שנוספו: {', '.join(added) or 'כריכה'}."
            pr = await create_pr(c, f"web-edit-{isbn}-{int(time.time())}", isbn, merged, webp, sha, "השלמת פרטים", note)
            result = "updated"
        if conflicts:
            await open_review(c, isbn, old["title"], conflicts, book)
            result = "updated_review" if pr else "review"
        return {"result": result, "pr": pr}

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
        return {"ok": True, **await process(isbn, book, webp)}
    except HTTPException: raise
    except httpx.HTTPError:
        raise HTTPException(502, "לא הצלחנו לשמור את הספר כרגע. נסו שוב מאוחר יותר.")
