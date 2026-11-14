# AXINUS 7a - circuit schematic engine: the drawing IS the netlist (connections correct by construction) + exact Fraction MNA solver
import math, os, io, pathlib, uuid
from fractions import Fraction as Fr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon

NAVY = "#0b2545"; BLUE = "#1f6feb"; GREY = "#5b6b7b"; LBLUE = "#e8f1fb"; RED = "#b3261e"
try: CIRC_DIR
except NameError: CIRC_DIR = None


def _k(p): return (round(float(p[0]), 3), round(float(p[1]), 3))
def fr(x): return x if isinstance(x, Fr) else Fr(x).limit_denominator(100000)
def fx(x, nd=3):
    """pretty number: exact integer, else decimal rounded to nd places"""
    x = fr(x)
    if x.denominator == 1: return str(x.numerator)
    s = ("%." + str(nd) + "f") % float(x); s = s.rstrip("0").rstrip("."); return s if s not in ("-0", "") else "0"
def unit_tex(u): return {"ohm": r"\Omega", "V": r"\mathrm{V}", "A": r"\mathrm{A}", "W": r"\mathrm{W}"}.get(u, u)
def L(sym, val=None, u=None):
    """mathtext label: L('R_1', 4, 'ohm') -> $R_1 = 4\\,\\Omega$"""
    if val is None: return "$%s$" % sym
    return "$%s = %s\\,%s$" % (sym, fx(val), unit_tex(u or ""))


