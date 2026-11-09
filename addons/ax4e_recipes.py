# AXINUS 4e - phone recipes (intent-first, deterministic) + fast path for simple commands (no LLM)
import re, time
PEND = globals().get("PEND") or {"kind": "", "t": 0}
_APPS = {"yt": "YouTube", "youtube": "YouTube", "wa": "WhatsApp", "whatsapp": "WhatsApp", "insta": "Instagram", "instagram": "Instagram", "gpt": "ChatGPT", "chatgpt": "ChatGPT",
         "freefire": "Free Fire", "free fire": "Free Fire", "ff": "Free Fire", "vedantu": "Vedantu", "drive": "Drive", "google drive": "Drive", "chrome": "Chrome", "google": "Google", "claude": "Claude", "settings": "Settings"}
def _app(n):
    n = re.sub(r"\s+", " ", str(n).strip().lower()); return _APPS.get(n, str(n).strip().title())
def _num(t):
    t = str(t).strip(); d = re.sub(r"[^\d+]", "", t)
    if len(re.sub(r"\D", "", d)) >= 10 and not re.search(r"[a-z]", t, re.I): return d
    r = resolve_contact(t) if "resolve_contact" in globals() else t
    return r if (r.startswith("+") and "X" not in r) else ""
def phone_do(action: str, target: str = "", text: str = ""):
    a = str(action).lower().strip(); t = str(target).strip(); x = str(text).strip()
    R = {"open_app": lambda: ("open_app", {"k": "open_app", "q": _app(t)}),
         "youtube_search": lambda: ("YouTube search: " + t, {"k": "youtube_search", "q": t}),
         "web_search": lambda: ("Google search: " + t, {"k": "web_search", "q": t}),
         "whatsapp_message": lambda: ("WhatsApp " + t + ": " + x, {"k": "whatsapp_message", "name": t, "num": _num(t), "text": x}),
         "call": lambda: ("Call " + t, {"k": "call", "name": t, "num": _num(t)}),
         "scroll_down": lambda: ("scroll down", {"k": "scroll", "d": "down"}), "scroll_up": lambda: ("scroll up", {"k": "scroll", "d": "up"}),
         "type": lambda: ("type text", {"k": "type", "q": t or x, "submit": False}), "type_submit": lambda: ("type text", {"k": "type", "q": t or x, "submit": True}),
         "click_text": lambda: ("tap " + t, {"k": "click_text", "q": t}), "split_screen": lambda: ("split screen", {"k": "split_screen"}),
         "back": lambda: ("back", {"k": "back"}), "home": lambda: ("home", {"k": "home"}),
         "confirm": lambda: ("confirm pending", {"k": "confirm"}), "deny": lambda: ("cancel pending", {"k": "deny"})}
    if a not in R: return "Error: unknown phone action. Allowed: " + ", ".join(R)
    if a == "confirm" and time.time() - PEND["t"] > 180: return "Not completed: koi pending message/call nahi hai."
    goal, rc = R[a]()
    if a == "open_app": goal = "Open the app " + rc["q"]
    if a == "whatsapp_message":
        goal = "Open WhatsApp, open chat with " + t + ", type this message (do NOT send): " + x
        if not rc["num"] and not rc["name"]: return "Error: kis ko bhejna hai?"
    if a in ("whatsapp_message", "call") and not rc.get("num") and not rc.get("name"): return "Error: contact/number batao."
    if a == "call": goal = "Open the phone dialer and search contact " + t + " (do NOT press call)"
    res = _submit(goal, rc)
    if a in ("whatsapp_message", "call") and res.startswith("Done") and "boliye" in res: PEND["kind"] = "send" if a == "whatsapp_message" else "call"; PEND["t"] = time.time()
    if a in ("confirm", "deny"): PEND["kind"] = ""; PEND["t"] = 0
    return res
def send_whatsapp(contact_or_number: str, message: str):
    return phone_do("whatsapp_message", contact_or_number, message)
reg_tool(phone_do, "FIRST CHOICE for phone actions (fast, reliable). action: open_app(target=app) | youtube_search(target=query) | web_search(target=query) | whatsapp_message(target=contact name/number, text=message; opens chat, user must confirm) | call(target=contact/number; opens dialer, user must confirm) | scroll_down | scroll_up | type(target=text) | type_submit(target=text) | click_text(target=visible text) | split_screen | back | home | confirm (only after the user clearly says yes/bhej do/call karo) | deny. Result is real; report it exactly.", "phone")
reg_tool(send_whatsapp, "WhatsApp message: opens the chat with the message typed; user must confirm before it is sent (contact_or_number, message)", "phone")
WRITE.add("send_whatsapp") if isinstance(WRITE, set) else None
if "PHONE FIRST RULE" not in DELEG:
    DELEG += "\n- PHONE FIRST RULE: for any phone/app action call phone_do (not phone_control) when an action fits; use phone_control(goal) only for unusual multi-step app tasks. NEVER say a message was sent or a call was made unless the tool result says 'Done: message bhej diya' / 'Done: call laga diya'. After phone_do whatsapp_message/call, tell the user it is waiting for their yes."

