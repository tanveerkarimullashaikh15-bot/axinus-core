# AXINUS 4f - self-test (golden tasks) + token meter API/UI
import time, re, json
ST = globals().get("ST") or {"last": None}
GOLD = [("youtube open karke lofi songs search karo", "youtube_search", "lofi songs"), ("Axinus scroll down", "scroll_down", ""), ("scroll up karo", "scroll_up", ""), ("free fire app open karo", "open_app", "free fire"),
        ("whatsapp open karke rahul ko message karo kal milte hain", "whatsapp_message", "rahul"), ("mummy ko phone karo", "call", "mummy"), ("google me weather search karo", "web_search", "weather"),
        ("hello world type karo", "type", "hello world"), ("split screen karo", "split_screen", ""), ("instagram open karo", "open_app", "instagram"), ("chrome app open karo", "open_app", "chrome"),
        ("youtube me arijit singh search karo", "youtube_search", "arijit singh"), ("back jao", "back", ""), ("home jao", "home", "")]
def _t(name, fn):
    t0 = time.time()
    try:
        d = fn(); ok, det = (d if isinstance(d, tuple) else (True, d))
    except Exception as e: ok, det = False, str(e)[:100]
    return {"name": name, "ok": bool(ok), "detail": str(det)[:110], "ms": int((time.time() - t0) * 1000)}
def selftest(deep=False):
    out = []
    bad = []
    for q, a, tg in GOLD:
        r = fast_parse(q)
        if not r or r[0] != a or (tg and tg not in str(r[1]).lower()): bad.append(q[:28] + "->" + str(r and r[0]))
    out.append({"name": "Voice-command parser (%d cmds)" % len(GOLD), "ok": not bad, "detail": "; ".join(bad)[:110] or "all correct", "ms": 0})
    def _tw():
        import inspect
        src = inspect.getsource(send_whatsapp).lower() + DESC.get("send_whatsapp", "").lower()
        return ("twilio" not in src and "send_whatsapp" in REG), "WhatsApp ab phone se (Twilio code nahi)"
    out.append(_t("Twilio removed", _tw))
    out.append(_t("Roles have live models", lambda: (all(cands(r) for r in ("brain", "coder", "phone")), ", ".join("%s=%d" % (r, len(cands(r))) for r in ROLES))))
    def pdf():
        o = REP_DIR + "/_selftest.pdf"; build_pdf(o, "Self test", "x", "sum", [("A", "- a\n- b\n\n| x | y |\n|--|--|\n| 1 | 2 |")], None, [], ["p"]); ok, i = verify_pdf(o); return ok, "%s | %s" % (ENGINE_LAST[0], i)
    out.append(_t("PDF build + verify", pdf))
    def dg():
        p, cap, m = make_diagram_core("A to B to C flow"); return os.path.exists(p) and os.path.getsize(p) > 2000, m
    if deep: out.append(_t("Diagram (designer LLM + render)", dg))
    out.append({"name": "Phone agent online", "ok": time.time() - PHONE.get("seen", 0) < 25, "detail": "Android app accessibility ON" if time.time() - PHONE.get("seen", 0) < 25 else "offline (app band/accessibility off)", "ms": 0})
    if deep:
        out.append(_t("Brain LLM answers", lambda: (lambda r: ("ok" in r[0].lower(), r[1]))(llm("brain", "Reply with exactly: ok", "ping", mt=20))))
        out.append(_t("Coder writes code", lambda: (lambda r: ("def " in r[0] or "print" in r[0], r[1]))(llm("coder", "Return only python code.", "function add(a,b)", mt=120))))
        out.append(_t("Brain uses tools (time)", lambda: (lambda r: (bool(re.search(r"\d{1,2}[:.]\d{2}|AM|PM|baj", r)), r[:60]))(_ASK_CORE("Abhi time kya hai? get_datetime tool use karo, short batao"))))
    p = sum(1 for x in out if x["ok"]); n = len(out)
    res = {"checks": out, "pass": p, "total": n, "pct": round(100 * p / n), "t": time.strftime("%H:%M:%S"), "deep": bool(deep)}
    ST["last"] = res; return J(res)
