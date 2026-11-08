# AXINUS 0 - model registry: roles -> ordered models, live discovery, health, daily meter, hedged calls
import re, time, json, threading, types, requests, pathlib, datetime, zoneinfo
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED

R0 = globals().get("R0") or {"dead": {}, "last": {}, "gids": [], "gt": 0, "rr": {}, "n": 0}
METER = globals().get("METER") or {"day": "", "m": {}}
SAMBA_DEAD = globals().get("SAMBA_DEAD") or [0]
GEM_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
SAMBA_URL = "https://api.sambanova.ai/v1/chat/completions"
BADM = re.compile(r"whisper|guard|tts|orpheus|embed|safeguard|rerank|allam|prompt", re.I)
GROQ_DAILY = 200000
ROLES = {
    "brain":    [("groq", r"gpt-oss-120b"), ("groq", r"qwen"), ("gemini", r"lite"), ("gemini", r"^(?!.*lite).*flash"), ("groq", r"gpt-oss-20b"), ("samba", r"gpt-oss")],
    "coder":    [("groq", r"qwen"), ("groq", r"gpt-oss-120b"), ("gemini", r"^(?!.*lite).*flash"), ("gemini", r"lite"), ("samba", r"glm|minimax")],
    "reasoner": [("groq", r"gpt-oss-120b"), ("gemini", r"^(?!.*lite).*flash"), ("groq", r"qwen"), ("samba", r"glm|gpt-oss|minimax")],
    "phone":    [("groq", r"gpt-oss-20b"), ("groq", r"qwen"), ("gemini", r"lite"), ("groq", r"gpt-oss-120b")],
    "designer": [("gemini", r"lite"), ("groq", r"gpt-oss-20b"), ("groq", r"qwen"), ("gemini", r"^(?!.*lite).*flash")],
    "writer":   [("gemini", r"^(?!.*lite).*flash"), ("groq", r"gpt-oss-120b"), ("gemini", r"lite"), ("groq", r"qwen")],
    "fast":     [("groq", r"gpt-oss-20b"), ("gemini", r"lite"), ("groq", r"qwen")],
}
IST0 = zoneinfo.ZoneInfo("Asia/Kolkata")

def _groq_ids():
    if R0["gids"] and time.time() - R0["gt"] < 600: return R0["gids"]
    try:
        ids = [m.id for m in groq_client.models.list().data if isinstance(m.id, str) and not BADM.search(m.id)]
        if ids: R0["gids"] = ids; R0["gt"] = time.time(); return ids
    except Exception: pass
    return R0["gids"] or ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]
def _gem_ids(): return [m for m in GEMINI_MODELS if m not in DEAD]
def _samba_ids():
    if SAMBA_DEAD[0] > time.time(): return []
    try: return [x for x in samba_models() if not BADM.search(x)]
    except Exception: return []
def label(c): return c[0] + ":" + c[1]
def cands(role):
    src = {"groq": _groq_ids(), "gemini": _gem_ids(), "samba": _samba_ids()}; out = []
    for prov, pat in ROLES[role]:
        for i in src[prov]:
            if re.search(pat, i, re.I) and (prov, i) not in out: out.append((prov, i))
    return [c for c in out if R0["dead"].get(c, 0) < time.time()]

def _wrap(m):
    if not isinstance(m, dict): return m
    tcs = [types.SimpleNamespace(id=c.get("id") or ("c%d" % i), function=types.SimpleNamespace(name=c["function"]["name"], arguments=c["function"].get("arguments") or "{}")) for i, c in enumerate(m.get("tool_calls") or [])]
    return types.SimpleNamespace(content=m.get("content") or "", tool_calls=tcs or None)
def _http(url, key, model, msgs, tools, mt, timeout):
    p = {"model": model, "messages": msgs}
    if tools: p["tools"] = tools
    if mt: p["max_tokens"] = mt
    r = requests.post(url, headers={"Authorization": "Bearer " + str(key), "Content-Type": "application/json"}, json=p, timeout=timeout)
    if r.status_code != 200: raise RuntimeError("HTTP %s: %s" % (r.status_code, r.text[:160]))
    j = r.json(); u = j.get("usage") or {}
    return _wrap(j["choices"][0]["message"]), (u.get("prompt_tokens", 0) or 0, u.get("completion_tokens", 0) or 0)
def _call(c, msgs, tools, role, mt, timeout):
    prov, model = c
    if prov == "groq":
        kw = {}
        if "gpt-oss" in model: kw["reasoning_effort"] = "high" if role == "reasoner" else "low"
        if mt: kw["max_tokens"] = mt
        if tools: kw["tools"] = tools
        try: r = groq_client.chat.completions.create(model=model, messages=msgs, **kw)
        except Exception as e:
            if "reasoning_effort" in kw and not re.search(r"429|rate|quota", str(e), re.I):
                kw.pop("reasoning_effort"); r = groq_client.chat.completions.create(model=model, messages=msgs, **kw)
            else: raise
        u = getattr(r, "usage", None)
        return r.choices[0].message, (getattr(u, "prompt_tokens", 0) or 0, getattr(u, "completion_tokens", 0) or 0)
    if prov == "gemini": return _http(GEM_URL, API_KEY, model, msgs, tools, mt, timeout)
    return _http(SAMBA_URL, SAMBA_KEY, model, msgs, tools, mt, timeout)

