# AXINUS ADDON 4d - phone control brain (Android accessibility agent): queue + step planner + safety
import re, json, time, uuid, threading
PHONE = globals().get("PHONE") or {"q": [], "stop": False, "cur": None}
PH_SYS = """You control an Android phone for the user. You get GOAL, RECENT steps and SCREEN (JSON: pkg + items[i=index,t=text,c=clickable,e=editable,s=scrollable]).
Reply with EXACTLY ONE JSON object, nothing else:
{"a":"open","app":"app name"} | {"a":"click","i":N} | {"a":"type","i":N,"t":"text","submit":true|false} | {"a":"scroll","d":"down"|"up"} | {"a":"back"} | {"a":"home"} | {"a":"wait"} | {"a":"done","msg":"short result for the user"} | {"a":"fail","msg":"why"}
Rules: to search inside an app: click the search icon/box first, then on the next screen type into the editable item with submit:true. use ONLY indexes present in SCREEN. One step at a time. If the app is not open, use open first. Never repeat the same failing action more than twice - try another way or fail. After typing a message, do not press send/pay/buy/delete/transfer: finish with done and tell the user to tap it. Never enter passwords, OTP or UPI PIN. Finish with done as soon as the goal is achieved. Keep msg short, in Hinglish."""
import threading
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
WN["phone"] = "PHONE AGENT"
PH = globals().get("PH") or {"pool": [], "t": 0, "rr": 0, "dead": {}}
def _ph_llm(user):
    t, used = llm("phone", PH_SYS, user, mt=300, hedge=True, timeout=30)
    if "{" not in t: raise ValueError("no json")
    PH["last"] = used
    return t
def phone_step(goal, screen, hist):
    if PHONE["stop"]: return J({"a": "fail", "msg": "Sir, phone control rok diya."})
    with Stage("phone", "Phone step", PH.get("last", "phone")) as st:
        try:
            raw = _ph_llm("GOAL: " + str(goal)[:300] + "\nRECENT:\n" + str(hist)[-900:] + "\nSCREEN:\n" + str(screen)[:7000])
            m = re.search(r"\{.*\}", raw, re.S)
            a = json.loads(m.group(0)) if m else None
            if not isinstance(a, dict) or a.get("a") not in ("open", "click", "type", "scroll", "back", "home", "wait", "done", "fail"): raise ValueError("bad action: " + raw[:80])
            return J(a)
        except Exception as e:
            st.fail = True
            return J({"a": "fail", "msg": "Planner error: " + str(e)[:100]})
PHONE.setdefault("seen", 0); PHONE.setdefault("items", {}); PHONE["cur"] = None
def _submit(goal, recipe=None):
    if time.time() - PHONE["seen"] > 25: return "Error: phone agent online nahi hai. Android app me Accessibility ON karo aur app me sahi URL/PIN rakho. Kaam nahi hua."
    c = PHONE.get("cur")
    if c and not c["ev"].is_set():
        c["ev"].wait(110); return c.get("res") or "Error: pehle wale kaam ka result nahi aaya."
    it = {"id": uuid.uuid4().hex[:6], "goal": goal[:300], "recipe": recipe, "ev": threading.Event(), "res": ""}
    PHONE["stop"] = False; PHONE["items"][it["id"]] = it; PHONE["cur"] = it; PHONE["q"].append(it)
    PHONE["lastdata"] = ""
    if not it["ev"].wait(110): it["ev"].set(); PHONE["q"][:] = [x for x in PHONE["q"] if x is not it]; it["res"] = "Error: phone agent ne 110 second me jawab nahi diya. Kaam poora hua ya nahi, pakka nahi."
    PHONE["lastdata"] = it.get("data", "")
    return it["res"] or "Error: koi result nahi aaya."
def phone_control(goal: str):
    return _submit(goal)