def meter(): return J(meter_data())
ADDON_API.update({"selftest": selftest, "meter": meter})
UI_JS = r"""try{
TABS.push(['meter','Tokens'],['self','Self-test'],['phone','Phone setup']);
const bar=(p,c)=>'<div style="height:6px;background:#0a1621;border-radius:4px;overflow:hidden;margin:3px 0 7px"><div style="height:6px;width:'+Math.min(100,p||0)+'%;background:'+c+'"></div></div>';
TAB.meter=async function(){$('sbody').innerHTML='<div class="emp">Loading...</div>';const r=await api('meter');if(!r||r.error){$('sbody').innerHTML='<div class="emp">Meter nahi mila</div>';return;}
$('sbody').innerHTML='<div class="g">AAJ KA USE ('+E(r.day)+') - Groq limit ~200K tokens/din/model</div>'+((r.rows||[]).map(x=>'<div class="row"><span>'+E(x.model)+'</span><span>'+x.calls+' calls · '+x.tokens+' tok'+(x.err?' · <span class="bad">'+x.err+' err</span>':'')+(x.pct!=null?' · '+x.pct+'%':'')+'</span></div>'+(x.last?'<div style="font-size:11px;opacity:.7;margin:-4px 0 6px">last err: '+E(x.last)+'</div>':'')+(x.pct!=null?bar(x.pct,x.pct>80?'#ff5c5c':x.pct>50?'#ffb347':'#3ddc97'):'')).join('')||'<div class="emp">Abhi tak koi call nahi</div>')+
((r.dead||[]).length?'<div class="g">ABHI BAND (cooldown)</div>'+r.dead.map(d=>'<div class="row"><span class="bad">'+E(d.model)+'</span><span>'+Math.ceil(d.left_s/60)+' min</span></div>').join(''):'');};
TAB.self=function(){$('sbody').innerHTML='<button class="s" id="s1">Quick self-test</button><button class="s" id="s2">Deep self-test (tokens use)</button><div id="sr"></div>';
const go=async d=>{$('sr').innerHTML='<div class="emp">Chal raha hai...</div>';const r=await api('selftest',[d]);if(!r||!r.checks){$('sr').innerHTML='<div class="emp">Fail</div>';return;}
$('sr').innerHTML='<div class="g">PASS RATE: '+r.pct+'% ('+r.pass+'/'+r.total+') · '+E(r.t)+'</div>'+bar(r.pct,r.pct>=90?'#3ddc97':r.pct>=70?'#ffb347':'#ff5c5c')+r.checks.map(c=>'<div class="row"><span class="'+(c.ok?'ok':'bad')+'">'+(c.ok?'✓':'✗')+' '+E(c.name)+'</span><span style="text-align:right;max-width:55%">'+E(c.detail)+'</span></div>').join('');};
$('s1').onclick=()=>go(false);$('s2').onclick=()=>go(true);};
TAB.phone=function(){const A=window.AXAND,on=!!(A&&A.accessEnabled&&A.accessEnabled()),wk=!!(A&&A.wakeOn&&A.wakeOn());
const st=(o,t)=>'<div class="row"><span class="'+(o?'ok':'bad')+'">'+(o?'✓ ':'✗ ')+t+'</span></div>';
$('sbody').innerHTML=(A?st(on,'Accessibility service (phone control)')+st(wk,'Wake word "Hey Axinus" (Vosk)'):'<div class="emp">Ye setup sirf AXINUS Android app me dikhta hai</div>')+
'<div class="g">VIVO Y35 (Funtouch OS 14) - EK BAAR SETUP</div><div class="row"><span>1. Settings > Accessibility > Installed apps > AXINUS Phone Control > ON</span></div><div class="row"><span>2. Settings > Battery > Background power consumption > AXINUS > Allow</span></div><div class="row"><span>3. Settings > Apps > AXINUS > Autostart ON + Permissions: Microphone, Contacts, Notifications</span></div><div class="row"><span>4. Recent apps me AXINUS card ko lock karo (pull down ya lock icon)</span></div><div class="row"><span>5. Settings > Display & brightness me "Pop-up in background" allow (agar mile)</span></div><button class="s" id="pa">Accessibility settings kholo</button><button class="s" id="pw">Hey Axinus wake ON/OFF</button>';
if($('pa'))$('pa').onclick=()=>{try{A.openAccessSettings();}catch(e){}};if($('pw'))$('pw').onclick=()=>{try{A.wakeSetup();}catch(e){}setTimeout(TAB.phone,2500);};};
var c=document.querySelector('.chips');if(c){var b=document.createElement('button');b.className='chip';b.id='mtr';b.textContent='🔋 tokens';b.onclick=()=>settings('meter');c.appendChild(b);
const up=async()=>{try{const r=await api('meter');const g=(r.rows||[]).filter(x=>x.pct!=null).sort((a,b)=>b.pct-a.pct)[0];b.textContent='🔋 '+(g?g.pct+'% '+g.model.split('/').pop().slice(0,12):'tokens');b.style.color=g&&g.pct>80?'#ff5c5c':'';}catch(e){}};up();setInterval(up,60000);}}catch(e){console.log('ax4f ui',e);}
"""
_ANCH = "$('bset').onclick=()=>settings('voice');"
if "TAB.meter" not in UI_BODY:
    assert _ANCH in UI_BODY, "ui anchor missing"
    UI_BODY = UI_BODY.replace(_ANCH, _ANCH + "\n" + UI_JS, 1)
if "API" in globals() and "build_old_js" in globals():
    API.update(ADDON_API)
    _oj, _w = build_old_js(PAGE)
    UI_HTML = '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>AXINUS</title></head><body>' + UI_BODY.replace("__OLD__", _oj) + '</body></html>'
print("✅ ax4f self-test + token meter OK")
