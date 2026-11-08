# AXINUS ADDON 2b - news + briefing, memory, search, export (needs ax2a)
import json, time, threading, re, os, uuid, pathlib, datetime, glob, html, email.utils
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
# =============== 3. NEWS + DAILY BRIEFING ===============
GN = "&hl=en-IN&gl=IN&ceid=IN:en"
FEEDS = {
    "top": [("https://www.thehindu.com/news/national/feeder/default.rss", "The Hindu"), ("https://feeds.feedburner.com/ndtvnews-top-stories", "NDTV"), ("https://timesofindia.indiatimes.com/rssfeedstopstories.cms", "Times of India"), ("https://news.google.com/rss/headlines/section/topic/NATION?" + GN[1:], "Google News")],
    "tech": [("https://techcrunch.com/feed/", "TechCrunch"), ("https://www.theverge.com/rss/index.xml", "The Verge"), ("https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?" + GN[1:], "Google News")],
    "ai": [("https://venturebeat.com/category/ai/feed/", "VentureBeat"), ("https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", "The Verge"), ("https://news.google.com/rss/search?q=artificial+intelligence" + GN, "Google News")],
    "science": [("https://www.nasa.gov/feed/", "NASA"), ("https://www.sciencedaily.com/rss/top/science.xml", "ScienceDaily"), ("https://news.google.com/rss/search?q=ISRO+OR+space+OR+science" + GN, "Google News")],
    "business": [("https://economictimes.indiatimes.com/rssfeedsdefault.cms", "Economic Times"), ("https://www.business-standard.com/rss/home_page_top_stories.rss", "Business Standard"), ("https://news.google.com/rss/headlines/section/topic/BUSINESS?" + GN[1:], "Google News")],
    "world": [("http://feeds.bbci.co.uk/news/world/rss.xml", "BBC"), ("https://www.aljazeera.com/xml/rss/all.xml", "Al Jazeera"), ("https://news.google.com/rss/headlines/section/topic/WORLD?" + GN[1:], "Google News")],
}
CAT_ALIAS = {"india": "top", "top": "top", "headlines": "top", "tech": "tech", "technology": "tech", "ai": "ai", "science": "science", "space": "science", "business": "business", "market": "business", "economy": "business", "world": "world", "international": "world"}
NEWS_C = globals().get("NEWS_C") or {}
def _loc(t): return str(t).rsplit("}", 1)[-1]
def _child(e, *names):
    for c in e:
        if _loc(c.tag) in names and (c.text or "").strip(): return c.text.strip()
    return ""
def _link(e):
    for c in e:
        if _loc(c.tag) == "link":
            if (c.text or "").strip(): return c.text.strip()
            if c.get("href") and c.get("rel", "alternate") == "alternate": return c.get("href")
    return ""
def _clean(x, n=230):
    x = re.sub(r"<[^>]+>", " ", html.unescape(x or "")); x = re.sub(r"\s+", " ", x).strip()
    return (x[:n].rsplit(" ", 1)[0] + "…") if len(x) > n else x
def _ts(s):
    try: return email.utils.parsedate_to_datetime(s).timestamp()
    except Exception: pass
    try: return datetime.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
    except Exception: return 0

def fetch_feed(url, src):
    r = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0 AXINUS"})
    root = ET.fromstring(r.content); out = []
    for e in [x for x in root.iter() if _loc(x.tag) in ("item", "entry")][:14]:
        title = _clean(_child(e, "title"), 160); link = _link(e)
        if not title or not link: continue
        s = src
        if src == "Google News" and " - " in title: title, s = title.rsplit(" - ", 1)
        summ = _clean(_child(e, "description", "summary", "encoded", "content"))
        if not summ or summ.lower().startswith(title.lower()[:30]): summ = ""
        ts = _ts(_child(e, "pubDate", "published", "updated", "date"))
        out.append({"title": title, "summary": summ, "source": s, "ts": ts, "date": datetime.datetime.fromtimestamp(ts, IST).strftime("%d %b, %I:%M %p").lstrip("0") if ts else "", "link": link})
    return out