class Sch:
    def __init__(s): s.el = []; s.wr = []; s.tx = []; s.arr = []; s.terms = []; s.gnds = []; s.cyc = []; s.extra = []; s.custom = []
    def R(s, a, b, name="", val=None, side=1, txt=None):
        s.el.append(["R", _k(a), _k(b), None if val is None else fr(val), name, side, txt]); return len(s.el) - 1
    def V(s, a, b, name="", val=None, side=1, txt=None):   # + terminal at a
        s.el.append(["V", _k(a), _k(b), None if val is None else fr(val), name, side, txt]); return len(s.el) - 1
    def I(s, a, b, name="", val=None, side=1, txt=None):   # current flows a -> b THROUGH the source (injects into b)
        s.el.append(["I", _k(a), _k(b), None if val is None else fr(val), name, side, txt]); return len(s.el) - 1
    def W(s, *pts): s.wr.append([_k(p) for p in pts])
    def T(s, xy, text, ha="center", va="center", fs=10, color=NAVY, bold=False): s.tx.append((xy, text, ha, va, fs, color, bold))
    def term(s, xy, name, dx=0.32, dy=0.0, ha="left"): s.terms.append((_k(xy), name, dx, dy, ha))
    def gnd(s, xy): s.gnds.append(_k(xy))
    def arrow(s, p, q, text="", off=(0, 0.3), color=BLUE): s.arr.append((p, q, text, off, color))
    def cycle(s, c, r, text="", cw=True, color=RED): s.cyc.append((c, r, text, cw, color))

    # ----- netlist / solver -----
    def _classes(s):
        par = {}
        def f(x):
            par.setdefault(x, x)
            while par[x] != x: par[x] = par[par[x]]; x = par[x]
            return x
        def u(a, b): par[f(a)] = f(b)
        for e in s.el: f(e[1]); f(e[2])
        for w in s.wr:
            for a, b in zip(w, w[1:]): u(a, b)
            f(w[0])
        for g in s.gnds: f(g)
        return f

    def solve(s, gnd):
        f = s._classes(); g = f(_k(gnd)); roots = sorted({f(x) for e in s.el for x in (e[1], e[2])} | {g}); roots.remove(g)
        idx = {r: i for i, r in enumerate(roots)}; n = len(roots)
        vs = [i for i, e in enumerate(s.el) if e[0] == "V" and e[3] is not None]; m = len(vs); N = n + m
        A = [[Fr(0)] * N for _ in range(N)]; z = [Fr(0)] * N
        def add(r, c, v):
            if r is not None and c is not None: A[r][c] += v
        for i, e in enumerate(s.el):
            if e[3] is None and e[0] != "V": continue   # open (no value)
            a, b = f(e[1]), f(e[2]); ia, ib = idx.get(a), idx.get(b)
            if e[0] == "R":
                gdt = 1 / e[3]
                add(ia, ia, gdt); add(ib, ib, gdt); add(ia, ib, -gdt); add(ib, ia, -gdt)
            elif e[0] == "I":     # current a->b through source: leaves node a, enters node b
                if ia is not None: z[ia] -= e[3]
                if ib is not None: z[ib] += e[3]
        for j, i in enumerate(vs):
            e = s.el[i]; a, b = f(e[1]), f(e[2]); ia, ib = idx.get(a), idx.get(b); c = n + j
            add(ia, c, 1); add(ib, c, -1); add(c, ia, 1); add(c, ib, -1); z[c] = e[3]   # i_src: current a->b through source
        # shorts (V with val None are wires handled in union by caller)
        for r in range(N):   # gauss
            p = next((q for q in range(r, N) if A[q][r] != 0), None)
            if p is None: raise ValueError("singular circuit")
            A[r], A[p] = A[p], A[r]; z[r], z[p] = z[p], z[r]; d = A[r][r]
            A[r] = [x / d for x in A[r]]; z[r] /= d
            for q in range(N):
                if q != r and A[q][r] != 0:
                    k = A[q][r]; A[q] = [x - k * y for x, y in zip(A[q], A[r])]; z[q] -= k * z[r]
        volt = {g: Fr(0)}; volt.update({r: z[idx[r]] for r in roots}); isrc = {vs[j]: z[n + j] for j in range(m)}
        return Sol(s, f, volt, isrc)

    def req(s, a, b):
        """equivalent resistance seen at a-b (independent sources must already be deactivated in this netlist)"""
        t = Sch(); t.el = [list(e) for e in s.el]; t.wr = [list(w) for w in s.wr]
        t.el.append(["I", _k(b), _k(a), Fr(1), "", 1, None])
        return t.solve(b).vd(a, b)

    # ----- drawing -----
    def draw(s, path, scale=0.45, pad=1.0, title=None, dpi=200, minw=0):
        pts = [e[1] for e in s.el] + [e[2] for e in s.el] + [p for w in s.wr for p in w] + [t[0] for t in s.tx] + [t[0] for t in s.terms] + [c[0] for c in s.cyc]
        for c in s.cyc: pts += [(c[0][0] - c[1], c[0][1] - c[1]), (c[0][0] + c[1], c[0][1] + c[1])]
        for p in s.custom: pts += p[1]
        x0 = min(p[0] for p in pts) - pad; x1 = max(p[0] for p in pts) + pad; y0 = min(p[1] for p in pts) - pad - (0.3 if s.gnds else 0); y1 = max(p[1] for p in pts) + pad
        if title: y1 += 0.7
        W = max(x1 - x0, minw); fig = plt.figure(figsize=(W * scale, (y1 - y0) * scale)); ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(x0, x1 if W == x1 - x0 else x0 + W); ax.set_ylim(y0, y1); ax.set_aspect("equal"); ax.axis("off")
        lw = 1.7
        for w in s.wr: ax.plot([p[0] for p in w], [p[1] for p in w], color=NAVY, lw=lw, solid_capstyle="round", solid_joinstyle="round", zorder=2)
        deg = {}
        for e in s.el:
            for p in (e[1], e[2]): deg[p] = deg.get(p, 0) + 1
        for w in s.wr:
            for i, p in enumerate(w): deg[p] = deg.get(p, 0) + (1 if i in (0, len(w) - 1) else 2)
        for p, d in deg.items():
            if d >= 3: ax.add_patch(Circle(p, 0.09, color=NAVY, zorder=5))
        for e in s.el: s._body(ax, e)
        for (p, q, text, off, col) in s.arr:
            ax.annotate("", xy=q, xytext=p, arrowprops=dict(arrowstyle="-|>", color=col, lw=1.6, mutation_scale=14), zorder=6)
            if text: ax.text((p[0] + q[0]) / 2 + off[0], (p[1] + q[1]) / 2 + off[1], text, ha="center", va="center", fontsize=10.5, color=col, zorder=7)
        for (c, r, text, cw, col) in s.cyc:
            a0, a1 = (60, 60 - 300) if cw else (120, 120 + 300); n = 60
            xs = [c[0] + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]; ys = [c[1] + r * math.sin(math.radians(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]
            ax.plot(xs[:-1], ys[:-1], color=col, lw=1.5, zorder=3)
            ax.annotate("", xy=(xs[-1], ys[-1]), xytext=(xs[-3], ys[-3]), arrowprops=dict(arrowstyle="-|>", color=col, lw=1.5, mutation_scale=13), zorder=4)
            if text: ax.text(c[0], c[1], text, ha="center", va="center", fontsize=11, color=col, zorder=7)
        for (p, name, dx, dy, ha) in s.terms:
            ax.add_patch(Circle(p, 0.11, facecolor="white", edgecolor=NAVY, lw=1.6, zorder=6)); ax.text(p[0] + dx, p[1] + dy, name, ha=ha, va="center", fontsize=11, color=NAVY, zorder=7)
        for p in s.gnds:
            for i, hw in enumerate((0.42, 0.28, 0.14)): ax.plot([p[0] - hw, p[0] + hw], [p[1] - 0.18 - i * 0.14] * 2, color=NAVY, lw=1.6, zorder=3)
            ax.plot([p[0], p[0]], [p[1], p[1] - 0.18], color=NAVY, lw=1.6)
        for (xy, text, ha, va, fs, col, bold) in s.tx: ax.text(xy[0], xy[1], text, ha=ha, va=va, fontsize=fs, color=col, fontweight="bold" if bold else "normal", zorder=7)
        for fn, _ in s.custom: fn(ax)
        if title: ax.text((x0 + x1) / 2, y1 - 0.45, title, ha="center", va="center", fontsize=11.5, color=NAVY, fontweight="bold")
        fig.savefig(path, dpi=dpi, facecolor="white", bbox_inches="tight", pad_inches=0.12); plt.close(fig); return path

    def _body(self, ax, e):
        kind, a, b, val, name, side, txt = e; ax_, ay = a; bx, by = b; Ln = math.hypot(bx - ax_, by - ay); ux, uy = (bx - ax_) / Ln, (by - ay) / Ln; nx, ny = -uy * side, ux * side; cx, cy = (ax_ + bx) / 2, (ay + by) / 2
        P = lambda t, o=0.0: (ax_ + ux * t + nx * o, ay + uy * t + ny * o)   # point at distance t along a->b, offset o sideways
        lw = 1.7
        if kind == "R":
            bl = min(2.2, 0.62 * Ln); t0 = (Ln - bl) / 2; ax.plot(*zip(a, P(t0)), color=NAVY, lw=lw, zorder=3); ax.plot(*zip(P(t0 + bl), b), color=NAVY, lw=lw, zorder=3)
            seg = 7; pts = [P(t0)]
            for i in range(seg): pts.append(P(t0 + bl * (i + 0.5) / seg, 0.2 * (1 if i % 2 == 0 else -1)))
            pts.append(P(t0 + bl)); ax.plot([q[0] for q in pts], [q[1] for q in pts], color=NAVY, lw=lw, zorder=3, solid_joinstyle="miter"); lo = 0.55
        elif kind == "V":
            ax.plot(*zip(a, P(Ln / 2 - 0.12)), color=NAVY, lw=lw, zorder=3); ax.plot(*zip(P(Ln / 2 + 0.12), b), color=NAVY, lw=lw, zorder=3)
            l1, l2 = P(Ln / 2 - 0.12, -0.38), P(Ln / 2 - 0.12, 0.38); ax.plot(*zip(l1, l2), color=NAVY, lw=2.6, zorder=3)
            s1, s2 = P(Ln / 2 + 0.12, -0.2), P(Ln / 2 + 0.12, 0.2); ax.plot(*zip(s1, s2), color=NAVY, lw=2.6, zorder=3)
            pp = P(Ln / 2 - 0.45, 0.42); mm = P(Ln / 2 + 0.45, 0.42); ax.text(pp[0], pp[1], "+", ha="center", va="center", fontsize=11, color=RED, fontweight="bold", zorder=7); ax.text(mm[0], mm[1], "−", ha="center", va="center", fontsize=12, color=BLUE, fontweight="bold", zorder=7); lo = 0.85
        else:
            r = 0.4; ax.plot(*zip(a, P(Ln / 2 - r)), color=NAVY, lw=lw, zorder=3); ax.plot(*zip(P(Ln / 2 + r), b), color=NAVY, lw=lw, zorder=3)
            ax.add_patch(Circle((cx, cy), r, facecolor="white", edgecolor=NAVY, lw=lw, zorder=4))
            p0, p1 = P(Ln / 2 - 0.26), P(Ln / 2 + 0.26); ax.annotate("", xy=p1, xytext=p0, arrowprops=dict(arrowstyle="-|>", color=RED, lw=1.8, mutation_scale=13), zorder=6); lo = 0.65
        un = {"R": "ohm", "V": "V", "I": "A"}[kind]
        if txt is not None: text = txt
        elif name and val is not None: text = (L(name) + "\n$%s\\,%s$" % (fx(val), unit_tex(un))) if abs(nx) > 0.3 else L(name, val, un)
        else: text = L(name) if name else ""
        if text:
            lx, ly = cx + nx * lo, cy + ny * lo; ha = "left" if nx > 0.3 else ("right" if nx < -0.3 else "center"); va = "bottom" if ny > 0.3 else ("top" if ny < -0.3 else "center")
            ax.text(lx, ly, text, ha=ha, va=va, fontsize=10.5, color=NAVY, zorder=7)


class Sol:
    def __init__(s, sch, f, volt, isrc): s.sch = sch; s.f = f; s.volt = volt; s.isrc = isrc
    def v(s, p): return s.volt[s.f(_k(p))]
    def vd(s, p, q): return s.v(p) - s.v(q)
    def i(s, k):
        """current a->b through element k (positive when flowing from first to second point)"""
        e = s.sch.el[k]
        if e[0] == "R": return (s.v(e[1]) - s.v(e[2])) / e[3]
        if e[0] == "I": return e[3]
        return s.isrc[k]


def _out(name):
    d = CIRC_DIR or (str(pathlib.Path(os.environ.get("TMPDIR", "/tmp")) / "ax_circ")); pathlib.Path(d).mkdir(parents=True, exist_ok=True); return d + "/" + name + "_" + uuid.uuid4().hex[:5] + ".png"


# =================== topologies (drawing == netlist) ===================
def twomesh(V1=None, R1=1, R2=1, R3=1, V2=None, v2_plus_bottom=True, load=None, names=True, o=(0, 0)):
    """left V1 | R1 top-left | R2 middle | R3 top-right | right V2. V1 + at top. Value None -> wire (source shorted)."""
    s = Sch(); ox, oy = o; P = lambda x, y: (ox + x, oy + y); ix = {}
    TL, TM, TR, BL, BM, BR = P(0, 3), P(4, 3), P(8, 3), P(0, 0), P(4, 0), P(8, 0)
    if V1 is None and names is not False and False: pass
    ix["V1"] = s.V(TL, BL, "V_1", V1, side=-1) if V1 is not None else (s.W(TL, BL) or None)
    ix["R1"] = s.R(TL, TM, "R_1", R1, side=1); ix["R2"] = s.R(TM, BM, "R_2", R2, side=1); ix["R3"] = s.R(TM, TR, "R_3", R3, side=1)
    if V2 is not None: ix["V2"] = s.V(BR, TR, "V_2", V2, side=-1) if v2_plus_bottom else s.V(TR, BR, "V_2", V2, side=-1)
    else: s.W(TR, BR)
    s.W(BL, BM, BR); s.gnd(BL); s.pts = dict(TL=TL, TM=TM, TR=TR, BL=BL, BM=BM, BR=BR); s.ix = ix; return s


def nodal(I1=None, RA=1, R12=1, RB=1, I2=None, left="I", V1=None, R1=None, i2_in=True, o=(0, 0), title=None):
    """ground rail at bottom, nodes A and B. left branch 'I' = current source I1 into A, or 'VR' = V1 in series R1 into A. I2 injects (or sinks) at B."""
    s = Sch(); ox, oy = o; P = lambda x, y: (ox + x, oy + y); ix = {}
    G0, A, B, G1, G2, G3 = P(0, 0), P(4, 4), P(9, 4), P(4, 0), P(9, 0), P(12, 0)
    s.W(G0, G1, G2, G3); s.gnd(G0)
    if left == "I":
        ix["I1"] = s.I(G0, P(0, 4), "I_1", I1, side=-1); s.W(P(0, 4), A)
    else:
        ix["V1"] = s.V(P(0, 2), G0, "V_1", V1, side=-1); ix["R1"] = s.R(P(0, 4), P(0, 2), "R_1", R1, side=-1); s.W(P(0, 4), A)
    ix["RA"] = s.R(A, G1, "R_A", RA, side=1); ix["R12"] = s.R(A, B, "R_{12}", R12, side=1); ix["RB"] = s.R(B, G2, "R_B", RB, side=1)
    if I2 is not None:
        if i2_in: ix["I2"] = s.I(P(12, 0), P(12, 4), "I_2", I2, side=1)
        else: ix["I2"] = s.I(P(12, 4), P(12, 0), "I_2", I2, side=1)
        s.W(P(12, 4), B)
    else: s.W(B, P(10.2, 4))
    s.pts = dict(A=A, B=B, G=G0); s.ix = ix
    s.T((A[0] - 0.45, A[1] + 0.3), "A", color=BLUE, bold=True); s.T((B[0] + 0.45, B[1] + 0.3), "B", color=BLUE, bold=True); return s


def ladder(Vs=None, R1=1, R2=1, R3=1, RL=None, Ish=None, term=True, o=(0, 0), thev_names=False):
    """Vs - R1 - A ; R2 shunt at x=3 ; optional shunt current source Ish at node A (pushes up into A) ; R3 series to terminals a-b ; optional RL across a-b"""
    s = Sch(); ox, oy = o; P = lambda x, y: (ox + x, oy + y); ix = {}
    TL, T3, A, TR, BL, B3, B5, BR = P(0, 3), P(3, 3), P(5, 3), P(8, 3), P(0, 0), P(3, 0), P(5, 0), P(8, 0)
    ix["V"] = s.V(TL, BL, "V_S", Vs, side=-1) if Vs is not None else (s.W(TL, BL) or None)
    ix["R1"] = s.R(TL, T3, "R_1", R1, side=1); s.W(T3, A); ix["R2"] = s.R(T3, B3, "R_2", R2, side=-1 if Ish is not None else 1)
    if Ish is not None: ix["I"] = s.I(B5, A, "I_S", Ish, side=1)
    ix["R3"] = s.R(A, TR, "R_3", R3, side=1); s.W(BL, B3, B5, BR)
    a, b = P(9.5, 3), P(9.5, 0); s.W(TR, a); s.W(BR, b)
    if term: s.term(a, "a"); s.term(b, "b")
    if RL is not None:
        c, d = P(11.5, 3), P(11.5, 0); s.W(a, c); s.W(b, d); ix["RL"] = s.R(c, d, "R_L", RL, side=1)
    s.pts = dict(a=a, b=b, A=A, G=BL, T3=T3); s.ix = ix; return s


def thev_eq(Vth, Rth, RL=None, o=(0, 0), nm=("V_{th}", "R_{th}")):
    s = Sch(); ox, oy = o; P = lambda x, y: (ox + x, oy + y); ix = {}
    ix["V"] = s.V(P(0, 3), P(0, 0), nm[0], Vth, side=-1); ix["R"] = s.R(P(0, 3), P(4, 3), nm[1], Rth, side=1); a, b = P(6, 3), P(6, 0); s.W(P(4, 3), a); s.W(P(0, 0), b)
    if RL is None: s.term(a, "a"); s.term(b, "b")
    else:
        s.W(a, P(7.5, 3)); s.W(b, P(7.5, 0)); ix["RL"] = s.R(P(7.5, 3), P(7.5, 0), "R_L", RL, side=1); s.term(a, "a"); s.term(b, "b")
    s.pts = dict(a=a, b=b, G=P(0, 0)); s.ix = ix; return s


def norton_eq(In, Rn, RL=None, o=(0, 0), nm=("I_N", "R_N")):
    s = Sch(); ox, oy = o; P = lambda x, y: (ox + x, oy + y); ix = {}
    ix["I"] = s.I(P(0, 0), P(0, 3), nm[0], In, side=-1); s.W(P(0, 3), P(3, 3)); s.W(P(0, 0), P(3, 0)); ix["R"] = s.R(P(3, 3), P(3, 0), nm[1], Rn, side=1)
    a, b = P(5.5, 3), P(5.5, 0); s.W(P(3, 3), a); s.W(P(3, 0), b); s.term(a, "a"); s.term(b, "b")
    if RL is not None:
        s.W(a, P(7.5, 3)); s.W(b, P(7.5, 0)); ix["RL"] = s.R(P(7.5, 3), P(7.5, 0), "R_L", RL, side=1)
    s.pts = dict(a=a, b=b, G=P(0, 0)); s.ix = ix; return s


# =================== concept figures ===================
def fig_kcl(path=None, ins=(("I_1", 5), ("I_2", 3)), outs=(("I_3", 2), ("I_4", 6))):
    s = Sch(); c = (0, 0); s.custom.append((lambda ax: ax.add_patch(Circle(c, 0.13, color=NAVY, zorder=5)), [(-1, -1), (1, 1)]))
    legs = [(-4, 2.2), (-4, -2.2), (4, 2.2), (4, -2.2)]; names = [x[0] for x in ins] + [x[0] for x in outs]; vals = [x[1] for x in ins] + [x[1] for x in outs]
    for i, (lx, ly) in enumerate(legs):
        s.W(c, (lx, ly)); inflow = i < len(ins); f = 0.38 if inflow else 0.62
        p0 = (lx * (1 - 0.30) if inflow else lx * 0.34, ly * (1 - 0.30) if inflow else ly * 0.34); p1 = (lx * 0.62, ly * 0.62) if inflow else (lx * 0.72, ly * 0.72)
        if inflow: s.arrow((lx * 0.86, ly * 0.86), (lx * 0.40, ly * 0.40), "", color=BLUE)
        else: s.arrow((lx * 0.30, ly * 0.30), (lx * 0.78, ly * 0.78), "", color=RED)
        s.T((lx * 0.62 + (0.0), ly * 0.62 + (0.55 if ly > 0 else -0.55)), "$%s = %s\\,\\mathrm{A}$" % (names[i], fx(vals[i])), fs=11, color=BLUE if inflow else RED)
    s.T((0, -1.0), "node (junction)", fs=9, color=GREY); s.T((0, -3.6), "$\\sum I_{in} = \\sum I_{out}$   →   %s = %s" % (" + ".join(fx(v) for v in vals[:len(ins)]), " + ".join(fx(v) for v in vals[len(ins):])), fs=11)
    s.T((-3.2, 3.5), "currents entering (blue)", fs=9, color=BLUE, ha="center"); s.T((3.2, 3.5), "currents leaving (red)", fs=9, color=RED, ha="center")
    return s.draw(path or _out("kcl"))


def fig_kvl(path=None, V=24, Rs=(2, 4, 6)):
    s = Sch(); R1, R2, R3 = Rs; s.V((0, 4), (0, 0), "V_S", V, side=-1); s.R((0, 4), (5, 4), "R_1", R1, side=1); s.R((5, 4), (5, 0), "R_2", R2, side=1); s.R((5, 0), (0, 0), "R_3", R3, side=1)
    s.cycle((2.5, 2), 0.9, "$I$", cw=True)
    s.T((2.5, -1.3), "KVL:  $V_S - IR_1 - IR_2 - IR_3 = 0$", fs=11.5)
    return s.draw(path or _out("kvl"))


def fig_vsources(path=None, V=12, Rs=2, RL=4):
    s = Sch(); s.V((0, 3), (0, 0), "V", None, side=-1, txt="$V_S$"); s.W((0, 3), (3, 3)); s.W((0, 0), (3, 0)); s.term((3, 3), "a"); s.term((3, 0), "b"); s.T((1.5, -1.0), "(a) Ideal voltage source", fs=10.5, bold=True)
    ox = 8; s.V((ox, 3), (ox, 0), "V", None, side=-1, txt="$V_S$"); s.R((ox, 3), (ox + 4, 3), "R_s", None, side=1, txt="$R_s$ (internal)"); s.W((ox + 4, 3), (ox + 6, 3)); s.W((ox, 0), (ox + 6, 0)); s.term((ox + 6, 3), "a"); s.term((ox + 6, 0), "b")
    s.R((ox + 9, 3), (ox + 9, 0), "R_L", None, side=1, txt="$R_L$"); s.W((ox + 6, 3), (ox + 9, 3)); s.W((ox + 6, 0), (ox + 9, 0)); s.T((ox + 4.3, -1.0), "(b) Practical voltage source with load", fs=10.5, bold=True)
    return s.draw(path or _out("vsrc"))


def fig_isources(path=None):
    s = Sch(); s.I((0, 0), (0, 3), "I", None, side=-1, txt="$I_S$"); s.W((0, 3), (3, 3)); s.W((0, 0), (3, 0)); s.term((3, 3), "a"); s.term((3, 0), "b"); s.T((1.5, -1.0), "(a) Ideal current source", fs=10.5, bold=True)
    ox = 8; s.I((ox, 0), (ox, 3), "I", None, side=-1, txt="$I_S$"); s.W((ox, 3), (ox + 3, 3)); s.W((ox, 0), (ox + 3, 0)); s.R((ox + 3, 3), (ox + 3, 0), "R_p", None, side=1, txt="$R_p$ (internal)")
    s.W((ox + 3, 3), (ox + 6, 3)); s.W((ox + 3, 0), (ox + 6, 0)); s.term((ox + 6, 3), "a"); s.term((ox + 6, 0), "b"); s.W((ox + 6, 3), (ox + 8.5, 3)); s.W((ox + 6, 0), (ox + 8.5, 0)); s.R((ox + 8.5, 3), (ox + 8.5, 0), "R_L", None, side=1, txt="$R_L$")
    s.T((ox + 4.2, -1.0), "(b) Practical current source with load", fs=10.5, bold=True); return s.draw(path or _out("isrc"))


def fig_vi_curves(path=None, V=12, Rs=2, I=6, Rp=2):
    import numpy as np
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.2, 3.4)); i = np.linspace(0, V / Rs, 50)
    a1.plot(i, [V] * 50, color=BLUE, lw=2, label="ideal  $V=V_S$"); a1.plot(i, V - Rs * i, color=RED, lw=2, label="practical  $V=V_S-IR_s$"); a1.set_xlabel("load current I (A)"); a1.set_ylabel("terminal voltage V (V)"); a1.set_title("Voltage source V–I characteristic", fontsize=10.5, color=NAVY); a1.legend(fontsize=8.5, loc="lower left"); a1.grid(alpha=.3); a1.set_ylim(0, V * 1.2)
    v = np.linspace(0, I * Rp, 50); a2.plot(v, [I] * 50, color=BLUE, lw=2, label="ideal  $I=I_S$"); a2.plot(v, I - v / Rp, color=RED, lw=2, label="practical  $I=I_S-V/R_p$"); a2.set_xlabel("terminal voltage V (V)"); a2.set_ylabel("load current I (A)"); a2.set_title("Current source V–I characteristic", fontsize=10.5, color=NAVY); a2.legend(fontsize=8.5, loc="lower left"); a2.grid(alpha=.3); a2.set_ylim(0, I * 1.2)
    fig.tight_layout(); p = path or _out("vi"); fig.savefig(p, dpi=170, facecolor="white"); plt.close(fig); return p


