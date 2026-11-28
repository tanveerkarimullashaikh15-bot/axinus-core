# AXINUS 0 - model registry: roles -> ordered models, live discovery, health, daily meter, hedged calls
import re, time, json, threading, types, requests, pathlib, datetime, zoneinfo
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED

R0 = globals().get("R0") or {"dead": {}, "last": {}, "gids": [], "gt": 0, "rr": {}, "n": 0}
METER = globals().get("METER") or {"day": "", "m": {}}
SAMBA_DEAD = globals().get("SAMBA_DEAD") or [0]
GEM_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
SAMBA_URL = "https://api.sambanova.ai/v1/chat/completions"
CER_URL = "https://api.cerebras.ai/v1/chat/completions"
CFA = sec("CF_ACCOUNT_ID", "CLOUDFLARE_ACCOUNT_ID"); CFT = sec("CF_API_TOKEN", "CLOUDFLARE_API_TOKEN")
CF_URL = "https://api.cloudflare.com/client/v4/accounts/%s/ai/v1/chat/completions" % CFA
CF_TXT = ["@cf/openai/gpt-oss-120b"]
NVK = sec("NVIDIA_API_KEY", "NVIDIA_KEY"); NV_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
_NVC = {"t": 0, "ids": []}; _NVT = []
def _nv_ids():
    """NVIDIA Build free models (one key, ~40 RPM shared). Only strong text families; cached 1h."""
    if not NVK: return []
    if _NVC["ids"] and time.time() - _NVC["t"] < 3600: return _NVC["ids"]
    try:
        j = requests.get("https://integrate.api.nvidia.com/v1/models", headers={"Authorization": "Bearer " + NVK}, timeout=15).json()
        _NVC["ids"] = [m["id"] for m in j.get("data", []) if re.search(r"kimi|deepseek|glm|nemotron|qwen|gpt-oss", m["id"], re.I) and not re.search(r"embed|rerank|guard|safety|vision|-vl|parse|clip|reward|translate|coder", m["id"], re.I)]
        _NVC["t"] = time.time()
    except Exception: pass
    return _NVC["ids"]
def _nv_gate():
    now = time.time(); _NVT[:] = [t for t in _NVT if now - t < 60]
    if len(_NVT) >= 32: raise RuntimeError("HTTP 429: local nvidia limit 32/min, retry in 20 s")
    _NVT.append(now)
def cf_image(prompt, steps=6):
    """FLUX.1 schnell on Cloudflare Workers AI (free ~10K neurons/day). Returns image bytes or raises."""
    if not (CFA and CFT): raise RuntimeError("cloudflare key nahi")
    import base64 as _b64
    r = requests.post("https://api.cloudflare.com/client/v4/accounts/%s/ai/run/@cf/black-forest-labs/flux-1-schnell" % CFA, headers={"Authorization": "Bearer " + CFT}, json={"prompt": str(prompt)[:1800], "steps": steps}, timeout=90)
    j = r.json()
    b = (j.get("result") or {}).get("image")
    if not b: raise RuntimeError("cf image: " + str(j.get("errors") or j)[:120])
    data = _b64.b64decode(b)
    if len(data) < 5000: raise RuntimeError("cf image too small")
    return data
