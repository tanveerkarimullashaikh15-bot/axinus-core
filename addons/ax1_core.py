# AXINUS ADDON 1 - core: event bus, orchestrator, error recovery, stats, diagnostics
import time, threading, json, re, os, uuid, hmac, hashlib, datetime, zoneinfo, pathlib, shutil, urllib.parse

IST = zoneinfo.ZoneInfo("Asia/Kolkata")
def now_ist(): return datetime.datetime.now(IST)
def J(x): return JSON(x)

WN = {"brain": "AXINUS CORE", "reason": "REASONER", "eyes": "VISION", "coder": "CODER", "research": "RESEARCH", "utils": "UTILS", "mail": "MAIL & NOTES"}
TG = {"get_datetime": "utils", "youtube_search": "research", "generate_image": "eyes", "run_code": "coder", "search_drive": "research", "read_csv": "utils", "tavily_live_search": "research", "qwen_vibe_coder": "coder", "sambanova_heavy_reasoning": "reason", "analyze_video": "eyes", "analyze_image": "eyes", "analyze_pdf": "eyes", "send_corporate_email": "mail", "save_smart_note": "mail", "make_quiz": "mail", "send_whatsapp": "mail", "manage_contact": "mail", "read_note": "mail", "list_notes": "mail", "make_pdf": "utils", "read_doc": "utils", "read_webpage": "research"}
ADDON_API = globals().get("ADDON_API") or {}
LASTUP = globals().get("LASTUP") or {"path": "", "t": 0}
WARN = globals().get("WARN") or []

def reg_tool(fn, desc, worker):
    REG[fn.__name__] = fn; DESC[fn.__name__] = desc; TG[fn.__name__] = worker
    BRAIN_TOOLS[:] = [x for x in BRAIN_TOOLS if x.__name__ != fn.__name__] + [fn]

# ---------- signed file links ----------
def sign(rel): return hmac.new(str(globals().get("PIN", "x")).encode(), rel.encode(), hashlib.sha256).hexdigest()[:20]
def file_link(path):
    try:
        rp = os.path.realpath(path); root = os.path.realpath(ROOT_DIR)
        base = globals().get("URL")
        if not base or not rp.startswith(root + os.sep): return str(path)
        rel = rp[len(root) + 1:]
        return base + "/f?p=" + urllib.parse.quote(rel) + "&s=" + sign(rel)
    except Exception:
        return str(path)

# ---------- event bus ----------
EV = globals().get("EV") or []
EVL = globals().get("EVL") or threading.Lock()
EVN = globals().get("EVN") or [0]
RUN = globals().get("RUN") or {}
RUNC = globals().get("RUNC") or {}
LASTW = globals().get("LASTW") or {}
STATS = globals().get("STATS") or {}
USAGE = globals().get("USAGE") or {"groq_calls": 0, "groq_in": 0, "groq_out": 0, "samba_calls": 0, "tool_calls": 0, "retries": 0}
JOB = globals().get("JOB") or {"workers": [], "models": {}}

def emit(w, state, msg, model="", ms=0, tool="", k=""):
    with EVL:
        EVN[0] += 1
        e = {"id": EVN[0], "k": k or ("m%d" % EVN[0]), "t": now_ist().strftime("%H:%M:%S"), "w": w, "n": WN.get(w, w), "s": state, "m": str(msg)[:160], "model": model, "ms": int(ms), "tool": tool}
        EV.append(e)
        del EV[:-300]
    try:
        open(MEM_DIR + "/agent_events.log", "a").write(json.dumps(e, ensure_ascii=False) + "\n")
    except Exception:
        pass
    return e

