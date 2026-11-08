# AXINUS 3b - PDF Studio v2: Jinja2 HTML themes -> Chromium / WeasyPrint / ReportLab chain + pdf tools + image generation
import re, os, io, glob, html as _html, base64, threading, subprocess, shutil, pathlib, time, uuid, requests

THEMES = {
    "modern":   {"bg": "#ffffff", "fg": "#1b2733", "ac": "#0b6bcb", "ac2": "#e8f1fb", "font": "'Segoe UI','Noto Sans','DejaVu Sans',Arial,sans-serif", "hd": "'Segoe UI','Noto Sans',Arial,sans-serif"},
    "classic":  {"bg": "#ffffff", "fg": "#222", "ac": "#0b3c5d", "ac2": "#eaf3fa", "font": "'Noto Serif','DejaVu Serif',Georgia,serif", "hd": "'Noto Serif','DejaVu Serif',Georgia,serif"},
    "dark":     {"bg": "#0f1720", "fg": "#e4ecf4", "ac": "#4cc2ff", "ac2": "#17232f", "font": "'Segoe UI','Noto Sans',Arial,sans-serif", "hd": "'Segoe UI','Noto Sans',Arial,sans-serif"},
    "minimal":  {"bg": "#ffffff", "fg": "#111", "ac": "#111", "ac2": "#f3f3f3", "font": "'Helvetica Neue','Noto Sans',Arial,sans-serif", "hd": "'Helvetica Neue','Noto Sans',Arial,sans-serif"},
    "academic": {"bg": "#ffffff", "fg": "#1a1a1a", "ac": "#7a1f2b", "ac2": "#f7eeee", "font": "'Noto Serif','DejaVu Serif','Times New Roman',serif", "hd": "'Noto Sans','DejaVu Sans',Arial,sans-serif"},
}
TPL = """<!doctype html><html><head><meta charset="utf-8"><style>
@page { size: A4; margin: 16mm 15mm 18mm 15mm; }
*{box-sizing:border-box} html,body{background:{{t.bg}};} body{font-family:{{t.font}};color:{{t.fg}};font-size:10.6pt;line-height:1.55;margin:0}
h1{font-family:{{t.hd}};font-size:25pt;line-height:1.15;margin:0 0 4px;color:{{t.ac}}} .sub{font-size:9.5pt;opacity:.7;margin-bottom:10px;padding-bottom:8px;border-bottom:2px solid {{t.ac}}}
h2{font-family:{{t.hd}};font-size:14.5pt;color:{{t.ac}};margin:18px 0 6px;break-after:avoid} h3{font-family:{{t.hd}};font-size:11.8pt;margin:12px 0 4px;break-after:avoid}
p{margin:0 0 7px;text-align:left} ul,ol{margin:0 0 8px 20px;padding:0} li{margin-bottom:3px}
.box{background:{{t.ac2}};border-left:4px solid {{t.ac}};padding:9px 12px;margin:10px 0;border-radius:3px;break-inside:avoid}
table{border-collapse:collapse;width:100%;margin:8px 0 12px;font-size:9.4pt;break-inside:avoid} th{background:{{t.ac}};color:{{t.bg}};text-align:left;padding:5px 7px} td{border:1px solid {{t.ac}}55;padding:5px 7px;vertical-align:top} tr:nth-child(even) td{background:{{t.ac2}}}
figure{margin:12px 0;text-align:center;break-inside:avoid} figure img{max-width:100%;max-height:105mm} figcaption{font-size:8.6pt;opacity:.7;margin-top:3px}
code{font-family:'DejaVu Sans Mono',monospace;font-size:9pt;background:{{t.ac2}};padding:1px 4px;border-radius:3px}
pre{font-family:'DejaVu Sans Mono',monospace;font-size:8.6pt;background:{{t.ac2}};padding:8px 10px;border-radius:4px;white-space:pre-wrap;break-inside:avoid}
.kp li::marker{color:{{t.ac}}}
</style></head><body>
<h1>{{title}}</h1><div class="sub">{{subtitle}} · {{stamp}}</div>
{% if summary %}<div class="box"><b>Summary</b><br>{{summary|safe}}</div>{% endif %}
{% if image %}<figure><img src="{{image}}"><figcaption>{{image_cap}}</figcaption></figure>{% endif %}
{% for s in sections %}{% if s.h %}<h2>{{s.h}}</h2>{% endif %}{{s.body|safe}}{% endfor %}
{% for d in diagrams %}{% if loop.first %}<h2>Diagram</h2>{% endif %}<figure><img src="{{d.src}}"><figcaption>Figure {{loop.index}}: {{d.cap}}</figcaption></figure>{% endfor %}
{% if points %}<h2>Key Points</h2><ul class="kp">{% for p in points %}<li>{{p|safe}}</li>{% endfor %}</ul>{% endif %}
</body></html>"""
def _e(s): return _html.escape(str(s))
def _inl_h(s):
    s = _e(s); s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s); s = re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<i>\1</i>", s); return re.sub(r"`(.+?)`", r"<code>\1</code>", s)