CEREBRAS_KEY = globals().get("CEREBRAS_KEY") or sec("CEREBRAS_API_KEY", "CEREBRAS")
LIMITS = {"groq": 200000, "cerebras": 1000000}
BADM = re.compile(r"whisper|guard|tts|orpheus|embed|safeguard|rerank|allam|prompt", re.I)
GROQ_DAILY = 200000
ROLES = {
    "think":    [("nvidia", r"kimi"), ("nvidia", r"deepseek"), ("nvidia", r"glm"), ("nvidia", r"nemotron"), ("cerebras", r"gpt-oss-120b"), ("gemini", r"^(?!.*lite).*flash"), ("groq", r"gpt-oss-120b"), ("cloudflare", r"gpt-oss-120b")],
    "docw":     [("nvidia", r"glm"), ("nvidia", r"kimi"), ("nvidia", r"deepseek"), ("cerebras", r"gpt-oss-120b"), ("gemini", r"^(?!.*lite).*flash"), ("groq", r"gpt-oss-120b"), ("cloudflare", r"gpt-oss-120b")],
    "docr":     [("nvidia", r"deepseek"), ("nvidia", r"kimi"), ("nvidia", r"glm"), ("cerebras", r"gpt-oss-120b"), ("cerebras", r"qwen.*235"), ("groq", r"gpt-oss-120b"), ("cloudflare", r"gpt-oss-120b")],
    "brain":    [("cerebras", r"gpt-oss-120b"), ("groq", r"gpt-oss-120b"), ("cerebras", r"qwen.*235"), ("gemini", r"lite"), ("gemini", r"^(?!.*lite).*flash"), ("groq", r"gpt-oss-20b"), ("cloudflare", r"gpt-oss-120b")],
    "coder":    [("groq", r"qwen"), ("cerebras", r"qwen.*235"), ("cerebras", r"gpt-oss-120b"), ("groq", r"gpt-oss-120b"), ("gemini", r"^(?!.*lite).*flash"), ("gemini", r"lite")],
    "reasoner": [("cerebras", r"gpt-oss-120b"), ("cerebras", r"qwen.*235"), ("groq", r"gpt-oss-120b"), ("gemini", r"^(?!.*lite).*flash"), ("groq", r"qwen"), ("cloudflare", r"gpt-oss-120b")],
    "phone":    [("groq", r"gpt-oss-20b"), ("cerebras", r"llama.*8b|llama3.1"), ("groq", r"qwen"), ("gemini", r"lite"), ("cerebras", r"gpt-oss-120b"), ("groq", r"gpt-oss-120b")],
    "designer": [("cerebras", r"gpt-oss-120b"), ("gemini", r"lite"), ("groq", r"gpt-oss-20b"), ("groq", r"qwen"), ("gemini", r"^(?!.*lite).*flash"), ("cloudflare", r"gpt-oss-120b")],
    "writer":   [("cerebras", r"gpt-oss-120b"), ("gemini", r"^(?!.*lite).*flash"), ("groq", r"gpt-oss-120b"), ("gemini", r"lite"), ("groq", r"qwen"), ("cloudflare", r"gpt-oss-120b")],
    "fast":     [("groq", r"gpt-oss-20b"), ("cerebras", r"llama.*8b|llama3.1"), ("gemini", r"lite"), ("groq", r"qwen")],
}
IST0 = zoneinfo.ZoneInfo("Asia/Kolkata")

def _groq_ids():
    if R0["gids"] and time.time() - R0["gt"] < 600: return R0["gids"]
    try:
        ids = [m.id for m in groq_client.models.list().data if isinstance(m.id, str) and not BADM.search(m.id)]
        if ids: R0["gids"] = ids; R0["gt"] = time.time(); return ids
    except Exception: pass
    return R0["gids"] or ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]
def _cer_ids():
    if not CEREBRAS_KEY: return []
    if R0.get("cids") and time.time() - R0.get("ct", 0) < 600: return R0["cids"]
    try:
        r = requests.get("https://api.cerebras.ai/v1/models", headers={"Authorization": "Bearer " + CEREBRAS_KEY}, timeout=10)
        ids = [m["id"] for m in r.json().get("data", []) if not BADM.search(m["id"])]
        if ids: R0["cids"] = ids; R0["ct"] = time.time(); return ids
    except Exception: pass
    return R0.get("cids") or ["gpt-oss-120b", "qwen-3-235b-a22b-instruct-2507", "llama3.1-8b"]
