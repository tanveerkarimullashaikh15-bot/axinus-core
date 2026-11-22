# AXINUS boot: runs core cells then add-ons from this repo (Colab: exec(open('/content/axc/boot.py').read()))
import os, glob, traceback, subprocess
R = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else "/content/axc"
if "AXC_ROOT" in globals(): R = AXC_ROOT
os.system("pip install -q groq cohere google-genai python-docx ddgs fpdf2 pypdf phonenumbers reportlab pillow matplotlib pypdf jinja2 weasyprint pdfplumber plotly >/dev/null 2>&1")
os.system("which dot >/dev/null 2>&1 || (apt-get -qq update >/dev/null 2>&1; apt-get -qq install -y graphviz >/dev/null 2>&1)")
def _x(f):
    try: exec(compile(open(f).read(), f, "exec"), globals())
    except Exception:
        print("FAILED:", f); traceback.print_exc()
for f in ("c2_keys", "c3_tools", "c4_brain", "c5_page"):
    _x(R + "/core/" + f + ".py")
    if f == "c2_keys" and "sec" not in globals():
        print("❌ c2_keys fail hua - upar ka pehla error dekho (pip packages / Colab Secrets). Boot ruk gaya."); raise SystemExit
for f in sorted(glob.glob(R + "/addons/ax*.py")): _x(f)
print("AXINUS boot done:", open(R + "/VERSION").read().strip() if os.path.exists(R + "/VERSION") else "")

# keep the Colab runtime busy (a finished cell lets Colab idle-disconnect). Ctrl+C / stop the cell to exit.
try:
    if not (sec("AXINUS_NOBLOCK") if "sec" in globals() else ""):
        import time as _t
        print("Server chal raha hai. Is cell ko band mat karo (runtime alive rakhne ke liye).")
        while True: _t.sleep(60)
except KeyboardInterrupt:
    print("stopped")
