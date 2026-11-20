# AXINUS 8a - workspace backend: Code Studio files, Projects, Artifacts, shared activity memory (chat + voice), phone status
import os, re, json, time, subprocess, sys, uuid, threading, shutil
WS_DIR = (ROOT_DIR + "/workspace") if "ROOT_DIR" in globals() else "/tmp/axinus_ws"
try: os.makedirs(WS_DIR, exist_ok=True)
except Exception: WS_DIR = "/tmp/axinus_ws"; os.makedirs(WS_DIR, exist_ok=True)
ART_DIR = WS_DIR + "/_artifacts"; os.makedirs(ART_DIR, exist_ok=True)
MAXF = 400000
def _pn(name):
    n = re.sub(r"[^A-Za-z0-9_\- ]", "", str(name or "")).strip().replace(" ", "_")[:40]
    return n or "scratch"
def _pd(name): d = WS_DIR + "/" + _pn(name); os.makedirs(d, exist_ok=True); return d
def _fp(proj, rel):
    rel = str(rel or "").replace("\\", "/").strip().lstrip("/")
    if not rel or ".." in rel.split("/") or len(rel) > 120 or not re.match(r"^[\w\-. /]+$", rel): return None
    d = os.path.realpath(_pd(proj)); p = os.path.realpath(d + "/" + rel)
    return p if p.startswith(d + os.sep) else None
def _meta(proj):
    try: return json.load(open(_pd(proj) + "/project.json"))
    except Exception: return {"name": _pn(proj), "instructions": "", "created": time.time()}

# ---------------- projects ----------------
def ws_projects():
    out = []
    for n in sorted(os.listdir(WS_DIR)):
        d = WS_DIR + "/" + n
        if n.startswith("_") or not os.path.isdir(d): continue
        m = _meta(n); fs = [f for f in os.listdir(d) if f != "project.json"]
        out.append({"name": n, "instructions": m.get("instructions", "")[:300], "files": len(fs), "t": os.path.getmtime(d)})
    out.sort(key=lambda x: -x["t"]); return JSON({"projects": out})
def ws_project_new(name, instructions=""):
    n = _pn(name); d = _pd(n); m = _meta(n); m["instructions"] = str(instructions or "")[:3000]; m["name"] = n
    json.dump(m, open(d + "/project.json", "w")); return JSON({"ok": True, "name": n})
def ws_project_del(name):
    n = _pn(name)
    if n == "scratch": return JSON({"error": "scratch project delete nahi hota"})
    shutil.rmtree(WS_DIR + "/" + n, ignore_errors=True); return JSON({"ok": True})
def ws_files(proj="scratch"):
    d = _pd(proj); out = []
    for r, _, fs in os.walk(d):
        for f in fs:
            if f == "project.json": continue
            p = os.path.join(r, f); out.append({"path": os.path.relpath(p, d).replace(os.sep, "/"), "size": os.path.getsize(p), "t": os.path.getmtime(p)})
    out.sort(key=lambda x: x["path"]); return JSON({"files": out[:300], "instructions": _meta(proj).get("instructions", "")})
def ws_read(proj, path):
    p = _fp(proj, path)
    if not p or not os.path.isfile(p): return JSON({"error": "file nahi mili"})
    return JSON({"content": open(p, encoding="utf-8", errors="replace").read(MAXF)})
def ws_write(proj, path, content=""):
    p = _fp(proj, path)
    if not p: return JSON({"error": "galat file naam (sirf letters, numbers, - _ . /)"})
    s = str(content or "")
    if len(s) > MAXF: return JSON({"error": "file bahut badi hai"})
    os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "w", encoding="utf-8").write(s); return JSON({"ok": True})
def ws_delete(proj, path):
    p = _fp(proj, path)
    if p and os.path.isfile(p): os.remove(p)
    return JSON({"ok": True})
def ws_run(proj, path, stdin=""):
    p = _fp(proj, path)
    if not p or not os.path.isfile(p): return JSON({"error": "file nahi mili"})
    ext = p.rsplit(".", 1)[-1].lower()
    if ext in ("html", "htm"): return JSON({"kind": "html", "html": open(p, encoding="utf-8", errors="replace").read(MAXF)})
    cmd = {"py": [sys.executable, "-I", p], "js": ["node", p], "sh": ["bash", p]}.get(ext)
    if not cmd: return JSON({"error": "Run sirf .py, .js, .sh aur .html ke liye hai"})
    if ext == "py": cmd = [sys.executable, p]
    try:
        r = subprocess.run(cmd, cwd=os.path.dirname(p), input=str(stdin or ""), capture_output=True, text=True, timeout=25)
        out = (r.stdout or "") + (("\n" + r.stderr) if r.stderr else "")
        return JSON({"kind": "text", "out": out[-9000:] or "(koi output nahi)", "code": r.returncode})
    except subprocess.TimeoutExpired: return JSON({"kind": "text", "out": "Timeout: 25 second me khatam nahi hua.", "code": -1})
    except Exception as e: return JSON({"error": str(e)[:200]})
