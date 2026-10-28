"""Web server for the E Worldwide Consulting site (Python standard library only).

    python3 -I server.py                 # http://127.0.0.1:8080
    HOST=0.0.0.0 PORT=8000 python3 -I server.py

Serves public/ and handles POST /api/contact:
  * validates every field server-side (the browser checks are a convenience only)
  * spam protection: honeypot field, minimum fill time, per-IP rate limit, body size limit
  * stores each enquiry in data/submissions.jsonl (created with owner-only permissions)
  * optionally emails it when CONTACT_SMTP_* environment variables are set (never in frontend code)

For production, run behind a TLS-terminating reverse proxy (see README.md).
"""
import json
import os
import re
import smtplib
import ssl
import threading
import time
from email.message import EmailMessage
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / "public"
DATA = ROOT / "data"
SUBMISSIONS = DATA / "submissions.jsonl"

MAX_BODY = 20_000
MIN_FILL_SECONDS = 3
RATE_LIMIT = 5            # submissions
RATE_WINDOW = 600         # seconds

REGIONS = {"United States", "South Africa", "Other"}
SERVICES = {"AI agents and intelligent automation", "Application development", "Cloud and DevOps",
            "Digital transformation and technology consulting", "Data migration and integration", "Not sure yet"}
BUDGETS = {"", "Under $25,000", "$25,000 to $100,000", "$100,000 to $250,000", "Over $250,000", "To be determined"}
TIMELINES = {"", "As soon as possible", "Within 3 months", "3 to 6 months", "6 months or more", "Exploring options"}
EMAIL_RE = re.compile(r"^[^\s@<>\"(),;:]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$")

SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; script-src 'self'; style-src 'self' https://fonts.googleapis.com; "
        "font-src https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'; "
        "frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'"
    ),
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), interest-cohort=()",
    "Cross-Origin-Opener-Policy": "same-origin",
}

_rate = {}
_lock = threading.Lock()


def rate_limited(ip):
    now = time.time()
    with _lock:
        hits = [t for t in _rate.get(ip, []) if now - t < RATE_WINDOW]
        limited = len(hits) >= RATE_LIMIT
        if not limited:
            hits.append(now)
        _rate[ip] = hits
        return limited


def clean(value, limit):
    value = value if isinstance(value, str) else ""
    value = value.replace("\x00", "").strip()
    return value[:limit]


def validate(form):
    data = {
        "name": clean(form.get("name"), 120),
        "email": clean(form.get("email"), 200),
        "company": clean(form.get("company"), 160),
        "region": clean(form.get("region"), 40),
        "service": clean(form.get("service"), 80),
        "message": clean(form.get("message"), 4000),
        "budget": clean(form.get("budget"), 40),
        "timeline": clean(form.get("timeline"), 40),
        "consent": clean(form.get("consent"), 10),
    }
    errors = {}
    if len(data["name"]) < 2 or re.search(r"[\r\n]", data["name"]):
        errors["name"] = "Enter your full name."
    if not EMAIL_RE.match(data["email"]):
        errors["email"] = "Enter a valid business email address."
    if len(data["company"]) < 2:
        errors["company"] = "Enter your company name."
    if data["region"] not in REGIONS:
        errors["region"] = "Select your country or region."
    if data["service"] not in SERVICES:
        errors["service"] = "Select the service you are interested in."
    if len(data["message"]) < 20:
        errors["message"] = "Describe your project in at least 20 characters."
    if data["budget"] not in BUDGETS:
        data["budget"] = ""
    if data["timeline"] not in TIMELINES:
        data["timeline"] = ""
    if data["consent"] != "yes":
        errors["consent"] = "Please agree to the privacy notice so we can respond."
    return data, errors