def news_items(cat="top", force=False):
    cat = CAT_ALIAS.get(str(cat).lower().strip(), "top")
    c = NEWS_C.get(cat)
    if c and not force and time.time() - c["t"] < 1800: return cat, c["items"], False
    def one(f):
        try: return fetch_feed(*f)
        except Exception: return []
    with ThreadPoolExecutor(4) as ex: res = list(ex.map(one, FEEDS[cat]))
    items = []; seen = set()
    for lst in res:
        for it in lst:
            k = re.sub(r"\W+", "", it["title"].lower())[:50]
            if k not in seen: seen.add(k); items.append(it)
    items.sort(key=lambda x: x["ts"], reverse=True)
    if items:
        NEWS_C[cat] = {"t": time.time(), "items": items[:12]}; jw(NEWS_PATH, {k: v for k, v in NEWS_C.items()})
        return cat, items[:12], False
    old = c or jr(NEWS_PATH, {}).get(cat)
    return cat, (old["items"] if old else []), True

def news(cat="top", force=False):
    cat, items, stale = news_items(cat, force)
    return J({"cat": cat, "items": items, "stale": stale})

def get_news(category: str = "top", n: int = 5):
    with Stage("research", "Fetching " + str(category) + " news", "rss") as st:
        cat, items, stale = news_items(category)
        if not items: st.fail = True; return "Error: news abhi nahi mil payi (internet/feeds)."
    n = max(1, min(int(n), 8))
    return "News (" + cat + ")" + (" [old cache]" if stale else "") + ":\n" + "\n".join(str(i + 1) + ". " + x["title"] + " (" + x["source"] + ", " + x["date"] + ")" + ("\n   " + x["summary"] if x["summary"] else "") + "\n   " + x["link"] for i, x in enumerate(items[:n]))

def briefing_text():
    lines = ["Good day Sir, aaj ka briefing."]
    with Stage("research", "Collecting headlines", "rss") as st:
        _, top, _s = news_items("top"); _, tech, _s2 = news_items("tech")
        if not top and not tech: st.fail = True
    if top: lines.append("Top khabrein: " + " | ".join(str(i + 1) + ") " + x["title"] for i, x in enumerate(top[:3])))
    if tech: lines.append("Tech: " + tech[0]["title"])
    with Stage("mail", "Reading today's tasks", "tasks.json"):
        td = now_ist().date().isoformat(); ts = sorted([t for t in _tasks() if t["status"] == "pending" and t["due"][:10] <= td], key=lambda t: t["due"])
    lines.append("Aaj ke tasks: " + ("; ".join(fmt_dt(t["due"]) + " " + t["title"] for t in ts[:6]) if ts else "koi pending task nahi."))
    return "\n".join(lines) + "\nTake care, Sir."

def daily_briefing(): return briefing_text()

# =============== 4. MEMORY, SEARCH, EXPORT ===============
def _facts(): return jr(FACTS_PATH, [])
def remember_fact(text: str):
    t = str(text).strip()[:300]
    if len(t) < 3: return "Error: fact khaali hai."
    fs = _facts()
    if any(f["text"].lower() == t.lower() for f in fs): return "Saved: Ye fact pehle se yaad hai."
    fs.append({"id": uuid.uuid4().hex[:5], "text": t, "ts": now_ist().isoformat(timespec="minutes")}); jw(FACTS_PATH, fs)
    return "Saved: Yaad rakh liya - " + t
def recall_facts(query: str = ""):
    q = str(query).lower(); fs = [f for f in _facts() if q in f["text"].lower()][-15:]
    return "\n".join("- " + f["text"] + " (id " + f["id"] + ")" for f in fs) if fs else "Koi fact nahi mila."
def forget_fact(fid):
    fs = _facts(); n = [f for f in fs if f["id"] != str(fid)]; jw(FACTS_PATH, n); return J({"ok": len(n) != len(fs)})
def facts_text(): return "\n".join("- " + f["text"] for f in _facts()[-12:])
def facts_list(): return J({"facts": _facts()})

