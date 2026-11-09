# AXINUS ADDON 5 - server: UI, API merge, signed file route, tunnel
import os, re, time, threading, random, subprocess, hmac, base64, mimetypes
os.system("pip install -q fastapi uvicorn")
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, Response
from starlette.concurrency import run_in_threadpool

def voice_preview(voice="Kore"):
    if voice not in ("Puck", "Charon", "Kore", "Fenrir", "Aoede", "Leda", "Orus", "Zephyr"): voice = "Kore"
    last = "no response"
    for mdl in ("gemini-2.5-flash-preview-tts", "gemini-2.5-flash-tts"):
        try:
            body = {"contents": [{"parts": [{"text": "Namaste Sir, main Axinus hoon. Aapki kya madad karun?"}]}], "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}}}
            r = requests.post("https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent" % mdl, headers={"x-goog-api-key": API_KEY}, json=body, timeout=40)
            if r.status_code != 200: last = "HTTP %s" % r.status_code; continue
            part = r.json()["candidates"][0]["content"]["parts"][0]["inlineData"]
            return JSON({"pcm": part["data"], "rate": 24000})
        except Exception as e: last = str(e)[:80]
    return JSON({"error": "Preview abhi available nahi (" + last + "). Voice phir bhi CONNECT par apply hogi."})
ADDON_API["voice_preview"] = voice_preview

if "PIN" not in globals() or not PIN: PIN = sec("AXINUS_PIN") or str(random.randint(100000, 999999))
PIN = str(PIN)
WARN = []
old_js, WARN = build_old_js(PAGE)
if WARN: print("⚠️ old-script patches skipped:", WARN)
UI_HTML = '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>AXINUS</title></head><body>' + UI_BODY.replace("__OLD__", old_js) + '</body></html>'

API = {"get_token": get_token, "start_job": start_job, "poll_job": poll_job, "answer_approval": answer_approval, "save_chunk": save_chunk}
API.update(ADDON_API)
def _handle(name, pin, args):
    if not hmac.compare_digest(str(pin), PIN): return 401, {"error": "bad pin"}
    if name not in API: return 404, {"error": "unknown"}
    try:
        r = API[name](*args)
        return 200, (r.data if hasattr(r, "data") else r)
    except Exception as e:
        return 200, {"error": "%s: %s" % (type(e).__name__, str(e)[:150])}
app = FastAPI()
@app.get("/", response_class=HTMLResponse)
def home(): return UI_HTML
@app.post("/api/{name}")
async def api(name: str, request: Request):
    try: b = await request.json()
    except Exception: b = {}
    s, o = await run_in_threadpool(_handle, name, request.headers.get("x-pin", ""), b.get("args", []))
    return JSONResponse(o, status_code=s)
@app.get("/f")
def fileroute(p: str = "", s: str = ""):
    try:
        if not p or not hmac.compare_digest(s, sign(p)): return Response("forbidden", status_code=403)
        fp = os.path.realpath(os.path.join(ROOT_DIR, p)); root = os.path.realpath(ROOT_DIR)
        if not fp.startswith(root + os.sep) or not os.path.isfile(fp): return Response("not found", status_code=404)
        return FileResponse(fp, media_type=mimetypes.guess_type(fp)[0] or "application/octet-stream")
    except Exception: return Response("error", status_code=500)

if "SERVER" in globals(): SERVER.should_exit = True; time.sleep(1.5)
os.system("pkill cloudflared")
SERVER = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="warning"))
threading.Thread(target=SERVER.run, daemon=True).start()
CFB = "/content/cloudflared"
for _try in range(3):
    if not (os.path.exists(CFB) and os.path.getsize(CFB) > 5_000_000):
        os.system("rm -f %s; wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O %s" % (CFB, CFB))
    os.system("chmod +x " + CFB)
    if os.path.exists(CFB) and os.path.getsize(CFB) > 5_000_000 and os.access(CFB, os.X_OK): break
    time.sleep(2)
p = subprocess.Popen(["/content/cloudflared", "tunnel", "--url", "http://127.0.0.1:8000", "--no-autoupdate"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
CF_LOG = []
threading.Thread(target=lambda: [CF_LOG.append(l) for l in p.stdout], daemon=True).start()
URL = None
for _ in range(45):
    found = [u for u in re.findall(r"https://[a-z0-9-]+\.trycloudflare\.com", "".join(CF_LOG)) if not u.startswith("https://api.")]
    if found:
        URL = found[-1]
        break
    time.sleep(1)
print("✅ SERVER URL:", URL)
print("🔑 PIN:", PIN)