def fig_source_transform(path=None, Vs=12, Rs=3, RL=None):
    Is = fr(Vs) / fr(Rs); s = Sch()
    s.V((0, 3), (0, 0), "V_S", Vs, side=-1); s.R((0, 3), (4, 3), "R_s", Rs, side=1); s.W((4, 3), (6, 3)); s.W((0, 0), (6, 0)); s.term((6, 3), "a"); s.term((6, 0), "b")
    s.T((3, -1.0), "Voltage source form", fs=10.5, bold=True)
    s.T((8.5, 1.5), "⇄", fs=26, color=BLUE); s.T((8.5, 0.55), "transform", fs=8.5, color=GREY)
    ox = 11; s.I((ox, 0), (ox, 3), "I_S", Is, side=-1); s.W((ox, 3), (ox + 3, 3)); s.W((ox, 0), (ox + 3, 0)); s.R((ox + 3, 3), (ox + 3, 0), "R_p", Rs, side=1); s.W((ox + 3, 3), (ox + 5, 3)); s.W((ox + 3, 0), (ox + 5, 0)); s.term((ox + 5, 3), "a"); s.term((ox + 5, 0), "b")
    s.T((ox + 2.5, -1.0), "Current source form", fs=10.5, bold=True); s.T((8.5, 5.0), "$I_S = V_S / R_s$ ,  $R_p = R_s$", fs=11.5); return s.draw(path or _out("srctrans"))