# ---------- fast path ----------
_STRIP = re.compile(r"^(?:hey |ok |okay )?(?:axinus|axis|jarvis)[,.! ]*", re.I)
def _fclean(t): return _STRIP.sub("", str(t).strip()).strip(" .!?")
_BADT = re.compile(r"\b(aur|and|karke|phir|fir|then|play|open karo|kholo)\b", re.I)
def fast_parse(task):
    r = _fast_parse(task)
    if r and r[0] in ("youtube_search", "web_search", "type", "whatsapp_message", "call") and _BADT.search(str(r[1])): return None
    return r
def _fast_parse(task):
    t = _fclean(task); low = t.lower()
    if len(t) > 160: return None
    pend = PEND["kind"] and time.time() - PEND["t"] < 180
    if pend and re.fullmatch(r"(?:(?:haan|han|ha|yes|yeah|ok|okay|ji|theek hai)[, ]*)?(?:(?:haan|yes|ok|ji)[, ]*)?(?:kar do|bhej do|send kar do|call kar do|call karo|bhejo|laga do|lagao|send|send karo|yes|haan|han|ha|ok|okay|theek hai)(?: ji| sir| boss)?", low): return ("confirm", "", "")
    if pend and re.fullmatch(r"(nahi|nahin|no|cancel|mat karo|mat bhejo|rehne do|ruk jao)( sir| boss)?", low): return ("deny", "", "")
    if re.fullmatch(r"(?:please )?scroll (?:down|neeche)(?: karo)?|neeche scroll karo|neeche karo", low): return ("scroll_down", "", "")
    if re.fullmatch(r"(?:please )?scroll (?:up|upar)(?: karo)?|upar scroll karo|upar karo", low): return ("scroll_up", "", "")
    if re.search(r"split ?screen", low): return ("split_screen", "", "")
    if re.fullmatch(r"(?:back|piche|peeche)(?: jao| karo)?", low): return ("back", "", "")
    if re.fullmatch(r"home(?: par| pe)?(?: jao| chalo)?|home screen(?: par jao)?", low): return ("home", "", "")
    m = re.match(r"(?:youtube|yt)(?: me| mein| par| pe)?(?: open karke)?\s+(.+?)\s+(?:search karo|search kar|search|dhundo|play karo)$", low)
    if m: return ("youtube_search", m.group(1), "")
    m = re.match(r"(?:youtube|yt) open karke (?:search karo )?(.+)$", low)
    if m: return ("youtube_search", re.sub(r"\s*search karo$", "", m.group(1)), "")
    m = re.match(r"(?:whatsapp|wa)(?: open karke| me| mein| par| pe)?\s+(.+?)\s+ko\s+(?:message|msg|text)\s+(?:karo|bhejo|send karo|kar do)[:,]?\s+(.+)$", low)
    if m: return ("whatsapp_message", m.group(1), t[t.lower().rfind(m.group(2)):] if m.group(2) in t.lower() else m.group(2))
    m = re.match(r"(.+?)\s+ko\s+(?:phone|call|fone)\s+(?:karo|lagao|laga do|kar do)$", low)
    if m: return ("call", m.group(1), "")
    m = re.match(r"(.+?)\s+(?:me|mein|par|pe)\s+(.+?)\s+search\s+(?:karo|kar)$", low)
    if m and m.group(1) in ("google", "chrome", "browser"): return ("web_search", m.group(2), "")
    if m and m.group(1) in ("youtube", "yt"): return ("youtube_search", m.group(2), "")
    m = re.match(r"(.+?)\s+type\s+(?:karo|kar do|kar)$", t, re.I)
    if m: return ("type", m.group(1), "")
    m = re.match(r"(?:open\s+(.+?)|(.+?)\s+(?:app\s+)?(?:open|kholo|khol do|chalu)\s*(?:karo|kar do)?)$", low)
    if m:
        n = (m.group(1) or m.group(2) or "").replace(" app", "").strip()
        if n and len(n.split()) <= 3 and n not in ("file", "pdf"): return ("open_app", n, "")
    return None
