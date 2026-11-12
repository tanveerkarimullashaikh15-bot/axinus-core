# AXINUS ADDON 4h - daily news memory: India + world digest stored 90 days, recallable by date/topic
import json, re, time, threading, datetime
NM_PATH = MEM_DIR + "/newsmem.json"; NM_KEEP = 90
NM = globals().get("NM") or {"busy": False, "last": ""}
def _nm(): return jr(NM_PATH, {})
def _today(): return now_ist().strftime("%Y-%m-%d")

def _digest(day=None, force=False):
    day = day or _today(); d = _nm()
    if day in d and not force: return d[day]
    with Stage("research", "Daily news digest", "rss") as st:
        ent = {"india": [], "world": [], "extra": []}
        for key, cat in (("india", "top"), ("world", "world"), ("extra", "business")):
            try:
                _, items, _s = news_items(cat, True)
                ent[key] = [{"t": i["title"], "s": i["source"], "l": i["link"], "d": (i.get("summary") or "")[:160]} for i in items[:10]]
            except Exception: pass
        if not ent["india"] and not ent["world"]:
            st.fail = True; return None
        raw = "\n".join("INDIA: %s (%s)" % (i["t"], i["s"]) for i in ent["india"][:8]) + "\n" + "\n".join("WORLD: %s (%s)" % (i["t"], i["s"]) for i in ent["world"][:8]) + "\n" + "\n".join("BUSINESS: " + i["t"] for i in ent["extra"][:4])
        try:
            sm, used = llm("writer", "Tum Axinus ho. In headlines ka Hinglish digest banao, phone screen ke liye chhota: 'INDIA' ke 5 bullets, 'DUNIYA' ke 5 bullets, 'ECONOMY' ke 2. Har bullet 1 line, sirf headlines me jo hai wahi likho, kuch invent mat karo.", raw, mt=700)
            ent["summary"] = sm.strip(); ent["model"] = used
        except Exception:
            ent["summary"] = "INDIA\n" + "\n".join("- " + i["t"] for i in ent["india"][:5]) + "\nDUNIYA\n" + "\n".join("- " + i["t"] for i in ent["world"][:5])
        ent["ts"] = now_ist().isoformat(timespec="minutes"); d[day] = ent
        for k in sorted(d)[:-NM_KEEP]: d.pop(k, None)
        jw(NM_PATH, d); NM["last"] = day
        return ent

def news_today(refresh: bool = False):
    """Today's saved India + world news digest (built if missing)."""
    e = _digest(force=bool(refresh))
    if not e: return "Error: news abhi nahi mili (internet/RSS issue). Thodi der baad try karo."
    return "📰 " + _today() + "\n" + e["summary"]

def news_refresh():
    return news_today(True)

def news_recall(query: str = "", days: int = 7):
    """Search saved past news by topic/date. query keywords (empty = latest days), days = how far back."""
    d = _nm()
    if not d: return "Abhi tak koi news save nahi hui. news_today se shuru karo."
    q = str(query).lower().strip(); m = re.search(r"(20\d\d-\d\d-\d\d)", q)
    try: days = max(1, min(int(days), NM_KEEP))
    except Exception: days = 7
    keys = sorted(d)[-days:] if not m else [k for k in d if k == m.group(1)]
    if m: q = q.replace(m.group(1), "").strip()
    qt = [w for w in re.findall(r"\w{3,}", q) if w not in ("news", "khabar", "about", "kya", "tha", "thi", "baare", "mein")]
    out = []
    for k in reversed(keys):
        e = d[k]; hits = []
        for sec in ("india", "world", "extra"):
            for i in e.get(sec, []):
                if not qt or any(w in (i["t"] + " " + i.get("d", "")).lower() for w in qt): hits.append("- [%s] %s (%s)" % (sec[:2].upper(), i["t"], i["s"]))
        if hits: out.append(k + "\n" + "\n".join(hits[:6 if qt else 4]))
    return "\n\n".join(out[:6]) or "Is topic par saved news me kuch nahi mila (last %d din)." % days

ADDON_API["news_digest"] = lambda *a: J({"text": news_today()})
reg_tool(news_today, "Today's India + world news digest, saved in memory (refresh=true to rebuild)", "research")
reg_tool(news_recall, "Recall SAVED past news by topic/date (query keywords or YYYY-MM-DD, days back). Use for 'pichle hafte X ke baare me kya hua'", "research")
reg_tool(news_refresh, "Rebuild today's saved news digest now", "research")
_GRP.append((r"news|khabar|samachar|headline|duniya|world|aaj kya hua|pichle|last week|kal kya", ["news_today", "news_recall", "news_refresh", "get_news", "tavily_live_search"]))
DELEG += "\n- NEWS: 'aaj ki khabar/duniya me kya hua' -> news_today (saved digest). 'pichle din/hafte X ke baare me kya tha' -> news_recall. Fresh single-topic live info -> tavily_live_search.\n"

def _nm_loop():
    time.sleep(40)
    while True:
        try:
            h = now_ist().hour
            if h >= 7 and _today() not in _nm() and not NM["busy"]:
                NM["busy"] = True
                try: _digest()
                finally: NM["busy"] = False
        except Exception as e: print("newsmem err:", str(e)[:80])
        time.sleep(900)
if not globals().get("_NM_ON"):
    threading.Thread(target=_nm_loop, daemon=True).start(); _NM_ON = True
print("✅ ax6b news memory OK | daily digest, 90 days")
