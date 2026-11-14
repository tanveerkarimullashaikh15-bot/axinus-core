# AXINUS 7c - long-document engine: math rendering, textbook HTML, TOC with real page numbers, page-count loop, DC-circuits pack assembly, generic sectioned writer
import re, os, io, json, base64, html as _h, pathlib, uuid, time, datetime, threading, contextlib
from concurrent.futures import ThreadPoolExecutor

CUR_TASK = globals().get("CUR_TASK") or [""]
LONG_DIR = globals().get("LONG_DIR") or "/tmp/ax_long"
_MC = globals().get("_MC") or {}

@contextlib.contextmanager
def _stage(w, msg, model=""):
    if "Stage" in globals():
        with Stage(w, msg, model) as st: yield st
    else:
        class _S: fail = False; note = ""; model = ""
        yield _S()

# ---------------- math -> image ----------------
def _tex_fix(t):
    t = re.sub(r"\\(?:text|mathrm)\{([^{}]*)\}", lambda m: r"\mathrm{" + m.group(1).strip().replace(" ", r"\ ") + "}" if " " in m.group(1).strip() else m.group(0), t.strip())
    for a, b in ((r"\dfrac", r"\frac"), (r"\tfrac", r"\frac"), (r"\text{", r"\mathrm{"), (r"\dots", r"\ldots"), (r"\Longleftrightarrow", r"\Leftrightarrow"), (r"\longrightarrow", r"\rightarrow"), (r"\!", ""), (r"\displaystyle", "")): t = t.replace(a, b)
    return t
def _plain_tex(t):
    for a, b in ((r"\Omega", "Ω"), (r"\Delta", "Δ"), (r"\Sigma", "Σ"), (r"\eta", "η"), (r"\pi", "π"), (r"\times", "×"), (r"\parallel", "∥"), (r"\Rightarrow", "⇒"), (r"\rightarrow", "→"), (r"\sum", "Σ"), (r"\quad", "  "), (r"\qquad", "   "), (r"\,", " "), (r"\mathrm", ""), (r"\frac", ""), (r"\left", ""), (r"\right", "")): t = t.replace(a, b)
    return re.sub(r"[{}\\]", "", t)
def _math_png(tex, fs):
    key = (tex, fs)
    if key in _MC: return _MC[key]
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from PIL import Image
    import numpy as np
    plt.rcParams["mathtext.fontset"] = "dejavusans"; dpi = 300
    fig = plt.figure(figsize=(14, 2.2), dpi=dpi); fig.patch.set_alpha(0)
    t = fig.text(0.02, 0.5, "$" + _tex_fix(tex) + "$", fontsize=fs, color="#1b2733", va="baseline", ha="left")
    fig.canvas.draw(); bb = t.get_window_extent(fig.canvas.get_renderer()); H = fig.get_size_inches()[1] * dpi; base = 0.5 * H
    buf = np.asarray(fig.canvas.buffer_rgba()).copy(); plt.close(fig); pad = 4
    x0, x1 = int(max(bb.x0 - pad, 0)), int(min(bb.x1 + pad, buf.shape[1])); y0, y1 = int(max(bb.y0 - pad, 0)), int(min(bb.y1 + pad, buf.shape[0]))
    crop = buf[buf.shape[0] - y1: buf.shape[0] - y0, x0:x1]; im = Image.fromarray(crop); bio = io.BytesIO(); im.save(bio, "PNG")
    r = ("data:image/png;base64," + base64.b64encode(bio.getvalue()).decode(), (x1 - x0) * 72 / dpi, (y1 - y0) * 72 / dpi, (base - y0) * 72 / dpi)
    _MC[key] = r; return r
def _math_html(tex, display, fs_body=10.4):
    rows = [tex]
    if "aligned" in tex:
        body = re.sub(r"\\(begin|end)\{aligned\}", "", tex); rows = [r.replace("&", " ") for r in re.split(r"\\\\", body) if r.strip()]
    out = []
    for r in rows:
        try:
            src, w, h, dep = _math_png(r, 13 if display else fs_body)
            out.append('<img class="mi" src="%s" style="width:%.1fpt;height:%.1fpt;vertical-align:-%.1fpt">' % (src, w, h, dep) if not display else '<img class="md" src="%s" style="width:%.1fpt;height:%.1fpt">' % (src, w, h))
        except Exception:
            out.append("<i>%s</i>" % _h.escape(_plain_tex(r)))
    return ('<div class="dm">' + "<br>".join(out) + "</div>") if display else "".join(out)

_MR = re.compile(r"(\$\$.+?\$\$|\$(?![\s$])[^$\n]+?(?<![\s$])\$)", re.S)
def _inl(s):
    s = _h.escape(s, quote=False); s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s); s = re.sub(r"(?<![\*\w])\*(?!\s)(.+?)(?<!\s)\*(?![\*\w])", r"<i>\1</i>", s); return re.sub(r"`(.+?)`", r"<code>\1</code>", s)
def _rich(s, wrap=True):
    parts = _MR.split(s); out = []; run = []
    def fl():
        if run:
            t = "".join(run).strip()
            if t: out.append("<p>%s</p>" % t if wrap else t)
            run.clear()
    for i, p in enumerate(parts):
        if i % 2 == 0: run.append(_inl(p))
        elif p.startswith("$$") and wrap: fl(); out.append(_math_html(p[2:-2], True))
        else: run.append(_math_html(p[2:-2] if p.startswith("$$") else p[1:-1], False))
    fl(); return "".join(out)