def _cf_ids(): return list(CF_TXT) if (CFA and CFT) else []
def _gem_ids(): return [m for m in GEMINI_MODELS if m not in DEAD]
def _samba_ids():
    return []  # SambaNova removed (no free credits)
    if SAMBA_DEAD[0] > time.time(): return []
    try: return [x for x in samba_models() if not BADM.search(x)]
    except Exception: return []
def label(c): return c[0] + ":" + c[1]
def cands(role):
    src = {"groq": _groq_ids(), "gemini": _gem_ids(), "samba": _samba_ids(), "cerebras": _cer_ids(), "cloudflare": _cf_ids(), "nvidia": _nv_ids()}; out = []
    for prov, pat in ROLES[role]:
        for i in src[prov]:
            if re.search(pat, i, re.I) and (prov, i) not in out: out.append((prov, i))
    return [c for c in out if R0["dead"].get(c, 0) < time.time()]

def _nox(msgs):
    out = []
    for m in msgs:
        if isinstance(m, dict) and m.get("tool_calls"): m = dict(m, tool_calls=[{k: v for k, v in c.items() if k != "extra_content"} for c in m["tool_calls"]])
        out.append(m)
    return out
def _msgwrap(m):
    if not isinstance(m, dict): return m
    tcs = [types.SimpleNamespace(id=c.get("id") or ("c%d" % i), function=types.SimpleNamespace(name=c["function"]["name"], arguments=c["function"].get("arguments") or "{}"), extra_content=c.get("extra_content")) for i, c in enumerate(m.get("tool_calls") or [])]
    return types.SimpleNamespace(content=m.get("content") or "", tool_calls=tcs or None)
def _http(url, key, model, msgs, tools, mt, timeout):
    p = {"model": model, "messages": msgs}
    if tools: p["tools"] = tools
    if mt: p["max_tokens"] = mt
    r = requests.post(url, headers={"Authorization": "Bearer " + str(key), "Content-Type": "application/json"}, json=p, timeout=timeout)
    if r.status_code != 200: raise RuntimeError("HTTP %s: %s" % (r.status_code, r.text[:160]))
    j = r.json(); u = j.get("usage") or {}
    return _msgwrap(j["choices"][0]["message"]), (u.get("prompt_tokens", 0) or 0, u.get("completion_tokens", 0) or 0)
def _call(c, msgs, tools, role, mt, timeout):
    prov, model = c
    if prov == "groq":
        kw = {}
        if "gpt-oss" in model: kw["reasoning_effort"] = "high" if role == "reasoner" else "low"
        if mt: kw["max_tokens"] = mt
        if tools: kw["tools"] = tools
        try: r = groq_client.chat.completions.create(model=model, messages=_nox(msgs), **kw)
        except Exception as e:
            if "reasoning_effort" in kw and not re.search(r"429|rate|quota", str(e), re.I):
                kw.pop("reasoning_effort"); r = groq_client.chat.completions.create(model=model, messages=_nox(msgs), **kw)
            else: raise
        u = getattr(r, "usage", None)
        return r.choices[0].message, (getattr(u, "prompt_tokens", 0) or 0, getattr(u, "completion_tokens", 0) or 0)
    if prov == "gemini": return _http(GEM_URL, API_KEY, model, msgs, tools, mt, timeout)
    if prov == "cerebras": return _http(CER_URL, CEREBRAS_KEY, model, msgs, tools, mt, timeout)
    if prov == "cloudflare": return _http(CF_URL, CFT, model, msgs, tools, mt, timeout)
    if prov == "nvidia": _nv_gate(); return _http(NV_URL, NVK, model, msgs, tools, mt, max(timeout, 90))
    return _http(SAMBA_URL, SAMBA_KEY, model, msgs, tools, mt, timeout)

