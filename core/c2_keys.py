import os, re, json, time, glob, pathlib, datetime, zoneinfo, inspect, threading, uuid, base64, smtplib, urllib.parse
import requests
import docx
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google import genai
from google.genai import types
from google.colab import userdata, drive, output
from IPython.display import HTML, JSON, display
from ddgs import DDGS
from fpdf import FPDF
from groq import Groq
import cohere

drive.mount('/content/drive')

DRIVE_ROOT = "/content/drive/MyDrive"
ROOT_DIR = DRIVE_ROOT + "/AXINUS_SYSTEM"
MEM_DIR = ROOT_DIR + "/memory"
NOTES_DIR = ROOT_DIR + "/notes"
MEDIA_DIR = ROOT_DIR + "/media"
BACKUP_DIR = ROOT_DIR + "/code_backups"

for d in [ROOT_DIR, MEM_DIR, NOTES_DIR, MEDIA_DIR, BACKUP_DIR]:
    pathlib.Path(d).mkdir(parents=True, exist_ok=True)

PROFILE_PATH = MEM_DIR + "/profile.json"
CONTACTS_PATH = MEM_DIR + "/contacts.json"
HIST_PATH = MEM_DIR + "/chat_history.json"

if not os.path.exists(PROFILE_PATH):
    pathlib.Path(PROFILE_PATH).write_text(json.dumps({"name": "Tanveer Shaikh", "role": "First-Year Engineering Student", "field": "Electronics, CS, and AI", "identity": "Creator and Lead Architect of AXINUS", "people": {}}))

if not os.path.exists(CONTACTS_PATH):
    pathlib.Path(CONTACTS_PATH).write_text(json.dumps({"self": "+91XXXXXXXXXX", "papa": "+91XXXXXXXXXX", "sir": "teacher@example.com"}))

GEMINI_MODELS = ["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.6-flash", "gemini-2.5-flash"]
LIVE_M = "gemini-3.8-live"
GROQ_M = "openai/gpt-oss-120b"
COHERE_M = "command-r-plus-08-2024"
CODER_PREFS = ["Qwen2.5-Coder", "coder", "deepseek", "minimax", "qwen", "llama-3.3"]
REASON_PREFS = ["405B", "deepseek", "minimax", "qwen3", "llama-3.3", "gemma"]
NOTICE = "[⚠️ Notice: Executed via Groq Backup]"


def sec(*names):
    for n in names:
        try:
            v = userdata.get(n)
            if v:
                return v
        except Exception:
            pass
    return None


API_KEY = sec("GEMINI_API_KEY")
LIVE_KEY = sec("GEMINI_LIVE_API_KEY")
GROQ_KEY = sec("GROQ_API_KEY")
COHERE_KEY = sec("COHERE_API_KEY")
SAMBA_KEY = sec("SAMBANOVA_API_KEY", "SAMBANO", "SAMBANC")
TAVILY_KEY = sec("TAVILY_API_KEY", "TAVILY")
YT_KEY = sec("YOUTUBE_API_KEY", "YOUTUBE")
GMAIL_USER = sec("GMAIL_USER", "GMAIL")
GMAIL_PASS = sec("GMAIL_APP_PASS", "GMAIL_AI")

assert API_KEY, "GEMINI_API_KEY missing!"
assert LIVE_KEY, "GEMINI_LIVE_API_KEY missing!"
assert GROQ_KEY, "GROQ_API_KEY missing!"

client = genai.Client(api_key=API_KEY)
live_client = genai.Client(api_key=LIVE_KEY)
groq_client = Groq(api_key=GROQ_KEY)
cohere_client = cohere.ClientV2(api_key=COHERE_KEY) if COHERE_KEY else None

JOBS = {}
APPR = {}
TRACE = []
DEAD = set()
SAMBA_MODELS = []
LOCK = threading.Lock()


def yes(msg):
    APPR.clear()
    ev = threading.Event()
    APPR.update({"ev": ev, "ans": False, "msg": msg})
    ev.wait(90)
    r = APPR.get("ans", False)
    APPR.clear()
    return r