def _strip_fence(t):
    t = str(t).strip(); m = re.search(r"```[\w+-]*\n(.*?)```", t, re.S)
    return (m.group(1) if m else re.sub(r"^```[\w+-]*\n?|```$", "", t)).strip("\n")
def code_gen(proj, path, prompt):
    """vibe coding: write or modify one file from a plain-language request"""
    p = _fp(proj, path)
    if not p: return JSON({"error": "galat file naam"})
    cur = open(p, encoding="utf-8", errors="replace").read(60000) if os.path.isfile(p) else ""
    others = [f["path"] for f in json.loads(ws_files(proj))["files"] if f["path"] != path][:30]
    sysm = ("You are a senior software engineer. Return ONLY the complete final content of the single file requested, no explanations, no markdown fences. Write clean, working, well-commented code. "
            "For .html files make ONE self-contained page (inline CSS and JS, no external libraries unless a CDN is essential), responsive and good-looking. For Python, use only the standard library unless asked otherwise.")
    u = "Project instructions: " + (_meta(proj).get("instructions") or "none") + "\nFile: " + path + "\nOther files in project: " + ", ".join(others) + "\n" + ("CURRENT CONTENT:\n" + cur + "\n" if cur else "(new empty file)\n") + "REQUEST: " + str(prompt)[:3000]
    with Stage("coder", "Writing " + path, "") as st:
        t, mdl = llm("coder", sysm, u, mt=6000, hedge=False, timeout=120); st.model = mdl
    code = _strip_fence(t)
    if len(code) < 3: return JSON({"error": "Model ne code nahi diya, dobara try karo"})
    os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "w", encoding="utf-8").write(code); return JSON({"ok": True, "content": code, "model": mdl})

# ---------------- artifacts ----------------
def art_list():
    out = []
    for f in os.listdir(ART_DIR):
        if f.endswith(".json"):
            try: a = json.load(open(ART_DIR + "/" + f)); out.append({"id": a["id"], "title": a["title"], "kind": a["kind"], "t": a["t"], "size": len(a.get("content", ""))})
            except Exception: pass
    out.sort(key=lambda x: -x["t"]); return JSON({"items": out[:200]})
def art_get(aid):
    p = ART_DIR + "/" + re.sub(r"\W", "", str(aid)) + ".json"
    return open(p).read() if os.path.exists(p) else JSON({"error": "artifact nahi mila"})
def art_save(title, kind, content):
    aid = uuid.uuid4().hex[:8]; k = kind if kind in ("html", "code", "markdown", "svg") else "code"
    json.dump({"id": aid, "title": str(title or "Untitled")[:80], "kind": k, "content": str(content or "")[:MAXF], "t": time.time()}, open(ART_DIR + "/" + aid + ".json", "w")); return JSON({"ok": True, "id": aid})
def art_del(aid):
    p = ART_DIR + "/" + re.sub(r"\W", "", str(aid)) + ".json"
    if os.path.exists(p): os.remove(p)
    return JSON({"ok": True})
def art_gen(prompt, kind="html"):
    sysm = {"html": "Create ONE complete self-contained HTML page (inline CSS and JS) that fulfils the request. Modern, responsive, polished. Return ONLY the HTML, no fences.",
            "svg": "Create ONE SVG image that fulfils the request. Return ONLY the <svg> markup.", "markdown": "Write a well structured markdown document. Return ONLY the markdown.", "code": "Write the requested code. Return ONLY the code, no fences."}.get(kind, "Return only the requested content.")
    with Stage("coder", "Creating artifact", "") as st:
        t, mdl = llm("coder", sysm, str(prompt)[:3000], mt=6000, hedge=False, timeout=120); st.model = mdl
    c = _strip_fence(t); title = re.sub(r"\s+", " ", str(prompt))[:50]
    return art_save(title, kind, c)

def artifact_create(title: str, kind: str, content: str):
    return "Artifact saved (Studio tab me dikhega): " + json.loads(art_save(title, kind, content))["id"]