def phone_stop():
    PHONE["stop"] = True; PHONE["q"].clear()
    c = PHONE.get("cur")
    if c and not c["ev"].is_set(): c["res"] = "Phone control rok diya gaya."; c["ev"].set()
    return "Phone control rok diya."
def phone_poll():
    for _ in range(48):
        PHONE["seen"] = time.time()
        if PHONE["q"]: break
        time.sleep(0.25)
    if PHONE["q"]:
        it = PHONE["q"].pop(0); PHONE["stop"] = False
        return J({"id": it["id"], "goal": it["goal"], "recipe": it.get("recipe")})
    return J({})
def phone_done(pid, msg, data=""):
    it = PHONE["items"].get(str(pid))
    if it and not it["ev"].is_set():
        it["data"] = str(data or "")[:600000]
        m = str(msg)[:250]; it["res"] = ("Done: " if not re.match(r"(?i)(sir,? )?(ruk|nahi|server|payment|planner|error)", m) else "Not completed: ") + m; it["ev"].set()
    try: _alert("phone", {"id": str(pid), "title": "Phone agent"}, str(msg)[:200])
    except Exception: pass
    return J({"ok": True})
reg_tool(phone_control, "USE THIS (not youtube_search) whenever the user wants something done INSIDE an app or on the phone screen: search in YouTube/Instagram app, play a short, open settings, scroll, type in an app. Control the user's Android phone (open apps, tap, type, scroll) to do a task via accessibility. Waits and returns the REAL result; report exactly that result to the user, never claim success otherwise. goal = plain instruction. Needs the Android app with Accessibility ON", "phone")
reg_tool(phone_stop, "Stop the phone agent immediately", "phone")
if "PHONE CONTROL RULE" not in DELEG:
    DELEG += "\n- PHONE CONTROL RULE: if the user wants an action inside an app or on the phone screen (search in the YouTube app, play a Short, open settings, scroll, type in an app) call phone_control(goal). Use youtube_search ONLY when the user explicitly asks for links.\n"
ADDON_API.update({"phone_step": phone_step, "phone_poll": phone_poll, "phone_done": phone_done})
PIN_JS = "<script>try{if(window.AXAND&&AXAND.setPin)AXAND.setPin(localStorage.getItem('pin')||'');}catch(e){}</script>"
if "setPin" not in UI_BODY:
    UI_BODY = UI_BODY + PIN_JS
WAKE_JS = """<script>(function(){if(!window.AXAND||!AXAND.wakeSetup)return;
var g=function(i){return document.getElementById(i)},last=Date.now(),pm='';
try{new MutationObserver(function(){last=Date.now();}).observe(g('lg'),{childList:true,subtree:true,characterData:true});}catch(e){}
g('bstop').addEventListener('click',function(){try{AXAND.voiceOff();}catch(e){}});g('bgo').addEventListener('click',function(){try{AXAND.keepAlive();}catch(e){}});
setInterval(function(){var m=document.body.dataset.m;if(m==='live'&&pm!=='live')last=Date.now();pm=m;if(m==='live'&&Date.now()-last>60000)g('bstop').click();},4000);
var b=document.createElement('button');b.className='chip';b.id='wkb';var u=function(){b.textContent='\\uD83C\\uDF99 Hey AXINUS: '+(AXAND.wakeOn()?'ON':'SETUP');};u();
b.onclick=function(){AXAND.wakeSetup();setTimeout(u,2500);};var c=document.querySelector('.chips');if(c)c.appendChild(b);})();</script>"""
if "wakeSetup" not in UI_BODY: UI_BODY = UI_BODY + WAKE_JS
if "API" in globals() and "build_old_js" in globals():
    API.update(ADDON_API)
    _oj, _w = build_old_js(PAGE)
    UI_HTML = '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>AXINUS</title></head><body>' + UI_BODY.replace("__OLD__", _oj) + '</body></html>'
print("✅ phone agent brain ON | tools: phone_control, phone_stop")
