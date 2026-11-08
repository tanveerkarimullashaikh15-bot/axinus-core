# AXINUS ADDON 4 - UI (history sidebar, tasks, news, activity, settings) + safe patches for the old live-voice script
UI_BODY = r"""
<style>
:root{--bg:#05090f;--ln:#16364a;--cy:#22d3ee;--cy2:#0e7490;--tx:#d5e6ee;--mut:#6d8a99;--ok:#34d399;--wr:#f59e0b;--er:#f43f5e}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{margin:0}
body{background:radial-gradient(1200px 600px at 70% -10%,#0b2a36 0,transparent 60%),radial-gradient(900px 500px at -10% 110%,#0a1f33 0,transparent 55%),var(--bg);color:var(--tx);font-family:Inter,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;min-height:100vh;padding:10px}
button{font-family:inherit}
.app{max-width:1500px;margin:auto;display:flex;flex-direction:column;gap:10px}
.col{display:contents}
#pOrb{order:1}#pChat{order:2}#pAct{order:3}#pTown{order:4}#pTasks{order:5}#pNews{order:6}#pMedia{order:7}#pMap{order:8}
.top{display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:2px 4px}
.brand{display:flex;align-items:center;gap:10px;flex:1;min-width:0}
.brand svg{width:26px;height:26px;stroke:var(--cy);fill:none;stroke-width:1.6;stroke-linejoin:round;flex:none}
.brand b{display:block;font:800 15px ui-monospace,Menlo,Consolas,monospace;letter-spacing:.26em;color:#e8f7fb}
.brand span{display:block;font:500 9px ui-monospace,Menlo,monospace;letter-spacing:.22em;color:var(--mut);margin-top:2px}
.pill{display:flex;align-items:center;gap:8px;padding:7px 12px;border:1px solid var(--ln);border-radius:999px;background:#08131c;font:500 11.5px ui-monospace,Menlo,monospace;color:#9fc3d3;flex:1 1 100%;order:5}
.pill span{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pill i{flex:none;width:8px;height:8px;border-radius:50%;background:#4b6b80}
.pill[data-m=live] i{background:var(--ok);box-shadow:0 0 8px var(--ok)}
.pill[data-m=think] i{background:var(--cy);box-shadow:0 0 8px var(--cy);animation:bl .6s infinite alternate}
.pill[data-m=wait] i{background:var(--wr);box-shadow:0 0 8px var(--wr)}
.pill[data-m=err] i{background:var(--er);box-shadow:0 0 8px var(--er)}
@keyframes bl{to{opacity:.3}}
.ib{width:38px;height:38px;flex:none;border-radius:9px;border:1px solid var(--ln);background:#08131c;color:#9fc3d3;display:grid;place-items:center;cursor:pointer}
.ib svg{width:19px;height:19px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.pn{position:relative;background:linear-gradient(180deg,rgba(13,27,39,.92),rgba(8,17,26,.92));border:1px solid var(--ln);border-radius:14px;padding:12px;box-shadow:0 10px 30px rgba(0,0,0,.35);min-width:0}
.pn:before,.pn:after{content:"";position:absolute;width:12px;height:12px;border:2px solid var(--cy);opacity:.55;pointer-events:none}
.pn:before{top:-1px;left:-1px;border-right:0;border-bottom:0;border-top-left-radius:14px}
.pn:after{bottom:-1px;right:-1px;border-left:0;border-top:0;border-bottom-right-radius:14px}
.hd{display:flex;align-items:center;gap:8px;font:700 10.5px ui-monospace,Menlo,Consolas,monospace;letter-spacing:.16em;color:var(--cy);margin-bottom:10px}
.hd:before{content:"";width:7px;height:7px;border-radius:50%;background:var(--cy);box-shadow:0 0 8px var(--cy)}
.hd em{margin-left:auto;font-style:normal;color:var(--mut);letter-spacing:.08em;font-weight:500;cursor:default}
.stage{position:relative;display:grid;grid-template-columns:1fr;gap:8px}
#fx{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}
.nodes{position:relative;z-index:1;display:grid;grid-template-columns:repeat(4,1fr);gap:8px}
.nodes button{display:flex;flex-direction:column;align-items:center;gap:5px;padding:9px 4px;border-radius:10px;border:1px solid color-mix(in srgb,var(--c) 40%,#0b1722);background:linear-gradient(180deg,color-mix(in srgb,var(--c) 12%,#0b1722),#09131c);color:var(--c);font:700 9.5px ui-monospace,Menlo,monospace;letter-spacing:.14em;cursor:pointer}
.nodes button svg{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.nodes button:active{transform:scale(.97)}
.oc{position:relative;min-height:290px}
.ctl{position:absolute;left:0;right:0;bottom:4px;display:flex;justify-content:center;gap:10px}
.ctl button{font:700 12px ui-monospace,Menlo,monospace;letter-spacing:.18em;border-radius:10px;padding:12px 22px;cursor:pointer}
#bgo{border:1px solid var(--cy);background:linear-gradient(180deg,#0c4256,#082c3a);color:#a5f3fc;box-shadow:0 0 16px rgba(34,211,238,.25)}
#bstop{border:1px solid #3a2a33;background:#150d13;color:#fda4af}
@media(min-width:640px){.stage{grid-template-columns:150px 1fr;gap:14px}.nodes{grid-template-columns:1fr;align-content:center;gap:12px}.nodes button{flex-direction:row;padding:11px 12px;gap:10px;font-size:10.5px}.oc{min-height:300px}}
#pChat{display:flex;flex-direction:column}
#lg{flex:1;min-height:300px;max-height:58vh;overflow:auto;display:flex;flex-direction:column;gap:8px;padding:2px 2px 8px;font-size:14px;line-height:1.5;scrollbar-width:thin;scrollbar-color:#16364a transparent}
#lg:empty:before{content:"SYSTEM READY\A Aapka personal AI assistant. Bataiye Sir, kya karna hai?";white-space:pre-wrap;text-align:center;color:var(--mut);margin:auto;font-size:12.5px;line-height:1.8}
#lg>div{padding:9px 12px;border-radius:12px;border:1px solid var(--ln);background:#0a1621;word-break:break-word;max-width:94%;align-self:flex-start}
#lg>div>b{display:block;font:700 9.5px ui-monospace,Menlo,monospace;letter-spacing:.16em;text-transform:uppercase;color:var(--mut);margin-bottom:3px}
#lg>.u{align-self:flex-end;background:#0c2a3a;border-color:#155e75}
#lg>.a,#lg>.r{background:#0b1b27}
#lg>.a>b,#lg>.r>b{color:var(--cy)}
#lg>.t{display:none;background:transparent;border-style:dashed;color:var(--mut);font-size:12.5px}
body.dev #lg>.t{display:block}
#lg>.e{border-color:#7f1d3a;background:#1f0b14}
#lg a{color:#67e8f9}
#lg img{max-width:100%;border-radius:10px;margin-top:6px;display:block}
#lg pre{position:relative;background:#050c14;border:1px solid #14455a;border-radius:8px;padding:10px;margin:6px 0;overflow:auto;font:12px ui-monospace,Menlo,monospace;color:#bdeaf5;white-space:pre}
#lg pre code{font:inherit}
#lg .cp{position:absolute;top:4px;right:4px;font:10px system-ui;background:#0c2a3a;border:1px solid #155e75;color:#a5f3fc;border-radius:6px;padding:3px 8px;cursor:pointer}
.ic{background:#0c2230;padding:1px 5px;border-radius:4px;font:12px ui-monospace,monospace;color:#9fe8f5}
.wk{display:inline-block;margin-top:6px;font:500 10.5px ui-monospace,monospace;color:#6d8a99}
.chips{display:flex;gap:6px;overflow-x:auto;padding:2px 0 8px;scrollbar-width:none}
.chip{flex:none;border:1px solid var(--ln);background:#0a1621;color:#9fc3d3;border-radius:999px;padding:6px 11px;font:500 11.5px system-ui;cursor:pointer}
.inp{display:flex;align-items:center;gap:6px;background:#08131c;border:1px solid var(--ln);border-radius:12px;padding:5px}
.inp:focus-within{border-color:var(--cy2);box-shadow:0 0 0 3px rgba(34,211,238,.08)}
#tx{flex:1;min-width:0;background:transparent;border:0;outline:0;color:#fff;font:16px system-ui;padding:8px 6px}
.inp .ib{border:0;background:transparent}
#bsend{background:var(--cy2);color:#fff}
.ap{margin:0 0 8px;padding:10px 12px;border:1px solid #b45309;border-radius:12px;background:linear-gradient(180deg,#2a1d0b,#1c1407)}
.aph{font:700 10px ui-monospace,Menlo,monospace;letter-spacing:.16em;color:#fbbf24;margin-bottom:6px}
#apm{white-space:pre-wrap;font-size:13px;color:#fde7b0;margin-bottom:8px;max-height:140px;overflow:auto}
.apb{display:flex;gap:8px}.apb button{flex:1;padding:10px;border-radius:9px;border:0;font:700 13px system-ui;color:#fff;cursor:pointer}
#apy{background:#059669}#apn{background:#be123c}
#town,#map{width:100%;display:block;image-rendering:pixelated;border-radius:10px;border:1px solid #0f2433;background:#07111a}
.eq{display:flex;align-items:flex-end;gap:3px;height:46px;padding:6px 8px;border:1px solid var(--ln);border-radius:10px;background:#07111a;margin-bottom:10px}
.eq i{flex:1;height:14%;background:linear-gradient(var(--cy),var(--cy2));border-radius:2px;opacity:.35;animation:eq .9s ease-in-out infinite;animation-delay:calc(var(--i)*-.13s);animation-play-state:paused}
body[data-m=live] .eq i{animation-play-state:running;opacity:.85}
body[data-m=think] .eq i{animation-play-state:running;animation-duration:.45s;opacity:1}
@keyframes eq{0%,100%{height:12%}50%{height:95%}}
.kv{display:flex;justify-content:space-between;gap:8px;font:12px ui-monospace,Menlo,monospace;padding:7px 0;border-top:1px solid #0f2433}
.kv span{color:var(--mut)}.kv b{color:#cfe8f1;font-weight:600;text-align:right}
/* activity */
#al{max-height:230px;overflow:auto;display:flex;flex-direction:column;gap:5px;scrollbar-width:thin;scrollbar-color:#16364a transparent}
.ev{display:flex;gap:8px;align-items:flex-start;font-size:12px;line-height:1.4;padding:6px 8px;border-radius:8px;background:#08131c;border:1px solid #0f2433}
.ev>i{flex:none;width:6px;height:6px;border-radius:50%;margin-top:5px}
.ev>div{flex:1;min-width:0;word-break:break-word}
.ev .t{flex:none;font:10px ui-monospace,monospace;color:var(--mut)}
.ev em{font-style:normal;color:#7fb2c7;font-size:11px}.ev small{color:var(--mut)}
.ev.run .ic2{color:var(--cy);animation:bl .6s infinite alternate}.ev.done .ic2{color:var(--ok)}.ev.fail{border-color:#7f1d3a}.ev.fail .ic2{color:var(--er)}.ev.retry .ic2{color:var(--wr)}
.ev.mk{background:transparent;border:0;border-left:2px solid var(--cy2);border-radius:0;color:#9fc3d3;font:600 10.5px ui-monospace,monospace;letter-spacing:.06em;padding:3px 8px}
.emp{color:var(--mut);font-size:12.5px;padding:6px 2px;text-align:center}
/* tasks */
.tk{display:flex;align-items:center;gap:10px;padding:8px;border:1px solid #0f2433;border-radius:10px;background:#08131c;margin-bottom:6px}
.tk>div{flex:1;min-width:0}.tt{font-size:13.5px;word-break:break-word}.tm{font:11px ui-monospace,monospace;color:var(--mut);margin-top:2px}
.tk.sn{border-color:#b45309}.tk.sn .tm{color:#fbbf24}.tk.od{border-color:#7f1d3a}.tk.od .tm{color:#fda4af}.tk.dn .tt{text-decoration:line-through;color:var(--mut)}
.ck{width:24px;height:24px;flex:none;border-radius:7px;border:1.5px solid var(--cy2);background:transparent;color:var(--ok);cursor:pointer;font-size:14px;line-height:1}
.rm{border:0;background:transparent;color:var(--mut);cursor:pointer;font-size:14px;padding:4px}
.tf{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}
.tf input{flex:1 1 140px;min-width:0;background:#08131c;border:1px solid var(--ln);border-radius:8px;color:#fff;padding:8px;font:14px system-ui;color-scheme:dark}
.btn{background:#0c2a3a;border:1px solid #155e75;color:#a5f3fc;border-radius:8px;padding:8px 12px;cursor:pointer;font:600 12.5px system-ui}
.lnk{background:none;border:0;color:#67e8f9;cursor:pointer;font:12px system-ui;padding:8px 0 0}
/* news */
.tabs{display:flex;gap:6px;overflow-x:auto;padding-bottom:8px;scrollbar-width:none}
.tab{flex:none;border:1px solid var(--ln);background:#0a1621;color:#9fc3d3;border-radius:999px;padding:5px 11px;font:500 11.5px system-ui;cursor:pointer}
.tab.on{background:#0c4256;border-color:var(--cy);color:#fff}
#nl{max-height:420px;overflow:auto;scrollbar-width:thin;scrollbar-color:#16364a transparent}
.nw{padding:9px 0;border-top:1px solid #0f2433}.nw:first-child{border-top:0}
.nh{color:#e6f4fa;text-decoration:none;font-size:13.5px;font-weight:600;line-height:1.35;display:block}
.ns{font-size:12px;color:#9fb6c3;margin-top:3px;line-height:1.4;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.nm{font:10.5px ui-monospace,monospace;color:var(--mut);margin-top:4px;display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.nm button{background:none;border:1px solid #14455a;color:#67e8f9;border-radius:6px;padding:2px 8px;font:10.5px system-ui;cursor:pointer}
.sk{height:11px;border-radius:5px;margin:12px 0;background:linear-gradient(90deg,#0f2433,#16384c,#0f2433);background-size:200% 100%;animation:sh 1.6s linear infinite}
@keyframes sh{to{background-position:-200% 0}}
/* sidebar + modal + toasts */
#ov{position:fixed;inset:0;background:rgba(2,6,10,.6);display:none;z-index:20}
#sb{position:fixed;top:0;bottom:0;left:0;width:310px;max-width:88vw;background:#07111a;border-right:1px solid var(--cy2);z-index:21;transform:translateX(-102%);transition:transform .22s;display:flex;flex-direction:column;padding:12px;gap:8px}
#sb.on{transform:none}
.sbh{display:flex;justify-content:space-between;align-items:center;font:700 11px ui-monospace,monospace;letter-spacing:.18em;color:var(--cy)}
#sq,.fl input[type=text],.fl select{background:#08131c;border:1px solid var(--ln);border-radius:8px;color:#fff;padding:9px;font:14px system-ui;width:100%}
#sl{flex:1;overflow:auto;display:flex;flex-direction:column;gap:6px;scrollbar-width:thin}
.si{padding:9px 10px;border:1px solid #0f2433;border-radius:10px;background:#08131c;cursor:pointer;display:flex;gap:6px;align-items:flex-start}
.si.on{border-color:var(--cy)}.si>div{flex:1;min-width:0}
.si b{display:block;font-size:13px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.si small{color:var(--mut);font:10.5px ui-monospace,monospace;display:block;margin-top:2px}
.si button{background:none;border:0;color:var(--mut);cursor:pointer;font-size:13px;padding:2px 4px}
.mod{position:fixed;inset:0;background:rgba(2,6,10,.75);display:none;align-items:center;justify-content:center;padding:14px;z-index:30}
.mb{width:100%;max-width:460px;max-height:86vh;overflow:auto;background:#0a1621;border:1px solid var(--cy2);border-radius:14px;padding:14px;font-size:13.5px;line-height:1.55}
.mh{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;font:700 12px ui-monospace,monospace;letter-spacing:.16em;color:var(--cy)}
.mh button,.mb button.s{background:#0c2a3a;border:1px solid #155e75;color:#a5f3fc;border-radius:8px;padding:8px 12px;cursor:pointer;margin:4px 6px 0 0}
.mb code{display:block;background:#07111a;padding:8px;border-radius:8px;color:#9fe8f5;font-size:12px;margin-top:6px}
.g{margin:8px 0 2px;font:700 10px ui-monospace,monospace;letter-spacing:.14em;color:var(--mut)}
.tg{display:inline-block;margin:3px 4px 0 0;padding:3px 8px;border-radius:6px;background:#0c2230;border:1px solid #14455a;font:11.5px ui-monospace,monospace;color:#9fe8f5}
.st{display:flex;gap:6px;overflow-x:auto;margin-bottom:10px;scrollbar-width:none}
.fl{margin:10px 0}.fl label{display:block;font:600 11px ui-monospace,monospace;letter-spacing:.1em;color:var(--mut);margin-bottom:4px}
.hint{font-size:11.5px;color:var(--mut)}
.row{display:flex;justify-content:space-between;gap:8px;padding:6px 0;border-top:1px solid #0f2433;font-size:12.5px}
.ok{color:var(--ok)}.bad{color:var(--er)}
.toasts{position:fixed;top:10px;left:10px;right:10px;z-index:40;display:flex;flex-direction:column;gap:8px;align-items:center;pointer-events:none}
.toast{pointer-events:auto;max-width:440px;width:100%;background:#1c1407;border:1px solid #b45309;color:#fde7b0;border-radius:12px;padding:10px 12px;font-size:13.5px;display:flex;gap:10px;align-items:center;box-shadow:0 10px 30px rgba(0,0,0,.5)}
.toast.i{background:#0a1621;border-color:var(--cy2);color:var(--tx)}
.toast b{flex:1}.toast button{background:none;border:0;color:inherit;cursor:pointer;font-size:16px}
@media(min-width:1180px){
.app{display:grid;grid-template-columns:310px minmax(0,1fr) 400px;gap:12px;align-items:start}
.top{grid-column:1/-1}.pill{flex:0 1 auto;order:0;max-width:46vw}
.col{display:flex;flex-direction:column;gap:12px}
#pChat{height:calc(100vh - 90px);min-height:640px}
#lg{max-height:none}
}
</style>
<div id="ov"></div>
<aside id="sb"><div class="sbh"><span>CHATS</span><button class="ib" id="sbx" style="width:30px;height:30px">✕</button></div>
<button class="btn" id="snew">＋ New chat</button><input id="sq" placeholder="Search history..." autocomplete="off"><div id="sl"></div></aside>
<div class="toasts" id="toasts"></div>
<div class="app">
<header class="top">
<button class="ib" id="bmenu" title="History"><svg viewBox="0 0 24 24"><path d="M4 6h16M4 12h16M4 18h10"/></svg></button>
<div class="brand"><svg viewBox="0 0 24 24"><path d="M12 2 21 7v10l-9 5-9-5V7z"/><path d="M12 8v8M8 10l4 2 4-2"/></svg><div><b>AXINUS</b><span>EXECUTIVE AI</span></div></div>
<button class="ib" id="bsearch" title="Search everything"><svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg></button>
<button class="ib" id="bset" title="Settings"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M19.1 4.9 17 7M7 17l-2.1 2.1"/></svg></button>
<div class="pill" id="pill" data-m="off"><i></i><span id="st">Status: ready</span></div>
</header>

<div class="col">
<section class="pn" id="pTasks"><div class="hd">TODAY'S TASKS<em id="tcnt">0 pending</em></div><div id="tl"></div>
<div class="tf"><input id="tt" placeholder="New task..." autocomplete="off"><input id="tw" type="datetime-local"><button class="btn" id="tbtn">Add</button></div>
<button class="lnk" id="th">Show history</button></section>
<section class="pn" id="pNews"><div class="hd">NEWS<em id="nref" style="cursor:pointer">↻ refresh</em></div><div class="tabs" id="ntabs"></div><div id="nl"></div><button class="lnk" id="nbrief">▶ Daily Briefing (voice)</button></section>
<section class="pn" id="pMedia"><div class="hd">MEDIA LINK<em id="lk">OFFLINE</em></div>
<div class="eq" id="eq"></div>
<div class="kv"><span>VOICE</span><b>Gemini Live</b></div>
<div class="kv"><span>BRAIN</span><b>Groq · gpt-oss-120b</b></div>
<div class="kv"><span>TOOLS</span><b id="tcn">33 online</b></div>
</section>
<section class="pn" id="pMap"><div class="hd">SAT-LINK FEED<em>placeholder</em></div><canvas id="map" width="300" height="150"></canvas></section>
</div>

<div class="col">
<section class="pn" id="pOrb"><div class="hd">NEURAL CORE<em id="ol">OFFLINE</em></div>
<div class="stage"><canvas id="fx"></canvas>
<nav class="nodes" id="nodes">
<button data-k="memory" style="--c:#22d3ee"><svg viewBox="0 0 24 24"><rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4"/></svg><span>MEMORY</span></button>
<button data-k="skills" style="--c:#fb923c"><svg viewBox="0 0 24 24"><path d="M13 2 4 14h7l-1 8 9-12h-7z"/></svg><span>SKILLS</span></button>
<button data-k="voices" style="--c:#34d399"><svg viewBox="0 0 24 24"><path d="M3 12h2M7 8v8M11 5v14M15 8v8M19 11v2"/></svg><span>VOICES</span></button>
<button data-k="settings" style="--c:#cbd5e1"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M19.1 4.9 17 7M7 17l-2.1 2.1"/></svg><span>SETTING</span></button>
</nav>
<div class="oc" id="oc"><div class="ctl"><button id="bgo">START AI</button><button id="bstop">STOP</button></div></div>
</div></section>
<section class="pn" id="pAct"><div class="hd">ACTIVITY<em id="ac">idle</em></div><div id="al"><div class="emp">Workers ka live kaam yahan dikhega</div></div></section>
<section class="pn" id="pTown"><div class="hd">AGENT TOWN<em id="tc">0/6 busy</em></div><canvas id="town" width="360" height="290"></canvas></section>
</div>

<div class="col">
<section class="pn" id="pChat"><div class="hd">AGENT CONSOLE<em>GROQ BRAIN</em></div>
<div id="ap" class="ap" style="display:none"><div class="aph">APPROVAL REQUIRED</div><div id="apm"></div><div class="apb"><button id="apy">Approve</button><button id="apn">Deny</button></div></div>
<div id="lg"></div>
<div class="chips"><button class="chip" data-q="Abhi ka time batao">Time</button><button class="chip" data-q="Mere pending tasks batao">Tasks</button><button class="chip" data-q="Daily briefing do">Briefing</button><button class="chip" data-q="Aaj ka gold rate batao">Gold rate</button></div>
<div class="inp"><button class="ib" id="bup" title="Attach file"><svg viewBox="0 0 24 24"><path d="M21 11.5 12.5 20a5 5 0 0 1-7-7l9-9a3.3 3.3 0 0 1 4.7 4.7l-9 9a1.7 1.7 0 0 1-2.4-2.4l8-8"/></svg></button><input id="tx" placeholder="Type instruction or command..." autocomplete="off"><button class="ib" id="bsend" title="Send"><svg viewBox="0 0 24 24"><path d="M12 19V5M5 12l7-7 7 7"/></svg></button></div>
<input type="file" id="fi" accept="image/*,application/pdf,video/*" style="display:none">
</section>
</div>
</div>
<div class="mod" id="mod"><div class="mb"><div class="mh"><b id="mt"></b><button id="mx">✕</button></div><div id="mc"></div></div></div>
<script>__OLD__</script>
<script>
(function(){
const $=id=>document.getElementById(id);
const E=s=>String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let act={},run={},mode='off',curSid=null,EVLOG=[];
const WC={brain:'#22d3ee',coder:'#4da3ff',reason:'#c084fc',eyes:'#f472b6',mail:'#fbbf24',research:'#34d399',utils:'#fb923c'};
const api=async(n,a)=>{try{const r=await fetch('/api/'+n,{method:'POST',headers:{'Content-Type':'application/json','X-Pin':localStorage.getItem('pin')||''},body:JSON.stringify({args:a||[]})});if(r.status===401)return{error:'Wrong PIN'};return await r.json();}catch(e){return{error:String(e)};}};
const ls=(k,d)=>{try{const v=localStorage.getItem(k);return v==null?d:v;}catch(e){return d;}};
const ss=(k,v)=>{try{localStorage.setItem(k,v);}catch(e){}};
function toast(h,cls,ms){const t=document.createElement('div');t.className='toast '+(cls||'');t.innerHTML='<b>'+h+'</b><button>✕</button>';t.querySelector('button').onclick=()=>t.remove();$('toasts').appendChild(t);if(ms!==0)setTimeout(()=>t.remove(),ms||7000);}
/* ---------- formatter (replaces old formatText) ---------- */
window.AXFMT=function(t){t=String(t==null?'':t);const bl=[];
t=t.replace(/```(\w*)\n?([\s\S]*?)```/g,(m,l,c)=>{bl.push(c);return '\u0001B'+(bl.length-1)+'\u0001';});
t=E(t).replace(/`([^`\n]+)`/g,'<code class="ic">$1</code>').replace(/\*\*([^*\n]+)\*\*/g,'<b>$1</b>');
t=t.replace(/(^|\n)— Workers: ([^\n]*)/,'$1<span class="wk">⚙ $2</span>');
t=t.replace(/https?:\/\/[^\s<]+/g,function(u){
if(u.indexOf('https://image.pollinations.ai/')===0||/\/f\?p=[^&\s]+\.(png|jpe?g)/i.test(u))return '<br><img src="'+u+'" loading="lazy"><br>';
if(/\/f\?p=[^&\s]+\.pdf/i.test(u))return '<a href="'+u+'" target="_blank" rel="noopener">📄 Open PDF</a>';
return '<a href="'+u+'" target="_blank" rel="noopener">▶ Open Link / Media</a>';});
t=t.replace(/\n/g,'<br>');
return t.replace(/\u0001B(\d+)\u0001/g,(m,i)=>'<pre><button class="cp">Copy</button><code>'+E(bl[i].replace(/\n$/,''))+'</code></pre>');};
document.addEventListener('click',e=>{const b=e.target.closest&&e.target.closest('.cp');if(b){try{navigator.clipboard.writeText(b.nextElementSibling.textContent);}catch(x){}b.textContent='Copied';setTimeout(()=>b.textContent='Copy',1200);}});
/* ---------- status + bubble tagging ---------- */
const LB={off:'OFFLINE',live:'ONLINE',think:'THINKING',wait:'LINKING',err:'ALERT'};
function sm(){const t=$('st').textContent.toLowerCase();mode=/running|thinking/.test(t)?'think':/error|fail|disconn|timeout/.test(t)?'err':/live|ready sir/.test(t)?'live':/connect|token|upload|ws/.test(t)?'wait':'off';document.body.dataset.m=mode;$('ol').textContent=LB[mode];$('lk').textContent=LB[mode];$('pill').dataset.m=mode;
if(/disconn/.test(t)&&window.__conn&&Date.now()-window.__conn.t<5000&&window.__conn.v){ss('axvoice','');toast('Ye voice model support nahi kar raha. Default voice par wapas.','i');window.__conn=null;}}
new MutationObserver(sm).observe($('st'),{childList:true,characterData:true,subtree:true});sm();
let rf=null;
new MutationObserver(ms=>{ms.forEach(m=>m.addedNodes.forEach(n=>{if(n.nodeType!==1||n.className)return;const b=(n.querySelector('b')||{}).textContent||'';n.className=/^Tum/.test(b)?'u':/^Axinus/.test(b)?'a':/Task/.test(b)?'t':/Result/.test(b)?'r':/❌/.test(b)?'e':'';}));clearTimeout(rf);rf=setTimeout(()=>{loadSess($('sq').value);loadTasks();},1800);}).observe($('lg'),{childList:true});
document.querySelectorAll('.chip').forEach(b=>b.onclick=()=>send(b.dataset.q));
function send(q){$('tx').value=q;$('bsend').click();}
let eh='';for(let i=0;i<18;i++)eh+='<i style="--i:'+i+'"></i>';$('eq').innerHTML=eh;
/* ---------- pulse: workers, events, alerts ---------- */
let evLast=-1,alLast=parseInt(ls('axal','-1'),10);const rows={};
function addEv(e){EVLOG.push(e);if(EVLOG.length>120)EVLOG.shift();const L=$('al');if(L.querySelector('.emp'))L.innerHTML='';let el=rows[e.k];
if(e.s==='mark'){el=document.createElement('div');el.className='ev mk';el.innerHTML='<span class="t">'+e.t+'</span> '+E(e.m);L.prepend(el);}
else{if(!el){el=document.createElement('div');rows[e.k]=el;L.prepend(el);}
const ic={run:'▶',done:'✓',fail:'✗',retry:'↻'}[e.s]||'•',c=WC[e.w]||'#9fc3d3';el.className='ev '+e.s;
el.innerHTML='<i style="background:'+c+'"></i><div><b style="color:'+c+'">'+E(e.n)+'</b> <span class="ic2">'+ic+'</span> '+E(e.m)+(e.model?' <em>'+E(e.model)+'</em>':'')+(e.ms?' <small>'+(e.ms/1000).toFixed(1)+'s</small>':'')+(document.body.classList.contains('dev')&&e.tool?' <small>['+E(e.tool)+']</small>':'')+'</div><span class="t">'+e.t+'</span>';}
while(L.children.length>40)L.lastChild.remove();}
async function pulse(){const r=await api('pulse',[evLast,alLast]);if(!r||r.error)return;act={};(r.active||[]).forEach(k=>act[k]=1);run=r.running||{};
if(evLast<0){evLast=r.last;}else{(r.events||[]).forEach(addEv);evLast=r.last;}
const n=Object.keys(run).length;$('ac').textContent=n?n+' running':'idle';$('tc').textContent=['coder','reason','eyes','mail','research','utils'].filter(k=>act[k]).length+'/6 busy';
if(alLast<0){alLast=r.al_last;ss('axal',alLast);}else{(r.alerts||[]).forEach(onAlert);if(r.al_last>alLast){alLast=r.al_last;ss('axal',alLast);}}}
setInterval(pulse,700);
/* ---------- reminders ---------- */
function beep(){try{const c=new AudioContext(),o=c.createOscillator(),g=c.createGain();o.frequency.value=880;g.gain.value=.15;o.connect(g);g.connect(c.destination);o.start();setTimeout(()=>{o.frequency.value=1175;},180);setTimeout(()=>{o.stop();c.close();},380);}catch(e){}}
function speak(m){try{const w=window.AXWS&&window.AXWS();if(w&&w.ws&&w.ws.readyState===1&&w.ready){w.ws.send(JSON.stringify({clientContent:{turns:[{role:'user',parts:[{text:'SYSTEM REMINDER. Tell Sir this in one short sentence: '+m}]}],turnComplete:true}}));return;}}catch(e){}
try{const u=new SpeechSynthesisUtterance('Sir, '+m);u.lang='en-IN';speechSynthesis.speak(u);}catch(e){}}
function onAlert(a){toast('⏰ '+E(a.text),'',0);beep();try{navigator.vibrate&&navigator.vibrate([200,100,200]);}catch(e){}
try{if(window.Notification&&Notification.permission==='granted')new Notification('AXINUS',{body:a.text});}catch(e){}
speak(a.text);loadTasks();}
/* ---------- tasks ---------- */
let tasks=[],hist=false;
function rel(d){const now=new Date(),df=d-now,m=Math.round(df/6e4),t=d.toLocaleTimeString([],{hour:'numeric',minute:'2-digit'}),day=d.toDateString()===now.toDateString()?'Today':new Date(now.getTime()+864e5).toDateString()===d.toDateString()?'Tomorrow':d.toLocaleDateString([],{day:'numeric',month:'short'});
return day+' '+t+(m>0&&m<90?' · in '+m+' min':m<=0&&m>-600?' · overdue':'');}
function renderTasks(){const now=Date.now();const sel=tasks.filter(t=>hist?(t.status==='done'||t.status==='missed'):t.status==='pending').sort((a,b)=>a.due<b.due?-1:1);
$('tcnt').textContent=tasks.filter(t=>t.status==='pending').length+' pending';
$('tl').innerHTML=sel.length?sel.map(t=>{const d=new Date(t.due),df=d-now,c=t.status!=='pending'?'dn':df<0?'od':df<9e5?'sn':'';return '<div class="tk '+c+'" data-id="'+t.id+'"><button class="ck" data-a="done">'+(t.status==='done'?'✓':'')+'</button><div><div class="tt">'+E(t.title)+'</div><div class="tm">'+rel(d)+(t.status==='missed'?' · missed':'')+'</div></div><button class="rm" data-a="del">✕</button></div>';}).join(''):'<div class="emp">'+(hist?'History khaali hai':'Koi pending task nahi. Axinus ko bolo ya neeche add karo.')+'</div>';}
async function loadTasks(){const r=await api('task_list');if(r&&!r.error){tasks=r.tasks||[];renderTasks();}}
$('tl').onclick=async e=>{const b=e.target.closest('button'),row=e.target.closest('.tk');if(!b||!row)return;if(b.dataset.a==='done')await api('task_done',[row.dataset.id]);else if(confirm('Delete task?'))await api('task_del',[row.dataset.id]);loadTasks();};
async function addTask(){const t=$('tt').value.trim(),w=$('tw').value;if(!t||!w){toast('Task aur time dono daalo','i');return;}const r=await api('task_add_ui',[t,w]);if(r&&r.ok){$('tt').value='';toast('Task saved. 15 min pehle alert aayega.','i');loadTasks();}else toast(E((r&&r.error)||'Task save nahi hua'),'i');}
$('tbtn').onclick=addTask;$('tt').onkeydown=e=>{if(e.key==='Enter')addTask();};
$('th').onclick=()=>{hist=!hist;$('th').textContent=hist?'Show pending':'Show history';renderTasks();};
setInterval(loadTasks,30000);
/* ---------- news ---------- */
const CATS=[['top','Top India'],['tech','Tech'],['ai','AI'],['science','Science'],['business','Business'],['world','World']];let ncat='top';
$('ntabs').innerHTML=CATS.map(c=>'<button class="tab'+(c[0]===ncat?' on':'')+'" data-c="'+c[0]+'">'+c[1]+'</button>').join('');
$('ntabs').onclick=e=>{const b=e.target.closest('.tab');if(!b)return;ncat=b.dataset.c;document.querySelectorAll('.tab').forEach(x=>x.classList.toggle('on',x===b));loadNews(false);};
async function loadNews(force){$('nl').innerHTML='<div class="sk"></div><div class="sk"></div><div class="sk"></div>';const r=await api('news',[ncat,!!force]);
if(!r||r.error||!(r.items||[]).length){$('nl').innerHTML='<div class="emp">News abhi nahi mil payi. Thodi der baad refresh karo.</div>';return;}
$('nl').innerHTML=(r.stale?'<div class="emp">Purani cache dikha raha hoon</div>':'')+r.items.slice(0,8).map(x=>'<div class="nw"><a class="nh" href="'+E(x.link)+'" target="_blank" rel="noopener">'+E(x.title)+'</a>'+(x.summary?'<div class="ns">'+E(x.summary)+'</div>':'')+'<div class="nm"><span>'+E(x.source)+(x.date?' · '+E(x.date):'')+'</span><button data-l="'+E(x.link)+'">Explain</button></div></div>').join('');}
$('nl').onclick=e=>{const b=e.target.closest('button');if(b)send('Is article ko padho aur 3 lines me samjhao: '+b.dataset.l);};
$('nref').onclick=()=>loadNews(true);$('nbrief').onclick=()=>send('Daily briefing do');
/* ---------- history sidebar ---------- */
const sb=$('sb'),ov=$('ov');
function openSb(){sb.classList.add('on');ov.style.display='block';loadSess($('sq').value);}function closeSb(){sb.classList.remove('on');ov.style.display='none';}
$('bmenu').onclick=openSb;$('sbx').onclick=closeSb;ov.onclick=closeSb;
function tfmt(s){try{return new Date(s).toLocaleString([],{day:'numeric',month:'short',hour:'numeric',minute:'2-digit'});}catch(e){return s;}}
async function loadSess(q){const r=await api('sess_list',[q||'']);if(!r||r.error)return;curSid=r.cur;
$('sl').innerHTML=(r.items||[]).length?r.items.map(i=>'<div class="si'+(i.id===curSid?' on':'')+'" data-id="'+i.id+'"><div><b>'+E(i.title)+'</b><small>'+tfmt(i.updated)+' · '+i.n+' msgs</small>'+(i.snip?'<small>…'+E(i.snip)+'…</small>':'')+'</div><button data-a="ren" title="Rename">✎</button><button data-a="del" title="Delete">🗑</button></div>').join(''):'<div class="emp">Koi chat nahi mili</div>';}
let sqt=null;$('sq').oninput=()=>{clearTimeout(sqt);sqt=setTimeout(()=>loadSess($('sq').value),250);};
function showMsgs(ms){const L=$('lg');L.innerHTML='';(ms||[]).forEach(m=>{const d=document.createElement('div');d.className=m.role==='user'?'u':'a';d.innerHTML='<b>'+(m.role==='user'?'Tum':'Axinus')+' · '+tfmt(m.ts)+'</b>'+window.AXFMT(m.content);L.appendChild(d);});L.scrollTop=1e9;}
async function openSess(id){const r=await api('sess_open',[id]);if(r&&!r.error){curSid=r.id;showMsgs(r.messages);}}
$('sl').onclick=async e=>{const row=e.target.closest('.si');if(!row)return;const id=row.dataset.id,b=e.target.closest('button');
if(b&&b.dataset.a==='ren'){const t=prompt('New name?',row.querySelector('b').textContent);if(t){await api('sess_rename',[id,t]);loadSess($('sq').value);}return;}
if(b&&b.dataset.a==='del'){if(confirm('Ye chat delete karni hai?')){await api('sess_delete',[id]);if(id===curSid)$('lg').innerHTML='';loadSess($('sq').value);}return;}
await openSess(id);closeSb();};
$('snew').onclick=async()=>{await api('sess_new');$('lg').innerHTML='';curSid=null;closeSb();};
window.__voiceLog=(i,o)=>{const c=x=>(x||'').replace(/^(Tum|Axinus):\s*/,'').trim();if(c(i))api('sess_log',['user',c(i)]);if(c(o))api('sess_log',['assistant',c(o)]);};
/* ---------- voice settings (applied by patched old script) ---------- */
const VOICES=['Puck','Charon','Kore','Fenrir','Aoede','Leda','Orus','Zephyr'];
const vol=()=>Math.max(0,Math.min(1,parseInt(ls('axvol','100'),10)/100));
window.AXSETUP=S=>{const c=JSON.parse(JSON.stringify(S)),v=ls('axvoice','');if(v)c.setup.generationConfig.speechConfig={voiceConfig:{prebuiltVoiceConfig:{voiceName:v}}};
const pc=ls('axpace','n'),lg=ls('axlang','auto');let x='';if(pc==='s')x+=' Speak slowly and clearly.';if(pc==='f')x+=' Speak at a brisk pace.';if(lg==='en')x+=' Always speak English with an Indian accent.';if(lg==='hi')x+=' Reply in simple Hindi (Hinglish) only.';
if(x)c.setup.systemInstruction.parts[0].text+='\n'+x;window.__conn={t:Date.now(),v:v};return c;};
window.AXGAIN=ctx=>{if(!ctx.__g){const g=ctx.createGain();g.gain.value=vol();g.connect(ctx.destination);ctx.__g=g;window.__gain=g;}return ctx.__g;};
$('bgo').addEventListener('click',()=>{try{if(window.Notification&&Notification.permission==='default')Notification.requestPermission();}catch(e){}});
async function preview(v){const r=await api('voice_preview',[v||'Kore']);if(!r||r.error){toast(E((r&&r.error)||'Preview fail'),'i',9000);return;}
try{const b=atob(r.pcm),u=new Uint8Array(b.length);for(let i=0;i<b.length;i++)u[i]=b.charCodeAt(i);const n=u.length>>1,dv=new DataView(u.buffer),c=new AudioContext({sampleRate:r.rate||24000}),buf=c.createBuffer(1,n,r.rate||24000),ch=buf.getChannelData(0);for(let i=0;i<n;i++)ch[i]=dv.getInt16(i*2,true)/32768;const s=c.createBufferSource(),g=c.createGain();g.gain.value=vol();s.buffer=buf;s.connect(g);g.connect(c.destination);s.start();}catch(e){toast('Preview play fail','i');}}
/* ---------- modal: node info, settings, search ---------- */
const G={Coder:['qwen_vibe_coder','run_code','make_diagram'],Reasoner:['sambanova_heavy_reasoning'],Vision:['analyze_image','analyze_pdf','analyze_video','generate_image'],'Mail / Notes':['send_corporate_email','save_smart_note','make_quiz','send_whatsapp','add_task','list_tasks','complete_task','delete_task','remember_fact','recall_facts','manage_contact','read_note','list_notes'],Research:['tavily_live_search','youtube_search','read_webpage','search_drive','get_news','daily_briefing'],Utils:['get_datetime','read_csv','make_pdf','make_rich_pdf','read_doc'],Core:['image_report (multi-worker pipeline)']};
const mod=$('mod');function openMod(t,h){$('mt').textContent=t;$('mc').innerHTML=h;mod.style.display='flex';}
$('mx').onclick=()=>{mod.style.display='none';};mod.onclick=e=>{if(e.target===mod)mod.style.display='none';};
const INFO={memory:['MEMORY',()=>'<p>Chats, tasks, notes aur remembered facts Drive me save hote hain:</p><code>MyDrive/AXINUS_SYSTEM/memory</code><div id="fx2"></div>'],
skills:['SKILLS',()=>Object.keys(G).map(k=>'<div class="g">'+k.toUpperCase()+'</div>'+G[k].map(x=>'<span class="tg">'+x+'</span>').join('')).join('')],
voices:['VOICES',()=>'<p>Voice: Gemini Live. Brain: Groq. Backups: SambaNova, Cohere, Gemini.</p><p>Voice change karne ke liye Settings kholo.</p>'],
settings:['SETTINGS',()=>'']};
document.querySelectorAll('#nodes button').forEach(b=>b.onclick=()=>{const k=b.dataset.k;if(k==='settings'||k==='voices'){settings(k==='voices'?'voice':'voice');return;}openMod(INFO[k][0],INFO[k][1]());if(k==='memory')api('facts_list').then(r=>{if(r&&r.facts)$('fx2').innerHTML='<div class="g">REMEMBERED FACTS</div>'+(r.facts.length?r.facts.map(f=>'<div class="row"><span>'+E(f.text)+'</span><button class="s" data-f="'+f.id+'">✕</button></div>').join(''):'<div class="emp">Koi fact nahi. Axinus ko bolo "yaad rakho ..."</div>');});});
$('mc').addEventListener('click',async e=>{const f=e.target.closest('[data-f]');if(f){await api('forget_fact',[f.dataset.f]);f.closest('.row').remove();}});
const TABS=[['voice','Voice'],['usage','Agents & Usage'],['security','Security'],['dev','Developer'],['export','Export'],['diag','Diagnose']];
function settings(tab){tab=tab||'voice';openMod('SETTINGS','<div class="st">'+TABS.map(t=>'<button class="tab'+(t[0]===tab?' on':'')+'" data-t="'+t[0]+'">'+t[1]+'</button>').join('')+'</div><div id="sbody"></div>');
$('mc').querySelector('.st').onclick=e=>{const b=e.target.closest('.tab');if(b)settings(b.dataset.t);};TAB[tab]();}
const TAB={
voice(){const v=ls('axvoice',''),p=ls('axpace','n'),l=ls('axlang','auto');
$('sbody').innerHTML='<div class="fl"><label>VOICE</label><select id="sv"><option value="">Default (model voice)</option>'+VOICES.map(x=>'<option'+(x===v?' selected':'')+'>'+x+'</option>').join('')+'</select><button class="s" id="svp">▶ Preview</button></div><div class="fl"><label>VOLUME <span id="svo">'+Math.round(vol()*100)+'%</span></label><input type="range" id="svr" min="0" max="100" value="'+Math.round(vol()*100)+'" style="width:100%"></div><div class="fl"><label>SPEAKING PACE (best effort)</label><select id="ssp"><option value="n"'+(p==='n'?' selected':'')+'>Normal</option><option value="s"'+(p==='s'?' selected':'')+'>Slower</option><option value="f"'+(p==='f'?' selected':'')+'>Faster</option></select></div><div class="fl"><label>LANGUAGE</label><select id="slg"><option value="auto"'+(l==='auto'?' selected':'')+'>Auto (English + Hinglish)</option><option value="en"'+(l==='en'?' selected':'')+'>English (India)</option><option value="hi"'+(l==='hi'?' selected':'')+'>Hindi / Hinglish</option></select></div><p class="hint">Voice, pace aur language agle CONNECT par apply hote hain, volume turant. Agar model kisi voice ko support na kare to AXINUS khud default par wapas aa jata hai.</p>';
$('sv').onchange=()=>ss('axvoice',$('sv').value);$('svp').onclick=()=>preview($('sv').value||'Kore');$('ssp').onchange=()=>ss('axpace',$('ssp').value);$('slg').onchange=()=>ss('axlang',$('slg').value);
$('svr').oninput=()=>{ss('axvol',$('svr').value);$('svo').textContent=$('svr').value+'%';if(window.__gain)window.__gain.gain.value=vol();};},
async usage(){$('sbody').innerHTML='<div class="emp">Loading...</div>';const r=await api('stats');if(!r||r.error){$('sbody').innerHTML='<div class="emp">Stats nahi mile</div>';return;}
const p=r.perf||{},u=r.usage||{};$('sbody').innerHTML='<div class="g">WORKER SUCCESS</div>'+(Object.keys(p).length?Object.keys(p).map(k=>{const x=p[k],t=x.ok+x.fail,pc=t?Math.round(100*x.ok/t):0;return '<div class="row"><span>'+E(k)+'</span><span class="'+(pc>=80?'ok':'bad')+'">'+pc+'% · '+x.ok+'/'+t+' · '+(x.avg_ms/1000).toFixed(1)+'s avg</span></div>';}).join(''):'<div class="emp">Abhi koi kaam nahi hua</div>')+'<div class="g">API USAGE (this session)</div><div class="row"><span>Groq calls / tokens</span><span>'+u.groq_calls+' / '+(u.groq_in+u.groq_out)+'</span></div><div class="row"><span>SambaNova calls</span><span>'+u.samba_calls+'</span></div><div class="row"><span>Tool calls / retries</span><span>'+u.tool_calls+' / '+u.retries+'</span></div><div class="row"><span>Est. cost (set prices)</span><span>$'+r.cost+'</span></div><div class="fl"><label>PRICE per 1M tokens: input / output (USD)</label><input type="text" id="pi" value="'+r.prices.in+'" style="width:45%"> <input type="text" id="po" value="'+r.prices.out+'" style="width:45%"><button class="s" id="ps">Save</button></div>';
$('ps').onclick=async()=>{await api('set_prices',[$('pi').value,$('po').value]);TAB.usage();};},
security(){$('sbody').innerHTML='<div class="row"><span>PIN protection</span><span class="ok">ON</span></div><div class="row"><span>File access</span><span>Google Drive only</span></div><div class="row"><span>Upload limit</span><span>30 MB</span></div><div class="row"><span>Approval needed for</span><span>email, WhatsApp, notes, contacts, make_pdf</span></div><div class="row"><span>File links</span><span>signed, tamper-proof</span></div><div class="row"><span>Web content</span><span>treated as untrusted</span></div><div class="row"><span>Code changes</span><span>never automatic</span></div><button class="s" id="rp">Reset PIN</button><button class="s" id="cl">Clear chat view</button>';
$('rp').onclick=()=>{try{localStorage.removeItem('pin');}catch(e){}location.reload();};$('cl').onclick=()=>{$('lg').innerHTML='';mod.style.display='none';};},
dev(){const on=document.body.classList.contains('dev');$('sbody').innerHTML='<div class="fl"><label><input type="checkbox" id="dv"'+(on?' checked':'')+'> Developer mode (tool names, task bubbles)</label></div><button class="s" id="dc">Copy last 100 events</button>';
$('dv').onchange=()=>{document.body.classList.toggle('dev',$('dv').checked);ss('axdev',$('dv').checked?'1':'0');};$('dc').onclick=()=>{try{navigator.clipboard.writeText(JSON.stringify(EVLOG,null,1));toast('Copied','i',2000);}catch(e){}};},
async export(){$('sbody').innerHTML='<div class="emp">Loading...</div>';const f=await api('files_list');$('sbody').innerHTML='<div class="g">CURRENT CHAT</div><button class="s" data-x="md">Export .md</button><button class="s" data-x="json">Export .json</button><div class="g">RECENT FILES (reports, notes, exports)</div>'+((f&&f.files||[]).map(x=>'<div class="row"><a href="'+E(x.link)+'" target="_blank" style="color:#67e8f9">'+E(x.name)+'</a></div>').join('')||'<div class="emp">Abhi koi file nahi</div>');
$('sbody').onclick=async e=>{const b=e.target.closest('[data-x]');if(!b)return;if(!curSid){toast('Pehle koi chat kholo','i');return;}const r=await api('export_chat',[curSid,b.dataset.x]);if(r&&r.ok)window.open(r.link,'_blank');else toast('Export fail','i');};},
diag(){$('sbody').innerHTML='<button class="s" id="d1">Quick check</button><button class="s" id="d2">Deep test (calls APIs)</button><div id="dr"></div>';
const go=async d=>{$('dr').innerHTML='<div class="emp">Running... (deep test me ~1 min lag sakta hai)</div>';const r=await api('diagnose',[d]);$('dr').innerHTML=(r&&r.checks||[]).map(c=>'<div class="row"><span class="'+(c.ok?'ok':'bad')+'">'+(c.ok?'✓':'✗')+' '+E(c.name)+'</span><span style="text-align:right;max-width:55%">'+E(c.detail)+'</span></div>').join('')||'<div class="emp">Fail</div>';};
$('d1').onclick=()=>go(false);$('d2').onclick=()=>go(true);}};
$('bset').onclick=()=>settings('voice');
$('bsearch').onclick=()=>{openMod('SEARCH EVERYTHING','<input id="uq" type="text" placeholder="chats, notes, reports, tasks, facts..." style="width:100%;background:#08131c;border:1px solid #16364a;border-radius:8px;color:#fff;padding:10px;font:14px system-ui"><div id="ur"></div>');let t=null;$('uq').oninput=()=>{clearTimeout(t);t=setTimeout(async()=>{const r=await api('usearch',[$('uq').value]);$('ur').innerHTML=((r&&r.items)||[]).map(i=>'<div class="row" style="flex-direction:column"><b>'+({chat:'💬',note:'📝',report:'📄',task:'⏰',fact:'🧠'}[i.type]||'')+' '+E(i.title)+'</b>'+(i.snip?'<small style="color:#6d8a99">'+E(i.snip)+'</small>':'')+(i.type==='chat'?'<button class="s" data-o="'+i.ref+'">Open chat</button>':/^http/.test(i.ref||'')?'<a href="'+E(i.ref)+'" target="_blank" style="color:#67e8f9">Open file</a>':'')+'</div>').join('')||'<div class="emp">Kuch nahi mila</div>';},300);};$('uq').focus();};
$('mc').addEventListener('click',async e=>{const o=e.target.closest('[data-o]');if(o){await openSess(o.dataset.o);mod.style.display='none';}});
/* ---------- canvases ---------- */
function fit(c){const r=c.getBoundingClientRect(),d=Math.min(devicePixelRatio||1,2),w=Math.round(r.width*d),h=Math.round(r.height*d);if(c.width!==w||c.height!==h){c.width=w;c.height=h;}const x=c.getContext('2d');x.setTransform(d,0,0,d,0,0);return[x,r.width,r.height];}
function pathPt(P,f){let L=0;const s=[];for(let i=1;i<P.length;i++){const d=Math.hypot(P[i][0]-P[i-1][0],P[i][1]-P[i-1][1]);s.push(d);L+=d;}let t=f*L;for(let i=0;i<s.length;i++){if(t<=s[i]){const k=s[i]?t/s[i]:0;return[P[i][0]+(P[i+1][0]-P[i][0])*k,P[i][1]+(P[i+1][1]-P[i][1])*k];}t-=s[i];}return P[P.length-1];}
const fx=$('fx'),oc=$('oc'),nodes=[...document.querySelectorAll('#nodes button')],NC=nodes.map(n=>n.style.getPropertyValue('--c').trim());
const PT=[];for(let i=0;i<260;i++){const y=1-2*(i+.5)/260,r=Math.sqrt(1-y*y),a=i*2.399963;PT.push([Math.cos(a)*r,y,Math.sin(a)*r]);}
const MC={off:'#4b6b80',live:'#22d3ee',think:'#34d399',wait:'#fbbf24',err:'#f43f5e'};
function drawFx(t){const[c,w,h]=fit(fx),cr=fx.getBoundingClientRect(),or=oc.getBoundingClientRect();c.clearRect(0,0,w,h);
const R=Math.min(78,or.width*.27),ox=or.left-cr.left+or.width/2,oy=or.top-cr.top+or.height*.42,col=MC[mode],busy=mode==='think'||act.brain,sp=busy?2.6:1;
nodes.forEach((n,i)=>{const nr=n.getBoundingClientRect(),side=nr.right<ox+cr.left-R-20,o=(i-1.5)*12,q=Math.sqrt(Math.max(R*R-o*o,1));let P;
if(side){const sx=nr.right-cr.left,sy=nr.top-cr.top+nr.height/2,ex=ox-q,ey=oy+o;P=[[sx,sy],[sx+26,sy],[ex-30,ey],[ex,ey]];}
else{const sx=nr.left-cr.left+nr.width/2,sy=nr.bottom-cr.top,ex=ox+o,ey=oy-q;P=[[sx,sy],[sx,sy+12],[ex,Math.min(ey-20,sy+30)],[ex,ey]];}
c.globalAlpha=.5;c.strokeStyle=NC[i];c.lineWidth=1.4;c.beginPath();P.forEach((p,j)=>j?c.lineTo(p[0],p[1]):c.moveTo(p[0],p[1]));c.stroke();
const d=pathPt(P,((t*.22*sp)+i*.23)%1);c.globalAlpha=1;c.fillStyle=NC[i];c.shadowColor=NC[i];c.shadowBlur=10;c.beginPath();c.arc(d[0],d[1],2.6,0,6.283);c.fill();c.shadowBlur=0;});
const g=c.createRadialGradient(ox,oy,R*.2,ox,oy,R*1.5);g.addColorStop(0,col);g.addColorStop(1,col+'00');c.globalAlpha=.2;c.fillStyle=g;c.fillRect(ox-R*1.6,oy-R*1.6,R*3.2,R*3.2);
const a=t*.45*sp,ca=Math.cos(a),sa=Math.sin(a),ct=Math.cos(.35),st=Math.sin(.35);c.fillStyle=col;
PT.forEach((p,k)=>{const x=p[0]*ca+p[2]*sa,z=-p[0]*sa+p[2]*ca,y2=p[1]*ct-z*st,z2=p[1]*st+z*ct,s=R*(1+(busy?Math.sin(t*3+k)*.03:0)),z3=(z2+1)/2;c.globalAlpha=.2+.8*z3;c.fillRect(ox+x*s-1,oy+y2*s-1,1.2+z3*1.6,1.2+z3*1.6);});
c.strokeStyle=col;c.lineWidth=1;c.globalAlpha=.55;c.beginPath();c.ellipse(ox,oy,R*1.12,R*.3,-.5+t*.2*sp,0,6.283);c.stroke();c.beginPath();c.ellipse(ox,oy,R*1.12,R*.3,.5-t*.15*sp,0,6.283);c.stroke();
c.globalAlpha=.35;c.beginPath();c.arc(ox,oy,R*.55,0,6.283);c.stroke();
if(busy){const ph=(t*.8)%1;c.globalAlpha=.5*(1-ph);c.beginPath();c.arc(ox,oy,R*(1+ph*.5),0,6.283);c.stroke();}
c.globalAlpha=1;c.shadowColor=col;c.shadowBlur=16;c.fillStyle=col;c.beginPath();c.arc(ox,oy,3+Math.sin(t*3*sp)*1.2,0,6.283);c.fill();c.shadowBlur=0;
c.globalAlpha=.85;c.fillStyle=col;c.font='10px ui-monospace,monospace';c.textAlign='center';c.fillText(String(run.brain?run.brain.msg:LB[mode]).slice(0,34).toUpperCase(),ox,oy+R*1.38);c.globalAlpha=1;}
const W=[['coder','CODER','#4da3ff','#3b2a1a'],['reason','REASONER','#c084fc','#e5e7eb'],['eyes','VISION','#f472b6','#5b3a1a'],['mail','MAIL·NOTES','#fbbf24','#1f1f2b'],['research','RESEARCH','#34d399','#7c3f1d'],['utils','UTILS','#fb923c','#2b2b2b']];
const tc=$('town'),tg=tc.getContext('2d');tg.imageSmoothingEnabled=false;
const R_=(x,y,w,h,c)=>{tg.fillStyle=c;tg.fillRect(Math.round(x),Math.round(y),w,h);};
const CX=[[0,14],[120,14],[240,14],[0,172],[120,172],[240,172]];let cour={x:210,y:140};
function cub(i,x,y,t){const w=W[i],on=act[w[0]],col=w[2],sk='#f2c9a0';
R_(x+4,y,112,94,'#0f1d2e');tg.globalAlpha=.4;R_(x+4,y,112,1,col);tg.globalAlpha=1;R_(x+2,y,2,94,'#1f3450');R_(x+116,y,2,94,'#1f3450');
R_(x+14,y+36,92,16,'#2c3d58');R_(x+14,y+36,92,2,'#476184');R_(x+14,y+50,92,2,'#1a2638');
if(on){tg.shadowColor=col;tg.shadowBlur=14;}R_(x+40,y+12,40,26,'#070d17');tg.shadowBlur=0;R_(x+43,y+15,34,18,on?'#04231b':'#0a1522');
if(on){for(let k=0;k<4;k++){const ww=6+(Math.sin(t*5+k*1.9+i)*.5+.5)*22;R_(x+45,y+17+k*4,ww,2,k%2?col:'#34d399');}}else{R_(x+46,y+18,12,2,'#1f3a55');R_(x+46,y+23,20,2,'#162b40');if((t*2|0)%2)R_(x+46,y+28,4,2,'#4b6b80');}
R_(x+57,y+38,6,3,'#1a2638');R_(x+46,y+43,28,5,'#0a1220');if(on)for(let k=0;k<5;k++)if(((t*14+k*3)|0)%3==0)R_(x+48+k*5,y+44,3,2,col);
R_(x+78,y+13,2,2,on?'#34d399':'#7f1d1d');
if(i%3==0){R_(x+8,y+80,8,7,'#5b3a29');R_(x+6,y+72,12,9,'#1f7a4d');R_(x+9,y+68,6,6,'#2ea06a');}
if(i%3==2){R_(x+104,y+80,8,7,'#5b3a29');R_(x+102,y+72,12,9,'#1f7a4d');R_(x+105,y+68,6,6,'#2ea06a');}
R_(x+46,y+54,28,22,'#16233a');R_(x+46,y+54,28,3,'#22344f');R_(x+54,y+75,5,6,'#18263c');R_(x+61,y+75,5,6,'#18263c');
const b=on?Math.sin(t*14+i):Math.sin(t*1.8+i)*.6,ah=on?Math.sin(t*18+i)*2:0;
R_(x+44,y+47+ah,5,13,col);R_(x+71,y+47-ah,5,13,col);R_(x+44,y+45+ah,5,3,sk);R_(x+71,y+45-ah,5,3,sk);
R_(x+49,y+58+b,22,16,col);R_(x+49,y+58+b,22,2,'rgba(255,255,255,.18)');R_(x+54,y+46+b,12,12,sk);R_(x+53,y+44+b,14,10,w[3]);R_(x+52,y+51+b,2,3,sk);R_(x+66,y+51+b,2,3,sk);
if(on){R_(x+84,y+4,22,12,'#e6f6ff');R_(x+86,y+16,3,3,'#e6f6ff');for(let k=0;k<3;k++)R_(x+88+k*5,y+9+(Math.sin(t*8+k)>0?-1:0),3,3,'#0b1220');}
else{tg.globalAlpha=.6;tg.fillStyle='#6d8a99';tg.font='bold 9px monospace';tg.textAlign='left';tg.fillText('z',x+84,y+30-((t*6+i*3)%10));tg.globalAlpha=1;}
tg.textAlign='center';tg.font='bold 9px monospace';tg.fillStyle=on?col:'#6d8a99';tg.fillText(w[1],x+60,y+90);
tg.font='8px monospace';tg.fillStyle=on?'#b6f5d8':'#44607a';const rr=run[w[0]];tg.fillText(String(rr?rr.msg:'idle').slice(0,22),x+60,y+101);}
function hub(t){const br=act.brain||mode==='think',c=br?'#34d399':'#22d3ee';R_(150,128,60,18,'#26384f');R_(150,128,60,2,'#46607f');R_(150,144,60,2,'#17243a');
tg.save();tg.globalAlpha=.22+.12*Math.sin(t*3);tg.fillStyle=c;tg.beginPath();tg.ellipse(180,124,22,7,0,0,7);tg.fill();tg.restore();
const r=br?6+Math.sin(t*8)*1.5:5,yy=116+Math.sin(t*2)*1.5;
if(br){tg.strokeStyle=c;tg.globalAlpha=.5;for(let k=0;k<6;k++){const a=k*1.047+t*2;tg.beginPath();tg.moveTo(180+Math.cos(a)*9,yy+Math.sin(a)*9);tg.lineTo(180+Math.cos(a)*16,yy+Math.sin(a)*16);tg.stroke();}tg.globalAlpha=1;}
tg.shadowColor=c;tg.shadowBlur=12;tg.fillStyle=c;tg.beginPath();tg.arc(180,yy,r,0,7);tg.fill();tg.shadowBlur=0;tg.textAlign='center';tg.font='8px monospace';tg.fillStyle='#6d8a99';tg.fillText('AXINUS CORE',180,160);}
function courier(t,dt){let tgt=[222,142],go=false;for(let i=0;i<6;i++)if(act[W[i][0]]){tgt=[CX[i][0]+60,CX[i][1]<100?118:164];go=true;break;}
const dx=tgt[0]-cour.x,dy=tgt[1]-cour.y,d=Math.hypot(dx,dy),mv=d>1.5;if(mv){const s=Math.min(d,60*dt);cour.x+=dx/d*s;cour.y+=dy/d*s;}
const bob=mv?Math.abs(Math.sin(t*14))*1.5:0,x=Math.round(cour.x),y=Math.round(cour.y);
R_(x-4,y+9,9,2,'#050a10');R_(x-4,y+2-bob,8,7,'#dbeafe');R_(x-3,y-5-bob,6,6,'#cfe3ea');R_(x-2,y-3-bob,4,2,'#22d3ee');
const lg=mv&&((t*10|0)%2);R_(x-3,y+9-(lg?1:0),2,2,'#7da0b8');R_(x+1,y+9-(lg?0:1),2,2,'#7da0b8');if(mv&&go)R_(x+4,y+2-bob,4,3,'#fbbf24');}
function town(t,dt){R_(0,0,360,290,'#0a1420');for(let y=0;y<290;y+=12)for(let x=0;x<360;x+=12)if(((x+y)/12)%2==0)R_(x,y,12,12,'#0c1826');
R_(0,0,360,12,'#17283d');R_(0,12,360,2,'#0b1624');for(let x=14;x<350;x+=58){R_(x,2,28,7,'#1f4466');R_(x,2,28,2,'#2f6a93');}
R_(0,112,360,58,'#0e1c2c');R_(0,111,360,1,'#1d3a56');R_(0,170,360,1,'#1d3a56');for(let x=0;x<360;x+=16)R_(x,140,8,1,'#1b3550');
for(let i=0;i<6;i++)cub(i,CX[i][0],CX[i][1],t);hub(t);courier(t,dt);}
const mp=$('map'),mg=mp.getContext('2d'),base=document.createElement('canvas');base.width=300;base.height=150;
(function(){const b=base.getContext('2d'),E2=[[.2,.35,.13,.2],[.28,.72,.05,.17],[.5,.28,.06,.09],[.52,.6,.07,.18],[.7,.35,.17,.17],[.84,.74,.05,.06]];b.fillStyle='#07111a';b.fillRect(0,0,300,150);b.fillStyle='#0d2233';for(let x=0;x<300;x+=25)b.fillRect(x,0,1,150);for(let y=0;y<150;y+=25)b.fillRect(0,y,300,1);
b.fillStyle='#0f766e';for(let x=3;x<300;x+=5)for(let y=3;y<150;y+=5){const u=x/300,v=y/150;if(E2.some(e=>((u-e[0])/e[2])**2+((v-e[1])/e[3])**2<1))b.fillRect(x,y,2,2);}})();
const M=[[.18,.3],[.49,.25],[.55,.55],[.7,.3],[.78,.4],[.3,.7]];
function map(t){mg.drawImage(base,0,0);M.forEach((m,i)=>{mg.globalAlpha=.4+.6*(Math.sin(t*3+i)+1)/2;mg.fillStyle='#f59e0b';mg.fillRect(m[0]*300-2,m[1]*150-2,4,4);});mg.globalAlpha=1;
const sx=(t*45)%330,gr=mg.createLinearGradient(sx-30,0,sx,0);gr.addColorStop(0,'rgba(34,211,238,0)');gr.addColorStop(1,'rgba(34,211,238,.28)');mg.fillStyle=gr;mg.fillRect(sx-30,0,30,150);mg.fillStyle='#3b6176';mg.font='9px monospace';mg.textAlign='left';mg.fillText('NO FEED · map module pending',8,142);}
let last=0;function f(ms){const t=ms/1000,dt=Math.min(.05,Math.max(0,(ms-last)/1000));last=ms;try{drawFx(t);town(t,dt);map(t);}catch(e){}requestAnimationFrame(f);}requestAnimationFrame(f);
/* ---------- boot ---------- */
if(ls('axdev','0')==='1')document.body.classList.add('dev');
(async()=>{await openSess(null);loadSess('');loadTasks();loadNews(false);pulse();})();
})();
</script>
"""

