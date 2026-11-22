# AXINUS 8 - workspace shell (Claude-style): drawer sidebar, home + composer, "+" sheet, voice screen with AXINUS core, settings list, Code / Projects / Artifacts / News / Maps / Tasks / PDF
import re, json
IC = {"menu": '<path d="M4 8h16M4 16h11"/>', "search": '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>', "compose": '<path d="M12 5H6a2 2 0 0 0-2 2v11a2 2 0 0 0 2 2h11a2 2 0 0 0 2-2v-6M17.5 3.5a2.1 2.1 0 0 1 3 3L11 16l-4 1 1-4z"/>',
      "proj": '<rect x="4" y="9" width="16" height="11" rx="2"/><path d="M7 6h10M9.5 3h5"/>', "code": '<path d="m8 7-5 5 5 5M16 7l5 5-5 5"/>', "art": '<path d="M7 4h10a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z"/><path d="M9 4v16M13 9h3"/>',
      "news": '<rect x="3.5" y="4.5" width="17" height="15" rx="2"/><path d="M7 9h6M7 13h10M7 16h10"/>', "map": '<path d="M9 4 3.5 6v14L9 18l6 2 5.5-2V4L15 6zM9 4v14M15 6v14"/>', "task": '<path d="M9 6h11M9 12h11M9 18h11"/><path d="m3.5 6 1.2 1.2L6.8 5M3.5 12l1.2 1.2L6.8 11M3.5 18l1.2 1.2L6.8 17"/>', "pdf": '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8zM14 3v5h5M9 14h6M9 17h4"/>',
      "set": '<circle cx="12" cy="12" r="3"/><path d="M12 3v2.5M12 18.5V21M3 12h2.5M18.5 12H21M5.6 5.6l1.8 1.8M16.6 16.6l1.8 1.8M18.4 5.6l-1.8 1.8M7.4 16.6l-1.8 1.8"/>', "plus": '<path d="M12 5v14M5 12h14"/>', "mic": '<rect x="9" y="3" width="6" height="12" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3"/>', "micoff": '<path d="M9 9V6a3 3 0 0 1 5.5-1.7M15 10v1a3 3 0 0 1-4.5 2.6M5 11a7 7 0 0 0 11 5.7M19 11a7 7 0 0 1-.5 2.6M12 18v3M3 3l18 18"/>',
      "send": '<path d="M12 19V5M5.5 11.5 12 5l6.5 6.5"/>', "x": '<path d="M6 6l12 12M18 6 6 18"/>', "chev": '<path d="m9 6 6 6-6 6"/>', "chat": '<path d="M20 12a8 8 0 0 1-11.5 7.2L4 20.5l1.3-4.2A8 8 0 1 1 20 12z"/>',
      "cam": '<path d="M4 8h3l1.5-2h7L17 8h3v11H4z"/><circle cx="12" cy="13.5" r="3.5"/>', "img": '<rect x="4" y="4" width="16" height="16" rx="2"/><circle cx="9" cy="9.5" r="1.5"/><path d="m20 16-5-5-9 9"/>', "file": '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8zM14 3v5h5M12 17v-5M9.5 14.5 12 12l2.5 2.5"/>',
      "hand": '<path d="M8 12V6.5a1.5 1.5 0 0 1 3 0V11M11 10V5a1.5 1.5 0 0 1 3 0v6M14 10V6.5a1.5 1.5 0 0 1 3 0V14a6 6 0 0 1-6 6h-.5a5 5 0 0 1-4-2L4 14.5a1.5 1.5 0 0 1 2.4-1.8L8 14"/>', "conn": '<rect x="4" y="4" width="7" height="7" rx="1.5"/><rect x="13" y="13" width="7" height="7" rx="1.5"/><path d="M15 4h5v5M9 20H4v-5"/>', "skill": '<path d="M13 3 5 14h6l-1 7 8-11h-6z"/>',
      "copy": '<rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"/>', "retry": '<path d="M20 11a8 8 0 1 0-2.3 5.7M20 4v7h-7"/>', "spk": '<path d="M4 10v4h4l5 4V6L8 10zM16.5 9a4 4 0 0 1 0 6M19 6.5a7.5 7.5 0 0 1 0 11"/>', "edit": '<path d="M4 20h4L19 9a2.8 2.8 0 0 0-4-4L4 16z"/>', "sel": '<path d="M5 7h14M5 12h14M5 17h8"/>',
      "user": '<circle cx="12" cy="8" r="3.5"/><path d="M5 20a7 7 0 0 1 14 0"/>', "brain": '<path d="M9.5 3A3.5 3.5 0 0 0 6 6.5v.3A3.5 3.5 0 0 0 4 10a3.5 3.5 0 0 0 1 2.4A3.5 3.5 0 0 0 6 18.5 3.5 3.5 0 0 0 9.5 21c1.4 0 2.5-.9 2.5-2V5c0-1.1-1.1-2-2.5-2zM14.5 3C13.1 3 12 3.9 12 5v14c0 1.1 1.1 2 2.5 2a3.5 3.5 0 0 0 3.5-2.5 3.5 3.5 0 0 0 1-6.1A3.5 3.5 0 0 0 18 6.8v-.3A3.5 3.5 0 0 0 14.5 3z"/>',
      "wave": '<path d="M4 12h2M8 8v8M12 5v14M16 8v8M20 11v2"/>', "type": '<path d="M5 7V5h14v2M12 5v14M9 19h6"/>', "gauge": '<path d="M4 17a8 8 0 1 1 16 0M12 17l4-5"/>', "lock": '<rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>', "dev": '<path d="m8 8-4 4 4 4M16 8l4 4-4 4M13.5 5l-3 14"/>', "exp": '<path d="M12 3v12M7 8l5-5 5 5M5 14v5h14v-5"/>', "diag": '<path d="M3 12h4l2-6 4 12 2-6h6"/>', "phone": '<rect x="7" y="3" width="10" height="18" rx="2"/><path d="M11 18h2"/>', "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v5.5M12 7.8h.01"/>'}
def _i(k, cls="ix"): return '<svg class="' + cls + '" viewBox="0 0 24 24">' + IC[k] + '</svg>'
MARK = '<svg viewBox="0 0 64 64" fill="currentColor"><path d="M32 5 5 59h13l4.2-9.5h19.6L46 59h13z M27.5 40 32 29.5 36.5 40z" fill-rule="evenodd"/></svg>'
SH_CSS = open(__file__.replace("ax8_shell.py", "ax8_shell.css")).read() if False else r"""html[data-theme=ax]{--bg:#1a1918;--card:#242321;--s1:#262523;--s2:#30302d;--ln:#3a3937;--ln2:#4b4946;--acc:#ece9e3;--accT:#171615;--orb:#ece9e3;--me:#ece9e3;--tx:#ece9e3;--mut:#a39e96;--in:#1f1e1c;--ok:#86b890;--wr:#d4aa66;--er:#d98577;--serif:ui-serif,'Iowan Old Style',Georgia,'Noto Serif','Times New Roman',serif;--sans:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif}
html[data-theme=ax] body{background:var(--bg);color:var(--tx);font-family:var(--sans)}
body.sans{--serif:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif}
header.top,#bsearch,.bot,#sb,#ov,#pTown,#pAct,#pSet,#pMedia,#pOrb{display:none!important}
.pn{display:none!important;background:none!important;border:0!important;box-shadow:none!important;padding:0!important;border-radius:0!important}
body[data-pg=code] #pCode,body[data-pg=projects] #pProj,body[data-pg=studio] #pArt,body[data-pg=access] #pAcc,body[data-pg=chats] #pChats,body[data-pg=settings] #pStg,body[data-pg=tasks] #pTasks,body[data-pg=pdf] #pPdf,body[data-pg=news] #pNews,body[data-pg=map] #pMap{display:block!important}
body[data-pg=chat] #pChat,body:not([data-pg]) #pChat{display:flex!important}
.app{display:block!important;max-width:760px;margin:0 auto;padding:70px 16px 48px}
body[data-pg=chat] .app,body:not([data-pg]) .app{padding:0;max-width:none}
.hd{font:500 24px var(--serif)!important;letter-spacing:0!important;text-transform:none!important;color:var(--tx)!important;margin:2px 0 16px!important}.hd:before{display:none!important}.hd em{font:13px var(--sans)!important;color:var(--mut)!important}
.mod{z-index:120!important}.mod .mb{background:var(--s1)!important;border:1px solid var(--ln2)!important;border-radius:18px!important;box-shadow:none!important}
.toasts{z-index:130}
#nov{position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:58;display:none}body.sbo #nov{display:block}
#nsb{position:fixed;inset:0 auto 0 0;width:min(320px,86vw);z-index:60;transform:translateX(-104%);transition:transform .22s;background:var(--bg);border-right:1px solid var(--ln);display:flex;flex-direction:column;padding:14px 12px 12px}
body.sbo #nsb{transform:none}
.nh{display:flex;align-items:center;padding:4px 8px 14px}.nh b{font:500 26px var(--serif);letter-spacing:.01em;flex:1}.nh button{background:none;border:0;color:var(--tx);padding:6px;cursor:pointer}.nh svg{width:22px;height:22px}
svg.ix{fill:none;stroke:currentColor;stroke-width:1.6;stroke-linecap:round;stroke-linejoin:round}
.ni{display:flex;align-items:center;gap:14px;width:100%;text-align:left;padding:11px 10px;border-radius:10px;border:0;background:none;color:var(--tx);font:500 16px var(--sans);cursor:pointer}
.ni svg{width:21px;height:21px;flex:none;color:var(--tx)}.ni.on,.ni:active{background:var(--s1)}
.nsep{height:1px;background:var(--ln);margin:10px 8px}
.nlb{font:500 14px var(--sans);color:var(--mut);padding:6px 10px}
#nrc{overflow:auto}#nrc .rc{display:flex;align-items:center;gap:12px;width:100%;text-align:left;border:0;background:none;color:var(--tx);font:15.5px var(--sans);padding:10px;border-radius:10px;cursor:pointer;white-space:nowrap}#nrc .rc span{overflow:hidden;text-overflow:ellipsis}#nrc .rc svg{width:16px;height:16px;flex:none;color:var(--mut)}#nrc .rc:active{background:var(--s1)}
.nva{color:var(--mut)!important;font-size:14.5px!important}
.nfl{flex:1}
.nbot{display:flex;align-items:center;justify-content:space-between;padding:10px 4px 0}
.cbtn{width:44px;height:44px;border-radius:50%;border:1px solid var(--ln2);background:var(--s1);color:var(--tx);display:grid;place-items:center;cursor:pointer}.cbtn svg{width:21px;height:21px}
.pill2{display:flex;align-items:center;gap:8px;height:44px;padding:0 18px;border-radius:22px;border:0;background:var(--tx);color:var(--accT);font:600 15px var(--sans);cursor:pointer}.pill2 svg{width:18px;height:18px}
#ntop{position:fixed;top:0;left:0;right:0;height:54px;z-index:40;display:flex;align-items:center;gap:8px;padding:0 8px;background:var(--bg)}
#ntop button{width:42px;height:42px;border:0;background:none;color:var(--tx);border-radius:10px;display:grid;place-items:center;cursor:pointer}#ntop button svg{width:23px;height:23px}#ntop button:active{background:var(--s1)}
#ntt{flex:1;text-align:center;font:500 16px var(--sans);overflow:hidden;white-space:nowrap;text-overflow:ellipsis}
@media(min-width:1000px){#nsb{transform:none}#nov{display:none!important}#ntop,#pChat{left:320px!important}.app{margin-left:320px!important;margin-right:0!important;max-width:none!important;padding-left:40px;padding-right:40px}.app>section{max-width:780px}#nhb{visibility:hidden}}
#pChat{position:fixed;top:54px;left:0;right:0;bottom:0;flex-direction:column;background:var(--bg)}
#wlc{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:20px;padding:0 24px 40px;text-align:center}
#wlc svg{width:46px;height:46px;color:var(--tx)}#wlc h1{margin:0;font:400 clamp(28px,7vw,38px)/1.2 var(--serif);color:var(--tx)}#wlc p{margin:0;color:var(--mut);font:15px var(--sans)}
body.hasmsg #wlc{display:none}body:not(.hasmsg) #lg{display:none!important}
#pChat #lg{flex:1;min-height:0;overflow-y:auto;width:100%;max-width:760px;margin:0 auto;padding:10px 16px 18px;display:flex;flex-direction:column;gap:16px;font:16.5px/1.65 var(--serif);-webkit-user-select:text;user-select:text}
#pChat #lg>div{padding:0;border:0;background:none;border-radius:0;color:var(--tx);align-self:stretch}
#pChat #lg>div>b:first-child{display:none}
#pChat #lg>.u{align-self:flex-end;max-width:86%;background:var(--s1);padding:10px 15px;border-radius:18px;font:16px/1.5 var(--sans);-webkit-touch-callout:none;-webkit-user-select:none;user-select:none}
#pChat #lg>.t{display:none}body.dev #pChat #lg>.t{display:block;font:12.5px var(--sans);color:var(--mut)}
#pChat #lg>.r{font:13.5px/1.5 var(--sans);color:var(--mut);border-left:2px solid var(--ln2);padding-left:12px}
#pChat #lg>.e{font:14.5px var(--sans);color:var(--er)}
#lg a{color:var(--tx);text-decoration:underline;text-decoration-color:var(--ln2)}
#lg pre{position:relative;background:var(--in);border:1px solid var(--ln);border-radius:12px;padding:12px;margin:10px 0;overflow:auto;font:13px/1.55 ui-monospace,Menlo,Consolas,monospace;color:var(--tx)}
#lg code{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.88em}#lg pre .cp,#lg pre .sv{position:absolute;top:6px;font:12px var(--sans);padding:3px 9px;border-radius:8px;border:1px solid var(--ln2);background:var(--s1);color:var(--tx);cursor:pointer}#lg pre .cp{right:6px}#lg pre .sv{right:62px}
#lg table{border-collapse:collapse;font:14px var(--sans)}#lg td,#lg th{border:1px solid var(--ln);padding:5px 9px}
.tbr{display:flex;gap:2px;margin:-8px 0 0 -8px}.tbr button{width:36px;height:34px;border:0;background:none;color:var(--mut);display:grid;place-items:center;cursor:pointer;border-radius:8px}.tbr button svg{width:18px;height:18px}.tbr button:active{background:var(--s1);color:var(--tx)}
#lact{display:none;max-width:728px;width:calc(100% - 32px);margin:0 auto 8px;border:1px solid var(--ln);border-radius:14px;background:var(--s1);overflow:hidden}#lact.on{display:block}
#lact .h{display:flex;align-items:center;gap:10px;padding:10px 14px;cursor:pointer;font:14px var(--sans);color:var(--tx)}#lact .h i{width:8px;height:8px;border-radius:50%;background:var(--tx);animation:bl .8s infinite alternate;flex:none}#lact .h em{margin-left:auto;font-style:normal;color:var(--mut);font-size:12.5px}
#lact .st{display:none;padding:0 14px 10px;max-height:180px;overflow:auto}#lact.open .st{display:block}#lact .st div{font:13px var(--sans);color:var(--mut);padding:3px 0 3px 10px;border-left:2px solid var(--ln2);margin:4px 0}#lact .st .done{border-color:var(--ok)}#lact .st .fail{border-color:var(--er);color:var(--er)}
.inp,.inp:focus-within{display:block;border:0;border-radius:0;gap:0;}.inp{width:100%;max-width:760px;margin:0 auto;padding:4px 12px calc(8px + env(safe-area-inset-bottom));background:var(--bg);position:relative}
#edb{display:none;align-items:center;gap:8px;padding:6px 14px;font:13px var(--sans);color:var(--mut)}#edb.on{display:flex}#edb button{margin-left:auto;background:none;border:0;color:var(--mut);cursor:pointer}
.cbox{border:1px solid var(--ln2);border-radius:26px;background:var(--s1);padding:10px 10px 8px 14px}
.cbox textarea{display:block;width:100%;background:none;border:0;outline:0;resize:none;color:var(--tx);font:16.5px/1.45 var(--sans);text-transform:none;letter-spacing:0;max-height:170px;min-height:28px;padding:6px 2px}.cbox textarea::placeholder{color:var(--mut)}
.crow{display:flex;align-items:center;gap:4px;margin-top:2px}.crow .sp{flex:1}
.cib{width:40px;height:40px;border:0;background:none;color:var(--tx);border-radius:50%;display:grid;place-items:center;cursor:pointer}.cib svg{width:23px;height:23px}.cib:active{background:var(--s2)}
#bsend{width:38px;height:38px;border-radius:50%;border:0;background:var(--s2);color:var(--mut);display:grid;place-items:center;cursor:pointer;margin-left:2px}#bsend svg{width:20px;height:20px}body.hastx #bsend{background:var(--tx);color:var(--accT)}
.cfoot{text-align:center;font:11.5px var(--sans);color:var(--mut);padding:7px 0 0}
#psh{position:fixed;inset:0;z-index:80;display:none;background:rgba(0,0,0,.5);align-items:flex-end;justify-content:center}#psh.on{display:flex}
#psp{width:100%;max-width:560px;max-height:88vh;overflow:auto;background:var(--s1);border-radius:22px 22px 0 0;padding:8px 14px 18px}
.grab{width:38px;height:4px;border-radius:2px;background:var(--ln2);margin:4px auto 10px}
.pshh{display:flex;align-items:center;justify-content:center;position:relative;font:500 16px var(--sans);padding:6px 0 12px}.pshh button{position:absolute;left:0;background:none;border:0;color:var(--tx);cursor:pointer;padding:6px}.pshh svg{width:22px;height:22px}
.tiles{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:12px}.tile{display:flex;flex-direction:column;align-items:center;gap:8px;padding:16px 4px;border-radius:14px;background:var(--s2);border:0;color:var(--tx);font:14px var(--sans);cursor:pointer}.tile svg{width:24px;height:24px}
.lst{background:var(--s2);border-radius:14px;overflow:hidden;margin-bottom:12px}
.row{display:flex;align-items:center;gap:14px;width:100%;text-align:left;padding:13px 14px;border:0;background:none;color:var(--tx);font:16px var(--sans);cursor:pointer;border-bottom:1px solid var(--ln)}.lst .row:last-child{border-bottom:0}
.row svg.ix{width:21px;height:21px;flex:none}.row small{display:block;color:var(--mut);font-size:13.5px;margin-top:1px}.row .ch{margin-left:auto;width:16px;height:16px;color:var(--mut)}.row .tg{margin-left:auto;color:var(--mut);font-size:13px}
#pChat .chips,#psp .chips{display:flex;flex-wrap:wrap;gap:8px;margin:4px 0 0}#psp .chip{background:var(--s2);border:1px solid var(--ln);color:var(--tx);border-radius:18px;padding:8px 13px;font:14px var(--sans);text-transform:none;letter-spacing:0}
#lpm{position:fixed;z-index:90;display:none;min-width:210px;background:var(--s1);border:1px solid var(--ln2);border-radius:14px;padding:6px;box-shadow:0 10px 30px rgba(0,0,0,.5)}#lpm.on{display:block}#lpm button{display:flex;align-items:center;gap:12px;width:100%;padding:11px 12px;border:0;background:none;color:var(--tx);font:15.5px var(--sans);border-radius:9px;cursor:pointer;text-align:left}#lpm button:active{background:var(--s2)}#lpm svg{width:19px;height:19px}
#vo{position:fixed;inset:0;z-index:100;background:var(--bg);display:none;flex-direction:column;align-items:center}#vo.on{display:flex}
#vo .vt{align-self:stretch;display:flex;justify-content:flex-end;padding:10px}#vo .vt button{width:42px;height:42px;border:0;background:none;color:var(--tx);cursor:pointer;display:grid;place-items:center}#vo .vt svg{width:23px;height:23px}
#vmid{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;padding:0 24px;text-align:center;width:100%;max-width:520px}
#vcv{width:260px;height:260px}#vgr{font:400 28px var(--serif)}#vst{font:14.5px var(--sans);color:var(--mut)}
#vtr{font:15.5px/1.5 var(--serif);color:var(--mut);max-height:96px;overflow:hidden;margin-top:6px}#vtr div{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;margin:3px 0}
#vmic{width:64px;height:64px;border-radius:50%;border:1px solid var(--ln2);background:var(--s1);color:var(--tx);display:grid;place-items:center;cursor:pointer;margin:6px auto 22px}#vmic svg{width:26px;height:26px}body.vlive #vmic{background:var(--tx);color:var(--accT)}
#vbar{align-self:stretch;display:flex;align-items:center;justify-content:space-between;padding:0 16px calc(18px + env(safe-area-inset-bottom))}
.chip2{display:flex;align-items:center;gap:6px;height:38px;padding:0 16px;border-radius:19px;background:var(--s1);border:1px solid var(--ln);font:500 14.5px var(--sans);color:var(--tx)}
#vx{width:46px;height:46px;border-radius:50%;border:0;background:var(--tx);color:var(--accT);display:grid;place-items:center;cursor:pointer}#vx svg{width:22px;height:22px}
.sub{font:500 13.5px var(--sans);color:var(--mut);margin:18px 2px 8px}
.fi3{width:100%;background:var(--in);border:1px solid var(--ln);color:var(--tx);border-radius:12px;padding:11px 12px;font:15px var(--sans);text-transform:none;letter-spacing:0}
.btn3{padding:10px 15px;border-radius:12px;border:1px solid var(--ln2);background:var(--s1);color:var(--tx);font:500 14.5px var(--sans);cursor:pointer;text-transform:none;letter-spacing:0}.btn3.p{background:var(--tx);border-color:var(--tx);color:var(--accT)}.btn3.d{color:var(--er)}.btn3:disabled{opacity:.5}
.row3{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:10px}.card3{border:1px solid var(--ln);border-radius:14px;background:var(--s1);padding:13px 15px;margin-bottom:10px}.card3 b{font-weight:600}.card3 small{color:var(--mut);display:block;margin-top:3px}
.stt{display:flex;align-items:center;gap:10px;padding:12px 14px;border:1px solid var(--ln);border-radius:12px;margin-bottom:8px;background:var(--s1)}.stt i{width:9px;height:9px;border-radius:50%;background:var(--er);flex:none}.stt.ok i{background:var(--ok)}.stt span{margin-left:auto;color:var(--mut);font-size:13.5px;text-align:right}
#csf{display:flex;gap:6px;overflow:auto;padding-bottom:6px;margin-bottom:8px}#csf button{flex:none;padding:7px 12px;border-radius:9px;border:1px solid var(--ln);background:var(--s1);color:var(--tx);font:13px ui-monospace,Menlo,monospace;cursor:pointer;text-transform:none}#csf button.on{background:var(--tx);color:var(--accT)}
#cse{width:100%;min-height:300px;background:var(--in);border:1px solid var(--ln);border-radius:12px;color:var(--tx);font:13px/1.55 ui-monospace,Menlo,Consolas,monospace;padding:12px;resize:vertical;tab-size:2;white-space:pre;text-transform:none}
#cso{background:var(--in);border:1px solid var(--ln);border-radius:12px;padding:10px;font:12.5px/1.5 ui-monospace,Menlo,monospace;color:var(--tx);white-space:pre-wrap;max-height:240px;overflow:auto;display:none}#csprev{width:100%;height:360px;border:1px solid var(--ln);border-radius:12px;background:#fff;display:none}
.agr{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px}.agr .card3{cursor:pointer;margin:0}.tagk{display:inline-block;font:500 11.5px var(--sans);padding:2px 8px;border-radius:7px;background:var(--s2);color:var(--mut);margin-bottom:6px}
#dlgw{position:fixed;inset:0;z-index:125;background:rgba(0,0,0,.55);display:none;align-items:center;justify-content:center;padding:16px}#dlgw.on{display:flex}#dlg{width:min(480px,100%);max-height:88vh;overflow:auto;border:1px solid var(--ln2);border-radius:18px;background:var(--s1);padding:18px}#dlg h3{margin:0 0 12px;font:500 19px var(--serif)}#dlg p{color:var(--mut);line-height:1.55;font-size:14.5px}
#avw{position:fixed;inset:0;z-index:92;background:var(--bg);display:none;flex-direction:column}#avw.on{display:flex}#avw .h{display:flex;align-items:center;gap:8px;padding:10px 12px;border-bottom:1px solid var(--ln)}#avw .h b{flex:1;font:500 15px var(--sans);overflow:hidden;white-space:nowrap;text-overflow:ellipsis}#avb{flex:1;overflow:auto;padding:12px}#avb iframe{width:100%;height:100%;border:0;background:#fff;border-radius:10px}#avb pre{white-space:pre-wrap;font:13px/1.55 ui-monospace,Menlo,monospace}
.srow{display:flex;align-items:center;gap:14px;padding:14px;width:100%;border:0;border-bottom:1px solid var(--ln);background:none;color:var(--tx);font:16px var(--sans);text-align:left;cursor:pointer}.srow:last-child{border-bottom:0}.srow svg{width:21px;height:21px;flex:none}.srow small{display:block;color:var(--mut);font-size:13.5px;margin-top:1px}
body.hasmsg #pChats #sl .si{background:none}
#pChats #sq{width:100%;background:var(--in);border:1px solid var(--ln);color:var(--tx);border-radius:12px;padding:11px 12px;font:15px var(--sans);margin-bottom:10px}
#pChats #sl .si{display:flex;align-items:center;gap:6px;padding:11px 12px;border:0;border-bottom:1px solid var(--ln);border-radius:0;background:none;cursor:pointer}#pChats #sl .si>div{flex:1;min-width:0}#pChats #sl .si b{font:500 15.5px var(--sans);color:var(--tx);display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}#pChats #sl .si small{display:block;color:var(--mut);font-size:12.5px}#pChats #sl .si button{background:none;border:0;color:var(--mut);padding:6px;cursor:pointer}
#tx::placeholder{text-transform:none!important;font-size:inherit!important;letter-spacing:0!important;color:var(--mut)!important}
#pChat #lg b,#pChat #lg>div>b:not(:first-child){display:inline!important;text-transform:none!important;font:inherit!important;font-weight:700!important;letter-spacing:0!important;color:inherit!important;margin:0!important}
#pChat #lg b:before{content:none!important}
#csai{flex:1 1 100%!important}
#pChat #lg>div>b:first-child{display:none!important}
"""
SH_HTML = ('<div id="nov"></div><aside id="nsb"><div class="nh"><b>AXINUS</b><button id="nsrch" title="Search">' + _i("search") + '</button></div>'
  + "".join('<button class="ni" data-go="%s">%s<span>%s</span></button>' % (k, _i(ic), n) for k, ic, n in [("projects", "proj", "Projects"), ("code", "code", "Code"), ("studio", "art", "Artifacts")])
  + '<div class="nsep"></div>'
  + "".join('<button class="ni" data-go="%s">%s<span>%s</span></button>' % (k, _i(ic), n) for k, ic, n in [("news", "news", "India News"), ("map", "map", "Maps"), ("tasks", "task", "Tasks"), ("pdf", "pdf", "PDF Studio")])
  + '<div class="nsep"></div><div class="nlb">Recents</div><div id="nrc"></div><button class="ni nva" id="nva">View all' + _i("chev") + '</button><div class="nfl"></div>'
  + '<div class="nbot"><button class="cbtn" data-go="settings" title="Settings">' + _i("set") + '</button><button class="pill2" id="nnew">' + _i("plus") + 'New chat</button></div></aside>'
  + '<div id="ntop"><button id="nhb" title="Menu">' + _i("menu") + '</button><div id="ntt"></div><button id="ncomp" title="New chat">' + _i("compose") + '</button></div>'
  + '<div id="psh"><div id="psp"><div class="grab"></div><div class="pshh"><button id="pshx">' + _i("x") + '</button>Add to chat</div>'
  + '<div class="tiles"><button class="tile" id="pcam">' + _i("cam") + 'Camera</button><button class="tile" id="pimg">' + _i("img") + 'Photos</button><button class="tile" id="pfil">' + _i("file") + 'Files</button></div>'
  + '<div class="lst"><button class="row" id="ppro">' + _i("proj") + '<div>Add to project<small id="pprn">None</small></div>' + _i("chev", "ix ch") + '</button><button class="row" id="pper">' + _i("hand") + '<div>Permission<small>Manual</small></div>' + _i("chev", "ix ch") + '</button><button class="row" id="pcon">' + _i("conn") + '<div>Connectors<small>Coming soon</small></div>' + _i("chev", "ix ch") + '</button><button class="row" id="pski">' + _i("skill") + '<div>Skills</div>' + _i("chev", "ix ch") + '</button></div>'
  + '<div class="sub" style="margin-top:6px">Quick actions</div><div id="pqa"></div></div></div>'
  + '<div id="lpm"></div>'
  + '<div id="vo"><div class="vt"><button id="vgear" title="Voice settings">' + _i("set") + '</button></div><div id="vmid"><canvas id="vcv"></canvas><div id="vgr"></div><div id="vst"></div><div id="vtr"></div></div><button id="vmic" title="Start / stop">' + _i("mic") + '</button><div id="vbar"><div class="chip2">Gemini Live</div><button id="vx" title="Close">' + _i("x") + '</button></div></div>'
  + '<div id="dlgw"><div id="dlg"></div></div><div id="avw"><div class="h"><b id="avt"></b><button class="btn3" id="avc">Copy</button><button class="btn3" id="avs">To Code Studio</button><button class="btn3 d" id="avd">Delete</button><button class="btn3" id="avx">Close</button></div><div id="avb"></div></div>')
def build_chat(chips):
    return ('<section class="pn" id="pChat"><div id="wlc">' + MARK + '<h1 id="wgr"></h1></div>'
            '<div id="ap" class="ap" style="display:none"><div class="aph">APPROVAL REQUIRED</div><div id="apm"></div><div class="apb"><button id="apy">Approve</button><button id="apn">Deny</button></div></div>'
            '<div id="lg"></div><div id="lact"><div class="h"><i></i><span id="lat">Working...</span><em>steps</em></div><div class="st" id="las"></div></div>'
            '<div class="inp"><div id="edb"><span>Editing message</span><button id="edx">Cancel</button></div><div class="cbox"><textarea id="tx" rows="1" placeholder="Chat with AXINUS..." autocomplete="off"></textarea><div class="crow"><button class="cib" id="cplus" title="Add">' + _i("plus") + '</button><span class="sp"></span><button class="cib" id="cmic" title="Voice">' + _i("mic") + '</button><button id="bsend" title="Send">' + _i("send") + '</button></div></div><div class="cfoot">AXINUS is AI and can make mistakes.</div></div>'
            '<button id="bup" style="display:none"></button><input type="file" id="fi" accept="image/*,application/pdf,video/*" style="display:none"><div style="display:none" id="chold">' + chips + '</div></section>')

PAGES = ('<section class="pn" id="pCode"><div class="hd">CODE STUDIO</div><div class="row3"><select id="csp" class="fi3" style="flex:1;min-width:130px"></select><button class="btn3" id="csnp">+ Project</button><button class="btn3" id="csnf">+ File</button></div><div id="csf"></div>'
         '<textarea id="cse" spellcheck="false" placeholder="File chuno ya + File dabao. Neeche likho ki kya banana hai, AI code likh dega (vibe coding)."></textarea>'
         '<div class="row3" style="margin-top:8px"><button class="btn3 p" id="css">Save</button><button class="btn3 p" id="csr">▶ Run</button><button class="btn3" id="csun">Undo AI</button><button class="btn3 d" id="csdel">Delete file</button></div>'
         '<div class="row3"><input id="csai" class="fi3" style="flex:1" placeholder="Kya banana hai? e.g. calculator web page, ya isme login add karo"><button class="btn3 p" id="csgo">Generate</button><button class="btn3 p" id="cspj">Full project</button></div><pre id="cso"></pre><iframe id="csprev" sandbox="allow-scripts"></iframe></section>'
         '<section class="pn" id="pProj"><div class="hd">PROJECTS</div><div class="card3"><div class="sub" style="margin-top:0">New project</div><input id="pjn" class="fi3" placeholder="Project name" style="margin-bottom:8px"><textarea id="pji" class="fi3" rows="3" placeholder="Instructions (AI is project ko aise samjhe...)"></textarea><div class="row3" style="margin-top:8px"><button class="btn3 p" id="pjc">Create</button></div></div><div id="pjl"></div></section>'
         '<section class="pn" id="pArt"><div class="hd">STUDIO · ARTIFACTS</div><div class="card3"><div class="sub" style="margin-top:0">Create with AI</div><textarea id="arp" class="fi3" rows="3" placeholder="Jaise: ek EMI calculator web page, ya Thevenin theorem ka interactive explainer"></textarea><div class="row3" style="margin-top:8px"><select id="ark" class="fi3" style="width:auto"><option value="html">HTML page</option><option value="svg">SVG image</option><option value="markdown">Document</option><option value="code">Code</option></select><button class="btn3 p" id="arg">Create</button></div></div><div class="agr" id="arl"></div></section>'
         '<section class="pn" id="pAcc"><div class="hd">ACCESSIBILITY &amp; PHONE CONTROL</div><div id="acs"></div><div class="sub">Quick tests</div><div class="row3" id="acq"></div><div class="sub">Hey AXINUS wake word</div><div class="row3" id="acw"></div><div class="sub">Recent activity</div><div id="aca"></div></section>')

PAGES = PAGES + ('<section class="pn" id="pChats"><div class="hd">All chats</div></section><section class="pn" id="pStg"><div class="hd">Settings</div><div id="stgl"></div></section>')
SH_JS = '<script>window.__IC=' + json.dumps(IC) + ';</script>' + r"""<script>(function(){
const $=id=>document.getElementById(id),E=s=>String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const api=async(n,a)=>{try{const r=await fetch('/api/'+n,{method:'POST',headers:{'Content-Type':'application/json','X-Pin':localStorage.getItem('pin')||''},body:JSON.stringify({args:a||[]})});if(r.status===401)return{error:'Wrong PIN'};return await r.json();}catch(e){return{error:String(e)};}};
const B=document.body,ls=(k,d)=>{try{return localStorage.getItem(k)||d;}catch(e){return d;}},ss=(k,v)=>{try{localStorage.setItem(k,v);}catch(e){}};
const SV=k=>'<svg class="ix" viewBox="0 0 24 24">'+(window.__IC[k]||'')+'</svg>';
const TT={chat:'',chats:'All chats',code:'Code',projects:'Projects',studio:'Artifacts',news:'India News',map:'Maps',tasks:'Tasks',pdf:'PDF Studio',settings:'Settings',access:'Phone control'},LEG={tasks:'tasks',pdf:'pdf',news:'news',map:'news'};
let CS={proj:'scratch',file:'',prev:null},AV=null,EDIT=null,CT='';
function toast2(m){const t=$('toasts');if(!t)return;const d=document.createElement('div');d.className='toast';d.textContent=m;t.appendChild(d);setTimeout(()=>d.remove(),3500);}
function ask(title,ph,val){return new Promise(res=>{$('dlg').innerHTML='<h3>'+E(title)+'</h3><input id="dlgi" class="fi3" placeholder="'+E(ph||'')+'" value="'+E(val||'')+'"><div class="row3" style="margin-top:14px;justify-content:flex-end"><button class="btn3" id="dlgn">Cancel</button><button class="btn3 p" id="dlgy">OK</button></div>';$('dlgw').classList.add('on');setTimeout(()=>$('dlgi').focus(),50);const f=v=>{$('dlgw').classList.remove('on');res(v);};$('dlgy').onclick=()=>f($('dlgi').value.trim());$('dlgn').onclick=()=>f(null);$('dlgi').onkeydown=e=>{if(e.key==='Enter')f($('dlgi').value.trim());};});}
function info(title,html){$('dlg').innerHTML='<h3>'+E(title)+'</h3>'+html+'<div class="row3" style="margin-top:14px;justify-content:flex-end"><button class="btn3 p" id="dlgy">Close</button></div>';$('dlgw').classList.add('on');$('dlgy').onclick=()=>$('dlgw').classList.remove('on');}
function openSb(o){B.classList.toggle('sbo',o);}
function shSheet(o){$('psh').classList.toggle('on',o);if(o)prjName();}
/* greeting */
function greet(){const h=new Date().getHours(),g=h<5?'Good evening':h<12?'Good morning':h<17?'Good afternoon':'Good evening',n=ls('axname','Tanveer');$('wgr').textContent=g+(n?', '+n:'');}
/* navigation */
function go(k){if(!TT.hasOwnProperty(k))k='chat';closeVoice(true);B.dataset.pg=k;ss('axpg',k);const b=document.querySelector('#bnav button[data-t="'+(LEG[k]||'home')+'"]');if(b)b.click();B.dataset.pg=k;
document.querySelectorAll('#nsb .ni[data-go]').forEach(x=>x.classList.toggle('on',x.dataset.go===k));$('ntt').textContent=k==='chat'?CT:TT[k];openSb(false);shSheet(false);window.scrollTo(0,0);
if(k==='code')codeInit();if(k==='projects')projLoad();if(k==='studio')artLoad();if(k==='access')accLoad();if(k==='settings')stgBuild();if(k==='chats')api('sess_list',['']).then(()=>$('sq').dispatchEvent(new Event('input')));greet();setTimeout(()=>window.dispatchEvent(new Event('resize')),120);}
document.addEventListener('click',e=>{const g=e.target.closest('[data-go]');if(g)go(g.dataset.go);});
$('nov').onclick=()=>openSb(false);$('nhb').onclick=()=>openSb(true);$('nsrch').onclick=()=>{openSb(false);const s=$('bsearch');if(s)s.click();};
$('nnew').onclick=$('ncomp').onclick=()=>{EDITOFF();$('snew').click();go('chat');};$('nva').onclick=()=>go('chats');
document.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'){e.preventDefault();$('nsrch').click();}});
/* recents (mirror of the legacy session list) */
$('pChats').appendChild($('sq'));$('pChats').appendChild($('sl'));
function recents(){const rows=[...$('sl').querySelectorAll('.si')];$('sl').querySelectorAll('.si button').forEach(b=>{b.textContent=b.dataset.a==='del'?'Delete':'Rename';});
$('nrc').innerHTML=rows.slice(0,3).map(r=>'<button class="rc" data-id="'+E(r.dataset.id)+'">'+SV('chat')+'<span>'+E(r.querySelector('b').textContent)+'</span></button>').join('')||'<div class="nlb" style="color:var(--mut)">No chats yet</div>';}
new MutationObserver(recents).observe($('sl'),{childList:true});recents();
$('nrc').onclick=e=>{const b=e.target.closest('.rc');if(!b)return;const r=$('sl').querySelector('.si[data-id="'+b.dataset.id+'"]');if(r)r.click();go('chat');};
$('sl').addEventListener('click',e=>{if(e.target.closest('.si')&&!e.target.closest('button'))setTimeout(()=>go('chat'),50);});
/* composer */
const tx=$('tx'),touch=matchMedia('(pointer:coarse)').matches;
function grow(){tx.style.height='auto';tx.style.height=Math.min(tx.scrollHeight,170)+'px';B.classList.toggle('hastx',!!tx.value.trim());}tx.addEventListener('input',grow);setInterval(grow,600);
document.addEventListener('keydown',e=>{if(e.target===tx&&e.key==='Enter'){if(e.shiftKey||touch)e.stopPropagation();else e.preventDefault();}},true);
function EDITOFF(){EDIT=null;$('edb').classList.remove('on');}
$('edx').onclick=()=>{EDITOFF();tx.value='';grow();};
function dropEdited(){if(!EDIT)return;let n=EDIT.nextElementSibling;const rm=[EDIT];while(n&&!n.classList.contains('u')){rm.push(n);n=n.nextElementSibling;}rm.forEach(x=>x.remove());EDITOFF();}
$('bsend').addEventListener('click',()=>{if(tx.value.trim())dropEdited();},true);
document.addEventListener('keydown',e=>{if(e.target===tx&&e.key==='Enter'&&!e.shiftKey&&!touch&&tx.value.trim())dropEdited();},true);
/* "+" sheet */
$('cplus').onclick=()=>shSheet(true);$('pshx').onclick=()=>shSheet(false);$('psh').onclick=e=>{if(e.target===$('psh'))shSheet(false);};
const fi=$('fi');
function pick(acc,cap){fi.accept=acc;if(cap)fi.setAttribute('capture','environment');else fi.removeAttribute('capture');shSheet(false);fi.click();}
$('pcam').onclick=()=>pick('image/*',true);$('pimg').onclick=()=>pick('image/*');$('pfil').onclick=()=>pick('image/*,application/pdf,video/*,.txt,.csv,.docx');
$('pper').onclick=()=>info('Permission','<p>Email, WhatsApp, delete, payment and phone-control actions always ask for your approval first. This mode is fixed to Manual.</p>');
$('pcon').onclick=()=>toast2('Connectors are not available yet');$('pski').onclick=()=>{shSheet(false);document.querySelector('#nodes button[data-k=skills]').click();};
$('pqa').appendChild($('chold').firstElementChild||document.createElement('div'));document.querySelectorAll('#pqa .chip').forEach(b=>b.addEventListener('click',()=>{shSheet(false);go('chat');}));
async function prjName(){$('pprn').textContent=ls('axproj','')||'None';}
$('ppro').onclick=async()=>{const r=await api('ws_projects'),L=(r&&r.projects)||[];info('Add to project','<div class="lst" style="margin:0">'+['None'].concat(L.map(p=>p.name)).map(n=>'<button class="row" data-pj="'+E(n)+'">'+E(n)+'</button>').join('')+'</div>');$('dlg').onclick=async e=>{const b=e.target.closest('[data-pj]');if(!b)return;const n=b.dataset.pj==='None'?'':b.dataset.pj;ss('axproj',n);await api('ws_ctx',[n]);$('dlgw').classList.remove('on');prjName();toast2(n?'Project: '+n:'Project removed');};};
if(ls('axproj',''))api('ws_ctx',[ls('axproj','')]);
$('cmic').onclick=()=>openVoice();
/* messages: state, title, toolbars, long-press menu */
const lg=$('lg');
const ACT=(k,t)=>'<button data-a="'+k+'" title="'+t+'">'+SV(k)+'</button>';
function msgText(n){const c=n.cloneNode(true);c.querySelectorAll('b:first-child,.cp,.sv,button').forEach(x=>x.remove());return(c.textContent||'').trim();}
function mirror(){const has=lg.children.length>0;B.classList.toggle('hasmsg',!!lg.querySelector(':scope>.u,:scope>.a'));const u=lg.querySelector('.u');CT=u?msgText(u).slice(0,34):'';if(B.dataset.pg==='chat'||!B.dataset.pg)$('ntt').textContent=CT;
lg.querySelectorAll(':scope>.a:not([data-tb])').forEach(n=>{n.dataset.tb=1;const t=document.createElement('div');t.className='tbr';t.innerHTML=ACT('copy','Copy')+ACT('retry','Ask again')+ACT('spk','Read aloud');n.after(t);});
lg.querySelectorAll('pre:not([data-s])').forEach(p=>{p.dataset.s=1;const b=document.createElement('button');b.className='sv';b.textContent='Artifact';b.onclick=async()=>{const t=p.textContent.replace(/(Artifact|Copy)$/g,'').trim();const r=await api('art_save',['Chat code',/<html|<!doctype/i.test(t)?'html':'code',t]);toast2(r&&r.ok?'Saved to Artifacts':'Save failed');};p.appendChild(b);});
const L=[...lg.querySelectorAll(':scope>.u,:scope>.a')].slice(-2);$('vtr').innerHTML=L.map(d=>'<div>'+E(msgText(d).slice(0,200))+'</div>').join('');}
new MutationObserver(mirror).observe(lg,{childList:true,subtree:true,characterData:true});mirror();
function copyT(t){try{navigator.clipboard.writeText(t);toast2('Copied');}catch(e){const a=document.createElement('textarea');a.value=t;document.body.appendChild(a);a.select();try{document.execCommand('copy');toast2('Copied');}catch(x){toast2('Copy failed');}a.remove();}}
lg.addEventListener('click',e=>{const b=e.target.closest('.tbr button');if(!b)return;const m=b.parentElement.previousElementSibling;if(!m)return;const t=msgText(m),a=b.dataset.a;
if(a==='copy')copyT(t);else if(a==='retry'){let p=m.previousElementSibling;while(p&&!p.classList.contains('u'))p=p.previousElementSibling;if(p){tx.value=msgText(p);grow();$('bsend').click();}}else if(a==='spk')readAloud(t);});
async function readAloud(t){if(!t)return;const live=()=>{try{const w=window.AXWS&&window.AXWS();return w&&w.ws&&w.ws.readyState===1&&w.ready?w:null;}catch(e){return null;}};let w=live();
if(!w){toast2('Starting voice...');const g=$('bgo');if(g)g.click();for(let i=0;i<40&&!(w=live());i++)await new Promise(r=>setTimeout(r,300));}
if(!w)return toast2('Voice could not start. Open the mic screen once and try again.');
w.ws.send(JSON.stringify({clientContent:{turns:[{role:'user',parts:[{text:'SYSTEM REMINDER. Read the following text aloud to Sir, naturally, in the same language, exactly as written. Do not add, explain or summarize anything: '+t.slice(0,3500)}]}],turnComplete:true}}));toast2('Reading aloud');}
let LPT=null,LPN=null;const lpm=$('lpm');
function lpHide(){lpm.classList.remove('on');}
function lpShow(n){LPN=n;const r=n.getBoundingClientRect();lpm.innerHTML='<button data-k="copy">'+SV('copy')+'Copy</button><button data-k="sel">'+SV('sel')+'Select text</button><button data-k="edit">'+SV('edit')+'Edit message</button>';lpm.classList.add('on');const h=lpm.offsetHeight,w=lpm.offsetWidth;lpm.style.left=Math.max(10,Math.min(innerWidth-w-10,r.right-w))+'px';lpm.style.top=Math.max(60,Math.min(innerHeight-h-10,r.bottom+8))+'px';if(navigator.vibrate)try{navigator.vibrate(15);}catch(e){}}
lg.addEventListener('pointerdown',e=>{const n=e.target.closest('.u');if(!n||e.target.closest('a'))return;clearTimeout(LPT);LPT=setTimeout(()=>lpShow(n),550);});
['pointerup','pointercancel','pointermove','scroll'].forEach(ev=>lg.addEventListener(ev,()=>clearTimeout(LPT),{passive:true}));
lg.addEventListener('contextmenu',e=>{if(e.target.closest('.u'))e.preventDefault();});
document.addEventListener('pointerdown',e=>{if(!e.target.closest('#lpm'))lpHide();},true);
lpm.onclick=e=>{const b=e.target.closest('button');if(!b||!LPN)return;const t=msgText(LPN),k=b.dataset.k;lpHide();
if(k==='copy')copyT(t);else if(k==='sel')info('Select text','<div style="-webkit-user-select:text;user-select:text;white-space:pre-wrap;line-height:1.55;font:16px var(--sans);background:var(--in);border-radius:12px;padding:12px;margin-bottom:4px">'+E(t)+'</div>');
else if(k==='edit'){EDIT=LPN;tx.value=t;grow();$('edb').classList.add('on');go('chat');tx.focus();}};
/* live activity */
const la=$('lact');let lt=null;la.querySelector('.h').onclick=()=>la.classList.toggle('open');
function steps(){const ev=[...$('al').querySelectorAll('.ev:not(.mk)')].slice(0,8),run=ev.some(e=>e.classList.contains('run')),th=B.dataset.m==='think';
if(run||th){la.classList.add('on');clearTimeout(lt);lt=setTimeout(()=>la.classList.remove('on'),2500);}
$('las').innerHTML=ev.map(e=>'<div class="'+(e.classList.contains('done')?'done':e.classList.contains('fail')?'fail':'')+'">'+E(e.textContent.trim().slice(0,120))+'</div>').join('')||'<div>Working...</div>';
const f=ev[0];$('lat').textContent=f?f.textContent.trim().slice(0,60):'Working...';}
new MutationObserver(steps).observe($('al'),{childList:true,subtree:true,attributes:true});new MutationObserver(steps).observe(B,{attributes:true,attributeFilter:['data-m']});
/* ---------- Voice screen with AXINUS core ---------- */
const vo=$('vo'),vcv=$('vcv'),vx=vcv.getContext('2d'),DPR=Math.min(2,window.devicePixelRatio||1);vcv.width=vcv.height=260*DPR;let vraf=0;
const VS={off:'Tap the mic to start',wait:'Connecting...',live:'Listening',think:'Thinking...',err:'Connection problem. Tap the mic to retry'};
function vstat(){const m=B.dataset.m||'off';$('vst').textContent=VS[m]||VS.off;B.classList.toggle('vlive',m==='live'||m==='think'||m==='wait');$('vmic').innerHTML=SV(m==='off'||m==='err'?'mic':'micoff');}
new MutationObserver(vstat).observe(B,{attributes:true,attributeFilter:['data-m']});vstat();
function vdraw(ms){if(!vo.classList.contains('on')){vraf=0;return;}const t=ms/1000,m=B.dataset.m||'off',amp=m==='live'?1.6+Math.sin(t*3.1)*Math.sin(t*1.7)*1.1:m==='think'?1.3:m==='wait'?.8:.35,R=58,c='236,233,227';
vx.setTransform(DPR,0,0,DPR,0,0);vx.clearRect(0,0,260,260);vx.translate(130,130);
for(let k=0;k<3;k++){vx.beginPath();vx.arc(0,0,R+k*14+Math.sin(t*(1.2+k*.5)+k)*amp*(1+k*.4),0,6.2832);vx.strokeStyle='rgba('+c+','+(.6-k*.17)+')';vx.lineWidth=1;vx.stroke();}
const n=64;for(let i=0;i<n;i++){const a=i/n*6.2832+t*(m==='think'?.7:.15),rr=R-11+Math.sin(i*5+t*(2+amp))*amp*2.4;vx.beginPath();vx.arc(Math.cos(a)*rr,Math.sin(a)*rr,1.3,0,6.2832);vx.fillStyle='rgba('+c+',.85)';vx.fill();}
if(m==='think'||m==='wait'){vx.beginPath();vx.arc(0,0,R+38,t*2.4,t*2.4+(m==='think'?1.5:.8));vx.strokeStyle='rgba('+c+',.9)';vx.lineWidth=2;vx.stroke();}
vx.beginPath();vx.arc(0,0,4+amp*.7,0,6.2832);vx.fillStyle='rgba('+c+',.95)';vx.fill();vx.setTransform(1,0,0,1,0,0);vraf=requestAnimationFrame(vdraw);}
function openVoice(){vo.classList.add('on');$('vgr').textContent="Let's talk"+(ls('axname','Tanveer')?', '+ls('axname','Tanveer'):'');vstat();if(!vraf)vraf=requestAnimationFrame(vdraw);const m=B.dataset.m||'off';if(m==='off'||m==='err')$('bgo').click();}
function closeVoice(quiet){if(!vo.classList.contains('on'))return;vo.classList.remove('on');if(!quiet&&(B.dataset.m||'off')!=='off')$('bstop').click();}
$('vx').onclick=()=>closeVoice(false);$('vmic').onclick=()=>{const m=B.dataset.m||'off';(m==='off'||m==='err'?$('bgo'):$('bstop')).click();};
$('vgear').onclick=()=>{document.querySelector('#nodes button[data-k=voices]').click();};
/* ---------- Settings (one place for everything) ---------- */
function modTab(t){document.querySelector('#nodes button[data-k=settings]').click();const b=document.querySelector('#mc .tab[data-t="'+t+'"]');if(b)b.click();}
const SG=[[['user','Profile',()=>ls('axname','Tanveer'),async()=>{const n=await ask('Your name','Name',ls('axname','Tanveer'));if(n!==null){ss('axname',n);greet();stgBuild();}}]],
[['brain','Memory','',()=>document.querySelector('#nodes button[data-k=memory]').click()],['skill','Skills','',()=>document.querySelector('#nodes button[data-k=skills]').click()],['wave','Voice','',()=>document.querySelector('#nodes button[data-k=voices]').click()],['conn','Connectors','Coming soon',()=>toast2('Connectors are not available yet')],['hand','Permissions','Manual',()=>$('pper').click()]],
[['type','Font style',()=>B.classList.contains('sans')?'Sans':'Default',()=>{B.classList.toggle('sans');ss('axsans',B.classList.contains('sans')?'1':'');stgBuild();}],['phone','Phone control','',()=>go('access')]],
[['gauge','Agents & usage','',()=>modTab('usage')],['lock','Security','',()=>modTab('security')],['dev','Developer','',()=>modTab('dev')],['exp','Export','',()=>modTab('export')],['diag','Diagnose','',()=>modTab('diag')]],
[['info','About AXINUS','',()=>info('About AXINUS','<p>AXINUS is a personal AI workspace: chat, voice, phone control, PDFs, code, projects and artifacts. The brain runs on Colab with several models; the Android app adds phone control.</p>')]]];
function stgBuild(){const h=SG.map((g,gi)=>'<div class="lst" style="background:var(--s1)">'+g.map((r,ri)=>{const v=typeof r[2]==='function'?r[2]():r[2];return '<button class="srow" data-g="'+gi+'" data-r="'+ri+'">'+SV(r[0])+'<div>'+E(r[1])+'</div>'+(v?'<span style="margin-left:auto;color:var(--mut);font-size:14px">'+E(v)+'</span>':'')+'</button>';}).join('')+'</div>').join('');$('stgl').innerHTML=h;}
$('stgl').onclick=e=>{const b=e.target.closest('.srow');if(b)SG[b.dataset.g][b.dataset.r][3]();};
if(ls('axsans',''))B.classList.add('sans');
/* ---------- Code Studio ---------- */
async function codeInit(){const r=await api('ws_projects');let L=(r&&r.projects)||[];if(!L.find(p=>p.name===CS.proj))L=[{name:CS.proj}].concat(L);$('csp').innerHTML=L.map(p=>'<option'+(p.name===CS.proj?' selected':'')+'>'+E(p.name)+'</option>').join('');await filesLoad();}
async function filesLoad(open){const r=await api('ws_files',[CS.proj]);const F=(r&&r.files)||[];$('csf').innerHTML=F.map(f=>'<button data-f="'+E(f.path)+'" class="'+(f.path===CS.file?'on':'')+'">'+E(f.path)+'</button>').join('')||'<span style="color:var(--mut);font-size:13px">Koi file nahi. + File dabao ya neeche likho ki kya banana hai.</span>';if(open){await fileOpen(open);}else if(!CS.file&&F.length)await fileOpen(F[0].path);}
async function fileOpen(p){CS.file=p;const r=await api('ws_read',[CS.proj,p]);$('cse').value=(r&&r.content)||'';CS.prev=null;showOut(null);document.querySelectorAll('#csf button').forEach(b=>b.classList.toggle('on',b.dataset.f===p));}
function showOut(r){const o=$('cso'),f=$('csprev');o.style.display=f.style.display='none';if(!r)return;if(r.kind==='html'){f.srcdoc=r.html;f.style.display='block';}else{o.textContent=r.out||r.error||'';o.style.display='block';}}
$('csp').onchange=()=>{CS.proj=$('csp').value;CS.file='';$('cse').value='';filesLoad();};$('csf').onclick=e=>{const b=e.target.closest('button');if(b)fileOpen(b.dataset.f);};
$('csnp').onclick=async()=>{const n=await ask('New project','name');if(!n)return;await api('ws_project_new',[n,'']);CS.proj=n.replace(/[^A-Za-z0-9_\- ]/g,'').replace(/ /g,'_')||'scratch';CS.file='';codeInit();};
$('csnf').onclick=async()=>{const n=await ask('New file','e.g. app.py or index.html');if(!n)return;const r=await api('ws_write',[CS.proj,n,'']);if(r.error)return toast2(r.error);CS.file=n;await filesLoad(n);};
$('css').onclick=async()=>{if(!CS.file)return toast2('Pehle file chuno');const r=await api('ws_write',[CS.proj,CS.file,$('cse').value]);toast2(r.ok?'Saved':(r.error||'Save fail'));};
$('csr').onclick=async()=>{if(!CS.file)return toast2('Pehle file chuno');await api('ws_write',[CS.proj,CS.file,$('cse').value]);showOut({out:'Running...',kind:'text'});showOut(await api('ws_run',[CS.proj,CS.file]));};
$('csdel').onclick=async()=>{if(!CS.file)return;if(!confirm('Delete '+CS.file+'?'))return;await api('ws_delete',[CS.proj,CS.file]);CS.file='';$('cse').value='';filesLoad();};
$('csun').onclick=async()=>{if(CS.prev==null)return toast2('Undo ke liye kuch nahi');$('cse').value=CS.prev;await api('ws_write',[CS.proj,CS.file,CS.prev]);CS.prev=null;toast2('Undo ho gaya');};
$('csgo').onclick=async()=>{const p=$('csai').value.trim();if(!p)return toast2('Pehle likho kya banana hai');let f=CS.file;if(!f){f=await ask('File ka naam','e.g. app.py, index.html');if(!f)return;}CS.prev=$('cse').value;const bt=$('csgo');bt.disabled=true;bt.textContent='Writing...';const r=await api('code_gen',[CS.proj,f,p]);bt.disabled=false;bt.textContent='Generate';if(r.error)return toast2(r.error);CS.file=f;$('csai').value='';await filesLoad(f);toast2('Code ready ('+(r.model||'')+')');};
$('cse').addEventListener('keydown',e=>{if(e.key==='Tab'){e.preventDefault();const s=e.target.selectionStart;e.target.setRangeText('  ',s,e.target.selectionEnd,'end');}if((e.ctrlKey||e.metaKey)&&e.key==='s'){e.preventDefault();$('css').click();}});
$('cspj').onclick=async()=>{const p=$('csai').value.trim();if(!p)return toast2('Pehle likho kya banana hai');const bt=$('cspj');bt.disabled=true;bt.textContent='Building (1-3 min)...';const r=await api('code_project',[CS.proj,p]);bt.disabled=false;bt.textContent='Full project';if(r.error)return toast2(r.error);CS.file='';$('csai').value='';await filesLoad(r.files.find(f=>/index\.html$/.test(f))||r.files[0]);info('Project ready','<p style="color:#c4d3f2;font-size:14px">'+r.files.length+' files: '+E(r.files.join(', '))+'</p><p style="color:'+(r.remaining_issues.length?'#fca5a5':'#86efac')+';font-size:13.5px">'+(r.remaining_issues.length?'Bache issues:<br>'+r.remaining_issues.map(E).join('<br>'):'Static checks pass'+(r.fix_pass?' (auto-fix ke baad)':''))+'</p><p style="color:#8a98b5;font-size:12.5px">'+E(r.note)+' Index.html ko Run dabake preview dekho.</p>');};
/* ---------- Projects ---------- */
async function projLoad(){const r=await api('ws_projects');const L=(r&&r.projects)||[];$('pjl').innerHTML=L.map(p=>'<div class="card3"><b>'+E(p.name)+'</b><small>'+p.files+' files'+(p.instructions?' · '+E(p.instructions.slice(0,120)):'')+'</small><div class="row3" style="margin-top:8px"><button class="btn3 p" data-o="'+E(p.name)+'">Open in Code Studio</button><button class="btn3 d" data-d="'+E(p.name)+'">Delete</button></div></div>').join('')||'<div class="card3"><small>Abhi koi project nahi. Upar naya banao.</small></div>';}
$('pjc').onclick=async()=>{const n=$('pjn').value.trim();if(!n)return toast2('Name likho');await api('ws_project_new',[n,$('pji').value]);$('pjn').value=$('pji').value='';projLoad();};
$('pjl').onclick=async e=>{const o=e.target.closest('[data-o]'),d=e.target.closest('[data-d]');if(o){CS.proj=o.dataset.o;CS.file='';go('code');}if(d&&confirm('Project delete karun?')){const r=await api('ws_project_del',[d.dataset.d]);if(r.error)toast2(r.error);projLoad();}};
/* ---------- Artifacts ---------- */
async function artLoad(){const r=await api('art_list');const L=(r&&r.items)||[];$('arl').innerHTML=L.map(a=>'<div class="card3" data-a="'+a.id+'"><span class="tagk">'+E(a.kind)+'</span><br><b>'+E(a.title)+'</b><small>'+new Date(a.t*1000).toLocaleString()+'</small></div>').join('')||'<div class="card3"><small>Abhi koi artifact nahi. Upar AI se banao ya chat ke code block par "Artifact" dabao.</small></div>';}
$('arl').onclick=async e=>{const c=e.target.closest('[data-a]');if(!c)return;const a=await api('art_get',[c.dataset.a]);if(a.error)return toast2(a.error);AV=a;$('avt').textContent=a.title;const b=$('avb');if(a.kind==='html'||a.kind==='svg'){b.innerHTML='<iframe sandbox="allow-scripts"></iframe>';b.firstChild.srcdoc=a.kind==='svg'?'<body style="margin:0;display:grid;place-items:center;height:100vh">'+a.content+'</body>':a.content;}else{b.innerHTML='<pre></pre>';b.firstChild.textContent=a.content;}$('avw').classList.add('on');};
$('avx').onclick=()=>$('avw').classList.remove('on');$('avc').onclick=()=>{try{navigator.clipboard.writeText(AV.content);toast2('Copied');}catch(e){toast2('Copy nahi hua');}};
$('avd').onclick=async()=>{if(!AV||!confirm('Delete artifact?'))return;await api('art_del',[AV.id]);$('avw').classList.remove('on');artLoad();};
$('avs').onclick=async()=>{if(!AV)return;const ext={html:'html',svg:'svg',markdown:'md',code:'txt'}[AV.kind]||'txt';const n='artifact_'+AV.id+'.'+ext;await api('ws_write',['scratch',n,AV.content]);CS.proj='scratch';CS.file=n;$('avw').classList.remove('on');go('code');};
$('arg').onclick=async()=>{const p=$('arp').value.trim();if(!p)return toast2('Kya banana hai likho');const b=$('arg');b.disabled=true;b.textContent='Creating...';const r=await api('art_gen',[p,$('ark').value]);b.disabled=false;b.textContent='Create';if(r.error)return toast2(r.error);$('arp').value='';artLoad();toast2('Artifact ready');};
/* ---------- Accessibility ---------- */
async function accLoad(){let a='Browser me hoon (APK me dikhega)',ok=false;try{if(window.AXAND&&AXAND.accessEnabled){ok=!!AXAND.accessEnabled();a=ok?'ON':'OFF - Settings me AXINUS ko ON karo';}}catch(e){}
const p=await api('phone_status');const on=p&&p.online;$('acs').innerHTML='<div class="stt'+(ok?' ok':'')+'"><i></i>Accessibility service<span>'+E(a)+'</span></div><div class="stt'+(on?' ok':'')+'"><i></i>Phone agent link<span>'+(on?('Online'+(p.busy?' · kaam chal raha hai':'')):'Offline'+(p&&p.ago>=0?' ('+p.ago+'s pehle)':''))+'</span></div><div class="row3"><button class="btn3 p" id="aco">Open Accessibility settings</button><button class="btn3" id="acr">Refresh</button></div>';
$('aco').onclick=()=>{try{AXAND.openAccessSettings();}catch(e){toast2('Ye sirf Android app me chalta hai');}};$('acr').onclick=accLoad;
$('acq').innerHTML=['YouTube kholo','Screen par kya hai?','Back jao','Neeche scroll karo','Home jao'].map(q=>'<button class="btn3" data-t="'+E(q)+'">'+E(q)+'</button>').join('');
const w=document.getElementById('wkb');if(w&&!$('acw').contains(w))$('acw').appendChild(w);else if(!w)$('acw').innerHTML='<span style="color:var(--mut);font-size:13px">Android app me yahan toggle dikhega</span>';
const r=await api('act_list');$('aca').innerHTML=((r&&r.items)||[]).map(x=>'<div class="card3"><b>'+E(x.task)+'</b><small>'+E(x.t)+' · '+E(x.status)+(x.result?' · '+E(x.result):'')+'</small></div>').join('')||'<div class="card3"><small>Abhi koi kaam nahi.</small></div>';}
$('acq').onclick=e=>{const b=e.target.closest('button');if(!b)return;go('chat');tx.value=b.dataset.t;$('bsend').click();};
document.querySelectorAll('.hd').forEach(h=>{const n=[...h.childNodes].find(x=>x.nodeType===3&&x.textContent.trim());if(n)n.textContent=n.textContent.trim().toLowerCase().replace(/(^|\s)(\S)/g,(m,a,b)=>a+b.toUpperCase()).replace('&amp;','&').replace('Pdf','PDF').replace('Sat-link Feed','Map');});
document.querySelectorAll('.lnk,.chip').forEach(b=>{b.textContent=b.textContent.replace(/^[^A-Za-z0-9]+/,'');});
const w0=$('wkb');if(w0)w0.textContent=w0.textContent.replace(/^[^A-Za-z]+/,'');
/* start */
document.documentElement.dataset.theme='ax';
go(ls('axpg','chat')==='voice'?'chat':ls('axpg','chat'));
})();</script>
"""
def _apply():
    global UI_BODY, UI_HTML
    ub = UI_BODY
    if 'id="nsb"' in ub: return
    old = re.search(r'<section class="pn" id="pChat">.*?</section>', ub, re.S)
    if not old: print("ax8: pChat not found, shell skipped"); return
    cm = re.search(r'<div class="chips">.*?</div>', old.group(0), re.S); chips = cm.group(0) if cm else '<div class="chips"></div>'
    ub = ub.replace(old.group(0), build_chat(chips), 1)
    ub = ub.replace("</style>", SH_CSS + "</style>", 1)
    ub = ub.replace('<div class="toasts" id="toasts"></div>', '<div class="toasts" id="toasts"></div>' + SH_HTML, 1)
    ub = ub.replace('<section class="pn" id="pTasks">', PAGES + '<section class="pn" id="pTasks">', 1)
    ub = ub + SH_JS
    UI_BODY = ub
    if "API" in globals() and "build_old_js" in globals():
        _oj, _w = build_old_js(PAGE)
        UI_HTML = '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>AXINUS</title></head><body>' + UI_BODY.replace("__OLD__", _oj) + '</body></html>'
    print("ax8 shell ON")
_apply()