class Stage:
    def __init__(self, w, msg, model="", tool=""):
        self.w = w; self.msg = msg; self.model = model; self.tool = tool; self.fail = False; self.note = ""; self.k = uuid.uuid4().hex[:6]
    def __enter__(self):
        self.t0 = time.time()
        RUNC[self.w] = RUNC.get(self.w, 0) + 1; RUN[self.w] = {"msg": self.msg, "model": self.model}; LASTW[self.w] = time.time()
        if self.w not in JOB["workers"]: JOB["workers"].append(self.w)
        emit(self.w, "run", self.msg, self.model, 0, self.tool, self.k)
        return self
    def __exit__(self, et, ev, tb):
        ms = (time.time() - self.t0) * 1000
        bad = bool(et) or self.fail
        RUNC[self.w] = max(0, RUNC.get(self.w, 1) - 1)
        if RUNC[self.w] == 0: RUN.pop(self.w, None)
        LASTW[self.w] = time.time()
        s = STATS.setdefault(self.w, {"ok": 0, "fail": 0, "ms": 0}); s["fail" if bad else "ok"] += 1; s["ms"] += ms
        if self.model: JOB["models"][self.w] = self.model
        emit(self.w, "fail" if bad else "done", self.note or (str(ev)[:100] if et else self.msg), self.model, ms, self.tool, self.k)
        return False

def active_list(): return [x for x in set(RUNC) | set(LASTW) if RUNC.get(x, 0) > 0 or time.time() - LASTW.get(x, 0) < 2.5]
def workers(): return J({"active": active_list()})

# ---------- result classification ----------
def is_fail(r):
    return bool(re.match(r"^(Tool Error|Error|Brain Error|[A-Za-z ]{0,20}Error:|YouTube API|.*credentials missing|.*key missing|File nahi mili|CSV file nahi|Email address not found|No note found)", str(r)[:200], re.I))

def model_of(n, r):
    s = str(r)
    if NOTICE in s: return "groq backup"
    m = re.search(r"\[Model: ([^\]]+)\]", s)
    if m: return m.group(1)
    g = TG.get(n)
    if g == "eyes" or n == "run_code": return next((x for x in GEMINI_MODELS if x not in DEAD), "gemini")
    if n in ("send_corporate_email", "save_smart_note", "make_quiz"): return COHERE_M
    if n == "tavily_live_search": return "tavily"
    return ""

RETRY_OK = {"youtube_search", "tavily_live_search", "read_webpage", "analyze_image", "analyze_pdf", "analyze_video", "get_news", "run_code"}
def _brief(a):
    try:
        v = next(iter(a.values())) if isinstance(a, dict) and a else ""
        return str(v).replace("\n", " ")[:48]
    except Exception:
        return ""

_AX_BASE_CALL = globals().get("_AX_BASE_CALL") or CALL
def CALL(n, a):
    w = TG.get(n, "utils"); USAGE["tool_calls"] += 1
    with Stage(w, n + (" · " + _brief(a) if a else ""), "", n) as st:
        r = _AX_BASE_CALL(n, a)
        if is_fail(r) and n in RETRY_OK and re.search(r"timeout|timed out|429|503|Connection|Max retries", str(r), re.I):
            USAGE["retries"] += 1; emit(w, "retry", "retry " + n, "", 0, n); time.sleep(2); r = _AX_BASE_CALL(n, a)
        st.fail = is_fail(r); st.model = model_of(n, r)
        if st.fail: st.note = str(r)[:100]
    return r

_AX_BASE_SAVE = globals().get("_AX_BASE_SAVE") or save_chunk
def save_chunk(uid, name, idx, total, data):
    r = _AX_BASE_SAVE(uid, name, idx, total, data)
    try:
        d = r.data
        if d.get("ok") and d.get("done"): LASTUP.update({"path": d["path"], "t": time.time()})
    except Exception:
        pass
    return r