def workspace_write(project: str, path: str, content: str):
    r = json.loads(ws_write(project, path, content)); return "Saved " + path + " in project " + _pn(project) if r.get("ok") else "Error: " + str(r.get("error"))
def workspace_run(project: str, path: str):
    r = json.loads(ws_run(project, path)); return ("Output:\n" + r.get("out", "")) if r.get("kind") == "text" else ("HTML page ready (Code Studio me Run dabao)" if r.get("kind") == "html" else "Error: " + str(r.get("error")))
def workspace_list(project: str = "scratch"):
    fs = json.loads(ws_files(project))["files"]; return "Files in " + _pn(project) + ": " + (", ".join(f["path"] for f in fs) or "(empty)")
for _f, _d, _w in [(artifact_create, "Save a finished HTML page / code / SVG / markdown as an Artifact shown in the Studio tab (title, kind=html|code|svg|markdown, content=full text)", "coder"), (workspace_write, "Create or overwrite a code file in a Code Studio project (project name, path like app.py, full content)", "coder"), (workspace_run, "Run a .py/.js/.sh file from a Code Studio project and return its output", "coder"), (workspace_list, "List files of a Code Studio project", "coder")]:
    try: reg_tool(_f, _d, _w)
    except Exception: pass

# ---------------- shared activity memory (chat + voice + phone) ----------------
ACT = globals().get("ACT") or []
_ask_orig = globals().get("_ask_orig") or ask
def ask(task):
    rec = {"id": uuid.uuid4().hex[:6], "t": time.time(), "task": str(task)[:240], "status": "running", "result": ""}
    ACT.append(rec); del ACT[:-40]
    try:
        r = _ask_orig(task); s = str(r); rec["status"] = "failed" if is_fail(s) else "done"; rec["result"] = s[:500]; return r
    except Exception as e:
        rec["status"] = "failed"; rec["result"] = "Error: " + str(e)[:200]; raise
def job_status(limit: int = 6):
    """what happened with recent tasks (PDFs, phone actions...) from ANY channel: chat, voice or phone"""
    if not ACT: return "Abhi tak koi kaam record nahi hua (server restart ke baad)."
    out = []
    for r in ACT[-int(limit):]:
        out.append("[%s] %s | %s | %s" % (time.strftime("%H:%M", time.localtime(r["t"])), r["status"].upper(), r["task"][:90], r["result"][:220].replace("\n", " ")))
    return "\n".join(out)
def recent_hook(task):
    rows = [r for r in ACT[-5:] if time.time() - r["t"] < 86400 and r["task"] != str(task)[:240]]
    return ("\nRECENT ACTIVITY (all channels, use it when Sir asks about earlier tasks/files; call job_status for more):\n" + "\n".join("- %s: %s => %s" % (r["status"], r["task"][:80], r["result"][:140].replace("\n", " ")) for r in rows)) if rows else ""
try:
    SYS_HOOKS[:] = [h for h in SYS_HOOKS if getattr(h, "__name__", "") != "recent_hook"] + [recent_hook]
    reg_tool(job_status, "Status of recent tasks from chat, voice and phone (is my PDF ready? what did you do earlier?)", "utils")
    if "job_status" not in _CORE_T: _CORE_T.add("job_status")
except Exception as _e: print("ax8a hook warn:", _e)
def act_list(): return JSON({"items": [{"id": r["id"], "t": time.strftime("%H:%M", time.localtime(r["t"])), "task": r["task"][:100], "status": r["status"], "result": r["result"][:160]} for r in ACT[-12:]][::-1]})
def phone_status():
    ph = globals().get("PHONE", {}); ago = time.time() - ph.get("seen", 0)
    return JSON({"online": ago < 25, "ago": int(ago) if ph.get("seen") else -1, "queued": len(ph.get("q", [])), "busy": bool(ph.get("cur") and not ph["cur"]["ev"].is_set())})
try: ADDON_API.update({k: v for k, v in dict(ws_projects=ws_projects, ws_project_new=ws_project_new, ws_project_del=ws_project_del, ws_files=ws_files, ws_read=ws_read, ws_write=ws_write, ws_delete=ws_delete, ws_run=ws_run, code_gen=code_gen, art_list=art_list, art_get=art_get, art_save=art_save, art_del=art_del, art_gen=art_gen, act_list=act_list, phone_status=phone_status).items()}); API.update(ADDON_API)
except NameError: pass
print("✅ ax8a workspace OK ->", WS_DIR)
