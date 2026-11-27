# AXINUS 7d - visuals for documents: a diagram per section + real photos (Wikimedia Commons, free licence) + optional Gemini image
import re, json, uuid, pathlib, requests
from concurrent.futures import ThreadPoolExecutor
_UA = {"User-Agent": "AXINUS/1.0 (personal study assistant; contact: owner)"}
_OKLIC = re.compile(r"cc0|public domain|cc[- ]by|pd", re.I)
def wiki_photo(q, work):
    """returns (path, caption) or None. Only freely licensed images, with credit."""
    try:
        r = requests.get("https://commons.wikimedia.org/w/api.php", params={"action": "query", "generator": "search", "gsrnamespace": 6, "gsrsearch": q + " filetype:bitmap", "gsrlimit": 8,
            "prop": "imageinfo", "iiprop": "url|mime|extmetadata|size", "iiurlwidth": 900, "format": "json"}, headers=_UA, timeout=15)
        pages = sorted((r.json().get("query", {}).get("pages", {})).values(), key=lambda p: p.get("index", 99))
        for p in pages:
            ii = (p.get("imageinfo") or [{}])[0]; md = ii.get("extmetadata", {}); lic = (md.get("LicenseShortName") or {}).get("value", "")
            if ii.get("mime") not in ("image/jpeg", "image/png") or not _OKLIC.search(lic) or ii.get("width", 0) < 500 or "-sa" in lic.lower() and False: continue
            u = ii.get("thumburl") or ii.get("url"); b = requests.get(u, headers=_UA, timeout=25).content
            if len(b) < 15000: continue
            f = work + "/ph_" + uuid.uuid4().hex[:5] + (".png" if ii["mime"].endswith("png") else ".jpg"); pathlib.Path(f).write_bytes(b)
            art = re.sub(r"<[^>]+>", "", (md.get("Artist") or {}).get("value", "Wikimedia Commons"))[:40]
            return f, "Photo: %s (%s, %s, Wikimedia Commons)" % (re.sub(r"^File:|\.\w+$", "", p["title"])[:55], art, lic)
    except Exception: pass
    return None
def gemini_image(prompt, work):
    try:
        if not globals().get("API_KEY"): return None
        r = requests.post("https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent", params={"key": API_KEY}, timeout=60,
            json={"contents": [{"parts": [{"text": "Clean, realistic educational illustration, no text or labels: " + prompt[:300]}]}]})
        for pt in r.json()["candidates"][0]["content"]["parts"]:
            d = pt.get("inlineData")
            if d:
                import base64; f = work + "/gi_" + uuid.uuid4().hex[:5] + ".png"; pathlib.Path(f).write_bytes(base64.b64decode(d["data"])); return f, "Illustration (AI-generated)"
    except Exception: pass
    return None
def add_visuals(secs, texts, work, stage=None):
    """secs: [{title,...}], texts: {i: md}. Adds a diagram to every substantial section (retry once) + photos where a concrete subject exists. Returns stats."""
    n = len(secs); st = {"diagrams": 0, "photos": 0, "ai": 0, "missing": [], "err": ""}; lock = []
    idx = [i for i in range(n) if len(texts.get(i, "")) > 500][:12]
    def dia(i):
        s = secs[i]
        for kind in ("auto", "flowchart"):
            try:
                dp, cap, mdl = make_diagram_core(s["title"] + "\n" + texts[i][:1800], kind); return i, dp, cap
            except Exception as e: st["err"] = str(e)[:90]
        return i, None, None
    got = {}
    if "make_diagram_core" in globals():
        with ThreadPoolExecutor(3) as ex:
            for f in [ex.submit(dia, i) for i in idx]:
                try: i, dp, cap = f.result(timeout=240); got[i] = (dp, cap) if dp else None
                except Exception: pass
    qs = {}
    try:
        t, _ = llm("fast", 'Reply JSON only: {"q": ["..."]}. For each section title give a short English Wikimedia Commons image search query for a REAL photo/picture of a concrete subject (organ, place, person-free object, landmark, machine, animal, plant), or "" if the topic is abstract (math, code, theory).',
                   "Document: %s\nSections:\n%s" % (secs[0].get("doc", ""), "\n".join("%d. %s" % (i + 1, secs[i]["title"]) for i in range(n))), mt=700)
        ql = json.loads(re.search(r"\{.*\}", t, re.S).group(0))["q"]; qs = {i: q for i, q in enumerate(ql[:n]) if q}
    except Exception: pass
    ph = {}
    def photo(i):
        r = wiki_photo(qs[i], work)
        if r: return i, r, "w"
        r = gemini_image(qs[i], work) if globals().get("AX_AI_IMAGES") else None
        return i, r, "a"
    with ThreadPoolExecutor(3) as ex:
        for f in [ex.submit(photo, i) for i in list(qs)[:8] if i in idx or True]:
            try:
                i, r, k = f.result(timeout=90)
                if r: ph[i] = (r, k)
            except Exception: pass
    for i in range(n):
        add = ""
        if got.get(i): add += _f(got[i][0], got[i][1]); st["diagrams"] += 1
        if i in ph:
            add += _f(ph[i][0][0], ph[i][0][1]); st["photos"] += 1; st["ai"] += ph[i][1] == "a"
        if not add and i in idx: st["missing"].append(secs[i]["title"][:30])
        if add:
            parts = re.split(r"(?<=\n)(?=## |### )", texts[i], 1) if False else None
            texts[i] = texts[i].rstrip() + "\n" + add
    return st
print("✅ ax7d visuals OK")