def _classify(e):
    s = str(e)
    if re.search(r"\b404\b|does not exist|decommission|no access|not found", s, re.I): return 3600
    if re.search(r"\b402\b|balance|payment|billing", s, re.I): return 21600
    if re.search(r"429|rate limit|quota|resource_exhausted|too many", s, re.I):
        m = re.search(r"try again in (?:(\d+)h)?\s*(?:(\d+)m)?\s*(?:([\d.]+)s)?", s)
        if m and (m.group(1) or m.group(2) or m.group(3)):
            return min(14400, int(m.group(1) or 0) * 3600 + int(m.group(2) or 0) * 60 + float(m.group(3) or 0) + 2)
        return 1800 if re.search(r"per day|tpd|rpd|daily", s, re.I) else 30
    if re.search(r"tool_use_failed|failed to call|invalid.*tool|\b50[0234]\b|time.?d? ?out|connection", s, re.I): return "retry"
    return 60

def _meter(c, tin=0, tout=0, err=False):
    d = datetime.datetime.now(IST0).strftime("%Y-%m-%d")
    if METER["day"] != d: METER["day"] = d; METER["m"] = {}
    x = METER["m"].setdefault(label(c), {"calls": 0, "tin": 0, "tout": 0, "err": 0})
    if err: x["err"] += 1
    else: x["calls"] += 1; x["tin"] += int(tin); x["tout"] += int(tout)
    R0["n"] += 1
    if R0["n"] % 15 == 0:
        try: pathlib.Path(MEM_DIR + "/meter.json").write_text(json.dumps(METER))
        except Exception: pass
def meter_data():
    rows = []
    for k, v in sorted(METER["m"].items()):
        used = v["tin"] + v["tout"]
        rows.append({"model": k, "calls": v["calls"], "tokens": used, "err": v["err"], "pct": round(100 * used / GROQ_DAILY) if k.startswith("groq:") else None})
    dead = [{"model": label(c), "left_s": int(t - time.time())} for c, t in R0["dead"].items() if t > time.time()]
    return {"day": METER["day"], "rows": rows, "dead": dead}

def _hedged(role, cs, msgs, tools, mt, timeout):
    k = R0["rr"].get(role, 0) % len(cs); R0["rr"][role] = k + 1; order = cs[k:] + cs[:k]
    ex = ThreadPoolExecutor(max_workers=len(order)); futs = {}; nxt = [0]; last = None
    def launch():
        if nxt[0] < len(order):
            c = order[nxt[0]]; nxt[0] += 1; futs[ex.submit(_call, c, msgs, tools, role, mt, timeout)] = c
            return True
        return False
    launch(); dl = time.time() + timeout
    while futs and time.time() < dl:
        done, _ = wait(list(futs), timeout=2.2, return_when=FIRST_COMPLETED)
        if not done: launch(); continue
        for f in done:
            c = futs.pop(f)
            try:
                m, (a, b) = f.result(); ex.shutdown(wait=False); _meter(c, a, b); R0["last"][role] = label(c); return m, label(c)
            except Exception as e:
                last = e; h = _classify(e); _meter(c, err=True); R0["dead"][c] = time.time() + (30 if h == "retry" else h); launch()
    ex.shutdown(wait=False); raise RuntimeError(str(last)[:160] if last else "timeout")

def chat(role, msgs, tools=None, mt=None, timeout=60, hedge=False):
    cs = cands(role); last = None
    if not cs: raise RuntimeError("Saare models busy/quota khatam (%s): koi alive nahi" % role)
    if hedge and len(cs) > 1:
        try: return _hedged(role, cs, msgs, tools, mt, timeout)
        except Exception as e: last = e; cs = cands(role)
    for c in cs:
        for attempt in (0, 1):
            try:
                m, (a, b) = _call(c, msgs, tools, role, mt, timeout); _meter(c, a, b); R0["last"][role] = label(c); return m, label(c)
            except Exception as e:
                last = e; h = _classify(e); _meter(c, err=True)
                if h == "retry" and attempt == 0: time.sleep(1.5); continue
                R0["dead"][c] = time.time() + (30 if h == "retry" else h); break
    raise RuntimeError("Saare models busy/quota khatam (%s). Last: %s" % (role, str(last)[:140]))
def llm(role, system, user, mt=None, hedge=False, timeout=60):
    m, used = chat(role, [{"role": "system", "content": system}, {"role": "user", "content": user}], mt=mt, hedge=hedge, timeout=timeout)
    return (m.content or ""), used

# ---- plug into the original cells ----
_orig_samba_pick = globals().get("_orig_samba_pick") or samba_pick
_orig_samba_chat = globals().get("_orig_samba_chat") or samba_chat
def samba_pick(prefs):
    if prefs is CODER_PREFS: return "auto-coder"
    if prefs is REASON_PREFS: return "auto-reasoner"
    return _orig_samba_pick(prefs)
def samba_chat(model, system_p, user_p, timeout=40):
    if str(model).startswith("auto-"): return llm(model[5:], system_p, user_p, timeout=max(timeout, 60))[0]
    if SAMBA_DEAD[0] > time.time(): raise RuntimeError("SambaNova HTTP 402 (balance 0, skipped)")
    try: return _orig_samba_chat(model, system_p, user_p, timeout)
    except Exception as e:
        if re.search(r"402|balance", str(e)): SAMBA_DEAD[0] = time.time() + 21600
        raise
def groq_chat(system_p, user_p): return llm("writer", system_p, user_p)[0]
try: METER.update(json.loads(pathlib.Path(MEM_DIR + "/meter.json").read_text())) if json.loads(pathlib.Path(MEM_DIR + "/meter.json").read_text()).get("day") == datetime.datetime.now(IST0).strftime("%Y-%m-%d") else None
except Exception: pass
print("✅ ax0 registry OK | roles:", ", ".join("%s=%d" % (r, len(cands(r))) for r in ROLES))
