# AXINUS ADDON 2 - history, tasks + reminders, news + briefing, memory, search, export
import json, time, threading, re, os, uuid, pathlib, datetime, glob, html, email.utils
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

SESS_DIR = MEM_DIR + "/sessions"; TASKS_PATH = MEM_DIR + "/tasks.json"; FACTS_PATH = MEM_DIR + "/facts.json"; NEWS_PATH = MEM_DIR + "/news_cache.json"
pathlib.Path(SESS_DIR).mkdir(parents=True, exist_ok=True)
DL = globals().get("DL") or threading.Lock()
TL = globals().get("TL") or threading.Lock()

def jr(path, default):
    try: return json.loads(pathlib.Path(path).read_text())
    except Exception: return default
def jw(path, obj):
    s = json.dumps(obj, ensure_ascii=False, indent=1)
    try:
        pathlib.Path(path + ".tmp").write_text(s); os.replace(path + ".tmp", path)
    except Exception:
        pathlib.Path(path).write_text(s)

def fmt_dt(x):
    try:
        d = datetime.datetime.fromisoformat(x) if isinstance(x, str) else x
        return d.astimezone(IST).strftime("%d %b, %I:%M %p").lstrip("0")
    except Exception:
        return str(x)

# =============== 1. CONVERSATION HISTORY ===============
CUR = globals().get("CUR") or {"sid": None}
def _sp(sid): return SESS_DIR + "/" + slug(sid) + ".json"
def _newid(): return now_ist().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:4]
def _title(text):
    t = str(text)
    m = re.search(r"Uploaded file path:\s*(\S+)", t)
    if m: return "File: " + os.path.basename(m.group(1))[:40]
    return re.sub(r"\s+", " ", t).strip()[:46] or "New chat"

def _sess_add(role, text, workers=None, via="text"):
    with DL:
        if not CUR["sid"]: CUR["sid"] = _newid()
        d = jr(_sp(CUR["sid"]), None) or {"id": CUR["sid"], "title": "", "created": now_ist().isoformat(timespec="seconds"), "messages": []}
        d["messages"].append({"role": role, "content": str(text)[:6000], "ts": now_ist().isoformat(timespec="seconds"), "via": via})
        if not d.get("title") and role == "user": d["title"] = _title(text)
        d["updated"] = now_ist().isoformat(timespec="seconds")
        jw(_sp(CUR["sid"]), d)

def remember_turn(task, final, workers=None):
    HISTORY.append({"role": "user", "content": str(task)[:600]})
    HISTORY.append({"role": "assistant", "content": str(final)[:600]})
    del HISTORY[:-12]
    try: pathlib.Path(HIST_PATH).write_text(json.dumps(HISTORY, ensure_ascii=False))
    except Exception: pass
    try:
        _sess_add("user", task); _sess_add("assistant", final)
    except Exception as e:
        print("session save fail:", str(e)[:80])

def _restore(d):
    HISTORY[:] = [{"role": m["role"], "content": m["content"][:600]} for m in d.get("messages", [])[-12:] if m.get("role") in ("user", "assistant")]
    try: pathlib.Path(HIST_PATH).write_text(json.dumps(HISTORY, ensure_ascii=False))
    except Exception: pass

def sess_list(q=""):
    out = []; ql = str(q).strip().lower()
    for f in glob.glob(SESS_DIR + "/*.json"):
        d = jr(f, None)
        if not d or "id" not in d: continue
        msgs = d.get("messages", []); snip = ""
        if ql:
            hit = next((m for m in msgs if ql in m["content"].lower()), None)
            if ql not in d.get("title", "").lower() and not hit: continue
            if hit: i = hit["content"].lower().find(ql); snip = hit["content"][max(0, i - 25):i + 55].replace("\n", " ")
        out.append({"id": d["id"], "title": d.get("title") or "New chat", "updated": d.get("updated", ""), "n": len(msgs), "snip": snip})
    out.sort(key=lambda x: x["updated"], reverse=True)
    return J({"items": out[:200], "cur": CUR["sid"]})

def sess_open(sid=None):
    sid = sid or CUR["sid"]
    d = jr(_sp(sid), None) if sid else None
    if not d: return J({"id": None, "title": "", "messages": []})
    CUR["sid"] = d["id"]; _restore(d)
    return J({"id": d["id"], "title": d.get("title", ""), "messages": d.get("messages", [])})

def sess_new():
    CUR["sid"] = None; HISTORY.clear()
    try: pathlib.Path(HIST_PATH).write_text("[]")
    except Exception: pass
    return J({"ok": True})