# ---------- orchestrator ----------
_AX_SYS0 = globals().get("_AX_SYS0") or BRAIN_SYS
DELEG = """
ORCHESTRATION RULES (you are the central orchestrator. Use the workers, do not do their jobs):
- Code, scripts, debugging -> call qwen_vibe_coder. Never write code yourself.
- Maths, circuits, derivations, heavy logic -> call sambanova_heavy_reasoning.
- Images, PDFs, videos -> analyze_image / analyze_pdf / analyze_video.
- Image + PDF report + save to Drive -> call image_report once (it coordinates Vision, Research, Reasoner, Coder, Utils and saving).
- A DETAILED / long / multi-page PDF, full chapter, complete notes, study material, syllabus coverage, or any request that says N pages -> make_long_pdf (pass request = the user's COMPLETE original message and pages = e.g. 10-15). A short one-page PDF -> make_rich_pdf. Only a diagram, flowchart or chart -> make_diagram.
- Live info -> tavily_live_search. News -> get_news. Daily briefing -> daily_briefing.
- Tasks and reminders -> add_task (when = YYYY-MM-DD HH:MM in IST), list_tasks, complete_task, delete_task.
- Facts the user wants remembered -> remember_fact. Recall -> recall_facts.
- Multi-step jobs: call tools one after another and pass earlier results into later calls. If a step needs another worker (research before a PDF, reasoner before a diagram), call it too.
- EXCEPTION to brevity: when a tool returns code, a list, a table or a link, show it in full after one short sentence (code inside ``` blocks). Brevity applies to your own commentary only.
"""
SYS_HOOKS = []
IMG_EXT = (".jpg", ".jpeg", ".png", ".webp")

def _recent_img():
    p = LASTUP.get("path", "")
    return p if p and time.time() - LASTUP.get("t", 0) < 7200 and p.lower().endswith(IMG_EXT) and os.path.exists(p) else ""

def route_task(t):
    low = t.lower()
    if re.search(r"mail|whatsapp|email", low): return ("brain",)
    m = re.search(r"uploaded file path:\s*(\S+?\.(?:jpg|jpeg|png|webp))", t, re.I)
    if m and re.search(r"\bpdf\b|report|document", low): return ("report", m.group(1), t[m.end():].lstrip(". "))
    ri = _recent_img()
    if ri and re.search(r"\bpdf\b|report", low) and re.search(r"\b(image|photo|picture|pic|isko|ise|this|file)\b", low): return ("report", ri, t)
    if re.search(r"daily briefing|\bbriefing\b|morning brief", low): return ("briefing",)
    return ("brain",)

def brain_step(msgs, tl, first):
    with Stage("brain", "Planning" if first else "Reviewing results", "auto") as st:
        m, used = chat("brain", msgs, tl, timeout=60)
        st.model = used
    USAGE["groq_calls"] += 1
    return m

_CORE_T = {"get_datetime", "phone_do", "recall_facts", "remember_fact", "tavily_live_search"}
_GRP = [
 (r"task|reminder|alarm|yaad|remind|todo|briefing|schedule", ["add_task", "list_tasks", "complete_task", "delete_task", "daily_briefing"]),
 (r"note|likh|save|memo", ["save_smart_note", "read_note", "list_notes"]),
 (r"mail|email|contact|whatsapp|message|msg|number|send", ["send_corporate_email", "manage_contact", "send_whatsapp"]),
 (r"pdf|report|document|\bdoc\b|docx|chapter|notes|syllabus|study material", ["make_pdf", "make_long_pdf", "make_rich_pdf", "image_report", "read_doc", "analyze_pdf"]),
 (r"merge|split|watermark|table|pdf text|pdf to image", ["pdf_merge", "pdf_split", "pdf_watermark", "pdf_tables", "pdf_text", "pdf_to_images"]),
 (r"image|photo|pic|picture|video|screenshot|dekho|poster|generate|banao|uploaded file", ["analyze_image", "analyze_video", "generate_image", "analyze_pdf", "image_report", "read_doc", "read_csv"]),
 (r"code|python|script|program|function|bug|debug|calculate|run |algorithm", ["run_code", "qwen_vibe_coder", "sambanova_heavy_reasoning"]),
 (r"reason|solve|math|plan|strategy|analy|compare|explain|why|kyu", ["sambanova_heavy_reasoning", "run_code"]),
 (r"search|news|khabar|weather|mausam|price|rate|latest|web|http|www|gold|score", ["tavily_live_search", "get_news", "read_webpage", "state_info"]),
 (r"youtube|song|gaana|gana", ["youtube_search"]),
 (r"csv|excel|sheet|drive|file", ["read_csv", "search_drive", "read_doc"]),
 (r"quiz|mcq|test me", ["make_quiz"]),
 (r"diagram|flowchart|chart|graph|architecture", ["make_diagram", "make_rich_pdf", "make_long_pdf"]),
 (r"state|map|india|population|rajya|maharashtra", ["state_info", "get_news"]),
 (r"open|kholo|call|phone|app|scroll|type|click|instagram|chrome|swipe|split", ["phone_control", "phone_stop", "phone_do", "send_whatsapp"]),
]
def pick_tools(task, tl):
    t = str(task).lower(); names = set(_CORE_T); hit = False
    for pat, ns_ in _GRP:
        if re.search(pat, t): names.update(ns_); hit = True
    if not hit: names.update(["phone_control", "add_task", "list_tasks", "save_smart_note", "get_news"])
    sub = [x for x in tl if x["function"]["name"] in names]
    return sub if len(sub) >= 3 else tl

