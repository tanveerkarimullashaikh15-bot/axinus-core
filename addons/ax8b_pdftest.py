# AXINUS 8b - PDF Day-1 test: 10 topics, verify pages/diagrams/size
import re, time, pathlib
PDF_TOPICS = [("Photosynthesis", "make_rich_pdf", ""), ("Indian Constitution basics", "make_rich_pdf", ""), ("Python programming for beginners", "make_rich_pdf", ""),
    ("Newton's laws of motion with diagrams", "make_rich_pdf", ""), ("Machine learning overview", "make_rich_pdf", ""), ("Human digestive system", "make_rich_pdf", ""),
    ("World War 2 timeline", "make_rich_pdf", ""), ("Compound interest and finance basics", "make_rich_pdf", ""),
    ("Complete DC circuits chapter: KCL, KVL, mesh, nodal, Thevenin, Norton, superposition, star-delta", "make_long_pdf", "15-20"),
    ("Data structures and algorithms study notes", "make_long_pdf", "12-18")]
def pdf_test(n=10):
    rows = []; fn = {"make_rich_pdf": globals().get("make_rich_pdf"), "make_long_pdf": globals().get("make_long_pdf")}
    for t, tool, pg in PDF_TOPICS[:int(n or 10)]:
        t0 = time.time(); r = ""; ok = False; pages = 0; imgs = 0; kb = 0
        try:
            r = fn[tool](t, pages=pg) if tool == "make_long_pdf" else fn[tool](t)
            m = re.search(r"Saved: PDF (\S+)", str(r)) or re.search(r"(/\S+\.pdf)", str(r))
            if m:
                p = m.group(1).rstrip(",)."); kb = pathlib.Path(p).stat().st_size // 1024
                try:
                    import fitz; d = fitz.open(p); pages = len(d); imgs = sum(len(pg_.get_images()) + (1 if pg_.get_drawings() else 0) for pg_ in d)
                except Exception:
                    try:
                        from pypdf import PdfReader; rd = PdfReader(p); pages = len(rd.pages)
                    except Exception: pass
                ok = pages >= 1 and kb > 5
        except Exception as e: r = "Error: " + str(e)[:120]
        rows.append({"topic": t[:60], "tool": tool, "ok": ok, "pages": pages, "figs": imgs, "kb": kb, "sec": int(time.time() - t0), "note": "" if ok else str(r)[:140]})
    return {"pass": sum(x["ok"] for x in rows), "total": len(rows), "rows": rows}
try: ADDON_API["pdf_test"] = pdf_test; API.update(ADDON_API)
except NameError: pass
print("✅ ax8b pdf test OK")