NEW_INV = """const PIN=localStorage.getItem('pin')||prompt('AXINUS PIN?')||'';localStorage.setItem('pin',PIN);
const inv=async(n,a)=>{try{const r=await fetch('/api/'+n,{method:'POST',headers:{'Content-Type':'application/json','X-Pin':PIN},body:JSON.stringify({args:a||[]})});if(r.status===401){localStorage.removeItem('pin');return{error:'Wrong PIN, app dobara kholo'};}return await r.json();}catch(e){return{error:String(e)};}};
"""

def build_old_js(page):
    warn = []
    js = re.search(r"<script>(.*)</script>", page, re.S).group(1)
    js = re.sub(r"const inv=async[^\n]*\n", lambda m: NEW_INV, js)
    def rep(a, b, name):
        nonlocal js
        if a in js: js = js.replace(a, b)
        else: warn.append(name)
    rep("ws.send(JSON.stringify(SETUP))", "ws.send(JSON.stringify(window.AXSETUP?window.AXSETUP(SETUP):SETUP))", "voice-setup")
    rep("s.connect(ctxOut.destination)", "s.connect(window.AXGAIN?window.AXGAIN(ctxOut):ctxOut.destination)", "volume")
    rep("const cur={in:null,out:null};", "const cur={in:null,out:null};window.AXWS=()=>({ws:ws,ready:ready});", "ws-expose")
    rep("if(sc.turnComplete){cur.in=null;cur.out=null;}", "if(sc.turnComplete){try{window.__voiceLog&&window.__voiceLog(cur.in&&cur.in.textContent,cur.out&&cur.out.textContent);}catch(e){}cur.in=null;cur.out=null;}", "voice-log")
    rep("function formatText(t){", "function formatText(t){return window.AXFMT?window.AXFMT(t):__f0(t);}\nfunction __f0(t){", "formatter")
    assert "invokeFunction" not in js, "UI patch fail (invokeFunction)"
    return js, warn

print("✅ ax4 UI OK | ui chars:", len(UI_BODY))