def store(record):
    DATA.mkdir(mode=0o700, exist_ok=True)
    fd = os.open(SUBMISSIONS, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    with os.fdopen(fd, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def send_email(record):
    """Forward an enquiry by email if SMTP is configured. Failures are logged, never shown to visitors."""
    host = os.environ.get("CONTACT_SMTP_HOST")
    to = os.environ.get("CONTACT_TO")
    if not host or not to:
        return
    msg = EmailMessage()
    msg["Subject"] = f"Website enquiry: {record['service']} ({record['company']})"
    msg["From"] = os.environ.get("CONTACT_FROM", to)
    msg["To"] = to
    msg["Reply-To"] = record["email"]
    msg.set_content("\n".join(f"{k}: {v}" for k, v in record.items()))
    try:
        port = int(os.environ.get("CONTACT_SMTP_PORT", "587"))
        with smtplib.SMTP(host, port, timeout=15) as s:
            s.starttls(context=ssl.create_default_context())
            user = os.environ.get("CONTACT_SMTP_USER")
            if user:
                s.login(user, os.environ.get("CONTACT_SMTP_PASSWORD", ""))
            s.send_message(msg)
    except Exception as exc:  # noqa: BLE001 - keep the visitor's submission even if email fails
        print(f"[contact] email forwarding failed: {exc!r}")


class Handler(SimpleHTTPRequestHandler):
    server_version = "EWWC"
    sys_version = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PUBLIC), **kwargs)

    def end_headers(self):
        for k, v in SECURITY_HEADERS.items():
            self.send_header(k, v)
        path = urlsplit(self.path).path
        if path.startswith("/assets/"):
            self.send_header("Cache-Control", "public, max-age=86400")
        else:
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    # Static files: no directory listings, branded 404 page
    def list_directory(self, path):
        self.send_error(HTTPStatus.NOT_FOUND)

    def send_error(self, code, message=None, explain=None):
        page = PUBLIC / "404.html"
        if code == HTTPStatus.NOT_FOUND and page.exists() and self.command != "HEAD":
            body = page.read_bytes()
            self.send_response(code)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().send_error(code, message, explain)

    def do_POST(self):
        if urlsplit(self.path).path != "/api/contact":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        wants_json = "application/json" in self.headers.get("Accept", "") or \
                     self.headers.get("Content-Type", "").startswith("application/json")

        def reply(status, payload):
            if wants_json:
                body = json.dumps(payload).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:  # plain HTML form post without JavaScript
                self.send_response(HTTPStatus.SEE_OTHER)
                self.send_header("Location", "/contact.html?status=" + ("sent" if status == 200 else "error") + "#form")
                self.send_header("Content-Length", "0")
                self.end_headers()

        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = -1
        if length < 0 or length > MAX_BODY:
            reply(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"message": "Your message is too long."})
            return
        raw = self.rfile.read(length).decode("utf-8", errors="replace")
        try:
            if self.headers.get("Content-Type", "").startswith("application/json"):
                form = json.loads(raw or "{}")
                if not isinstance(form, dict):
                    raise ValueError
            else:
                form = {k: v[0] for k, v in parse_qs(raw).items()}
        except ValueError:
            reply(HTTPStatus.BAD_REQUEST, {"message": "We could not read the form. Please try again."})
            return

        ip = self.headers.get("X-Forwarded-For", self.client_address[0]).split(",")[0].strip() \
            if os.environ.get("TRUST_PROXY") == "1" else self.client_address[0]
        if rate_limited(ip):
            reply(HTTPStatus.TOO_MANY_REQUESTS, {"message": "Too many submissions. Please try again in a few minutes."})
            return

        # Bots fill the hidden field or submit instantly: acknowledge, but discard.
        try:
            elapsed = time.time() - int(str(form.get("started", "0")))/1000
        except ValueError:
            elapsed = 0
        if clean(form.get("website"), 200) or (form.get("started") and elapsed < MIN_FILL_SECONDS):
            reply(HTTPStatus.OK, {"ok": True})
            return

        data, errors = validate(form)
        if errors:
            reply(HTTPStatus.UNPROCESSABLE_ENTITY, {"message": "Some fields need your attention.", "errors": errors})
            return

        record = {"received_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **data}
        store(record)
        threading.Thread(target=send_email, args=(record,), daemon=True).start()
        reply(HTTPStatus.OK, {"ok": True})

    def log_message(self, fmt, *args):
        # Log method/path/status only, not query strings or form contents.
        print(f"[{self.log_date_time_string()}] {self.command} {urlsplit(self.path).path} {args[1] if len(args) > 1 else ''}")


def main():
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8080"))
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"E Worldwide Consulting site on http://{host}:{port}  (serving {PUBLIC.relative_to(ROOT)}/)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