def sess_rename(sid, title):
    d = jr(_sp(sid), None)
    if not d: return J({"ok": False})
    d["title"] = str(title).strip()[:80] or d.get("title", ""); jw(_sp(sid), d)
    return J({"ok": True})

def sess_delete(sid):
    try: os.remove(_sp(sid))
    except Exception: return J({"ok": False})
    if CUR["sid"] == slug(sid): CUR["sid"] = None; HISTORY.clear()
    return J({"ok": True})

def sess_log(role, text):
    if role not in ("user", "assistant") or len(str(text).strip()) < 2: return J({"ok": False})
    _sess_add(role, str(text).strip(), via="voice")
    HISTORY.append({"role": role, "content": str(text)[:600]}); del HISTORY[:-12]
    return J({"ok": True})

# =============== 2. TASKS + REMINDERS ===============
ALERTS = globals().get("ALERTS") or []
ALN = globals().get("ALN") or [0]
def _tasks(): return jr(TASKS_PATH, [])


def _nl_when(s):
    t = str(s).lower().strip(); now = now_ist()
    m = re.search(r"(\d+(?:\.\d+)?)\s*(min|mins|minute|minutes|minat|ghanta|ghante|ghanta|hour|hours|hr|hrs|din|day|days)\b", t)
    if m and re.search(r"\b(in|me|mein|baad|after|ke baad|later)\b", t):
        n = float(m.group(1)); u = m.group(2)
        return now + (datetime.timedelta(minutes=n) if u.startswith(("min", "minat")) else datetime.timedelta(hours=n) if u.startswith(("gh", "h")) else datetime.timedelta(days=n))
    day = now.date()
    if re.search(r"\b(parso|day after tomorrow)\b", t): day += datetime.timedelta(days=2)
    elif re.search(r"\b(kal|tomorrow|tmrw)\b", t): day += datetime.timedelta(days=1)
    hh = mm = None
    m = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm|baje|bje)?", t)
    if m and (m.group(2) or m.group(3)):
        hh = int(m.group(1)); mm = int(m.group(2) or 0); ap = m.group(3)
        if ap == "pm" and hh < 12: hh += 12
        elif ap == "am" and hh == 12: hh = 0
        elif ap in ("baje", "bje") or ap is None:
            if re.search(r"shaam|sham|evening|raat|night|dopahar|afternoon", t) and hh < 12: hh += 12
    else:
        m2 = re.search(r"\b(\d{1,2})\b", t)
        if m2 and re.search(r"subah|morning|shaam|sham|evening|raat|night|dopahar|afternoon", t):
            hh = int(m2.group(1)); mm = 0
            if re.search(r"shaam|sham|evening|raat|night|dopahar|afternoon", t) and hh < 12: hh += 12
        elif re.search(r"subah|morning", t): hh, mm = 8, 0
        elif re.search(r"shaam|sham|evening", t): hh, mm = 18, 0
        elif re.search(r"raat|night", t): hh, mm = 21, 0
        elif re.search(r"dopahar|afternoon", t): hh, mm = 14, 0
    if hh is None or hh > 23: return None
    d = datetime.datetime.combine(day, datetime.time(hh, mm), tzinfo=IST)
    if d <= now and not re.search(r"\b(kal|tomorrow|parso|tmrw)\b", t): d += datetime.timedelta(days=1)
    return d

def parse_when(s):
    s = str(s).strip().replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%d-%m-%Y %H:%M", "%d/%m/%Y %H:%M", "%Y-%m-%d %I:%M %p", "%Y-%m-%d %I %p"):
        try: return datetime.datetime.strptime(s, fmt).replace(tzinfo=IST)
        except ValueError: pass
    m = re.match(r"^(\d{1,2}):(\d{2})\s*(am|pm)?$", s, re.I)
    if m:
        h = int(m.group(1)) % 12 + (12 if (m.group(3) or "").lower() == "pm" else 0) if m.group(3) else int(m.group(1))
        d = now_ist().replace(hour=h, minute=int(m.group(2)), second=0, microsecond=0)
        return d if d > now_ist() else d + datetime.timedelta(days=1)
    d0 = _nl_when(s)
    if d0: return d0
    try:
        from dateutil import parser as dp
        d = dp.parse(s, dayfirst=True)
        return d.replace(tzinfo=IST) if d.tzinfo is None else d.astimezone(IST)
    except Exception:
        return None