def fig_mesh(path=None, V1=10, R1=2, R2=4, R3=6, V2=8):
    s = twomesh(V1, R1, R2, R3, V2, True); s.cycle((2, 1.5), 0.65, "$I_1$", cw=True); s.cycle((6.3, 1.5), 0.65, "$I_2$", cw=True)
    s.T((2, 0.45), "Mesh 1", fs=9, color=GREY); s.T((6.3, 0.45), "Mesh 2", fs=9, color=GREY); return s.draw(path or _out("mesh"))


def fig_nodal(path=None, I1=5, RA=10, R12=5, RB=20, I2=3):
    s = nodal(I1, RA, R12, RB, I2); s.T((1, -1.0), "reference node (0 V)", fs=9, color=GREY, ha="left")
    s.T((4.0, 4.9), "$V_A$", fs=12, color=BLUE); s.T((9.0, 4.9), "$V_B$", fs=12, color=BLUE); return s.draw(path or _out("nodal"))


def _star(s, c, r, names, vals, o, term_names=("A", "B", "C")):
    cx, cy = c; ang = (90, 210, 330); ends = [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in ang]
    s.custom.append((lambda ax: ax.add_patch(Circle(c, 0.1, color=NAVY, zorder=5)), [(cx - 1, cy - 1), (cx + 1, cy + 1)]))
    for i, e in enumerate(ends):
        pe = (cx + (e[0] - cx) * 0.995, cy + (e[1] - cy) * 0.995); s.R(c, e, names[i], vals[i], side=-1 if i != 1 else 1)
        s.term(e, term_names[i], dx=(0.0 if i == 0 else (-0.3 if i == 1 else 0.3)), dy=(0.35 if i == 0 else -0.05), ha="center" if i == 0 else ("right" if i == 1 else "left"))
    s.T((cx + 0.3, cy + 0.0), "N", fs=9, color=GREY, ha="left", va="center")