def brain_loop(task):
    mem = globals().get("facts_text", lambda: "")()
    up = _recent_img() or (LASTUP.get("path", "") if time.time() - LASTUP.get("t", 0) < 7200 else "")
    sys_p = _AX_SYS0 + DELEG + ("\nMEMORY FACTS:\n" + mem if mem else "") + ("\nLAST UPLOADED FILE (use when user says this file/image): " + up if up else "") + "\nCURRENT TIME (IST): " + get_datetime() + "".join(f(task) for f in SYS_HOOKS)
    msgs = [{"role": "system", "content": sys_p}] + HISTORY[-10:] + [{"role": "user", "content": task}]
    tl = pick_tools(task, _tl(BRAIN_TOOLS))
    JOB["ntools"] = len(tl)
    final = ""
    for step in range(8):
        m = brain_step(msgs, tl, step == 0)
        if not m.tool_calls:
            final = finish(m.content or ""); break
        calls = [{"id": c.id, "type": "function", "function": {"name": c.function.name, "arguments": c.function.arguments}} for c in m.tool_calls]
        msgs.append({"role": "assistant", "content": m.content or "", "tool_calls": calls})
        for c in m.tool_calls:
            res = CALL(c.function.name, parse_args(c.function.arguments))
            msgs.append({"role": "tool", "tool_call_id": c.id, "content": str(res)[:6000]})
    else:
        final = finish("Task execution limit reached.")
    return final or "Sir, jawab khaali aaya, dobara bolein. Take care, Sir."

def footer():
    try:
        parts = []
        for w in JOB["workers"]:
            if w == "brain": continue
            mo = JOB["models"].get(w, "")
            parts.append(WN[w] + (" · " + mo if mo else ""))
        return ("\n— Workers: " + ", ".join(parts)) if parts else ""
    except Exception:
        return ""

CUR_TASK = globals().get("CUR_TASK") or [""]
def ask(task):
    CUR_TASK[0] = str(task); JOB["workers"] = []; JOB["models"] = {}; TRACE.clear()
    emit("brain", "mark", "TASK RECEIVED: " + str(task)[:70])
    ok = True; final = ""; base_used = False
    try:
        with Stage("brain", "Coordinating", GROQ_M):
            rt = route_task(str(task))
            if rt[0] == "report": final = run_report_job(rt[1], rt[2])
            elif rt[0] == "briefing": final = briefing_text()
            else: final = brain_loop(str(task))
    except Exception as e:
        ok = False; base_used = True
        emit("brain", "mark", "Brain failed: " + str(e)[:80])
        final = "Brain Error: " + str(e)[:200]
    final = str(final) + footer()
    emit("brain", "mark", "TASK COMPLETED" if ok else "TASK FAILED, fallback used")
    if not base_used:
        try: remember_turn(task, final)
        except Exception: pass
    return final

# ---------- pulse / stats / diagnostics ----------
def pulse(ev_since=0, al_since=0):
    ev_since = int(ev_since)
    with EVL:
        evs = [] if ev_since < 0 else [e for e in EV if e["id"] > ev_since][-60:]
        last = EVN[0]
    als, alm = [], 0
    fn = globals().get("alerts_since")
    if fn:
        try: als, alm = fn(al_since)
        except Exception: pass
    return J({"active": active_list(), "running": {k: dict(v) for k, v in RUN.items()}, "events": evs, "last": last, "alerts": als, "al_last": alm})