def get_datetime():
    return datetime.datetime.now(zoneinfo.ZoneInfo("Asia/Kolkata")).strftime("%A, %d %B %Y, %I:%M %p IST")


def log(q, a):
    open(MEM_DIR + "/activity_log.txt", "a").write(get_datetime() + " | Tum: " + str(q) + " | Axinus: " + str(a)[:200].replace("\n", " ") + "\n")


def slug(x):
    s = "".join(ch if (ch.isalnum() or ch in "-_") else "_" for ch in str(x).strip().lower())
    return s[:60] or "misc"


def safe_path(p):
    rp = os.path.realpath(str(p).strip())
    if rp.startswith("/content/drive/"):
        return rp
    return None


def resolve_contact(x):
    t = str(x).strip()
    if t.startswith("+") or "@" in t:
        return t
    try:
        cts = json.loads(pathlib.Path(CONTACTS_PATH).read_text())
    except Exception:
        cts = {}
    return cts.get(t.lower(), t)


def parse_args(s):
    try:
        return json.loads(s or "{}")
    except Exception:
        return {}


def gen(contents, config=None):
    err = None
    for m in GEMINI_MODELS:
        if m in DEAD:
            continue
        try:
            r = client.models.generate_content(model=m, contents=contents, config=config)
            return r.text or ""
        except Exception as e:
            err = e
            s = str(e)
            if "404" in s or "NOT_FOUND" in s or "no longer" in s:
                DEAD.add(m)
    raise (err if err else RuntimeError("No Gemini model available"))


def up(path):
    p = safe_path(path)
    if not p or not os.path.exists(p):
        raise RuntimeError("File nahi mili ya Drive ke bahar hai: " + str(path))
    f = client.files.upload(file=p)
    for _ in range(45):
        state = getattr(f.state, "name", str(f.state))
        if state != "PROCESSING":
            break
        time.sleep(2)
        f = client.files.get(name=f.name)
    return f


def groq_chat(system_p, user_p):
    last = None
    for i in range(2):
        try:
            r = groq_client.chat.completions.create(model=GROQ_M, messages=[{"role": "system", "content": system_p}, {"role": "user", "content": user_p}])
            return r.choices[0].message.content or ""
        except Exception as e:
            last = e
            if "429" in str(e) and i == 0:
                time.sleep(2)
            else:
                break
    raise last


def cohere_chat(system_p, user_p):
    if not cohere_client:
        raise RuntimeError("Cohere key missing")
    r = cohere_client.chat(model=COHERE_M, messages=[{"role": "system", "content": system_p}, {"role": "user", "content": user_p}])
    return r.message.content[0].text


def samba_models():
    if SAMBA_MODELS or not SAMBA_KEY:
        return SAMBA_MODELS
    try:
        r = requests.get("https://api.sambanova.ai/v1/models", headers={"Authorization": "Bearer " + SAMBA_KEY}, timeout=15)
        for x in r.json().get("data", []):
            SAMBA_MODELS.append(x["id"])
    except Exception:
        pass
    return SAMBA_MODELS


def samba_pick(prefs):
    ids = samba_models()
    for p in prefs:
        for i in ids:
            if p.lower() in i.lower():
                return i
    return ids[0] if ids else None


def samba_chat(model, system_p, user_p, timeout=40):
    h = {"Authorization": "Bearer " + SAMBA_KEY, "Content-Type": "application/json"}
    p = {"model": model, "messages": [{"role": "system", "content": system_p}, {"role": "user", "content": user_p}]}
    r = requests.post("https://api.sambanova.ai/v1/chat/completions", headers=h, json=p, timeout=timeout)
    if r.status_code != 200:
        raise RuntimeError("SambaNova HTTP " + str(r.status_code) + ": " + r.text[:150])
    return r.json()["choices"][0]["message"]["content"]


def run_with_backup(primary_fn, system_p, user_p):
    try:
        return primary_fn()
    except Exception:
        try:
            return NOTICE + "\n" + groq_chat(system_p, user_p)
        except Exception as e2:
            return "Error: primary aur Groq backup dono fail hue: " + str(e2)[:150]


print("✅ Cell 2 OK | Gemini:", GEMINI_MODELS[0], "| SambaNova models:", len(samba_models()))