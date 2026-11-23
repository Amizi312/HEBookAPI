#!/usr/bin/env python3
"""הופך גוף Issue (עם בלוק json) לקובץ ספר. הגוף מגיע ממשתנה סביבה, כי הוא קלט לא מהימן."""
import json, os, re, sys, uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build

body = os.environ.get("ISSUE_BODY", "")
m = re.search(r"```json\s*(\{.*?\})\s*```", body, re.S)
def die(msg):
    print(f"::error::{msg}"); Path("issue_error.txt").write_text(msg, encoding="utf-8"); sys.exit(1)
if not m: die("לא נמצא בלוק JSON בבקשה.")
try: data = json.loads(m.group(1))
except Exception as e: die(f"ה-JSON לא תקין: {e}")
if not isinstance(data, dict): die("ה-JSON צריך להיות אובייקט.")
allowed = set(build.REQUIRED) | set(build.OPTIONAL)
data = {k: v for k, v in data.items() if k in allowed and k != "cover_url"}
data.pop("isbn", None)
identifier = str(uuid.uuid4())
data["id"] = identifier
target = build.ROOT / "books" / f"{identifier}.json"
if target.exists(): die("הספר כבר קיים במאגר.")
target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
_, errs = build.validate(target)
if errs:
    target.unlink(); die("; ".join(errs))
print(f"id={identifier}")
Path(os.environ.get("GITHUB_OUTPUT", os.devnull)).open("a").write(f"id={identifier}\ntitle={data['title'].replace(chr(10),' ')}\n")