_PH_KW = re.compile(r"\b(open|kholo|khol|search|dhundo|call|phone|fone|message|msg|whatsapp|youtube|yt|scroll|type|play|app|instagram|insta|chrome|google|drive|vedantu|claude|chatgpt|free ?fire|split|back|home|click|tap|neeche|upar)\b", re.I)
def phone_like(q):
    q = str(q)
    try: return bool(fast_parse(q)) or (len(q) < 140 and bool(_PH_KW.search(q)))
    except Exception: return False
LLM_SYS = ("You convert a Hinglish/English spoken command into phone actions. Output ONLY a JSON array (max 4 steps), or [] if it is NOT a phone/app action (questions, chat, research, facts). "
 "Step = {\"a\":action,\"t\":target,\"x\":text}. Actions: open_app(t=app name) | youtube_search(t=query) | web_search(t=query) | whatsapp_message(t=contact,x=message) | call(t=contact or number) | scroll_down | scroll_up | type(t=text) | click_text(t=visible text) | split_screen | back | home. "
 "To play a video: youtube_search then click_text with t='play video'. Clean the query: remove words like open karo, search karo, aur, and, play karo. Examples: "
 "'youtube open karo aur cartoon search karo and play karo' -> [{\"a\":\"youtube_search\",\"t\":\"cartoon\"},{\"a\":\"click_text\",\"t\":\"play video\"}]; "
 "'whatsapp kholo' -> [{\"a\":\"open_app\",\"t\":\"WhatsApp\"}]; 'train timings to Solapur' -> []; 'YouTube Shilpa Shetty' -> [{\"a\":\"youtube_search\",\"t\":\"Shilpa Shetty\"}].")
OKA = {"open_app", "youtube_search", "web_search", "whatsapp_message", "call", "scroll_down", "scroll_up", "type", "click_text", "split_screen", "back", "home"}
def llm_steps(task):
    t, _ = llm("fast", LLM_SYS, str(task)[:200], mt=260, timeout=20)
    m = re.search(r"\[.*\]", t, re.S)
    if not m: return []
    out = []
    for d in json.loads(m.group(0))[:4]:
        if isinstance(d, dict) and d.get("a") in OKA: out.append((d["a"], str(d.get("t", "")), str(d.get("x", ""))))
    return out
def _preempt():
    PHONE["q"].clear(); c = PHONE.get("cur")
    if c and not c["ev"].is_set(): PHONE["stop"] = True; c["res"] = "Cancelled: naya command aaya."; c["ev"].set()
_ASK_CORE = globals().get("_ASK_CORE") or ask
def _run_steps(task, steps):
    JOB["workers"] = []; JOB["models"] = {}; TRACE.clear()
    outs = []; ok = True
    _preempt()
    for i, st in enumerate(steps):
        emit("brain", "mark", "PHONE: " + st[0] + " " + str(st[1])[:40])
        with Stage("phone", "Phone: " + st[0], "recipe") as s_:
            res = phone_do(*st); s_.fail = res.startswith(("Error", "Not completed", "BLOCKED"))
        outs.append(res.replace("Done: ", "", 1).replace("Not completed: ", "Nahi hua, Sir: ", 1))
        if s_.fail: ok = False; break
        if i + 1 < len(steps) and st[0] in ("youtube_search", "web_search", "open_app"): time.sleep(2.5)
    out = " | ".join(outs)
    try: remember_turn(task, out)
    except Exception: pass
    return out
def ask(task):
    JOB["links"] = []
    fp = None
    try: fp = fast_parse(task)
    except Exception: pass
    r = None
    if fp: r = _run_steps(task, [fp])
    elif len(str(task)) < 140 and _PH_KW.search(str(task)):
        try: steps = llm_steps(task)
        except Exception as e: steps = []; emit("brain", "mark", "parse fail: " + str(e)[:50])
        if steps: r = _run_steps(task, steps)
    if r is None: r = _ASK_CORE(task)
    for l in JOB.get("links", []):
        if l not in r: r += "\n" + l
    return r
_CALL0 = globals().get("_CALL0") or CALL
def CALL(name, args):
    res = _CALL0(name, args)
    try:
        for m in re.finditer(r"https?://\S+/f\?p=\S+", str(res)):
            if m.group(0) not in JOB.setdefault("links", []): JOB["links"].append(m.group(0))
    except Exception: pass
    return res
print("✅ ax4e recipes OK | tools: phone_do, send_whatsapp (confirm flow) + fast path + LLM command parser")