def _classify(e):
    s = str(e)
    if re.search(r"\b404\b|does not exist|decommission|no access|not found", s, re.I): return 3600
    if re.search(r"request too large|reduce your message|context.?length|too many tokens", s, re.I): return 300
    if re.search(r"\b402\b|balance|payment|billing", s, re.I): return 21600
    if re.search(r"429|rate limit|quota|resource_exhausted|too many", s, re.I):
        m = re.search(r"try again in (?:(\d+)h)?\s*(?:(\d+)m)?\s*(?:([\d.]+)s)?", s)
        if m and (m.group(1) or m.group(2) or m.group(3)):
            return min(14400, int(m.group(1) or 0) * 3600 + int(m.group(2) or 0) * 60 + float(m.group(3) or 0) + 2)
        return 1800 if re.search(r"per day|tpd|rpd|daily", s, re.I) else 30
    if re.search(r"tool_use_failed|failed to call|invalid.*tool|\b50[0234]\b|time.?d? ?out|connection", s, re.I): return "retry"
    return 60

def _meter(c, tin=0, tout=0, err=False, msg="", ms=0):
    d = datetime.datetime.now(IST0).strftime("%Y-%m-%d")
    if METER["day"] != d: METER["day"] = d; METER["m"] = {}
    x = METER["m"].setdefault(label(c), {"calls": 0, "tin": 0, "tout": 0, "err": 0})
    if err: x["err"] += 1; x["last"] = re.sub(r"(key|token)=[\w-]+", "***", str(msg))[:110]
    else:
        x["calls"] += 1; x["tin"] += int(tin); x["tout"] += int(tout)
        if ms: x["ms"] = int(ms) if not x.get("ms") else int(x["ms"] * 0.7 + ms * 0.3)
    R0["n"] += 1
    if R0["n"] % 15 == 0:
        try: pathlib.Path(MEM_DIR + "/meter.json").write_text(json.dumps(METER))
        except Exception: pass
GEM_RPD = {"lite": 500}
def meter_data():
    roles = {}
    for r in ROLES:
        for c in cands(r): roles.setdefault(label(c), set()).add(r)
    for g in GEMINI_MODELS: roles.setdefault("gemini:" + g, set()).add("vision")
    for g in GEMINI_MODELS: roles["gemini:" + g].add("vision")
    for k in globals().get("VIS_EXTRA", []): roles.setdefault(k, set()).add("vision")
    now = time.time(); dead = {label(c): int(t - now) for c, t in R0["dead"].items() if t > now}
    rows = []
    for k in sorted(set(roles) | set(METER["m"]), key=lambda x: (x.split(":")[0], x)):
        v = METER["m"].get(k, {"calls": 0, "tin": 0, "tout": 0, "err": 0}); used = v["tin"] + v["tout"]; prov = k.split(":")[0]
        lim = LIMITS.get(prov); lt = ""
        if lim: lt = "~%dK tok/din" % (lim // 1000)
        elif prov == "gemini":
            rpd = next((n for key, n in GEM_RPD.items() if key in k), None)
            lt = "~%d req/din" % rpd if rpd else "limit alag (pata nahi)"
        if prov in globals().get("EXTRA_LIM", {}): lt = EXTRA_LIM[prov]
        pct = round(100 * used / lim) if lim else (round(100 * v["calls"] / rpd) if prov == "gemini" and rpd else None)
        rows.append({"model": k, "roles": sorted(roles.get(k, [])), "calls": v["calls"], "tokens": used, "err": v["err"], "ms": v.get("ms", 0), "last": v.get("last", ""), "pct": pct, "limit": lt, "dead_s": dead.get(k, 0)})
    return {"day": METER["day"] or datetime.datetime.now(IST0).strftime("%Y-%m-%d"), "rows": rows}

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
                last = e; h = _classify(e); _meter(c, err=True, msg=e); R0["dead"][c] = time.time() + (30 if h == "retry" else h); launch()
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
                t0 = time.time(); m, (a, b) = _call(c, msgs, tools, role, mt, timeout); _meter(c, a, b, ms=(time.time() - t0) * 1000); R0["last"][role] = label(c); return m, label(c)
            except Exception as e:
                last = e; h = _classify(e); _meter(c, err=True, msg=e)
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
