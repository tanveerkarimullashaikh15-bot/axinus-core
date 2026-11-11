# AXINUS ADDON 4g - lessons: Axinus learns methods/procedures the user teaches and applies them later
import json, re, time, uuid
LES_PATH = MEM_DIR + "/lessons.json"
WN["learn"] = "LEARNER"
def _les(): return jr(LES_PATH, [])
_STOP = set("the a an is of to in and or for how kaise kya hai ka ki ke se me ko karo kar do batao bata sir ye woh iska uska".split())
def _toks(s): return {w for w in re.findall(r"[a-z0-9ऀ-ॿ]{2,}", str(s).lower()) if w not in _STOP}

def teach_lesson(title: str, content: str, kind: str = "method"):
    """Save a method/procedure taught by the user. title = short name (e.g. 'Thevenin theorem'), content = the steps exactly as taught, kind = method|phone|fact."""
    t = str(title).strip()[:80]; c = str(content).strip()[:4000]
    if not t or len(c) < 8: return "Error: title aur content dono chahiye (steps poore likhiye)."
    ls = _les(); k = _toks(t)
    for l in ls:
        if l["title"].lower() == t.lower() or (k and _toks(l["title"]) == k):
            l["content"] = c; l["kind"] = kind; l["ts"] = now_ist().isoformat(timespec="minutes"); l["ver"] = l.get("ver", 1) + 1
            jw(LES_PATH, ls); return "Lesson update kar diya: %s (v%d)." % (t, l["ver"])
    ls.append({"id": uuid.uuid4().hex[:5], "title": t, "content": c, "kind": kind if kind in ("method", "phone", "fact") else "method", "ts": now_ist().isoformat(timespec="minutes"), "ver": 1, "used": 0})
    jw(LES_PATH, ls[-200:]); return "Yaad kar liya, Sir: %s. Ab isi tareeke se solve karunga." % t

def list_lessons():
    ls = _les()
    if not ls: return "Abhi tak koi lesson nahi sikhaya, Sir."
    return "\n".join("%d. %s [%s]" % (i + 1, l["title"], l.get("kind", "method")) for i, l in enumerate(ls))

def forget_lesson(title: str):
    ls = _les(); k = str(title).lower().strip()
    n = [l for l in ls if k not in l["title"].lower() and l["id"] != k]
    if len(n) == len(ls): return "Aisa koi lesson nahi mila: " + str(title)
    jw(LES_PATH, n); return "Bhula diya: %d lesson." % (len(ls) - len(n))

def _match(q, n=3):
    qt = _toks(q); sc = []
    if not qt: return []
    for l in _les():
        tt = _toks(l["title"]); ct = _toks(l["content"])
        s = 3 * len(qt & tt) + 0.3 * len(qt & ct)
        if str(l["title"]).lower() in str(q).lower(): s += 5
        if s >= 3: sc.append((s, l))
    sc.sort(key=lambda x: -x[0]); return [l for _, l in sc[:n]]

def recall_lessons(query: str = ""):
    m = _match(query) if query else _les()[-5:]
    if not m: return "Is topic ka koi lesson nahi mila."
    return "\n\n".join("## %s\n%s" % (l["title"], l["content"]) for l in m)

def lessons_for(task):
    """Text injected into brain system prompt: titles + best matching lesson bodies."""
    try:
        ls = _les()
        if not ls: return ""
        m = _match(task); out = "\nTAUGHT LESSONS (user ne sikhaya. Matching ho to SIRF isi tareeke se solve/kaam karo, apna tareeka nahi): " + ", ".join(l["title"] for l in ls[-30:])
        for l in m:
            out += "\n### %s [%s]\n%s" % (l["title"], l.get("kind", "method"), l["content"][:1500]); l["used"] = l.get("used", 0) + 1
        if m: jw(LES_PATH, ls)
        return out
    except Exception:
        return ""

reg_tool(teach_lesson, "Save a method/procedure the user teaches (maths theorem steps, how to operate an app, etc). Call when user says seekho/yaad rakho/sikhata hoon + the steps. title, content (faithful steps), kind=method|phone|fact", "learn")
reg_tool(list_lessons, "List all lessons the user has taught", "learn")
reg_tool(forget_lesson, "Forget a taught lesson by title (title)", "learn")
reg_tool(recall_lessons, "Show the taught lesson(s) matching a topic (query)", "learn")

DELEG += """
- LESSONS: when the user teaches a method/steps ("seekho", "yaad rakho", "ye tareeka hai", "main sikhata hoon") call teach_lesson with their steps FAITHFULLY (do not improve them). Questions later that match a lesson listed under TAUGHT LESSONS must be solved in exactly that method; mention which lesson you used. Phone-procedure lessons guide phone_control goals.
"""
_GRP.append((r"seekh|sikh|yaad rakh|lesson|padh|taught|tareeka|method|theorem|sikha|bhul|forget", ["teach_lesson", "list_lessons", "forget_lesson", "recall_lessons", "sambanova_heavy_reasoning", "run_code"]))

SYS_HOOKS[:] = [h for h in SYS_HOOKS if h.__name__ != "lessons_for"] + [lessons_for]
print("✅ ax6 lessons OK | teach/recall + auto-inject")