def _mk(title, when):
    d = parse_when(when)
    if not d: return None, "Time samajh nahi aaya. Format: YYYY-MM-DD HH:MM (IST)."
    if d < now_ist() - datetime.timedelta(minutes=1): return None, "Ye time nikal chuka hai (" + fmt_dt(d) + ")."
    t = {"id": uuid.uuid4().hex[:6], "title": str(title).strip()[:200] or "Task", "due": d.isoformat(timespec="minutes"), "status": "pending", "n15": (d - now_ist()) < datetime.timedelta(minutes=15), "ns": False, "created": now_ist().isoformat(timespec="minutes")}
    with TL:
        ts = _tasks(); ts.append(t); jw(TASKS_PATH, ts)
    return t, ""

def add_task(title: str, when: str):
    t, err = _mk(title, when)
    if err: return "Error: " + err
    return "Saved: Task '" + t["title"] + "' at " + fmt_dt(t["due"]) + " (id " + t["id"] + "). 15 min pehle aur time par alert aayega."

def _find(ts, key, status=("pending",)):
    k = str(key).strip().lower()
    c = [t for t in ts if t["status"] in status and (t["id"] == k or k in t["title"].lower())]
    return sorted(c, key=lambda t: t["due"])[0] if c else None

def list_tasks(scope: str = "upcoming"):
    ts = _tasks(); today = now_ist().date().isoformat(); sc = str(scope).lower()
    if sc == "history": sel = [t for t in ts if t["status"] in ("done", "missed")]
    elif sc == "all": sel = ts
    elif sc == "today": sel = [t for t in ts if t["status"] == "pending" and t["due"][:10] <= today]
    else: sel = [t for t in ts if t["status"] == "pending"]
    sel = sorted(sel, key=lambda t: t["due"])[:25]
    if not sel: return "Koi task nahi (" + sc + ")."
    return "\n".join("- [" + t["status"] + "] " + t["title"] + " · " + fmt_dt(t["due"]) + " (id " + t["id"] + ")" for t in sel)

def complete_task(task: str):
    with TL:
        ts = _tasks(); t = _find(ts, task)
        if not t: return "Error: pending task nahi mila: " + task
        t["status"] = "done"; t["done_at"] = now_ist().isoformat(timespec="minutes"); jw(TASKS_PATH, ts)
    return "Saved: Task done - " + t["title"]

def delete_task(task: str):
    with TL:
        ts = _tasks(); t = _find(ts, task, ("pending", "done", "missed"))
        if not t: return "Error: task nahi mila: " + task
        ts.remove(t); jw(TASKS_PATH, ts)
    return "Saved: Task deleted - " + t["title"]

def task_list(): return J({"tasks": _tasks(), "now": now_ist().isoformat(timespec="minutes")})
def task_add_ui(title, when):
    t, err = _mk(title, when); return J({"ok": bool(t), "error": err, "task": t})
def task_done(tid):
    r = complete_task(tid); return J({"ok": r.startswith("Saved")})
def task_del(tid):
    r = delete_task(tid); return J({"ok": r.startswith("Saved")})

def _alert(kind, t, text):
    with TL:
        ALN[0] += 1; ALERTS.append({"id": ALN[0], "kind": kind, "task": t["id"], "title": t["title"], "text": text, "t": now_ist().isoformat(timespec="seconds")}); del ALERTS[:-100]
    emit("mail", "mark", "REMINDER: " + text)

def alerts_since(since=0):
    since = int(since)
    with TL: return ([a for a in ALERTS if a["id"] > since] if since >= 0 else []), ALN[0]

def _tick():
    now = now_ist(); pend = []
    with TL:
        ts = _tasks(); ch = False
        for t in ts:
            if t["status"] != "pending": continue
            due = datetime.datetime.fromisoformat(t["due"])
            if not t["n15"] and due - datetime.timedelta(minutes=15) <= now < due:
                t["n15"] = True; ch = True; pend.append(("soon", t, "15 minute baad: " + t["title"]))
            if not t["ns"] and now >= due:
                t["ns"] = True; ch = True
                if now - due > datetime.timedelta(minutes=30): t["status"] = "missed"; pend.append(("missed", t, "Task miss ho gaya: " + t["title"]))
                else: pend.append(("start", t, "Ab time ho gaya: " + t["title"]))
        if ch: jw(TASKS_PATH, ts)
    for k, t, x in pend: _alert(k, t, x)

def _sched_loop():
    while True:
        try: _tick()
        except Exception as e: print("sched err:", str(e)[:80])
        time.sleep(15)

if not globals().get("_SCHED_ON"):
    threading.Thread(target=_sched_loop, daemon=True).start(); _SCHED_ON = True

print("✅ ax2a OK | chats + tasks")