def _prices():
    try: return json.loads(pathlib.Path(MEM_DIR + "/prices.json").read_text())
    except Exception: return {"in": 0.0, "out": 0.0}

def set_prices(pin_, pout_):
    try:
        pathlib.Path(MEM_DIR + "/prices.json").write_text(json.dumps({"in": float(pin_), "out": float(pout_)}))
        return J({"ok": True})
    except Exception as e:
        return J({"ok": False, "error": str(e)[:100]})

def stats():
    perf = {WN.get(w, w): {"ok": v["ok"], "fail": v["fail"], "avg_ms": int(v["ms"] / max(1, v["ok"] + v["fail"]))} for w, v in STATS.items()}
    pr = _prices()
    cost = USAGE["groq_in"] * pr["in"] / 1e6 + USAGE["groq_out"] * pr["out"] / 1e6
    return J({"perf": perf, "usage": USAGE, "prices": pr, "cost": round(cost, 4)})

def _chk(name, fn):
    t0 = time.time()
    try:
        d = fn(); return {"name": name, "ok": True, "detail": str(d)[:120], "ms": int((time.time() - t0) * 1000)}
    except Exception as e:
        return {"name": name, "ok": False, "detail": str(e)[:120], "ms": int((time.time() - t0) * 1000)}

def diagnose(deep=False):
    out = []
    keys = {"Gemini": API_KEY, "Gemini Live": LIVE_KEY, "Groq": GROQ_KEY, "Cohere": COHERE_KEY, "SambaNova": SAMBA_KEY, "Tavily": TAVILY_KEY, "YouTube": YT_KEY, "Gmail": GMAIL_USER and GMAIL_PASS}
    for k, v in keys.items(): out.append({"name": "Key: " + k, "ok": bool(v), "detail": "present" if v else "missing in Colab Secrets", "ms": 0})
    out.append({"name": "SambaNova models", "ok": len(samba_models()) > 0, "detail": str(len(samba_models())) + " | coder=" + str(samba_pick(CODER_PREFS)) + " | reason=" + str(samba_pick(REASON_PREFS)), "ms": 0})
    for r in ROLES: out.append({"name": "Role: " + r, "ok": len(cands(r)) > 0, "detail": ", ".join(label(c) for c in cands(r)[:3]) or "koi alive nahi", "ms": 0})
    out.append({"name": "Gemini models alive", "ok": len([m for m in GEMINI_MODELS if m not in DEAD]) > 0, "detail": "dead: " + str(sorted(DEAD)), "ms": 0})
    for lib in ("reportlab", "PIL", "matplotlib", "pypdf"):
        out.append(_chk("Lib: " + lib, lambda lib=lib: __import__(lib).__name__))
    out.append({"name": "Graphviz (dot)", "ok": bool(shutil.which("dot")), "detail": str(shutil.which("dot")), "ms": 0})
    def _w():
        p = MEM_DIR + "/.diag"; pathlib.Path(p).write_text("ok"); os.remove(p); return "Drive writable"
    out.append(_chk("Drive write", _w))
    if deep:
        m = samba_pick(CODER_PREFS)
        out.append(_chk("SambaNova coder call", lambda: samba_chat(m, "Reply with OK", "OK", 25)[:40]))
        m2 = samba_pick(REASON_PREFS)
        out.append(_chk("SambaNova reasoner call", lambda: samba_chat(m2, "Reply with OK", "OK", 25)[:40]))
        out.append(_chk("Gemini call", lambda: gen("Reply with OK")[:40]))
        out.append(_chk("Groq call", lambda: groq_chat("Reply with OK", "OK")[:40]))
        if COHERE_KEY: out.append(_chk("Cohere call", lambda: cohere_chat("Reply with OK", "OK")[:40]))
    bad = [WN.get(w, w) for w, v in STATS.items() if v["fail"] > v["ok"]]
    if bad: out.append({"name": "Workers failing more than succeeding", "ok": False, "detail": ", ".join(bad), "ms": 0})
    return J({"checks": out})

ADDON_API.update({"pulse": pulse, "stats": stats, "diagnose": diagnose, "set_prices": set_prices, "workers": workers})
print("✅ ax1 core OK | events + orchestrator")