def md_html(text):
    out = []; para = []; rows = []; lst = []; code = []; incode = False
    def fl():
        nonlocal lst
        if para: out.append("<p>" + _inl_h(" ".join(para)) + "</p>"); para.clear()
        if lst: tag = lst[0][0]; out.append("<%s>%s</%s>" % (tag, "".join("<li>%s</li>" % _inl_h(x[1]) for x in lst), tag)); lst = []
        if rows:
            w = max(len(r) for r in rows); r2 = [r + [""] * (w - len(r)) for r in rows]
            out.append("<table><tr>%s</tr>%s</table>" % ("".join("<th>%s</th>" % _inl_h(c) for c in r2[0]), "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % _inl_h(c) for c in r) for r in r2[1:]))); rows.clear()
    for ln in str(text).splitlines():
        if ln.strip().startswith("```"):
            if incode: out.append("<pre>%s</pre>" % _e("\n".join(code))); code.clear(); incode = False
            else: fl(); incode = True
            continue
        if incode: code.append(ln); continue
        s = ln.strip()
        if not s: fl(); continue
        if s.startswith("|"):
            if para or lst: fl()
            c = [x.strip() for x in s.strip("|").split("|")]
            if not all(re.match(r"^:?-{2,}:?$", x) for x in c): rows.append(c)
            continue
        m = re.match(r"^(#{1,4})\s+(.*)", s)
        if m: fl(); out.append("<%s>%s</%s>" % ("h2" if len(m.group(1)) <= 2 else "h3", _inl_h(m.group(2)), "h2" if len(m.group(1)) <= 2 else "h3")); continue
        m = re.match(r"^([-*•])\s+(.*)", s)
        if m:
            if rows or para or (lst and lst[0][0] != "ul"): fl()
            lst.append(("ul", m.group(2))); continue
        m = re.match(r"^(\d+)[.)]\s+(.*)", s)
        if m:
            if rows or para or (lst and lst[0][0] != "ol"): fl()
            lst.append(("ol", m.group(2))); continue
        if lst or rows: fl()
        para.append(s)
    fl()
    if incode: out.append("<pre>%s</pre>" % _e("\n".join(code)))
    return "\n".join(out)
def _b64(p):
    try:
        p2, _ = _prep_img(p, 1800)
        ext = "png" if str(p2).lower().endswith("png") else "jpeg"
        return "data:image/%s;base64,%s" % (ext, base64.b64encode(open(p2, "rb").read()).decode())
    except Exception:
        return ""
def render_html(title, subtitle, summary, sections, image_path, diagrams, points, theme="modern"):
    import jinja2
    t = THEMES.get(theme, THEMES["modern"])
    env = jinja2.Environment(autoescape=False)
    ctx = {"t": t, "title": _e(title), "subtitle": _e(subtitle), "stamp": now_ist().strftime("%d %b %Y, %I:%M %p IST"), "summary": _inl_h(summary) if summary else "",
           "image": _b64(image_path) if image_path else "", "image_cap": _e(os.path.basename(image_path)) if image_path else "",
           "sections": [{"h": _e(h) if h else "", "body": md_html(b)} for h, b in sections], "diagrams": [{"src": _b64(p), "cap": _e(c)} for p, c in diagrams], "points": [_inl_h(x) for x in points[:10]]}
    return env.from_string(TPL).render(**ctx)

# ---- engines ----
PW = globals().get("PW") or {"state": "none", "err": ""}
def _pw_install():
    PW["state"] = "installing"
    try:
        import importlib
        try: importlib.import_module("playwright")
        except Exception: subprocess.run("pip install -q playwright", shell=True, check=True, timeout=300)
        r = subprocess.run("python -m playwright install --with-deps chromium", shell=True, capture_output=True, timeout=900)
        PW["state"] = "ready" if r.returncode == 0 else "failed"; PW["err"] = r.stderr.decode()[-120:] if r.returncode else ""
    except Exception as e: PW["state"] = "failed"; PW["err"] = str(e)[:100]
def _pw_probe():
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p: b = p.chromium.launch(args=["--no-sandbox"]); b.close()
        PW["state"] = "ready"
    except Exception as e:
        PW["state"] = "none"; PW["err"] = str(e)[:100]
        if "playwright" not in PW.get("started", ""): PW["started"] = "playwright"; threading.Thread(target=_pw_install, daemon=True).start()
if PW["state"] == "none": threading.Thread(target=_pw_probe, daemon=True).start()
def _pdf_chromium(h, out):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--no-sandbox"]); pg = b.new_page(); pg.set_content(h, wait_until="load")
        pg.pdf(path=out, format="A4", print_background=True, display_header_footer=True, margin={"top": "16mm", "bottom": "18mm", "left": "15mm", "right": "15mm"},
               header_template="<span></span>", footer_template='<div style="font-size:8px;width:100%;padding:0 15mm;color:#888;display:flex;justify-content:space-between"><span>AXINUS Report</span><span>Page <span class="pageNumber"></span>/<span class="totalPages"></span></span></div>')
        b.close()
def _pdf_weasy(h, out):
    from weasyprint import HTML
    HTML(string=h).write_pdf(out)
ENGINE_LAST = globals().get("ENGINE_LAST") or [""]
THEME_DEFAULT = globals().get("THEME_DEFAULT") or ["modern"]
_build_pdf_rl = globals().get("_build_pdf_rl") or build_pdf
def build_pdf(out, title, subtitle, summary, sections, image_path=None, diagrams=(), points=(), theme=None):
    h = None
    try: h = render_html(title, subtitle, summary, sections, image_path, diagrams, points, theme or THEME_DEFAULT[0])
    except Exception as e: ENGINE_LAST[0] = "reportlab (html err: %s)" % str(e)[:50]
    if h:
        for name, fn in (("chromium", _pdf_chromium), ("weasyprint", _pdf_weasy)):
            if name == "chromium" and PW["state"] != "ready": continue
            try:
                fn(h, out)
                if os.path.exists(out) and os.path.getsize(out) > 3000: ENGINE_LAST[0] = name; return
            except Exception as e: ENGINE_LAST[0] = name + " failed: " + str(e)[:50]
    _build_pdf_rl(out, title, subtitle, summary, sections, image_path, diagrams, points); ENGINE_LAST[0] = "reportlab"

# ---- theme-aware tools ----
_make_rich_pdf0 = globals().get("_make_rich_pdf0") or make_rich_pdf
def make_rich_pdf(topic: str, content: str = "", image_path: str = "", diagram: str = "auto", theme: str = "modern"):
    THEME_DEFAULT[0] = theme if theme in THEMES else "modern"
    try: r = _make_rich_pdf0(topic, content, image_path, diagram)
    finally: THEME_DEFAULT[0] = "modern"
    return r + " | engine: " + ENGINE_LAST[0] if r.startswith("Saved") else r

# ---- pdf utility tools ----
def _out(name): d = REP_DIR + "/tools"; pathlib.Path(d).mkdir(parents=True, exist_ok=True); return d + "/" + name + "_" + now_ist().strftime("%H%M%S") + ".pdf"
def _ok(path, tag):
    ok, info = verify_pdf(path) if os.path.getsize(path) > 3000 else (True, {"kb": os.path.getsize(path) // 1024})
    return ("Saved: " + tag + " " + path + "\nPDF link: " + file_link(path)) if ok else "Error: output verify fail - " + str(info)
def _paths(s): return [safe_path(x.strip()) or "" for x in re.split(r"[,;\n]", str(s)) if x.strip()]
def pdf_merge(files: str):
    from pypdf import PdfWriter
    ps = _paths(files)
    if len(ps) < 2 or not all(os.path.exists(p) for p in ps): return "Error: kam se kam 2 valid PDF paths do (comma se alag)"
    w = PdfWriter()
    for p in ps: w.append(p)
    o = _out("merged"); w.write(o); return _ok(o, "merged PDF")
def pdf_split(file: str, pages: str):
    from pypdf import PdfReader, PdfWriter
    p = safe_path(file)
    if not p or not os.path.exists(p): return "Error: file nahi mili"
    r = PdfReader(p); n = len(r.pages); idx = []
    for part in re.split(r"[,; ]+", str(pages).strip()):
        m = re.match(r"^(\d+)(?:-(\d+))?$", part)
        if m: a = int(m.group(1)); b = int(m.group(2) or a); idx += [i - 1 for i in range(a, b + 1) if 1 <= i <= n]
    if not idx: return "Error: pages galat (jaise 1-3,5). Total pages: %d" % n
    w = PdfWriter()
    for i in idx: w.add_page(r.pages[i])
    o = _out("split"); w.write(o); return _ok(o, "%d pages extract" % len(idx))
def pdf_watermark(file: str, text: str = "CONFIDENTIAL"):
    from pypdf import PdfReader, PdfWriter
    from reportlab.pdfgen import canvas
    p = safe_path(file)
    if not p or not os.path.exists(p): return "Error: file nahi mili"
    r = PdfReader(p); w = PdfWriter()
    for pg in r.pages:
        W, H = float(pg.mediabox.width), float(pg.mediabox.height); b = io.BytesIO(); c = canvas.Canvas(b, pagesize=(W, H)); c.setFillAlpha(0.13); c.setFont("Helvetica-Bold", 60); c.translate(W / 2, H / 2); c.rotate(40); c.drawCentredString(0, 0, str(text)[:30]); c.save(); b.seek(0)
        pg.merge_page(PdfReader(b).pages[0]); w.add_page(pg)
    o = _out("watermark"); w.write(o); return _ok(o, "watermarked PDF")
def pdf_tables(file: str):
    import pdfplumber
    out = []
    with pdfplumber.open(safe_path(file) or "/nonexistent") as pdf:
        for i, pg in enumerate(pdf.pages[:30]):
            for t in pg.extract_tables(): out.append("Page %d:\n" % (i + 1) + "\n".join(" | ".join((c or "").strip() for c in r) for r in t[:25]))
    return ("\n\n".join(out))[:5000] if out else "Koi table nahi mila (scanned ho to analyze_pdf use karo)."
def pdf_text(file: str, pages: str = "1-5"):
    from pypdf import PdfReader
    r = PdfReader(safe_path(file) or "/nonexistent"); m = re.match(r"^(\d+)(?:-(\d+))?$", str(pages).strip()); a = int(m.group(1)) if m else 1; b = int(m.group(2) or a) if m else 5
    t = "\n".join((r.pages[i].extract_text() or "") for i in range(a - 1, min(b, len(r.pages))))
    return t[:6000] if t.strip() else "Text nahi mila (scanned PDF lagta hai) - analyze_pdf use karo."
def pdf_to_images(file: str, pages: str = "1-3"):
    p = safe_path(file)
    if not p or not os.path.exists(p): return "Error: file nahi mili"
    m = re.match(r"^(\d+)(?:-(\d+))?$", str(pages).strip()); a = m.group(1) if m else "1"; b = m.group(2) or a if m else "3"
    d = REP_DIR + "/tools"; pathlib.Path(d).mkdir(parents=True, exist_ok=True); pre = d + "/pg_" + uuid.uuid4().hex[:5]
    r = subprocess.run(["pdftoppm", "-png", "-r", "110", "-f", a, "-l", b, p, pre], capture_output=True, timeout=120)
    fs = sorted(glob.glob(pre + "*.png")) if "glob" in globals() else sorted(str(x) for x in pathlib.Path(d).glob(os.path.basename(pre) + "*.png"))
    return ("Saved: %d images\n" % len(fs) + "\n".join(file_link(f) for f in fs)) if fs else "Error: pdftoppm fail " + r.stderr.decode()[:80]

# ---- image generation (Gemini image model -> Pollinations fallback), verified ----
IMG_MODELS = ["gemini-2.5-flash-image", "gemini-3.5-flash-image", "gemini-2.0-flash-preview-image-generation"]
def _gemini_image(prompt):
    last = None
    for m in IMG_MODELS:
        try:
            r = requests.post("https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent?key=%s" % (m, API_KEY),
                              json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}}, timeout=60)
            if r.status_code != 200: last = "%s HTTP %d" % (m, r.status_code); continue
            for c in r.json().get("candidates", []):
                for pt in c.get("content", {}).get("parts", []):
                    d = pt.get("inlineData") or pt.get("inline_data")
                    if d: return base64.b64decode(d["data"]), m
            last = m + " no image"
        except Exception as e: last = m + " " + str(e)[:50]
    raise RuntimeError(last or "gemini image fail")
_gi0 = globals().get("_gi0") or generate_image
def generate_image(prompt: str):
    """Image from text (Gemini image model, Pollinations fallback). Verified before reporting."""
    d = MEDIA_DIR + "/generated"; pathlib.Path(d).mkdir(parents=True, exist_ok=True); o = d + "/img_" + now_ist().strftime("%H%M%S") + ".png"; used = ""
    try:
        data, used = _gemini_image(prompt); open(o, "wb").write(data)
    except Exception as e1:
        try:
            r = requests.get("https://image.pollinations.ai/prompt/" + requests.utils.quote(prompt[:400]) + "?width=1024&height=1024&nologo=true", timeout=60)
            if r.status_code != 200 or len(r.content) < 5000: raise RuntimeError("HTTP %d" % r.status_code)
            open(o, "wb").write(r.content); used = "pollinations"
        except Exception as e2: return "Error: image nahi bani (gemini: %s | pollinations: %s)" % (str(e1)[:60], str(e2)[:50])
    try:
        from PIL import Image; im = Image.open(o); im.verify(); w, h = Image.open(o).size
    except Exception: return "Error: image file kharab nikli"
    return "Saved: image (%dx%d) via %s\nImage link: %s" % (w, h, used, file_link(o))
reg_tool(generate_image, "Create a real picture/illustration/poster/photo-style image from a text prompt (NOT for diagrams/charts - use make_diagram). prompt = detailed English description", "eyes")
reg_tool(pdf_merge, "Merge several PDFs into one (files = comma separated paths)", "utils")
reg_tool(pdf_split, "Extract pages from a PDF (file, pages like 1-3,5)", "utils")
reg_tool(pdf_watermark, "Add diagonal text watermark to every PDF page (file, text)", "utils")
reg_tool(pdf_tables, "Extract tables from a text PDF (file)", "utils")
reg_tool(pdf_text, "Read text of PDF pages without AI (file, pages=1-5)", "utils")
reg_tool(pdf_to_images, "Convert PDF pages to PNG images (file, pages)", "utils")
reg_tool(make_rich_pdf, "Professional PDF report on a topic, optional image and auto diagram, themes: modern|classic|dark|minimal|academic (topic, content, image_path, diagram=auto|yes|no, theme)", "utils")
print("✅ ax3b PDF v2 OK | themes:", ",".join(THEMES), "| chromium:", PW["state"], "| weasyprint:", bool(__import__("importlib").util.find_spec("weasyprint")))