def fig_star_delta(path=None, star=(None, None, None), delta=(None, None, None)):
    s = Sch(); _star(s, (0, 0), 3.0, ["R_A", "R_B", "R_C"], star, (0, 0)); s.T((0, -3.2), "Star (Y / T) network", fs=10.5, bold=True)
    s.T((5.0, 0.2), "⇄", fs=26, color=BLUE)
    c = (10.5, 0); r = 3.2; A = (c[0], c[1] + r); B = (c[0] - r * math.cos(math.radians(30)), c[1] - r / 2); C = (c[0] + r * math.cos(math.radians(30)), c[1] - r / 2)
    s.R(A, B, "R_{AB}", delta[0], side=-1); s.R(B, C, "R_{BC}", delta[1], side=-1); s.R(C, A, "R_{CA}", delta[2], side=-1)
    s.term(A, "A", dx=0, dy=0.35, ha="center"); s.term(B, "B", dx=-0.3, ha="right"); s.term(C, "C", dx=0.3, ha="left"); s.T((c[0], c[1] - 3.2), "Delta (Δ / π) network", fs=10.5, bold=True)
    return s.draw(path or _out("stardelta"))


def bridge(Vs=None, Rab=1, Rac=1, Rbc=1, Rbd=1, Rcd=1, o=(0, 0)):
    """Wheatstone bridge: A left, B top, C bottom, D right; supply across A-D through bottom wire. Rbc is the bridge arm."""
    s = Sch(); ox, oy = o; P = lambda x, y: (ox + x, oy + y); ix = {}
    A, B, C, D = P(0, 2.5), P(3.5, 5.0), P(3.5, 0.0), P(7.0, 2.5)
    ix["AB"] = s.R(A, B, "R_{AB}", Rab, side=1); ix["AC"] = s.R(A, C, "R_{AC}", Rac, side=-1); ix["BC"] = s.R(B, C, "R_{BC}", Rbc, side=1); ix["BD"] = s.R(B, D, "R_{BD}", Rbd, side=1); ix["CD"] = s.R(C, D, "R_{CD}", Rcd, side=-1)
    s.W(A, P(0, -2.2)); s.W(D, P(7, -2.2)); ix["V"] = s.V(P(0, -2.2), P(7, -2.2), "V_S", Vs, side=-1)
    for p, nme, dx, dy, ha in ((A, "A", -0.3, 0.0, "right"), (B, "B", 0.0, 0.4, "center"), (C, "C", 0.0, -0.4, "center"), (D, "D", 0.3, 0.0, "left")): s.T((p[0] + dx, p[1] + dy), nme, fs=11.5, color=BLUE, bold=True, ha=ha)
    s.pts = dict(A=A, B=B, C=C, D=D, G=P(0, -2.2)); s.ix = ix; return s


