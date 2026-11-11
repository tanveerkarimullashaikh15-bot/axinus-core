# AXINUS ADDON 4j - vision chain (Gemini -> Cohere Command A Vision -> Cloudflare Workers AI) + screen look/tap
import base64, json, re, time, requests
CF_ACC = sec("CF_ACCOUNT_ID", "CLOUDFLARE_ACCOUNT_ID"); CF_TOK = sec("CF_API_TOKEN", "CLOUDFLARE_API_TOKEN")
COH_V = "command-a-vision-07-2025"; CF_V = "@cf/meta/llama-3.2-11b-vision-instruct"; CF_V2 = "@cf/llava-hf/llava-1.5-7b-hf"
VIS_EXTRA = (["cohere:" + COH_V] if cohere_client else []) + (["cloudflare:" + CF_V] if (CF_ACC and CF_TOK) else [])
EXTRA_LIM = {"cohere": "~1000 call/mahina (trial)", "cloudflare": "free ~10K neurons/din"}
WN["eyes"] = "VISION"
VCOOL = globals().get("VCOOL") or {}
def _dead(k): return VCOOL.get(k, 0) > time.time()

def _v_gemini(img, mime, q):
    from google.genai import types
    last = None
    for m in _gem_ids():
        if R0["dead"].get(("gemini", m), 0) > time.time(): continue
        try:
            r = client.models.generate_content(model=m, contents=[types.Part.from_bytes(data=img, mime_type=mime), q])
            t = (r.text or "").strip()
            if t: _meter(("gemini", m)); return t, "gemini:" + m
        except Exception as e:
            last = e; _meter(("gemini", m), err=True, msg=e)
            c = _classify(e)
            if isinstance(c, (int, float)): R0["dead"][("gemini", m)] = time.time() + c
    raise last or RuntimeError("gemini: koi model nahi")

def _v_cohere(img, mime, q):
    if not cohere_client: raise RuntimeError("cohere key nahi")
    if _dead("cohere"): raise RuntimeError("cohere cooldown")
    try:
        r = cohere_client.chat(model=COH_V, messages=[{"role": "user", "content": [{"type": "text", "text": q}, {"type": "image_url", "image_url": {"url": "data:%s;base64,%s" % (mime, base64.b64encode(img).decode())}}]}], max_tokens=700)
        t = "".join(getattr(c, "text", "") or "" for c in r.message.content).strip()
        if not t: raise RuntimeError("cohere khaali jawab")
        _meter(("cohere", COH_V)); return t, "cohere:" + COH_V
    except Exception as e:
        _meter(("cohere", COH_V), err=True, msg=e); c = _classify(e); VCOOL["cohere"] = time.time() + (c if isinstance(c, (int, float)) else 60); raise

def _v_cf(img, mime, q):
    if not (CF_ACC and CF_TOK): raise RuntimeError("cloudflare key nahi")
    if _dead("cf"): raise RuntimeError("cloudflare cooldown")
    H = {"Authorization": "Bearer " + CF_TOK}; base = "https://api.cloudflare.com/client/v4/accounts/%s/ai/run/" % CF_ACC
    b64 = base64.b64encode(img).decode()
    try:
        body = {"messages": [{"role": "user", "content": [{"type": "text", "text": q}, {"type": "image_url", "image_url": {"url": "data:%s;base64,%s" % (mime, b64)}}]}], "max_tokens": 600}
        r = requests.post(base + CF_V, headers=H, json=body, timeout=45); j = r.json()
        if not j.get("success") and re.search(r"agree|license|terms", json.dumps(j), re.I):
            requests.post(base + CF_V, headers=H, json={"prompt": "agree"}, timeout=30)
            r = requests.post(base + CF_V, headers=H, json=body, timeout=45); j = r.json()
        res = j.get("result") or {}
        t = (res.get("response") or res.get("description") or "")
        if isinstance(t, dict): t = json.dumps(t)
        t = str(t).strip(); used = CF_V
        if not t:
            r = requests.post(base + CF_V2, headers=H, json={"prompt": q, "image": list(img), "max_tokens": 500}, timeout=60); j = r.json()
            t = str((j.get("result") or {}).get("description") or (j.get("result") or {}).get("response") or "").strip(); used = CF_V2
        if not t: raise RuntimeError("cloudflare: " + json.dumps(j.get("errors") or j)[:150])
        _meter(("cloudflare", used)); return t, "cloudflare:" + used
    except Exception as e:
        _meter(("cloudflare", CF_V), err=True, msg=e); c = _classify(e); VCOOL["cf"] = time.time() + (c if isinstance(c, (int, float)) else 60); raise

def vision(img, q, mime="image/jpeg", skip_gemini=False):
    """img bytes + question -> (text, model_used). Gemini first, then backups."""
    errs = []
    for name, fn in (("gemini", _v_gemini), ("cohere", _v_cohere), ("cloudflare", _v_cf)):
        if name == "gemini" and skip_gemini: continue
        try: return fn(img, mime, q)
        except Exception as e: errs.append(name + ": " + str(e)[:70])
    raise RuntimeError("Vision: saare models fail | " + " | ".join(errs))