def usearch(q):
    q = str(q).strip().lower(); out = []
    if len(q) < 2: return J({"items": []})
    for f in glob.glob(SESS_DIR + "/*.json"):
        d = jr(f, None)
        if not d: continue
        hit = next((m for m in d.get("messages", []) if q in m["content"].lower()), None)
        if q in d.get("title", "").lower() or hit:
            sn = ""
            if hit: i = hit["content"].lower().find(q); sn = hit["content"][max(0, i - 30):i + 70].replace("\n", " ")
            out.append({"type": "chat", "title": d.get("title", ""), "snip": sn, "ref": d["id"]})
    for f in glob.glob(NOTES_DIR + "/**/*.txt", recursive=True):
        try: body = pathlib.Path(f).read_text()
        except Exception: continue
        if q in f.lower() or q in body.lower():
            i = body.lower().find(q); out.append({"type": "note", "title": os.path.relpath(f, NOTES_DIR), "snip": body[max(0, i - 30):i + 70].replace("\n", " ") if i >= 0 else "", "ref": file_link(f)})
    for f in glob.glob(MEDIA_DIR + "/reports/**/*.pdf", recursive=True):
        if q in f.lower(): out.append({"type": "report", "title": os.path.basename(f), "snip": "", "ref": file_link(f)})
    for t in _tasks():
        if q in t["title"].lower(): out.append({"type": "task", "title": t["title"], "snip": fmt_dt(t["due"]) + " · " + t["status"], "ref": t["id"]})
    for fct in _facts():
        if q in fct["text"].lower(): out.append({"type": "fact", "title": fct["text"], "snip": "", "ref": fct["id"]})
    return J({"items": out[:60]})

def export_chat(sid, fmt="md"):
    d = jr(_sp(sid), None)
    if not d: return J({"ok": False, "error": "chat nahi mili"})
    pathlib.Path(MEDIA_DIR + "/exports").mkdir(parents=True, exist_ok=True)
    base = MEDIA_DIR + "/exports/" + slug(d.get("title", "chat"))[:40] + "_" + now_ist().strftime("%Y%m%d_%H%M")
    if fmt == "json": p = base + ".json"; pathlib.Path(p).write_text(json.dumps(d, ensure_ascii=False, indent=1))
    else:
        p = base + ".md"; pathlib.Path(p).write_text("# " + d.get("title", "Chat") + "\n\n" + "\n\n".join(("**You**" if m["role"] == "user" else "**AXINUS**") + " (" + fmt_dt(m["ts"]) + "):\n" + m["content"] for m in d["messages"]))
    return J({"ok": True, "link": file_link(p), "name": os.path.basename(p)})

def files_list():
    fs = sorted(glob.glob(MEDIA_DIR + "/reports/**/*.pdf", recursive=True) + glob.glob(MEDIA_DIR + "/exports/*") + glob.glob(NOTES_DIR + "/**/*.txt", recursive=True), key=os.path.getmtime, reverse=True)[:30]
    return J({"files": [{"name": os.path.relpath(f, ROOT_DIR), "link": file_link(f)} for f in fs]})

# ---------- registration ----------
def _reg2():
    for fn, d, w in [(add_task, "Add a task/reminder (title, when='YYYY-MM-DD HH:MM' IST). Alerts 15 min before and at start", "mail"), (list_tasks, "List tasks (scope: upcoming, today, all, history)", "mail"), (complete_task, "Mark a pending task done (task = id or title words)", "mail"), (delete_task, "Delete a task (task = id or title words)", "mail"), (get_news, "India/world news from RSS (category: top, tech, ai, science, business, world; n)", "research"), (daily_briefing, "Spoken daily briefing: top news + today's tasks", "research"), (remember_fact, "Remember an important fact about the user (text)", "mail"), (recall_facts, "Recall remembered facts (query)", "mail")]:
        reg_tool(fn, d, w)
_reg2()
ADDON_API.update({"sess_list": sess_list, "sess_open": sess_open, "sess_new": sess_new, "sess_rename": sess_rename, "sess_delete": sess_delete, "sess_log": sess_log, "task_list": task_list, "task_add_ui": task_add_ui, "task_done": task_done, "task_del": task_del, "news": news, "usearch": usearch, "export_chat": export_chat, "files_list": files_list, "facts_list": facts_list, "forget_fact": forget_fact})

# startup: continue the latest conversation
_fs = sorted(glob.glob(SESS_DIR + "/*.json"), key=os.path.getmtime)
if _fs and not CUR["sid"]:
    _d = jr(_fs[-1], None)
    if _d: CUR["sid"] = _d["id"]; _restore(_d)
print("✅ ax2 data OK | chats:", len(_fs), "| tasks:", len(_tasks()))