def fig_superposition(path=None, build=None):
    """build(V,I) -> Sch ; draws 3 panels: both, V only, I only"""
    raise NotImplementedError


def fig_p_vs_rl(path=None, Vth=12, Rth=4):
    import numpy as np
    r = np.linspace(0.2, 4 * float(Rth), 400); p = [float(Vth) ** 2 * x / (float(Rth) + x) ** 2 for x in r]; pm = float(Vth) ** 2 / (4 * float(Rth))
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.2, 3.4)); a1.plot(r, p, color=BLUE, lw=2); a1.axvline(float(Rth), color=RED, ls="--", lw=1.2); a1.plot([float(Rth)], [pm], "o", color=RED)
    a1.annotate("$P_{max}$ at $R_L=R_{th}$", (float(Rth), pm), xytext=(float(Rth) * 1.4, pm * 0.55), arrowprops=dict(arrowstyle="->", color=RED), fontsize=9.5, color=RED); a1.set_xlabel("load resistance $R_L$ (Ω)"); a1.set_ylabel("power in load (W)"); a1.set_title("Load power vs $R_L$", fontsize=10.5, color=NAVY); a1.grid(alpha=.3)
    eff = [100 * x / (float(Rth) + x) for x in r]; a2.plot(r, eff, color=NAVY, lw=2); a2.axhline(50, color=RED, ls="--", lw=1.2); a2.axvline(float(Rth), color=RED, ls="--", lw=1.2); a2.set_xlabel("load resistance $R_L$ (Ω)"); a2.set_ylabel("efficiency η (%)"); a2.set_title("Efficiency vs $R_L$ (50 % at maximum power)", fontsize=10.5, color=NAVY); a2.grid(alpha=.3); a2.set_ylim(0, 100)
    fig.tight_layout(); p_ = path or _out("pmax"); fig.savefig(p_, dpi=170, facecolor="white"); plt.close(fig); return p_


print("✅ ax7a circuit engine OK")


def merge(*parts):
    """combine several Sch objects into one drawing (for multi-panel figures); netlist of the merged object is NOT meant to be solved"""
    m = Sch()
    for p in parts:
        m.el += p.el; m.wr += p.wr; m.tx += p.tx; m.arr += p.arr; m.terms += p.terms; m.gnds += p.gnds; m.cyc += p.cyc; m.custom += p.custom
    return m