CO_LABEL = {"DEF": "Definition", "STATEMENT": "Statement", "FORMULA": "Key Formula", "EXAM": "Exam Point", "ANS": "Answer", "NOTE": "Note"}
def md2(text, st):
    out = []; para = []; rows = []; lst = []; ltag = [None, 1]
    def fl():
        if para: out.append(_rich(" ".join(para))); para.clear()
        if lst: out.append("<%s%s>%s</%s>" % (ltag[0], (' start="%d"' % ltag[1]) if ltag[0] == "ol" and ltag[1] != 1 else "", "".join("<li>%s</li>" % _rich(x, False) for x in lst), ltag[0])); lst.clear()
        if rows:
            w = max(len(r) for r in rows); r2 = [r + [""] * (w - len(r)) for r in rows]
            out.append('<table><tr>%s</tr>%s</table>' % ("".join("<th>%s</th>" % _rich(c, False) for c in r2[0]), "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % _rich(c, False) for c in r) for r in r2[1:]))); rows.clear()
    for ln in str(text).splitlines():
        s = ln.strip()
        if not s: fl(); continue
        m = re.match(r"^!\[(.*?)\]\((.+?)\)$", s)
        if m:
            fl(); st["fig"] += 1
            try:
                raw = open(m.group(2), "rb").read(); from PIL import Image as _I; w_, h_ = _I.open(io.BytesIO(raw)).size; b = "data:image/png;base64," + base64.b64encode(raw).decode()
                out.append('<figure%s><img src="%s"><figcaption><b>Figure %d.</b> %s</figcaption></figure>' % (' class="tall"' if h_ / max(w_, 1) > 0.6 else "", b, st["fig"], _inl(m.group(1))))
            except Exception: pass
            continue
        m = re.match(r"^>\s*\[(\w+)\]\s*(.*)", s)
        if m: fl(); k = m.group(1).upper(); out.append('<div class="co co-%s"><span class="tag">%s</span>%s</div>' % (k, CO_LABEL.get(k, k.title()), _rich(m.group(2)))); continue
        if s.startswith("|"):
            if para or lst: fl()
            c = [x.strip() for x in s.strip().strip("|").split("|")]
            if not all(re.match(r"^:?-{2,}:?$", x) for x in c): rows.append(c)
            continue
        m = re.match(r"^(#{1,4})\s+(.*)", s)
        if m: fl(); lv = len(m.group(1)); tg = "h2" if lv <= 2 else "h3"; out.append("<%s>%s</%s>" % (tg, _rich(m.group(2), False), tg)); continue
        m = re.match(r"^([-*•])\s+(.*)", s)
        if m:
            if rows or para or (lst and ltag[0] != "ul"): fl()
            ltag[0] = "ul"; lst.append(m.group(2)); continue
        m = re.match(r"^(\d+)[.)]\s+(.*)", s)
        if m:
            if rows or para or (lst and ltag[0] != "ol"): fl()
            if not lst: ltag[:] = ["ol", int(m.group(1))]
            lst.append(m.group(2)); continue
        if lst or rows: fl()
        para.append(s)
    fl(); return "\n".join(out)

CSS = """
*{box-sizing:border-box} html,body{background:#fff} body{font-family:'Noto Sans','DejaVu Sans',Arial,sans-serif;color:#1b2733;font-size:%(fs)spt;line-height:%(lh)s;margin:0}
.cover{height:262mm;display:flex;flex-direction:column;justify-content:center;page-break-after:always;border-left:10px solid #0b2545;padding-left:16mm}
.cover .k{color:#1f6feb;letter-spacing:.18em;text-transform:uppercase;font-size:10pt;font-weight:700}.cover h1{font-size:34pt;line-height:1.1;color:#0b2545;margin:8px 0 10px;border:0;padding:0}
.cover .s{font-size:13pt;color:#3b5878;margin-bottom:26px}.cover .m{font-size:10pt;color:#5b6b7b;line-height:1.7}.cover .bar{width:90px;height:5px;background:#1f6feb;margin:6px 0 20px}
h1.ch{font-size:21pt;color:#0b2545;margin:0 0 10px;padding-bottom:6px;border-bottom:3px solid #1f6feb;%(pb)s;break-after:avoid;break-inside:avoid}h1.ch .kick{display:block;font-size:9.5pt;color:#1f6feb;letter-spacing:.14em;text-transform:uppercase;margin-bottom:2px}
h2{font-size:13.5pt;color:#0b2545;margin:16px 0 5px;padding-left:8px;border-left:4px solid #1f6feb;break-after:avoid}h3{font-size:11.4pt;color:#1f4f99;margin:13px 0 4px;break-after:avoid}
p{margin:0 0 6px;text-align:justify;hyphens:auto}ul,ol{margin:2px 0 8px 20px;padding:0}li{margin-bottom:3px;text-align:left}
.co{margin:9px 0;padding:8px 12px;border-left:4px solid #1f6feb;background:#eef4fc;border-radius:2px;break-inside:avoid}.co .tag{display:block;font-size:7.8pt;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#1f6feb;margin-bottom:2px}
.co-FORMULA{background:#f4f8ff;border:1px solid #bcd3f2;border-left:4px solid #0b2545}.co-FORMULA .tag{color:#0b2545}.co-EXAM{background:#fff8e6;border-left-color:#c58b00}.co-EXAM .tag{color:#9a6b00}.co-ANS{background:#eaf6ee;border-left-color:#2c7a4b}.co-ANS .tag{color:#2c7a4b}
.co p{margin:0 0 3px}.dm{text-align:center;margin:5px 0}.dm img{max-width:100%%;height:auto}.mi{display:inline-block}
table{border-collapse:collapse;width:100%%;margin:8px 0 12px;font-size:9.3pt;break-inside:avoid}th{background:#0b2545;color:#fff;text-align:left;padding:5px 7px}td{border:1px solid #b9c7d8;padding:4px 7px;vertical-align:top}tr:nth-child(even) td{background:#f3f7fc}
figure{margin:10px 0;text-align:center;break-inside:avoid}figure img{max-width:100%%;max-height:%(fh)smm}figcaption{font-size:8.6pt;color:#4a5b6c;margin-top:3px}
.toc{page-break-after:always}.toc h1{font-size:22pt;color:#0b2545;border-bottom:3px solid #1f6feb;padding-bottom:6px}.toc .r{display:flex;align-items:baseline;margin:5px 0;font-size:11pt}.toc .r .t{flex:0 1 auto}.toc .r .d{flex:1 1 auto;border-bottom:1.3px dotted #8aa;margin:0 6px;position:relative;top:-3px}.toc .r .p{color:#0b2545;font-weight:700}.toc .sec{font-weight:700;color:#1f6feb;margin-top:12px;font-size:9pt;letter-spacing:.12em;text-transform:uppercase}
th .mi{filter:invert(1) brightness(1.5)}figure.tall img{max-height:%(th)smm}
code{font-family:'DejaVu Sans Mono',monospace;font-size:8.8pt;background:#eef2f7;padding:1px 4px;border-radius:3px}
"""
def build_html(meta, chapters, toc_pages=None, tier="full"):
    st = {"fig": 0}; pb = "break-before:page" if tier == "full" else "margin-top:20px"; fs = {"full": 10.4, "std": 10.2, "dense": 9.4, "dense2": 9.0, "compact": 9.6, "tight": 9.2}.get(tier, 10.4); fh = {"full": 95, "std": 88, "dense": 58, "dense2": 50, "compact": 66, "tight": 58}.get(tier, 90)
    h = ['<!doctype html><html><head><meta charset="utf-8"><style>' + (CSS % {"fs": fs, "pb": pb, "fh": fh, "lh": 1.42 if tier == "dense2" else 1.52, "th": {"full": 135, "std": 125, "dense": 100, "dense2": 82}.get(tier, 90)}) + "</style></head><body>"]
    h.append('<div class="cover"><div class="k">%s</div><div class="bar"></div><h1>%s</h1><div class="s">%s</div><div class="m">%s</div></div>' % (_h.escape(meta.get("kicker", "")), _h.escape(meta["title"]), _h.escape(meta.get("subtitle", "")), "<br>".join(_h.escape(x) for x in meta.get("lines", []))))
    h.append('<div class="toc"><h1>Table of Contents</h1>')
    for i, c in enumerate(chapters):
        if c.get("section"): h.append('<div class="sec">%s</div>' % _h.escape(c["section"]))
        h.append('<div class="r"><span class="t">%s</span><span class="d"></span><span class="p">%s</span></div>' % (_h.escape((c["kick"] + "  " if c.get("kick") else "") + c["title"]), (toc_pages or {}).get(i, "")))
    h.append("</div>")
    for c in chapters: h.append('<h1 class="ch" id="c%d">%s%s</h1>' % (chapters.index(c), ('<span class="kick">%s</span>' % _h.escape(c["kick"])) if c.get("kick") else "", _h.escape(c["title"]))); h.append(md2(c["md"], st))
    h.append("</body></html>"); return "\n".join(h)

# ---------------- rendering ----------------
def _chromium_ok():
    try:
        if "PW" in globals() and PW.get("state") == "ready": return True
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p: b = p.chromium.launch(args=["--no-sandbox"]); b.close()
        return True
    except Exception: return False
def _render_pdf(html, out, label):
    err = ""
    if _chromium_ok():
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                b = p.chromium.launch(args=["--no-sandbox"]); pg = b.new_page(); pg.set_content(html, wait_until="load")
                pg.pdf(path=out, format="A4", print_background=True, display_header_footer=True, margin={"top": "16mm", "bottom": "18mm", "left": "15mm", "right": "15mm"}, header_template="<span></span>",
                       footer_template='<div style="font-size:8px;width:100%%;padding:0 15mm;color:#6b7c8d;display:flex;justify-content:space-between;font-family:sans-serif"><span>%s</span><span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span></div>' % _h.escape(label))
                b.close()
            if os.path.exists(out) and os.path.getsize(out) > 5000: return "chromium"
        except Exception as e: err = "chromium: " + str(e)[:60]
    try:
        from weasyprint import HTML
        css = "@page{size:A4;margin:16mm 15mm 18mm 15mm;@bottom-right{content:'Page ' counter(page) ' of ' counter(pages);font-size:8pt;color:#6b7c8d}@bottom-left{content:'%s';font-size:8pt;color:#6b7c8d}}" % label.replace("'", "")
        HTML(string=html.replace("</style>", css + "</style>", 1)).write_pdf(out); return "weasyprint"
    except Exception as e: raise RuntimeError("no PDF engine worked (%s | weasyprint: %s)" % (err, str(e)[:60]))
def _norm(s):
    import unicodedata; return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", s).lower())
def _find_pages(pdf, chapters, skip):
    from pypdf import PdfReader
    r = PdfReader(pdf); txt = [_norm(p.extract_text() or "") for p in r.pages]; res = {}; cur = skip
    for i, c in enumerate(chapters):
        key = _norm((c.get("kick") or "") + c["title"]); hit = next((p for p in range(cur, len(txt)) if key in txt[p]), None)
        if hit is not None: res[i] = hit + 1; cur = hit
    return res, len(txt)
def build_doc(out, meta, chapters, tier="full"):
    """two-pass: render, locate headings, re-render with real TOC page numbers, add PDF bookmarks"""
    label = meta.get("footer", meta["title"])[:70]; eng = _render_pdf(build_html(meta, chapters, None, tier), out, label)
    pm, n = _find_pages(out, chapters, 2)
    if pm: eng = _render_pdf(build_html(meta, chapters, pm, tier), out, label); pm, n = _find_pages(out, chapters, 2)
    try:
        from pypdf import PdfReader, PdfWriter
        r = PdfReader(out); w = PdfWriter(); w.append(r); w.add_outline_item("Cover", 0); w.add_outline_item("Table of Contents", 1)
        for i, c in enumerate(chapters):
            if i in pm: w.add_outline_item(((c.get("kick") or "") + " " + c["title"]).strip(), pm[i] - 1)
        w.add_metadata({"/Title": meta["title"], "/Author": "AXINUS"}); w.write(out)
    except Exception: pass
    return eng, n, pm

def parse_pages(text):
    t = str(text).lower(); m = None
    for m in re.finditer(r"(\d{1,3})\s*(?:to|-|–|—|se)\s*(\d{1,3})\s*(?:pages?|pg|pp|page)", t): pass
    if m:
        a, b = int(m.group(1)), int(m.group(2)); return (min(a, b), max(a, b)) if 0 < min(a, b) <= max(a, b) <= 400 else (0, 0)
    ms = list(re.finditer(r"(\d{1,3})\s*\+?\s*pages?\b", t))
    if ms: n = int(ms[-1].group(1)); return (max(1, int(n * 0.85)), int(n * 1.15) + 1) if 1 < n <= 400 else (0, 0)
    return (0, 0)

# ---------------- DC circuits pack assembly ----------------
def _tbl(head, rows): return "| " + " | ".join(head) + " |\n|" + "---|" * len(head) + "\n" + "\n".join("| " + " | ".join(r) + " |" for r in rows) + "\n"
COMPARE = None
def _compare():
    return "\n".join([
        "## 1. Ideal vs Practical Voltage Source", _tbl(["Property", "Ideal voltage source", "Practical voltage source"], [["Internal resistance", "Zero", "Finite $R_s$ in series"], ["Terminal voltage", "Constant, $V = V_S$", "$V = V_S - IR_s$ (falls with load)"], ["Short-circuit current", "Infinite (not realisable)", "$V_S/R_s$"], ["V–I characteristic", "Horizontal line", "Straight line with slope $-R_s$"], ["Voltage regulation", "0 %", "Greater than 0 %"], ["Existence", "Theoretical model", "Real batteries and generators"]]),
        "## 2. Ideal vs Practical Current Source", _tbl(["Property", "Ideal current source", "Practical current source"], [["Internal resistance", "Infinite", "Finite $R_p$ in parallel"], ["Load current", "Constant, $I = I_S$", "$I = I_S - V/R_p$"], ["Open-circuit voltage", "Infinite (not realisable)", "$I_SR_p$"], ["V–I characteristic", "Vertical line", "Line with slope $-1/R_p$"], ["Must never be", "Open-circuited", "Open-circuited for long (large voltage)"], ["Existence", "Theoretical model", "Transistor and photodiode outputs"]]),
        "## 3. Voltage Source vs Current Source", _tbl(["Point", "Voltage source", "Current source"], [["Fixed quantity", "Voltage", "Current"], ["Ideal internal resistance", "Zero", "Infinite"], ["Practical model", "Series resistance", "Parallel resistance"], ["Forbidden condition", "Short circuit", "Open circuit"], ["Natural analysis method", "Mesh analysis", "Nodal analysis"], ["Typical examples", "Battery, DC supply", "Transistor collector, photodiode"]]),
        "## 4. Mesh Analysis vs Nodal Analysis", _tbl(["Point", "Mesh analysis", "Nodal analysis"], [["Basic law", "KVL", "KCL"], ["Unknowns", "Mesh currents", "Node voltages"], ["Number of equations", "Number of meshes", "Number of nodes minus one"], ["Best when", "More nodes than meshes, voltage sources", "More meshes than nodes, current sources"], ["Reference needed", "No", "Yes, reference node"], ["Limitation", "Planar circuits only", "Voltage source between two non-reference nodes needs a super-node (outside syllabus)"]]),
        "## 5. Thevenin vs Norton Equivalent", _tbl(["Point", "Thevenin equivalent", "Norton equivalent"], [["Source", "Voltage source $V_{th}$", "Current source $I_N$"], ["Resistance connection", "In series", "In parallel"], ["Found from", "Open-circuit voltage", "Short-circuit current"], ["Resistance value", "$R_{th}$", "$R_N = R_{th}$"], ["Conversion", "$I_N = V_{th}/R_{th}$", "$V_{th} = I_NR_N$"], ["Load current", "$V_{th}/(R_{th}+R_L)$", "$I_NR_N/(R_N+R_L)$"], ["Convenient for", "Series load", "Parallel load"]])])
def _formulas():
    rows = [["Ohm's law", "$V = IR$", "V in volt, I in ampere, R in ohm"], ["Power", "$P = VI = I^2R = V^2/R$", "P in watt"], ["KCL", "$\\sum I_{in} = \\sum I_{out}$", "At any node"], ["KVL", "$\\sum V = 0$ around a loop", "Rises positive, drops negative"], ["Series resistors", "$R_{eq} = R_1 + R_2 + \\ldots$", "Same current"], ["Parallel resistors", "$1/R_{eq} = 1/R_1 + 1/R_2 + \\ldots$", "Same voltage"], ["Voltage divider", "$V_k = V_S R_k/R_{eq}$", "Series circuit"], ["Current divider (2 branches)", "$I_1 = I R_2/(R_1+R_2)$", "Parallel circuit"],
            ["Practical voltage source", "$V = V_S - IR_s$", "$R_s$ = internal resistance"], ["Practical current source", "$I = I_S - V/R_p$", "$R_p$ = internal resistance"], ["Source transformation", "$I_S = V_S/R_s$, $R_p = R_s$", "Valid for external circuit only"],
            ["Mesh equations (2 meshes)", "$(R_1+R_2)I_1 - R_2I_2 = V_1$ and $-R_2I_1 + (R_2+R_3)I_2 = V_2$", "Clockwise mesh currents"], ["Nodal equations (2 nodes)", "$(G_A+G_{12})V_A - G_{12}V_B = I_A$ and $-G_{12}V_A + (G_B+G_{12})V_B = I_B$", "$G = 1/R$"],
            ["Star to delta", "$R_{AB} = (R_AR_B + R_BR_C + R_CR_A)/R_C$, and cyclic", "Balanced: $R_\\Delta = 3R_Y$"], ["Delta to star", "$R_A = R_{AB}R_{CA}/(R_{AB}+R_{BC}+R_{CA})$, and cyclic", "Balanced: $R_Y = R_\\Delta/3$"],
            ["Superposition", "$I = I' + I'' + \\ldots$", "Short voltage sources, open current sources; not for power"], ["Thevenin", "$I_L = V_{th}/(R_{th}+R_L)$", "$V_{th}$ open circuit, $R_{th}$ with sources off"], ["Norton", "$I_L = I_NR_N/(R_N+R_L)$, $I_N = V_{th}/R_{th}$", "$R_N = R_{th}$"], ["Maximum power transfer", "$R_L = R_{th}$, $P_{max} = V_{th}^2/(4R_{th})$", "Efficiency 50 % at maximum power"]]
    return "Symbols: V voltage, I current, R resistance, G conductance, P power, $\\eta$ efficiency.\n\n" + _tbl(["Topic", "Formula", "Meaning / condition"], rows)
def _exam():
    return """## Important Definitions
- **KCL:** the algebraic sum of currents at a node is zero.
- **KVL:** the algebraic sum of voltages around a closed loop is zero.
- **Ideal voltage source:** fixed terminal voltage, zero internal resistance.
- **Ideal current source:** fixed current, infinite internal resistance.
- **Source transformation:** replacing a voltage source with series resistance by a current source with the same resistance in parallel ($I_S = V_S/R_s$), and the reverse.
- **Mesh:** a loop that contains no other loop. **Node:** a point where two or more elements join.
- **Superposition theorem, Thevenin's theorem, Norton's theorem, maximum power transfer theorem:** statements as given in the chapters above.

## Important Theoretical Questions (practice)
1. State and explain KCL and KVL with neat diagrams.
2. Compare ideal and practical voltage sources with their V–I characteristics.
3. Explain source transformation with the proof of $I_S = V_S/R_s$.
4. Explain mesh analysis and nodal analysis. Compare them.
5. Derive the delta-to-star conversion formulas.
6. State and explain the superposition theorem. Why is it not applicable to power?
7. State Thevenin's theorem and list the steps to find $V_{th}$ and $R_{th}$.
8. State Norton's theorem and show its relation with Thevenin's theorem.
9. Derive the condition for maximum power transfer and find the efficiency.

## Short-Answer Questions
- What is a node, a branch and a loop? Which law is based on conservation of charge?
- Why must a current source never be open-circuited?
- What is the value of a delta resistor in a balanced star of 12 Ω? **Answer:** 36 Ω.
- What is the Norton resistance of a network with $R_{th} = 5\\,\\Omega$? **Answer:** 5 Ω.
- State the efficiency at maximum power transfer. **Answer:** 50 %.
- How is a voltage source deactivated in superposition? **Answer:** replaced by a short circuit.

## Long-Answer Questions (practice)
- Derive the star-delta and delta-star formulas and apply them to a Wheatstone bridge.
- Solve a two-mesh circuit by mesh analysis and verify with nodal analysis.
- Find the Thevenin and Norton equivalents of a network and the power in a given load, and find the load for maximum power.

## Important Numerical Problem Types
1. Unknown current at a node by KCL, and loop current with voltage drops by KVL.
2. Source transformation of a network to a single source and load current.
3. Mesh currents of two-mesh networks and nodal voltages of two-node networks.
4. Equivalent resistance of a bridge using delta-star conversion.
5. Branch current by superposition with two sources.
6. Thevenin equivalent, Norton equivalent and load current.
7. Load resistance and maximum power for a given network.

> [NOTE] These are practice questions based on the syllabus. They are not predictions, and there is no guarantee that any of them will appear in an examination.

## Common Mistakes to Avoid
- Mixing current directions and voltage polarities without marking them on the diagram.
- Forgetting that the shared resistor carries $I_1 - I_2$ (not $I_1 + I_2$) when both mesh currents are clockwise.
- Shorting a current source or opening a voltage source while deactivating sources.
- Adding powers in the superposition theorem. Add currents or voltages only.
- Putting the load resistor back in while finding $R_{th}$ or $V_{th}$.
- Using the wrong star or delta resistor in the formula. Each delta resistor uses the *opposite* star resistor in the denominator.
- Writing results without units, or ignoring the sign of a current.

## Final Quick Revision
- KCL: sum of currents in = sum out. KVL: sum of voltages in a loop = 0.
- Voltage source: $V = V_S - IR_s$. Current source: $I = I_S - V/R_p$.
- Source transformation: $I_S = V_S/R_s$, $R_p = R_s$.
- Mesh: KVL, clockwise currents. Nodal: KCL, reference node.
- Star to delta: sum of products ÷ opposite resistor. Delta to star: product of adjacent ÷ sum.
- Superposition: one source at a time; short voltage, open current.
- Thevenin: $V_{th}$ (open circuit), $R_{th}$ (sources off). Norton: $I_N = V_{th}/R_{th}$.
- Maximum power: $R_L = R_{th}$, $P_{max} = V_{th}^2/(4R_{th})$, efficiency 50 %."""

def build_dc_chapters(work, tier="full"):
    D = lambda n: work + "/" + n + "_" + uuid.uuid4().hex[:4] + ".png"
    pathlib.Path(work).mkdir(parents=True, exist_ok=True)
    N = _numericals(D); T = _theory(D); ch = []
    def trim(md):
        if tier in ("compact", "tight"):
            parts = re.split(r"(?=### Solved Example)", md); return parts[0] + (parts[1] if len(parts) > 1 else "")
        return md
    ch.append({"title": "Basics of DC Circuits", "kick": "Introduction", "md": T["intro"], "section": "Foundations"})
    figs = {"kirchhoff": "\n" + _f(fig_kcl(D("kcl"), (("I_1", 7), ("I_2", 2)), (("I_3", 4), ("I_4", 5))), "KCL at a junction: incoming (blue) and outgoing (red) currents") + _f(fig_kvl(D("kvl"), 12, (1, 2, 3)), "KVL in a closed series loop"),
            "vsrc": _f(fig_vsources(D("vs")), "Ideal and practical voltage sources") + _f(fig_vi_curves(D("vi")), "V–I characteristics of ideal and practical sources (voltage source on the left, current source on the right)"),
            "isrc": _f(fig_isources(D("is")), "Ideal and practical current sources"),
            "srctrans": _f(fig_source_transform(D("stt"), 12, 3), "Source transformation: before and after (illustrative values)"), "mesh": _f(fig_mesh(D("mesh"), 12, 3, 6, 3, 9), "Mesh analysis circuit with labelled clockwise mesh currents (illustrative values)"),
            "nodal": _f(fig_nodal(D("nod"), 6, 5, 10, 5, 4), "Nodal analysis circuit with reference node and node voltages (illustrative values)"), "star": _f(fig_star_delta(D("sdt"), (None, None, None), (None, None, None)), "Star and delta networks with terminals A, B, C")}
    for i, (key, name) in enumerate(TOPICS):
        md = T[key] + figs.get(key, "")
        if key in N: md += "\n\n## Solved Numerical Examples\n" + trim(N[key])
        ch.append({"title": name, "kick": "Chapter %d" % (i + 1), "md": md, "section": "Syllabus Topics" if i == 0 else None})
    ch.append({"title": "Comparison Tables", "kick": "Part A", "md": _compare(), "section": "Revision Material"}); ch.append({"title": "Important Formula Sheet", "kick": "Part B", "md": _formulas()}); ch.append({"title": "University Exam Preparation", "kick": "Part C", "md": _exam()})
    return ch

def _dc_meta(req):
    return {"kicker": "First Year Engineering · Mumbai University", "title": "DC Circuits", "subtitle": "Basic Electrical Engineering (BEE): Complete Chapter Study Material", "footer": "Basic Electrical Engineering · DC Circuits",
            "lines": ["Kirchhoff's Laws · Sources · Source Transformation", "Mesh and Nodal Analysis · Star-Delta · Network Theorems", "All numerical answers verified by an exact solver", "Generated by AXINUS · " + datetime.datetime.now().strftime("%d %b %Y")]}

def make_dc_pdf(request="", pages=None):
    pmin, pmax = pages if pages and pages[1] else (25, 40)
    work = LONG_DIR + "/w_" + uuid.uuid4().hex[:6]; out = LONG_DIR + "/BEE_DC_Circuits_" + datetime.datetime.now().strftime("%Y%m%d_%H%M") + ".pdf"; pathlib.Path(LONG_DIR).mkdir(parents=True, exist_ok=True); tried = []
    best = None
    for tier in ("full", "std", "dense", "dense2", "compact", "tight"):
        with _stage("utils", "Building DC chapter (%s layout)" % tier, "chromium") as st:
            ch = build_dc_chapters(work, tier); eng, n, pm = build_doc(out, _dc_meta(request), ch, tier)
        tried.append((tier, n)); best = (tier, n, eng, pm, len(ch))
        if n <= pmax: break
    return out, best, tried, (pmin, pmax)

# ---------------- generic sectioned writer ----------------
def _llm_call(role, system, user, mt=3000, timeout=90):
    if "llm" in globals(): return llm(role, system, user, mt=mt, hedge=False, timeout=timeout)
    raise RuntimeError("no llm available")
def _json(t):
    m = re.search(r"\{.*\}", t, re.S)
    if not m: raise ValueError("no json")
    return json.loads(m.group(0))
WSYS = ("You are an expert author of textbook-style study material. Write ONE section in markdown. Use ### subheadings. Explain concepts fully: definition, intuition, formulas (LaTeX only between $...$ inline and $$...$$ for display; simple LaTeX: \\frac, \\sqrt, \\sum, Greek letters, subscripts), step-by-step derivations, worked examples with realistic numbers (check all arithmetic), tables where useful, applications, common mistakes. "
        "Use callout lines that each fit on ONE line: '> [DEF] ...', '> [FORMULA] $$...$$', '> [EXAM] ...'. Never repeat other sections. No title line. No code fences. Be accurate; if unsure of a fact, leave it out.")
def make_generic_doc(topic, request, pages):
    pmin, pmax = pages if pages and pages[1] else (8, 12); target_pages = (pmin + pmax) / 2.0; wpp = 330
    with _stage("brain", "Planning outline", "") as st:
        sysm = "You plan long study documents. Reply with JSON only: {\"title\": str, \"subtitle\": str, \"sections\": [{\"title\": str, \"brief\": str (what to cover, 1-2 sentences), \"diagram\": bool}]}. Between 6 and 16 sections that cover the user's request completely, in logical order, without overlap. Follow any syllabus given exactly."
        t, mdl = _llm_call("writer", sysm, "Request:\n" + request[:6000] + "\nTarget length: about %d pages." % round(target_pages), mt=1800); plan = _json(t); st.model = mdl
    secs = [s for s in plan.get("sections", []) if s.get("title")][:18]
    if len(secs) < 3: raise RuntimeError("outline too short")
    per = int(max(250, min(1100, target_pages * wpp / len(secs)))); texts = {}; ndone = [0]
    def write(i, extra=""):
        s = secs[i]; u = "Document: %s\nSection %d of %d: %s\nCover: %s\nTarget length: about %d words.%s\nUser's overall request (for context, follow its rules):\n%s" % (plan.get("title", topic), i + 1, len(secs), s["title"], s.get("brief", ""), per, extra, request[:2500])
        t, mdl = _llm_call("writer", WSYS, u, mt=min(4000, int(per * 2.2) + 400), timeout=120); return i, re.sub(r"```.*?```", "", t, flags=re.S).strip()
    with _stage("writer", "Writing %d sections" % len(secs), "") as st:
        with ThreadPoolExecutor(3) as ex:
            futs = [ex.submit(write, i) for i in range(len(secs))]
            for f in futs:
                try: i, t = f.result(timeout=900); texts[i] = t
                except Exception as e: st.note = "section failed: " + str(e)[:60]
    for i in range(len(secs)):
        if i not in texts:
            try: texts[i] = write(i)[1]
            except Exception: texts[i] = "_This section could not be generated. Please request it again._"
    work = LONG_DIR + "/w_" + uuid.uuid4().hex[:6]; pathlib.Path(work).mkdir(parents=True, exist_ok=True)
    if "make_diagram_core" in globals():
        k = 0
        for i, s in enumerate(secs):
            if s.get("diagram") and k < 6:
                try:
                    with _stage("coder", "Diagram: " + s["title"][:30], ""):
                        dp, cap, mdl = make_diagram_core(s["title"] + "\n" + texts[i][:1800], "auto"); texts[i] += _f(dp, cap); k += 1
                except Exception: pass
    meta = {"kicker": "Study Material", "title": plan.get("title", topic)[:90], "subtitle": plan.get("subtitle", ""), "footer": plan.get("title", topic)[:60], "lines": ["Generated by AXINUS · " + datetime.datetime.now().strftime("%d %b %Y")]}
    chs = [{"title": s["title"], "kick": "Section %d" % (i + 1), "md": texts[i], "section": None} for i, s in enumerate(secs)]
    out = LONG_DIR + "/" + re.sub(r"\W+", "_", meta["title"])[:40] + "_" + datetime.datetime.now().strftime("%H%M%S") + ".pdf"; pathlib.Path(LONG_DIR).mkdir(parents=True, exist_ok=True)
    eng, n, pm = build_doc(out, meta, chs, "full"); rounds = 0
    while n < pmin and rounds < 2:
        rounds += 1; need = pmin - n
        with _stage("writer", "Expanding to reach %d pages (round %d)" % (pmin, rounds), "") as st:
            order = sorted(range(len(secs)), key=lambda i: len(texts[i]))[:max(3, min(len(secs), need * 2))]
            def grow(i):
                t, _ = _llm_call("writer", WSYS, "Document: %s\nSection: %s\nHere is the current text. Rewrite it with substantially MORE depth (about %d words in total): add derivations, more worked numerical examples, a comparison table, common mistakes and exam-style questions. Keep all existing correct content.\n\n%s" % (plan.get("title", topic), secs[i]["title"], int(per * 1.7), texts[i][:6000]), mt=4000, timeout=120); return i, t
            with ThreadPoolExecutor(3) as ex:
                for f in [ex.submit(grow, i) for i in order]:
                    try: i, t = f.result(timeout=600); texts[i] = t if len(t) > len(texts[i]) else texts[i]
                    except Exception: pass
        for i, c in enumerate(chs): c["md"] = texts[i]
        eng, n, pm = build_doc(out, meta, chs, "full")
    tier = "full"
    for tier in ("std", "dense", "dense2", "compact", "tight"):
        if n <= pmax: break
        eng, n, pm = build_doc(out, meta, chs, tier)
    return out, ((tier, n, eng, pm, len(chs))), (pmin, pmax)

def make_long_pdf(topic: str, request: str = "", pages: str = "") -> str:
    """Long, detailed, multi-page textbook-style PDF (chapters, notes, full study material): outline -> sections -> real equations, diagrams, TOC with page numbers, page-count check."""
    full = str(request or "").strip()
    ct = CUR_TASK[0] if CUR_TASK else ""
    if len(ct) > len(full) and len(ct) > len(str(topic)): full = ct
    full = (str(topic) + "\n" + full).strip() if str(topic) not in full else full
    pg = parse_pages(str(pages) + " " + full) if (pages or full) else (0, 0)
    try:
        if len(re.findall(DC_KEYS, full, re.I)) >= 3 and re.search(r"circuit|bee|electrical|network", full, re.I):
            out, (tier, n, eng, pm, nch), tried, (pmin, pmax) = make_dc_pdf(full, pg); mode = "DC-circuits pack (all numericals computed by exact solver)"
        else:
            out, (tier, n, eng, pm, nch), (pmin, pmax) = make_generic_doc(str(topic)[:100], full, pg); tried = []; mode = "sectioned writer"
    except Exception as e: return "Error: long PDF fail - " + str(e)[:200]
    ok, info = verify_pdf(out) if "verify_pdf" in globals() else (True, {})
    if not ok: return "Error: PDF verify fail - " + str(info)[:150]
    lk = file_link(out) if "file_link" in globals() else out
    note = "" if (n >= pmin and n <= pmax) else " (requested %d-%d pages; got %d - %s)" % (pmin, pmax, n, "sab content aa chuka, padding nahi ki" if n < pmin else "sabse compact layout bhi isse chhota nahi hua")
    return "Saved: PDF %s (%d pages, %d chapters, TOC + page numbers + bookmarks, engine: %s, %s)%s\nPDF link: %s " % (out, n, nch, eng, mode, note, lk)

try: reg_tool(make_long_pdf, "LONG detailed multi-page PDF: full chapter, complete notes, study material, textbook, 'N pages' (topic, request=full original user request, pages='10-15'). Real equations, circuit diagrams, TOC, page numbers. Use this instead of make_rich_pdf whenever the user wants detail, many pages, a chapter or a syllabus covered", "utils")
except NameError: pass
print("✅ ax7c long-document engine OK")

# make_rich_pdf delegates to the long engine when the request is clearly big
_mrp_short = globals().get("_mrp_short") or globals().get("make_rich_pdf") or (lambda *a, **k: "Error: short PDF tool missing")
def make_rich_pdf(topic: str, content: str = "", image_path: str = "", diagram: str = "auto", theme: str = "modern"):
    ct = CUR_TASK[0] if CUR_TASK else ""; blob = str(topic) + " " + str(content) + " " + ct
    if not image_path and (parse_pages(blob)[1] >= 3 or len(ct) > 700 or re.search(r"detailed|complete|full chapter|syllabus|study material|textbook|in depth|in-depth", blob, re.I) and len(blob) > 250):
        return make_long_pdf(topic, content)
    return _mrp_short(topic, content, image_path, diagram, theme)
try: reg_tool(make_rich_pdf, "Short professional PDF report on a topic with optional image/diagram (topic, content, image_path, diagram=auto|yes|no, theme). Switches to the long engine automatically for detailed/multi-page requests", "utils")
except NameError: pass