# ---- analyze_image: keep Gemini path, add backups on failure ----
_AI0 = globals().get("_AI0") or analyze_image
def analyze_image(path: str, question: str):
    r = _AI0(path, question)
    if not str(r).startswith("Image Error"): return r
    try:
        p = safe_path(path)
        if not p or not os.path.exists(p): return r
        ext = p.lower().rsplit(".", 1)[-1]; mime = {"png": "image/png", "webp": "image/webp"}.get(ext, "image/jpeg")
        t, used = vision(open(p, "rb").read(), question, mime, skip_gemini=True)
        return t + "\n[Model: %s (backup)]" % used
    except Exception as e:
        return "Image Error: " + str(e)[:200]
reg_tool(analyze_image, DESC.get("analyze_image", "Analyze an image file (path, question)"), "eyes")

# ---- screen vision ----
SCR = globals().get("SCR") or {"t": 0, "b": b""}
_SENS = re.compile(r"(?i)\b(send|pay|payment|buy|purchase|order|delete|remove|transfer|password|passcode|otp|pin|install|uninstall|logout|log out|sign out|submit|confirm|bhej|bhejo|kharid|delete)\b")
def _shot():
    res = _submit("Take a screenshot of the phone screen", {"k": "look"})
    d = PHONE.get("lastdata", "")
    if not d or not res.startswith("Done"): return None, res
    try: b = base64.b64decode(d)
    except Exception: return None, "Error: screenshot decode nahi hua."
    SCR.update({"t": time.time(), "b": b}); return b, res

def screen_look(question: str = "Screen par kya dikh raha hai? Short me batao."):
    """Take a screenshot of the user's phone and answer a question about what is on screen."""
    with Stage("eyes", "Screen dekh raha hoon", "screenshot") as st:
        b, res = _shot()
        if b is None: st.fail = True; return "Error: " + res.replace("Not completed: ", "")
        try:
            t, used = vision(b, "Ye Android phone ka screenshot hai. Sawal: " + str(question) + "\nHinglish me chhota jawab do. Jo dikh raha hai wahi batao. Password/OTP/card numbers ho to unhe mat likho.")
            st.model = used; return t + "\n[Model: %s]" % used
        except Exception as e:
            st.fail = True; return "Error: " + str(e)[:220]

def screen_tap(description: str):
    """Find the described button/item on the phone screen by looking at it, then tap it."""
    d = str(description).strip()
    if not d: return "Error: kya tap karna hai batao."
    if _SENS.search(d): return "Not completed: '%s' sensitive action hai (send/pay/delete/OTP...), main khud nahi dabaunga. Aap dabao." % d[:40]
    with Stage("eyes", "Screen par dhoondh raha hoon: " + d[:30], "screenshot") as st:
        b, res = _shot()
        if b is None: st.fail = True; return "Error: " + res.replace("Not completed: ", "")
        try:
            t, used = vision(b, 'Ye Android screenshot hai. Is element ko dhoondho: "%s". Reply sirf JSON: {"found":true|false,"x":0-1000,"y":0-1000,"label":"element ka text"} jahan x,y element ke center ka position hai (0,0 = top-left, 1000,1000 = bottom-right). Na mile to found=false.' % d)
            m = re.search(r"\{.*\}", t, re.S); j = json.loads(m.group(0)) if m else {}
        except Exception as e:
            st.fail = True; return "Error: " + str(e)[:200]
        if not j.get("found"): return "Not completed: screen par '%s' nahi dikha." % d
        lab = str(j.get("label", ""))
        if _SENS.search(lab): return "Not completed: wahan '%s' likha hai (sensitive), nahi dabaya." % lab[:40]
        try: x, y = int(j["x"]), int(j["y"])
        except Exception: st.fail = True; return "Error: coordinates samajh nahi aaye."
        r = _submit("tap", {"k": "tap_xy", "x": x, "y": y})
        st.model = used; return r + " (target: %s)" % (lab or d)

reg_tool(screen_look, "SEE the user's phone screen now (screenshot -> vision AI) and answer a question about it. Use for 'screen par kya hai', 'ye kya dikh raha hai', or before acting on an app screen (question)", "eyes")
reg_tool(screen_tap, "Tap a button/item on the phone screen identified by LOOKING at it (description e.g. 'search icon', 'first video', 'Subscribe button'). Never for send/pay/delete. Check with screen_look afterwards", "phone")
DELEG += "\n- SCREEN VISION: to act on an app screen you cannot name exactly, call screen_look (what is on screen), then screen_tap(description) or phone_do, then screen_look to verify. If a phone-kind lesson matches the app (see TAUGHT LESSONS), follow its steps. Never claim success without the tool result.\n"
_GRP.append((r"screen|dikh|dekh|look|what.?s on|tap|click kar|dabao|button|icon|video chal|play kar|screenshot", ["screen_look", "screen_tap", "phone_do", "phone_control", "recall_lessons"]))
print("✅ ax6d vision OK | backups:", ", ".join(VIS_EXTRA) or "none (keys missing)")
