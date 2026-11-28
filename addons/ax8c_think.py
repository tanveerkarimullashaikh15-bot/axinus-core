# Think route: general reasoning / explanation questions go to NVIDIA free models (Kimi/DeepSeek/GLM).
# PRIVACY: NVIDIA collects prompts, so nothing personal ever goes here (no memory, no history with private topics, no tools).
import re as _re_t
_AXPRIV = _re_t.compile(r"(?i)(whatsapp|youtube|yt\b|gmail|e-?mail|mail\b|contact|sms|message|msg|call\b|phone|dial|note|task|remind|alarm|calendar|location|password|otp|pin\b|bank|upi|payment|paytm|account|address|aadhaar|pan\b|my (file|image|photo|pdf|drive|memory)|upload|drive|screen|camera|apk|app\b|open |play |send |delete|install|volume|brightness|wifi|bluetooth|\bmera\b|\bmeri\b|\bmere\b|\bmujhe\b.*(bhej|call|dikha))")
_AXTHINK = _re_t.compile(r"(?i)(explain|why\b|kyun|kyu\b|samjha|compare|difference|vs\b|analy[sz]e|reason|brainstorm|plan\b|strategy|solve|prove|derive|calculate|math|logic|puzzle|pros and cons|advantage|how (does|do|to|can)|kaise|what is|kya hai|should i|suggest|idea|essay|summar|code review|algorithm|debug|architecture|design)")
_AXTSYS = "You are AXINUS, a calm, precise assistant (Jarvis-like; address the user as 'Sir'; reply in the user's language, Hinglish if they use it). Answer directly and correctly; short for simple questions, structured and detailed only when the question needs it. Reason carefully; if unsure, say so. Never invent facts."
def _ax_hist_private():
    try: return any(_AXPRIV.search(str(h.get("content", ""))) for h in HISTORY[-4:])
    except Exception: return False
def think_ok(task):
    t = str(task)
    return bool(NVK) and 12 < len(t) < 3000 and not _AXPRIV.search(t) and bool(_AXTHINK.search(t) or len(t) > 140) and not _ax_hist_private()
_ax_orig_brain = brain_loop
def brain_loop(task):
    if think_ok(task):
        try:
            hist = [h for h in HISTORY[-6:] if h.get("role") in ("user", "assistant") and isinstance(h.get("content"), str)]
            msgs = [{"role": "system", "content": _AXTSYS + "\nDate: " + get_datetime()}] + hist + [{"role": "user", "content": str(task)}]
            m, _u = chat("think", msgs, None, 1800, 90, False); t = (m.content or "")
            if t and len(t.strip()) > 2:
                try: JOB["ntools"] = 0
                except Exception: pass
                return t.strip()
        except Exception as e: print("[think] fallback:", str(e)[:120])
    return _ax_orig_brain(task)

def nvidia_check():
    """Lists NVIDIA free models actually available with your key and tests each family with one tiny call."""
    if not NVK: return "NVIDIA key not found. Colab secret name must be NVIDIA_API_KEY."
    ids = _nv_ids(); out = ["NVIDIA models visible: %d" % len(ids)]
    for fam in ("kimi", "deepseek", "glm", "nemotron"):
        m = [i for i in ids if fam in i.lower()]
        if not m: out.append(fam + ": not listed"); continue
        for mid in m[:2]:
            t0 = time.time()
            try:
                r = _call(("nvidia", mid), [{"role": "user", "content": "Say OK"}], None, "think", 20, 60)
                out.append("%s: OK %.1fs" % (mid, time.time() - t0))
            except Exception as e: out.append("%s: FAIL %s" % (mid, str(e)[:90]))
    return "\n".join(out)
try: reg_tool(nvidia_check, "Check which NVIDIA free models work (say 'nvidia check')", "utils"); _GRP.append((r"nvidia[ _]?check", ["nvidia_check"]))
except Exception as e: print("[think] reg", e)
