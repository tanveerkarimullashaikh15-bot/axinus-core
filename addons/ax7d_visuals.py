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
def ai_image(prompt, work):
    """FLUX.1 schnell via Cloudflare (free). Returns (path, caption) or None."""
    try:
        d = cf_image("Clean, realistic educational illustration, white background, soft lighting, high detail, no text, no labels, no watermark: " + prompt[:300])
        f = work + "/ai_" + uuid.uuid4().hex[:5] + ".jpg"; pathlib.Path(f).write_bytes(d); return f, "Illustration (AI-generated): " + prompt[:60]
    except Exception: return None
def _dia(title, text, out_dir):
    """diagram with role fallback (designer -> writer -> brain -> fast); last resort: no-LLM concept flow from the section's own headings."""
    last = ""
    for role in ("designer", "writer", "brain", "fast"):
        try:
            raw, _ = llm(role, SPEC_SYS, "Kind hint: auto\nDescription:\n" + (title + "\n" + text)[:3500], timeout=60)
            spec = _json_from(raw)
            if not isinstance(spec, dict): raise RuntimeError("spec parse")
            out = out_dir + "/dg_" + uuid.uuid4().hex[:6] + ".png"; ty = spec.get("type", "flowchart"); cap = str(spec.get("title", title))[:70]
            if ty == "chart": _render_chart(spec, out); return out, cap
            ns, es = _graph_from(spec)
            if len(ns) < 2: raise RuntimeError("too small")
            try: _render_dot(ns, es, out, lr=(ty == "timeline" or len(ns) > 7))
            except Exception: _render_mpl_graph(ns, es, out)
            return out, cap
        except Exception as e: last = role + ": " + str(e)[:70]
    hs = [re.sub(r"[*_`$]", "", h).strip()[:34] for h in re.findall(r"^#{2,3}\s+(.+)$", text, re.M)][:6]
    if len(hs) < 3: hs = [re.sub(r"[*_`$|]", "", x).strip()[:34] for x in re.findall(r"^\|\s*\**([^|*]{3,40})\**\s*\|", text, re.M)][:6]
    if len(hs) >= 3:
        out = out_dir + "/dg_" + uuid.uuid4().hex[:6] + ".png"; ns = [title[:34]] + hs; es = [[ns[0], x, ""] for x in hs]
        try: _render_dot(ns, es, out, lr=False)
        except Exception: _render_mpl_graph(ns, es, out)
        return out, "Overview: " + title[:50]
    raise RuntimeError(last or "no diagram")
def add_visuals(secs, texts, work, stage=None):
    """secs: [{title,...}], texts: {i: md}. Adds a diagram to every substantial section (retry once) + photos where a concrete subject exists. Returns stats."""
    n = len(secs); st = {"diagrams": 0, "photos": 0, "ai": 0, "missing": [], "err": ""}; lock = []
    idx = [i for i in range(n) if len(texts.get(i, "")) > 500][:12]
    def dia(i):
        s = secs[i]
        for kind in ("auto",):
            try:
                dp, cap = _dia(s["title"], texts[i][:1800], work); return i, dp, cap
            except Exception as e: st["err"] = str(e)[:120]
        return i, None, None
    got = {}
    if True:
        with ThreadPoolExecutor(3) as ex:
            for f in [ex.submit(dia, i) for i in idx]:
                try: i, dp, cap = f.result(timeout=240); got[i] = (dp, cap) if dp else None
                except Exception: pass
    qs = {}
    try:
        t, _ = llm("writer", 'Reply JSON only: {"q": ["..."]}. For each section title give a short English Wikimedia Commons image search query for a REAL photo/picture of a concrete subject (organ, place, person-free object, landmark, machine, animal, plant), or "" if the topic is abstract (math, code, theory).',
                   "Document: %s\nSections:\n%s" % (secs[0].get("doc", ""), "\n".join("%d. %s" % (i + 1, secs[i]["title"]) for i in range(n))), mt=700)
        ql = json.loads(re.search(r"\{.*\}", t, re.S).group(0))["q"]; qs = {i: q for i, q in enumerate(ql[:n]) if q}
    except Exception: pass
    if not qs: qs = {i: re.sub(r"\band\b|&", " ", secs[i]["title"]) for i in idx[:6]}; st["err"] += " (photo queries: titles)"
    ph = {}
    def photo(i):
        r = wiki_photo(qs[i], work)
        if r: return i, r, "w"
        r = ai_image(qs[i], work)
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
