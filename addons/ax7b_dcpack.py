# AXINUS 7b - DC Circuits knowledge pack: verified theory + solved numericals (numbers come from an exact solver, never from an LLM) + circuit figures
import re
from fractions import Fraction as Fr
try: ax7a_ready
except NameError: pass
DC_KEYS = r"kirchhoff|kcl|kvl|thevenin|thévenin|norton|superposition|mesh analysis|nodal analysis|star.?delta|delta.?star|maximum power transfer|source transformation"

def _chk(name, a, b):
    if abs(fr(a) - fr(b)) > Fr(1, 10 ** 6): raise AssertionError("DC pack check failed: %s: %s != %s" % (name, fx(a, 6), fx(b, 6)))
def _f(path, cap): return "\n![%s](%s)\n" % (cap, path)
def _S(sym, val, u): return "$%s = %s\\,%s$" % (sym, fx(val), unit_tex(u))
def _ex(no, title, given, find, fig, formula, steps, ans, ver):
    o = ["### Solved Example %s: %s" % (no, title), "**Step 1 – Given:** " + given, "**Step 2 – To find:** " + find, "**Step 3 – Circuit diagram:**" + fig, "**Step 4 – Formula / method:** " + formula, "**Steps 5 and 6 – Substitution and calculation:**"]
    o += ["%d. %s" % (i + 1, s) for i, s in enumerate(steps)]
    o += ["> [ANS] **Step 7 – Final answer:** " + ans, "**Step 8 – Verification:** " + ver]
    return "\n\n".join(o)


def _numericals(D):
    """returns dict topic -> markdown of solved examples (all numbers computed + cross-checked by exact MNA)"""
    N = {}
    # ---- KCL / KVL ----
    i4 = Fr(5) + 3 - 2; _chk("kcl", i4, 6)
    f1 = fig_kcl(D("kcl_ex"), (("I_1", 5), ("I_2", 3)), (("I_3", 2), ("I_4", i4)))
    e1 = _ex("1.1", "KCL at a junction", "Currents entering: $I_1 = 5\\,\\mathrm{A}$, $I_2 = 3\\,\\mathrm{A}$. Currents leaving: $I_3 = 2\\,\\mathrm{A}$ and $I_4$ (unknown).", "The current $I_4$.", _f(f1, "Junction with two incoming and two outgoing currents"),
             "KCL: $\\sum I_{in} = \\sum I_{out}$.", ["Write KCL: $I_1 + I_2 = I_3 + I_4$.", "Substitute: $5 + 3 = 2 + I_4$.", "Solve: $I_4 = 8 - 2 = 6\\,\\mathrm{A}$."], "$I_4 = 6\\,\\mathrm{A}$ (leaving the node).", "Total in = 5 + 3 = 8 A and total out = 2 + 6 = 8 A. The two sides are equal, so KCL is satisfied.")
    ks = []
    for no, V, Rs in (("1.2", 24, (2, 4, 6)), ("1.3", 36, (3, 6, 9))):
        R1, R2, R3 = Rs; I = Fr(V, sum(Rs)); s = Sch(); s.V((0, 4), (0, 0), "V", V); s.R((0, 4), (5, 4), "a", R1); s.R((5, 4), (5, 0), "b", R2); s.R((5, 0), (0, 0), "c", R3); s.W((0, 4), (0, 4))
        sol = s.solve((0, 0)); _chk("kvl", -sol.i(0) if False else I, abs(sol.i(1)))
        p = fig_kvl(D("kvl_ex"), V, Rs); d1, d2, d3 = I * R1, I * R2, I * R3
        ks.append(_ex(no, "KVL in a single series loop", "A battery $V_S = %s\\,\\mathrm{V}$ drives resistors $R_1 = %s\\,\\Omega$, $R_2 = %s\\,\\Omega$, $R_3 = %s\\,\\Omega$ in series." % (V, R1, R2, R3), "Loop current $I$ and the voltage drop across each resistor.", _f(p, "Series loop for KVL"),
                      "KVL: $V_S - IR_1 - IR_2 - IR_3 = 0$ so $I = V_S/(R_1+R_2+R_3)$.", ["$R_{total} = %s + %s + %s = %s\\,\\Omega$." % (R1, R2, R3, sum(Rs)), "$I = %s / %s = %s\\,\\mathrm{A}$." % (V, sum(Rs), fx(I)), "$V_1 = IR_1 = %s \\times %s = %s\\,\\mathrm{V}$." % (fx(I), R1, fx(d1)), "$V_2 = IR_2 = %s \\times %s = %s\\,\\mathrm{V}$." % (fx(I), R2, fx(d2)), "$V_3 = IR_3 = %s \\times %s = %s\\,\\mathrm{V}$." % (fx(I), R3, fx(d3))],
                      "$I = %s\\,\\mathrm{A}$; drops %s V, %s V, %s V." % (fx(I), fx(d1), fx(d2), fx(d3)), "Sum of drops = %s + %s + %s = %s V, which equals the supply of %s V, so KVL holds. Solver cross-check agrees." % (fx(d1), fx(d2), fx(d3), fx(d1 + d2 + d3), V)))
    N["kirchhoff"] = e1 + "\n\n" + "\n\n".join(ks)
    # ---- source transformation ----
    out = []
    for no, kind, Vs, Rs, RL in (("4.1", "v2i", 18, 3, 6), ("4.2", "i2v", 20, 4, 16)):
        Is = Fr(Vs, Rs); s = Sch(); s.V((0, 3), (0, 0), "", Vs); s.R((0, 3), (4, 3), "", Rs); s.R((4, 3), (4, 0), "", RL); s.W((0, 0), (4, 0)); sol = s.solve((0, 0)); IL = sol.i(2); _chk("st-div", IL, Is * Rs / (Rs + RL)); _chk("st-v", IL, Fr(Vs, Rs + RL))
        p = fig_source_transform(D("st_ex"), Vs, Rs)
        if kind == "v2i":
            out.append(_ex(no, "Voltage source to current source", "A practical voltage source of $V_S = %s\\,\\mathrm{V}$ with internal resistance $R_s = %s\\,\\Omega$ feeds a load $R_L = %s\\,\\Omega$." % (Vs, Rs, RL), "Equivalent current source and the load current by both forms.", _f(p, "Voltage source form and its equivalent current source form"), "$I_S = V_S/R_s$, $R_p = R_s$; current divider $I_L = I_S R_p/(R_p + R_L)$.",
                           ["$I_S = %s/%s = %s\\,\\mathrm{A}$ and $R_p = %s\\,\\Omega$ (in parallel with the source)." % (Vs, Rs, fx(Is), Rs), "Voltage form: $I_L = V_S/(R_s+R_L) = %s/%s = %s\\,\\mathrm{A}$." % (Vs, Rs + RL, fx(IL)), "Current form: $I_L = %s \\times %s/(%s+%s) = %s\\,\\mathrm{A}$." % (fx(Is), Rs, Rs, RL, fx(Is * Rs / (Rs + RL)))],
                           "$I_S = %s\\,\\mathrm{A}$ in parallel with $%s\\,\\Omega$; $I_L = %s\\,\\mathrm{A}$." % (fx(Is), Rs, fx(IL)), "Both forms give the same load current, %s A, as the transformation theory requires." % fx(IL)))
        else:
            out.append(_ex(no, "Current source to voltage source", "A practical current source $I_S = %s\\,\\mathrm{A}$ with parallel resistance $R_p = %s\\,\\Omega$ feeds $R_L = %s\\,\\Omega$." % (fx(Is), Rs, RL), "Equivalent voltage source and the load current.", _f(p, "Equivalent source forms (here the current-source form is the given one)"), "$V_S = I_S R_p$, $R_s = R_p$.",
                           ["$V_S = %s \\times %s = %s\\,\\mathrm{V}$ in series with $R_s = %s\\,\\Omega$." % (fx(Is), Rs, Vs, Rs), "$I_L = V_S/(R_s + R_L) = %s/(%s+%s) = %s\\,\\mathrm{A}$." % (Vs, Rs, RL, fx(IL))],
                           "Voltage source %s V in series with %s Ω; $I_L = %s\\,\\mathrm{A}$." % (Vs, Rs, fx(IL)), "Current divider on the original source: %s × %s/(%s+%s) = %s A. Same answer." % (fx(Is), Rs, Rs, RL, fx(Is * Rs / (Rs + RL)))))
    N["srctrans"] = "\n\n".join(out)
    # ---- mesh ----
    out = []
    for no, (V1, R1, R2, R3, V2) in (("5.1", (10, 2, 4, 6, 8)), ("5.2", (20, 5, 10, 5, 10))):
        Dd = (R1 + R2) * (R2 + R3) - R2 * R2; I1 = Fr(V1 * (R2 + R3) + R2 * V2, Dd); I2 = Fr((R1 + R2) * V2 + R2 * V1, Dd); s = twomesh(V1, R1, R2, R3, V2); sol = s.solve(s.pts["BL"]); _chk("mesh1", I1, sol.i(s.ix["R1"])); _chk("mesh2", I2, sol.i(s.ix["R3"])); _chk("mesh3", I1 - I2, sol.i(s.ix["R2"]))
        p = fig_mesh(D("mesh_ex"), V1, R1, R2, R3, V2)
        out.append(_ex(no, "Two-mesh network", "$V_1 = %s\\,\\mathrm{V}$, $V_2 = %s\\,\\mathrm{V}$, $R_1 = %s\\,\\Omega$, $R_2 = %s\\,\\Omega$, $R_3 = %s\\,\\Omega$. Mesh currents $I_1$, $I_2$ are taken clockwise." % (V1, V2, R1, R2, R3), "Mesh currents and the current in $R_2$.", _f(p, "Two-mesh circuit with clockwise mesh currents"), "KVL around each mesh (no super-mesh is needed).",
                       ["Mesh 1: $V_1 = I_1 R_1 + (I_1 - I_2)R_2$ so $%s I_1 - %s I_2 = %s$." % (R1 + R2, R2, V1), "Mesh 2: $V_2 = I_2 R_3 + (I_2 - I_1)R_2$ so $-%s I_1 + %s I_2 = %s$." % (R2, R2 + R3, V2), "Determinant: $\\Delta = (%s)(%s) - (%s)^2 = %s$." % (R1 + R2, R2 + R3, R2, Dd), "$I_1 = [%s \\times %s + %s \\times %s]/%s = %s\\,\\mathrm{A}$." % (V1, R2 + R3, R2, V2, Dd, fx(I1)), "$I_2 = [%s \\times %s + %s \\times %s]/%s = %s\\,\\mathrm{A}$." % (R1 + R2, V2, R2, V1, Dd, fx(I2)), "Current in $R_2$ (downwards) $= I_1 - I_2 = %s\\,\\mathrm{A}$." % fx(I1 - I2)],
                       "$I_1 = %s\\,\\mathrm{A}$, $I_2 = %s\\,\\mathrm{A}$, $I_{R_2} = %s\\,\\mathrm{A}$." % (fx(I1), fx(I2), fx(I1 - I2)), "Mesh 1 check: %s×%s + (%s)×%s = %s V = V₁. Mesh 2 check: %s×%s + (%s)×%s = %s V = V₂. The independent exact solver also gives the same currents." % (fx(I1), R1, fx(I1 - I2), R2, fx(I1 * R1 + (I1 - I2) * R2), fx(I2), R3, fx(I2 - I1), R2, fx(I2 * R3 + (I2 - I1) * R2))))
    N["mesh"] = "\n\n".join(out)
    # ---- nodal ----
    out = []
    for no, cfg in (("6.1", dict(left="I", I1=10, RA=4, R12=2, RB=4, I2=5, i2_in=True)), ("6.2", dict(left="VR", V1=16, R1=4, RA=4, R12=4, RB=4, I2=2, i2_in=False))):
        RA, R12, RB = cfg["RA"], cfg["R12"], cfg["RB"]; s = nodal(**cfg); sol = s.solve(s.pts["G"]); VA, VB = sol.v(s.pts["A"]), sol.v(s.pts["B"])
        GA, G12, GB = Fr(1, RA), Fr(1, R12), Fr(1, RB); I2s = Fr(cfg["I2"]) * (1 if cfg["i2_in"] else -1)
        if cfg["left"] == "I": G1, Ieq = Fr(0), Fr(cfg["I1"])
        else: G1, Ieq = Fr(1, cfg["R1"]), Fr(cfg["V1"], cfg["R1"])
        a11, a12, a22 = GA + G12 + G1, -G12, GB + G12; Dd = a11 * a22 - a12 * a12; vA = (Ieq * a22 - a12 * I2s) / Dd; vB = (a11 * I2s - a12 * Ieq) / Dd; _chk("nodalA", vA, VA); _chk("nodalB", vB, VB)
        if cfg["left"] == "I": p = fig_nodal(D("nodal_ex"), cfg["I1"], RA, R12, RB, cfg["I2"]); given = "$I_1 = %s\\,\\mathrm{A}$ into node A, $I_2 = %s\\,\\mathrm{A}$ into node B, $R_A = %s\\,\\Omega$, $R_{12} = %s\\,\\Omega$, $R_B = %s\\,\\Omega$." % (cfg["I1"], cfg["I2"], RA, R12, RB); eqA = "Node A: $(1/%s + 1/%s)V_A - (1/%s)V_B = %s$." % (RA, R12, R12, cfg["I1"])
        else:
            s2 = nodal(**cfg); p = s2.draw(D("nodal_ex")); given = "$V_1 = %s\\,\\mathrm{V}$ in series with $R_1 = %s\\,\\Omega$ feeding node A; $R_A = R_{12} = R_B = %s\\,\\Omega$; a sink $I_2 = %s\\,\\mathrm{A}$ leaves node B." % (cfg["V1"], cfg["R1"], RA, cfg["I2"]); eqA = "Node A: $(1/%s + 1/%s + 1/%s)V_A - (1/%s)V_B = %s/%s$." % (cfg["R1"], RA, R12, R12, cfg["V1"], cfg["R1"])
        eqB = "Node B: $-(1/%s)V_A + (1/%s + 1/%s)V_B = %s$." % (R12, R12, RB, fx(I2s))
        out.append(_ex(no, "Two-node network (reference node at the bottom)", given, "Node voltages $V_A$, $V_B$ and the current through $R_{12}$.", _f(p, "Nodal analysis circuit with reference node"), "KCL at each non-reference node (no super-node is needed).",
                       [eqA, eqB, "Numerical form: $%s V_A - %s V_B = %s$ and $-%s V_A + %s V_B = %s$." % (fx(a11), fx(G12), fx(Ieq), fx(G12), fx(a22), fx(I2s)), "Determinant: $\\Delta = %s \\times %s - %s^2 = %s$." % (fx(a11), fx(a22), fx(G12), fx(Dd, 5)), "$V_A = %s\\,\\mathrm{V}$, $V_B = %s\\,\\mathrm{V}$." % (fx(VA), fx(VB)), "$I_{12} = (V_A - V_B)/R_{12} = (%s - %s)/%s = %s\\,\\mathrm{A}$ (A to B)." % (fx(VA), fx(VB), R12, fx((VA - VB) / R12))],
                       "$V_A = %s\\,\\mathrm{V}$, $V_B = %s\\,\\mathrm{V}$, $I_{12} = %s\\,\\mathrm{A}$." % (fx(VA), fx(VB), fx((VA - VB) / R12)), "KCL at A: current in from the source side = %s A; current out = V_A/R_A + I_12 = %s A. They match, and the exact solver gives the same node voltages." % (fx(Ieq - G1 * VA), fx(VA / RA + (VA - VB) / R12))))
    N["nodal"] = "\n\n".join(out)
    # ---- star-delta ----
    out = []; RA, RB, RC = 10, 20, 20; S = RA * RB + RB * RC + RC * RA; dab, dbc, dca = Fr(S, RC), Fr(S, RA), Fr(S, RB)
    s = Sch(); s.R((0, 0), (1, 1), "", RA); s.R((0, 0), (1, -1), "", RB); s.R((0, 0), (-1, 0), "", RC)
    p = fig_star_delta(D("sd_ex"), (RA, RB, RC), (dab, dbc, dca))
    out.append(_ex("7.1", "Star to delta", "Star resistors $R_A = 10\\,\\Omega$, $R_B = 20\\,\\Omega$, $R_C = 20\\,\\Omega$.", "Equivalent delta resistors.", _f(p, "Star network and equivalent delta network"), "$R_{AB} = S/R_C$, $R_{BC} = S/R_A$, $R_{CA} = S/R_B$ where $S = R_AR_B + R_BR_C + R_CR_A$.",
                   ["$S = 10\\times20 + 20\\times20 + 20\\times10 = 200 + 400 + 200 = %s\\,\\Omega^2$." % S, "$R_{AB} = %s/20 = %s\\,\\Omega$." % (S, fx(dab)), "$R_{BC} = %s/10 = %s\\,\\Omega$." % (S, fx(dbc)), "$R_{CA} = %s/20 = %s\\,\\Omega$." % (S, fx(dca))], "$R_{AB} = %s\\,\\Omega$, $R_{BC} = %s\\,\\Omega$, $R_{CA} = %s\\,\\Omega$." % (fx(dab), fx(dbc), fx(dca)),
                   "Convert back: $R_A = R_{AB}R_{CA}/(R_{AB}+R_{BC}+R_{CA}) = %s\\times%s/%s = %s\\,\\Omega$, which is the original 10 Ω." % (fx(dab), fx(dca), fx(dab + dbc + dca), fx(dab * dca / (dab + dbc + dca)))))
    _chk("sd", dab * dca / (dab + dbc + dca), RA)
    S2 = 15; out.append(_ex("7.2", "Balanced star to delta", "Three equal star resistors of $15\\,\\Omega$.", "Equivalent delta resistors.", _f(fig_star_delta(D("sd_ex2"), (15, 15, 15), (45, 45, 45)), "Balanced star and delta"), "For a balanced network $R_\\Delta = 3R_Y$.", ["$R_\\Delta = 3 \\times 15 = 45\\,\\Omega$ for each side."], "Each delta resistor is $45\\,\\Omega$.", "Check with the general formula: S = 3×15×15 = 675, so $R_{AB} = 675/15 = 45\\,\\Omega$."))
    N["star"] = "\n\n".join(out)
    out = []; dAB, dBC, dCA = 30, 60, 90; Sd = dAB + dBC + dCA; rA, rB, rC = Fr(dAB * dCA, Sd), Fr(dAB * dBC, Sd), Fr(dBC * dCA, Sd); p = fig_star_delta(D("ds_ex"), (rA, rB, rC), (dAB, dBC, dCA))
    out.append(_ex("8.1", "Delta to star", "Delta resistors $R_{AB} = 30\\,\\Omega$, $R_{BC} = 60\\,\\Omega$, $R_{CA} = 90\\,\\Omega$.", "Equivalent star resistors.", _f(p, "Delta network and equivalent star network"), "$R_A = R_{AB}R_{CA}/\\Sigma$, $R_B = R_{AB}R_{BC}/\\Sigma$, $R_C = R_{BC}R_{CA}/\\Sigma$, $\\Sigma = R_{AB}+R_{BC}+R_{CA}$.",
                   ["$\\Sigma = 30 + 60 + 90 = %s\\,\\Omega$." % Sd, "$R_A = 30\\times90/%s = %s\\,\\Omega$." % (Sd, fx(rA)), "$R_B = 30\\times60/%s = %s\\,\\Omega$." % (Sd, fx(rB)), "$R_C = 60\\times90/%s = %s\\,\\Omega$." % (Sd, fx(rC))], "$R_A = %s\\,\\Omega$, $R_B = %s\\,\\Omega$, $R_C = %s\\,\\Omega$." % (fx(rA), fx(rB), fx(rC)), "Resistance between A and B: star gives $R_A + R_B = %s\\,\\Omega$; delta gives $30 \\parallel (60+90) = 30\\times150/180 = %s\\,\\Omega$. Equal, so the conversion is correct." % (fx(rA + rB), fx(Fr(30 * 150, 180)))))
    _chk("ds", rA + rB, Fr(30 * 150, 180))
    Rbd, Rcd, Vs = 10, 30, 60; b = bridge(Vs, dAB, dCA, dBC, Rbd, Rcd); Req = rA + ((rB + Rbd) * (rC + Rcd)) / (rB + Rbd + rC + Rcd); sol = b.solve(b.pts["G"]); Itot = Fr(Vs) / Req; _chk("bridge", Req, Fr(Vs) / -sol.i(b.ix["V"]) if False else Fr(Vs) / abs(sol.i(b.ix["V"])))
    pb = b.draw(D("bridge_ex")); par = ((rB + Rbd) * (rC + Rcd)) / (rB + Rbd + rC + Rcd)
    out.append(_ex("8.2", "Bridge network using delta-star conversion", "A bridge with $R_{AB} = 30$, $R_{AC} = 90$, $R_{BC} = 60$, $R_{BD} = 10$, $R_{CD} = 30\\,\\Omega$ is supplied by $V_S = 60\\,\\mathrm{V}$ across A and D.", "Total resistance and supply current.", _f(pb, "Bridge network. The delta ABC is replaced by a star"), "Replace delta ABC by a star, then use series-parallel reduction.",
                   ["Delta ABC (30, 60, 90 Ω) becomes star: $R_A = %s$, $R_B = %s$, $R_C = %s\\,\\Omega$ (Example 8.1)." % (fx(rA), fx(rB), fx(rC)), "Branch toward B-D: $R_B + R_{BD} = %s + %s = %s\\,\\Omega$." % (fx(rB), Rbd, fx(rB + Rbd)), "Branch toward C-D: $R_C + R_{CD} = %s + %s = %s\\,\\Omega$." % (fx(rC), Rcd, fx(rC + Rcd)), "Parallel: $%s \\parallel %s = %s\\,\\Omega$." % (fx(rB + Rbd), fx(rC + Rcd), fx(par)), "$R_{eq} = R_A + %s = %s + %s = %s\\,\\Omega$." % (fx(par), fx(rA), fx(par), fx(Req)), "$I = V_S/R_{eq} = 60/%s = %s\\,\\mathrm{A}$." % (fx(Req), fx(Itot))],
                   "$R_{eq} = %s\\,\\Omega$, $I = %s\\,\\mathrm{A}$." % (fx(Req), fx(Itot)), "The exact network solver, using the original bridge without any conversion, gives the same supply current of %s A." % fx(abs(sol.i(b.ix["V"])))))
    N["delta"] = "\n\n".join(out)
    # ---- superposition ----
    out = []
    V1, R1, R2, R3, V2 = 24, 4, 12, 6, 18; both = twomesh(V1, R1, R2, R3, V2); sb = both.solve(both.pts["BL"]); a1 = twomesh(V1, R1, R2, R3, None); s1 = a1.solve(a1.pts["BL"]); a2 = twomesh(None, R1, R2, R3, V2); s2 = a2.solve(a2.pts["BL"])
    Rp1 = Fr(R2 * R3, R2 + R3); It1 = Fr(V1) / (R1 + Rp1); i1 = It1 * R3 / (R2 + R3); Rp2 = Fr(R1 * R2, R1 + R2); It2 = Fr(V2) / (R3 + Rp2); i2 = -It2 * R1 / (R1 + R2)
    _chk("sup1", i1, s1.i(a1.ix["R2"])); _chk("sup2", i2, s2.i(a2.ix["R2"])); _chk("sup3", i1 + i2, sb.i(both.ix["R2"]))
    fig = merge(twomesh(V1, R1, R2, R3, V2, o=(0, 0)), twomesh(V1, R1, R2, R3, None, o=(0, -6.5)), twomesh(None, R1, R2, R3, V2, o=(0, -13))); fig.T((4, 4.5), "(a) Both sources acting", fs=10.5, bold=True); fig.T((4, -2.0), "(b) $V_1$ only ($V_2$ replaced by a short circuit)", fs=10.5, bold=True); fig.T((4, -8.5), "(c) $V_2$ only ($V_1$ replaced by a short circuit)", fs=10.5, bold=True); p = fig.draw(D("sup_ex"))
    out.append(_ex("9.1", "Two voltage sources", "$V_1 = 24\\,\\mathrm{V}$, $V_2 = 18\\,\\mathrm{V}$, $R_1 = 4\\,\\Omega$, $R_2 = 12\\,\\Omega$, $R_3 = 6\\,\\Omega$ (same layout as the mesh circuit).", "Current through $R_2$ (positive = downwards).", _f(p, "Superposition: each source acting alone"), "Total response = sum of responses due to each independent source acting alone (other voltage sources shorted).",
                   ["$V_1$ alone: $R_2 \\parallel R_3 = %s\\,\\Omega$, $I_T = 24/(4+%s) = %s\\,\\mathrm{A}$, so $I_{R_2}' = %s \\times 6/18 = %s\\,\\mathrm{A}$ (down)." % (fx(Rp1), fx(Rp1), fx(It1), fx(It1), fx(i1)), "$V_2$ alone: $R_1 \\parallel R_2 = %s\\,\\Omega$, $I_T = 18/(6+%s) = %s\\,\\mathrm{A}$, so $I_{R_2}'' = %s \\times 4/16 = %s\\,\\mathrm{A}$ (up, so it is %s downwards)." % (fx(Rp2), fx(Rp2), fx(It2), fx(It2), fx(-i2), fx(i2)), "Add: $I_{R_2} = %s + (%s) = %s\\,\\mathrm{A}$ (down)." % (fx(i1), fx(i2), fx(i1 + i2))], "$I_{R_2} = %s\\,\\mathrm{A}$ downwards." % fx(i1 + i2), "Solving the original circuit by mesh analysis (solver) gives %s A. Same." % fx(sb.i(both.ix["R2"]))))
    Vs, R1, R2, R3, RL, Is = 18, 3, 6, 2, 4, 3; lb = ladder(Vs, R1, R2, R3, RL, Is); sb = lb.solve(lb.pts["G"]); l1 = ladder(Vs, R1, R2, R3, RL, None); sv = l1.solve(l1.pts["G"]); l2 = ladder(None, R1, R2, R3, RL, Is); si = l2.solve(l2.pts["G"])
    Vth1, Rth1 = Fr(Vs * R2, R1 + R2), Fr(R1 * R2, R1 + R2); ia = Vth1 / (Rth1 + R3 + RL); ib = Is * Rth1 / (Rth1 + R3 + RL); _chk("s2a", ia, sv.i(l1.ix["RL"])); _chk("s2b", ib, si.i(l2.ix["RL"])); _chk("s2c", ia + ib, sb.i(lb.ix["RL"]))
    fig = merge(ladder(Vs, R1, R2, R3, RL, Is, o=(0, 0)), ladder(Vs, R1, R2, R3, RL, None, o=(0, -6.5)), ladder(None, R1, R2, R3, RL, Is, o=(0, -13))); fig.T((6, 4.5), "(a) Both sources acting", fs=10.5, bold=True); fig.T((6, -2.0), "(b) $V_S$ only ($I_S$ replaced by an open circuit)", fs=10.5, bold=True); fig.T((6, -8.5), "(c) $I_S$ only ($V_S$ replaced by a short circuit)", fs=10.5, bold=True); p = fig.draw(D("sup_ex2"))
    out.append(_ex("9.2", "One voltage source and one current source", "$V_S = 18\\,\\mathrm{V}$, $I_S = 3\\,\\mathrm{A}$, $R_1 = 3$, $R_2 = 6$, $R_3 = 2$, $R_L = 4\\,\\Omega$.", "Current through $R_L$.", _f(p, "Superposition with a voltage source and a current source"), "Voltage source alone (current source open); current source alone (voltage source shorted).",
                   ["$V_S$ alone: Thevenin of the left part $= 18\\times6/9 = %s$ V with $R = 3\\parallel6 = %s\\,\\Omega$; $I_L' = %s/(%s + 2 + 4) = %s\\,\\mathrm{A}$." % (fx(Vth1), fx(Rth1), fx(Vth1), fx(Rth1), fx(ia)), "$I_S$ alone: $R_1\\parallel R_2 = %s\\,\\Omega$ is in parallel with the $R_3 + R_L = 6\\,\\Omega$ branch; current divider gives $I_L'' = 3\\times%s/(%s+6) = %s\\,\\mathrm{A}$." % (fx(Rth1), fx(Rth1), fx(Rth1), fx(ib)), "$I_L = I_L' + I_L'' = %s + %s = %s\\,\\mathrm{A}$." % (fx(ia), fx(ib), fx(ia + ib))], "$I_L = %s\\,\\mathrm{A}$." % fx(ia + ib), "A direct solution of the full circuit (solver) gives %s A." % fx(sb.i(lb.ix["RL"]))))
    N["superposition"] = "\n\n".join(out)
    # ---- thevenin / norton / mpt ----
    cases = [(dict(Vs=18, R1=3, R2=6, R3=2, Ish=None), 4), (dict(Vs=18, R1=3, R2=6, R3=2, Ish=3), 4)]; out = []; TH = []
    for n, (cf, RL) in enumerate(cases):
        o = ladder(RL=None, **cf); so = o.solve(o.pts["G"]); Vth = so.vd(o.pts["a"], o.pts["b"]); d = ladder(Vs=None, R1=cf["R1"], R2=cf["R2"], R3=cf["R3"], RL=None, Ish=None); Rth = d.req(d.pts["a"], d.pts["b"]); Rp = Fr(cf["R1"] * cf["R2"], cf["R1"] + cf["R2"]); _chk("rth", Rth, Rp + cf["R3"])
        w = ladder(RL=None, **cf); w.W(w.pts["a"], w.pts["b"]); sw = w.solve(w.pts["G"]); IN = sw.i(w.ix["R3"]); _chk("in", IN, Vth / Rth); full = ladder(RL=RL, **cf); sf = full.solve(full.pts["G"]); IL = sf.i(full.ix["RL"]); _chk("il", IL, Vth / (Rth + RL)); TH.append((cf, RL, Vth, Rth, IN, IL))
        Vo = cf["Vs"] * Fr(cf["R2"], cf["R1"] + cf["R2"]); ex = (" Because the current source forces $%s$ A into node A with no path through $R_3$ at open circuit, it adds $I_S(R_1\\parallel R_2) = %s$ V." % (cf["Ish"], fx(cf["Ish"] * Rp))) if cf["Ish"] else ""
        fig = merge(ladder(RL=RL, o=(0, 0), **cf), thev_eq(Vth, Rth, RL, o=(1.5, -6))); fig.T((6, 4.5), "(a) Given network", fs=10.5, bold=True); fig.T((4.5, -2.0), "(b) Thevenin equivalent", fs=10.5, bold=True); p = fig.draw(D("thev_ex"))
        out.append(_ex("10.%d" % (n + 1), "Thevenin equivalent" + (" with a current source" if cf["Ish"] else ""), "$V_S = 18\\,\\mathrm{V}$, " + ("$I_S = 3\\,\\mathrm{A}$, " if cf["Ish"] else "") + "$R_1 = 3\\,\\Omega$, $R_2 = 6\\,\\Omega$, $R_3 = 2\\,\\Omega$, load $R_L = 4\\,\\Omega$ across a-b.", "$V_{th}$, $R_{th}$ and the load current.", _f(p, "Network, and its Thevenin equivalent connected to the load"), "Remove $R_L$; $V_{th}$ = open-circuit voltage; $R_{th}$ = resistance seen from a-b with sources deactivated; $I_L = V_{th}/(R_{th}+R_L)$.",
                       ["Open circuit: no current flows in $R_3$, so $V_{th}$ equals the voltage at node A. The voltage source with $R_1$, $R_2$ gives $18\\times6/(3+6) = %s$ V.%s" % (fx(Vo), ex), "So $V_{th} = %s\\,\\mathrm{V}$." % fx(Vth), "Deactivate sources (short $V_S$, open $I_S$): $R_{th} = R_3 + R_1\\parallel R_2 = 2 + %s = %s\\,\\Omega$." % (fx(Rp), fx(Rth)), "$I_L = %s/(%s + 4) = %s\\,\\mathrm{A}$." % (fx(Vth), fx(Rth), fx(IL))], "$V_{th} = %s\\,\\mathrm{V}$, $R_{th} = %s\\,\\Omega$, $I_L = %s\\,\\mathrm{A}$." % (fx(Vth), fx(Rth), fx(IL)), "Solving the full network with $R_L$ connected (solver) gives $I_L = %s$ A. Same."  % fx(IL)))
    N["thevenin"] = "\n\n".join(out); out = []
    for n, (cf, RL, Vth, Rth, IN, IL) in enumerate(TH):
        fig = merge(ladder(RL=RL, o=(0, 0), **cf), norton_eq(IN, Rth, RL, o=(1.5, -6))); fig.T((6, 4.5), "(a) Given network", fs=10.5, bold=True); fig.T((4.5, -2.0), "(b) Norton equivalent", fs=10.5, bold=True); p = fig.draw(D("nort_ex"))
        out.append(_ex("11.%d" % (n + 1), "Norton equivalent" + (" with a current source" if cf["Ish"] else ""), "Same network as Example 10.%d: $R_L = 4\\,\\Omega$." % (n + 1), "$I_N$, $R_N$ and the load current.", _f(p, "Network and its Norton equivalent"), "$I_N$ = short-circuit current through a-b; $R_N = R_{th}$; $I_L = I_N R_N/(R_N + R_L)$.",
                       ["Short a-b: $R_3$ now connects node A directly to the reference, giving $I_N = %s\\,\\mathrm{A}$ (equivalently $V_{th}/R_{th} = %s/%s$)." % (fx(IN), fx(Vth), fx(Rth)), "$R_N = R_{th} = %s\\,\\Omega$." % fx(Rth), "$I_L = %s \\times %s/(%s + 4) = %s\\,\\mathrm{A}$." % (fx(IN), fx(Rth), fx(Rth), fx(IL))], "$I_N = %s\\,\\mathrm{A}$, $R_N = %s\\,\\Omega$, $I_L = %s\\,\\mathrm{A}$." % (fx(IN), fx(Rth), fx(IL)), "Same load current as the Thevenin result and the full-network solution (%s A)." % fx(IL)))
    N["norton"] = "\n\n".join(out); out = []
    for n, (cf, RL, Vth, Rth, IN, IL) in enumerate(TH):
        RLm = Rth; Pm = Vth ** 2 / (4 * Rth); I = Vth / (2 * Rth); rows = ["| $R_L$ (Ω) | $I$ (A) | $P_L$ (W) |", "|---|---|---|"]
        for r in (1, 2, Rth, 8, 16):
            ii = Vth / (Rth + r); rows.append("| %s | %s | %s |" % (fx(r), fx(ii), fx(ii * ii * r)))
        _chk("pmax", Pm, I * I * RLm); fig = merge(thev_eq(Vth, Rth, None, o=(0, 0)), Sch()); fig.R((7.5, 3), (7.5, 0), "R_L", None, txt="$R_L$ (variable)"); fig.W((6, 3), (7.5, 3)); fig.W((6, 0), (7.5, 0)); p1 = fig.draw(D("mpt_c")); p2 = fig_p_vs_rl(D("mpt_p"), Vth, Rth)
        out.append(_ex("12.%d" % (n + 1), "Maximum power transfer", "A network has $V_{th} = %s\\,\\mathrm{V}$ and $R_{th} = %s\\,\\Omega$ (from Example 10.%d)." % (fx(Vth), fx(Rth), n + 1), "$R_L$ for maximum power, $P_{max}$ and efficiency.", _f(p1, "Thevenin source with variable load") + _f(p2, "Load power and efficiency against R_L"), "Maximum power when $R_L = R_{th}$; $P_{max} = V_{th}^2/(4R_{th})$.",
                       ["$R_L = R_{th} = %s\\,\\Omega$." % fx(Rth), "$I = V_{th}/(R_{th}+R_L) = %s/%s = %s\\,\\mathrm{A}$." % (fx(Vth), fx(2 * Rth), fx(I)), "$P_{max} = I^2R_L = %s^2 \\times %s = %s\\,\\mathrm{W}$; also $V_{th}^2/(4R_{th}) = %s^2/%s = %s\\,\\mathrm{W}$." % (fx(I), fx(Rth), fx(Pm), fx(Vth), fx(4 * Rth), fx(Vth ** 2 / (4 * Rth))), "Efficiency $\\eta = R_L/(R_{th}+R_L) = 50\\,\\%%$ (source also dissipates $%s$ W in $R_{th}$)." % fx(Pm), "Table of load power for other values:\n\n" + "\n".join(rows) + "\n"],
                       "$R_L = %s\\,\\Omega$, $P_{max} = %s\\,\\mathrm{W}$, $\\eta = 50\\,\\%%$." % (fx(Rth), fx(Pm)), "In the table, the power is largest (%s W) at $R_L = %s\\,\\Omega$ and smaller on both sides, confirming the theorem." % (fx(Pm), fx(Rth))))
    N["mpt"] = "\n\n".join(out); return N


# ------------------------------------------------ theory ------------------------------------------------
def _theory(D):
    T = {}
    T["intro"] = """Every analysis method in this chapter rests on a few basic quantities. **Voltage** $V$ (volt) is the energy per unit charge between two points. **Current** $I$ (ampere) is the rate of flow of charge, $I = dQ/dt$. **Resistance** $R$ (ohm, $\\Omega$) opposes current. **Power** is $P = VI = I^2R = V^2/R$ (watt).

> [FORMULA] Ohm's law: $$V = IR$$ For a resistor, the current flows from the higher to the lower potential. The voltage across it is a *drop* in the direction of current.

**Network terms.** A *node* is a point where two or more elements meet. A *branch* is an element or series path between two nodes. A *loop* is any closed path. A *mesh* is a loop that contains no other loop. *Independent sources* (ideal voltage or current sources) deliver values that do not depend on any other voltage or current. This chapter uses only independent sources.

**Sign conventions used in this document.** Current arrows show the assumed direction. A resistor drop is positive when travelling against the current arrow. A battery is drawn with the long plate as the positive terminal, and the + sign is also printed beside it. If a calculated current comes out negative, the real direction is opposite to the assumed arrow, and the magnitude is still correct.

> [EXAM] Always state the assumed current directions and polarity on the diagram before writing equations. Marks are lost for equations whose signs do not match the diagram."""
    T["kirchhoff"] = """## Definition and Introduction
Kirchhoff's laws are the two fundamental conservation laws of circuit theory. They hold for every lumped circuit, linear or not, and every other method in this chapter is built on them.

> [DEF] **Kirchhoff's Current Law (KCL):** the algebraic sum of the currents meeting at a node is zero. Equivalently, the total current entering a node equals the total current leaving it.

> [DEF] **Kirchhoff's Voltage Law (KVL):** the algebraic sum of all voltages around any closed loop is zero. Equivalently, the sum of voltage rises equals the sum of voltage drops.

## Working Principle
KCL expresses **conservation of charge**. A node cannot store charge, so whatever flows in must flow out. KVL expresses **conservation of energy**. A unit charge that returns to its starting point has no net change in potential energy.

> [FORMULA] $$\\sum I_{in} = \\sum I_{out} \\qquad \\Longleftrightarrow \\qquad \\sum_{k=1}^{n} I_k = 0$$ $$\\sum V_{rise} = \\sum V_{drop} \\qquad \\Longleftrightarrow \\qquad \\sum_{k=1}^{m} V_k = 0$$

## Derivation of the Series and Parallel Results from the Laws
*Series circuit.* The same current $I$ flows through $R_1, R_2, R_3$ (KCL at each junction). KVL gives $V_S = IR_1 + IR_2 + IR_3$, hence
$$R_{eq} = R_1 + R_2 + R_3 \\qquad \\text{and the voltage divider} \\qquad V_k = V_S \\frac{R_k}{R_{eq}}$$
*Parallel circuit.* The same voltage $V$ appears across every branch (KVL). KCL at the top node gives $I = V/R_1 + V/R_2$, hence
$$\\frac{1}{R_{eq}} = \\frac{1}{R_1} + \\frac{1}{R_2} \\qquad \\text{and the current divider} \\qquad I_1 = I \\frac{R_2}{R_1 + R_2}$$

## How to Apply the Laws
1. Mark a current direction in every branch and a polarity on every element.
2. Apply KCL at independent nodes.
3. Apply KVL around independent loops. Choose a direction and keep it.
4. Solve the simultaneous equations. A negative result means the actual direction is opposite.

## Practical Applications
Household wiring (parallel branches share the supply voltage, so each appliance draws its own current), battery banks, voltage-divider sensor circuits, current measurement with shunts, and every circuit simulator, which solves KCL and KVL equations numerically.

## Advantages and Limitations
They apply to any lumped circuit and give exact equations. The limitation is that the number of equations grows with circuit size, and at very high frequency, where wire length is comparable to wavelength, the lumped assumption fails and Maxwell's equations are needed.

> [EXAM] State both laws with their physical basis (charge and energy conservation). Draw the junction and the loop. For numericals, write the loop direction and sign convention first."""
    T["vsrc"] = """## Definition and Introduction
> [DEF] An **ideal voltage source** maintains a fixed terminal voltage $V_S$ whatever current is drawn from it. Its internal resistance is zero.

> [DEF] A **practical voltage source** is an ideal source $V_S$ in series with an internal resistance $R_s$. Its terminal voltage falls as the load current rises.

## Working Principle
A real battery or generator has resistance in its windings, electrodes and electrolyte. When load current flows, part of the emf is dropped across this internal resistance, so the terminal voltage is lower than the open-circuit voltage.

> [FORMULA] Terminal voltage: $$V = V_S - I R_s \\qquad I = \\frac{V_S}{R_s + R_L}$$ Short-circuit current: $$I_{sc} = \\frac{V_S}{R_s}$$ Voltage regulation: $$\\% \\, VR = \\frac{V_{NL} - V_{FL}}{V_{FL}} \\times 100$$

## Behaviour
The V–I characteristic of the ideal source is a horizontal line. The practical source gives a straight line with a downward slope equal to $-R_s$. The smaller $R_s$ is, the closer the source is to ideal. Source resistance also sets the maximum power the source can supply, which is discussed under maximum power transfer.

## Practical Applications
Batteries and cells, DC power supplies, solar cells (modelled with a source resistance), generators and the Thevenin model of any linear network.

## Advantages and Limitations
The ideal model keeps analysis simple. It is unrealistic because it would supply infinite current to a short circuit. The practical model is accurate for moderate loads, but it does not capture battery chemistry such as state of charge or temperature effects.

> [EXAM] Draw both symbols, show $V = V_S - IR_s$ and plot the V–I characteristic of both. Remember that a *voltage source must never be short-circuited*."""
    T["isrc"] = """## Definition and Introduction
> [DEF] An **ideal current source** delivers a fixed current $I_S$ to any load, whatever the terminal voltage. Its internal resistance is infinite.

> [DEF] A **practical current source** is an ideal current source $I_S$ in parallel with an internal resistance $R_p$. Part of $I_S$ is lost through $R_p$.

## Working Principle
A transistor biased in its active region, or a photodiode, behaves nearly as a constant-current device. The finite output resistance acts like $R_p$ across the terminals, so some current bypasses the load.

> [FORMULA] Load current: $$I_L = I_S - \\frac{V}{R_p} = I_S \\frac{R_p}{R_p + R_L}$$ Open-circuit voltage: $$V_{oc} = I_S R_p$$

## Behaviour
The ideal characteristic is a vertical line (constant current). The practical characteristic bends with slope $-1/R_p$. The larger $R_p$ is, the closer the source is to ideal. The dual of the voltage source rule applies: a *current source must never be open-circuited*, because the ideal source would then develop infinite voltage.

## Practical Applications
Transistor bias circuits, LED drivers, battery chargers, photodiode and sensor circuits, and the Norton model of any linear network.

## Advantages and Limitations
Current sources make nodal equations simple and give a constant current for varying load. The practical source loses current in $R_p$, and compliance voltage is limited in real devices.

> [EXAM] Draw both models with the load. Write $I_L = I_S R_p/(R_p + R_L)$. State that an ideal current source has infinite resistance, which is the opposite of an ideal voltage source."""
    T["srctrans"] = """## Definition and Introduction
> [DEF] **Source transformation** replaces a practical voltage source by an equivalent practical current source (or the reverse) without changing the voltage and current seen by any external load.

## Working Principle
Two sources are equivalent if they give the same terminal voltage for the same terminal current, that is, the same V–I line. Compare the open-circuit voltage and short-circuit current of the two forms.

## Derivation
Voltage form: open-circuit voltage $V_{oc} = V_S$, short-circuit current $I_{sc} = V_S/R_s$. Current form: $V_{oc} = I_S R_p$, $I_{sc} = I_S$. Equating the open-circuit voltages and short-circuit currents:
$$I_S = \\frac{V_S}{R_s} \\qquad R_p = R_s$$

> [FORMULA] $$V_S \\rightarrow I_S = \\frac{V_S}{R_s} \\text{ in parallel with } R_s \\qquad \\qquad I_S \\rightarrow V_S = I_S R_p \\text{ in series with } R_p$$ The arrow of the current source points toward the + terminal of the voltage source.

## Rules and Cautions
1. The equivalence is only for the *external* circuit. Internal power dissipation differs. An open-circuit voltage source dissipates nothing, but its equivalent current source still dissipates $I_S^2R_p$ in its own resistor.
2. An ideal voltage source (zero $R_s$) cannot be converted, and neither can an ideal current source (infinite $R_p$).
3. A resistor in parallel with a voltage source, or in series with a current source, does not affect the external circuit and can be ignored for the external response.

## Practical Applications
Simplifying ladder networks before mesh or nodal analysis, converting between Thevenin and Norton models, and designing bias networks.

## Advantages and Limitations
It reduces the number of nodes or loops step by step and avoids simultaneous equations in simple circuits. It cannot give the current or power inside the transformed source.

> [EXAM] Draw the before-and-after diagram and mark the arrow direction. State that the equivalence is valid only for the external load."""
    T["mesh"] = """## Definition and Introduction
> [DEF] **Mesh analysis** finds the unknown *mesh currents* of a planar network by writing KVL for each mesh. Branch currents are then found by combining mesh currents.

## Working Principle
A fictitious current circulates around each mesh. A branch shared by two meshes carries the difference (or sum) of the two mesh currents. Writing KVL for each mesh gives as many equations as meshes, and this is usually fewer than the number of branch currents. This document covers networks containing independent voltage sources and resistors, so no super-mesh is needed.

## Procedure
1. Identify the meshes and assign a mesh current to each, all clockwise.
2. Write KVL around each mesh: (sum of resistances in the mesh) × (own current) − (shared resistance) × (neighbouring current) = (sum of source rises in the mesh).
3. Solve the simultaneous equations by substitution or determinants.
4. Branch current in a shared resistor = difference of the two mesh currents.

> [FORMULA] For a two-mesh network with all mesh currents clockwise: $$\\begin{aligned}(R_1 + R_2) I_1 - R_2 I_2 &= V_1 \\\\ -R_2 I_1 + (R_2 + R_3) I_2 &= V_2\\end{aligned}$$ In general: $[R][I] = [V]$ with a symmetric resistance matrix when all mesh currents are clockwise.

## Practical Applications
Analysis of bridge-type and ladder networks, filter circuits, power-system loop studies, and as the basis of circuit simulation by loop-current methods.

## Advantages and Limitations
It needs fewer equations than the branch-current method and is best when the circuit has many series elements and voltage sources. It is awkward when current sources appear in a shared branch, because that case needs a super-mesh, which is outside this syllabus. It applies only to planar circuits.

> [EXAM] Always take every mesh current clockwise, so that the diagonal terms are positive and the off-diagonal terms are negative. Show the matrix form and the final branch currents with direction."""
    T["nodal"] = """## Definition and Introduction
> [DEF] **Nodal analysis** finds the unknown *node voltages*, measured with respect to a chosen reference node, by writing KCL at each non-reference node.

## Working Principle
Each branch current is expressed using Ohm's law in terms of node voltages: $I = (V_{a} - V_{b})/R$. KCL at a node then gives one equation per non-reference node. This document covers networks with independent current sources and with voltage sources in series with resistors, so no super-node is needed.

## Procedure
1. Select the reference (ground) node, usually the one with most branches.
2. Label the other node voltages.
3. At each node, set (sum of currents leaving through resistors) = (sum of source currents entering).
4. Solve the equations, then find branch currents from voltage differences.

> [FORMULA] For a two-node network (A, B) with conductances $G = 1/R$: $$\\begin{aligned}(G_A + G_{12}) V_A - G_{12} V_B &= I_A \\\\ -G_{12} V_A + (G_B + G_{12}) V_B &= I_B\\end{aligned}$$ Here $I_A$, $I_B$ are the source currents entering nodes A and B. A source $V_1$ in series with $R_1$ is counted as $G_1 = 1/R_1$ on the diagonal and $V_1/R_1$ on the right-hand side.

## Practical Applications
Analysis of power distribution networks, transistor circuits, and computer programs such as SPICE, which use modified nodal analysis.

## Advantages and Limitations
It needs only $n-1$ equations for $n$ nodes and handles current sources directly. It is the best method when the circuit has many parallel branches. A voltage source connected between two non-reference nodes needs a super-node, which is outside this syllabus.

> [EXAM] Draw the ground symbol and mark the node voltages. Write KCL with all unknown currents *leaving* the node, and keep the sign convention uniform."""
    T["star"] = """## Definition and Introduction
> [DEF] A **star (Y or T)** network has three resistors joined at a common point, with the other ends brought out as terminals A, B, C. A **delta (Δ or π)** network has three resistors connected in a triangle between the same three terminals.

## Working Principle
The two networks are equivalent if the resistance measured between each pair of terminals is the same in both. Star-delta transformation is used when resistors are neither in series nor in parallel, such as in a bridge.

## Derivation (star to delta)
Equate the resistances between each pair of terminals. For terminals A and B with C open:
$$R_A + R_B = \\frac{R_{AB}(R_{BC} + R_{CA})}{R_{AB} + R_{BC} + R_{CA}}$$
Write similar equations for B–C and C–A. Adding all three and dividing by two gives $R_A + R_B + R_C = \\dfrac{R_{AB}R_{BC} + R_{BC}R_{CA} + R_{CA}R_{AB}}{R_{AB}+R_{BC}+R_{CA}}$. Subtracting each pair equation from this result gives the delta-to-star formulas below, and dividing products yields the star-to-delta formulas.

> [FORMULA] Star to delta: $$R_{AB} = \\frac{R_AR_B + R_BR_C + R_CR_A}{R_C} \\qquad R_{BC} = \\frac{R_AR_B + R_BR_C + R_CR_A}{R_A} \\qquad R_{CA} = \\frac{R_AR_B + R_BR_C + R_CR_A}{R_B}$$ Balanced case: $$R_\\Delta = 3R_Y$$

## Memory Aid
Each delta resistor is (sum of products of star resistors taken two at a time) divided by the star resistor *opposite* to it. The star resistor opposite to $R_{AB}$ is $R_C$.

## Practical Applications
Bridge networks, three-phase systems (star and delta connected loads and transformers), and resistive attenuators.

## Advantages and Limitations
It converts a non-reducible network into a series-parallel one without solving simultaneous equations. The conversion is valid only for the three terminals involved, and internal currents of the replaced network are lost.

> [EXAM] Write the formulas for both directions, draw both networks with terminals labelled, and state $R_\\Delta = 3R_Y$ for the balanced case."""
    T["delta"] = """## Definition and Introduction
> [DEF] **Delta-star transformation** replaces a delta network of three resistors by an equivalent star network that gives identical resistances between each pair of terminals.

## Working Principle
Between any two terminals, the resistance of the delta (with the third terminal open) must equal the resistance of the star. The derivation is given under Star-Delta Transformation. Solving the three equations gives the formulas below.

## Derivation
From the pair equations $R_A + R_B = \\dfrac{R_{AB}(R_{BC}+R_{CA})}{\\Sigma}$, $R_B + R_C = \\dfrac{R_{BC}(R_{CA}+R_{AB})}{\\Sigma}$, $R_C + R_A = \\dfrac{R_{CA}(R_{AB}+R_{BC})}{\\Sigma}$ with $\\Sigma = R_{AB}+R_{BC}+R_{CA}$, add the first and third and subtract the second:
$$2R_A = \\frac{R_{AB}R_{BC} + R_{AB}R_{CA} + R_{CA}R_{AB} + R_{CA}R_{BC} - R_{BC}R_{CA} - R_{BC}R_{AB}}{\\Sigma}$$ which simplifies to $R_A = R_{AB}R_{CA}/\\Sigma$.

> [FORMULA] $$R_A = \\frac{R_{AB}R_{CA}}{R_{AB}+R_{BC}+R_{CA}} \\qquad R_B = \\frac{R_{AB}R_{BC}}{R_{AB}+R_{BC}+R_{CA}} \\qquad R_C = \\frac{R_{BC}R_{CA}}{R_{AB}+R_{BC}+R_{CA}}$$ Balanced case: $$R_Y = \\frac{R_\\Delta}{3}$$

## Memory Aid
Each star resistor is the product of the two delta resistors *adjacent to its terminal*, divided by the sum of all three delta resistors. $R_A$ touches $R_{AB}$ and $R_{CA}$.

## Practical Applications
Reducing Wheatstone bridges with an unbalanced detector arm, analysing three-phase delta loads as equivalent stars (per-phase analysis), and filter design.

## Advantages and Limitations
It turns bridges into series-parallel networks. The result always has smaller resistances than the delta, and the star point does not physically exist in the original circuit.

> [EXAM] Draw the delta and the star, label terminals A, B, C, and write all three formulas. For a bridge numerical, convert the delta that contains the bridge arm, then reduce the series-parallel network."""
    T["superposition"] = """## Definition and Introduction
> [STATEMENT] **Superposition theorem:** in a linear bilateral network containing more than one independent source, the current through (or voltage across) any element is the algebraic sum of the currents (or voltages) produced by each independent source acting alone, with all other independent sources replaced by their internal resistances.

## Working Principle
In a linear circuit the equations are linear, so the response to several inputs equals the sum of the responses to each input separately. An ideal voltage source is replaced by a **short circuit** and an ideal current source by an **open circuit** when it is switched off.

## Procedure
1. Keep one source, deactivate the others (voltage source → short, current source → open).
2. Find the required current or voltage using series-parallel reduction and divider rules.
3. Repeat for each source.
4. Add the results with their signs, taking the direction of the response into account.

> [FORMULA] $$I = I' + I'' + I''' + \\dots \\qquad V = V' + V'' + V''' + \\dots$$

## Practical Applications
Analysis of circuits with a DC source and an AC signal together (bias plus signal in amplifiers), multiple-supply systems, and sensor networks.

## Advantages and Limitations
It uses only series-parallel reduction, and it separates the effect of each source. It works only for linear circuits, so it **cannot be applied to power**, since $P = I^2R$ is not linear. Power must be computed from the final total current. It becomes long when there are many sources.

> [EXAM] State the theorem with the linearity condition and the rule for deactivating sources. Show a separate diagram for each source. Remember that power is not additive."""
    T["thevenin"] = """## Definition and Introduction
> [STATEMENT] **Thevenin's theorem:** any linear two-terminal network containing independent sources and resistors can be replaced, as seen from its terminals, by a single voltage source $V_{th}$ in series with a single resistance $R_{th}$.

## Working Principle
The $V_{th}$ and $R_{th}$ are chosen so that the replaced network gives the same V–I relationship at the terminals. $V_{th}$ is the open-circuit voltage, and $R_{th}$ is the resistance seen at the terminals when all independent sources are deactivated.

## Procedure
1. Remove the load resistor and mark the terminals a and b.
2. Find $V_{th}$ = open-circuit voltage $V_{ab}$.
3. Deactivate sources (voltage source short, current source open) and find $R_{th}$ looking into a-b.
4. Draw the equivalent circuit and reconnect the load.

> [FORMULA] $$I_L = \\frac{V_{th}}{R_{th} + R_L} \\qquad V_L = V_{th}\\frac{R_L}{R_{th}+R_L}$$

## Practical Applications
Studying the effect of a changing load without re-solving the network, designing power supplies and amplifiers (output resistance), and finding the source impedance of sensors and batteries.

## Advantages and Limitations
It simplifies the analysis when one part of a circuit, usually the load, changes. It applies to linear circuits only, and it gives the power delivered to the load but not the power dissipated inside the original network.

> [EXAM] Draw the original network, the open-circuit circuit, the deactivated circuit and the final equivalent. Write the 4-step procedure."""
    T["norton"] = """## Definition and Introduction
> [STATEMENT] **Norton's theorem:** any linear two-terminal network containing independent sources and resistors can be replaced by a single current source $I_N$ in parallel with a single resistance $R_N$.

## Working Principle
$I_N$ is the short-circuit current between the terminals, and $R_N$ equals the Thevenin resistance $R_{th}$, found with all independent sources deactivated. The Norton and Thevenin models are related by source transformation.

## Procedure
1. Short the terminals a-b (remove the load) and find the short-circuit current $I_{sc} = I_N$.
2. Deactivate sources and find $R_N$ seen from a-b.
3. Draw the equivalent circuit and connect the load across it.

> [FORMULA] $$I_L = I_N \\frac{R_N}{R_N + R_L} \\qquad I_N = \\frac{V_{th}}{R_{th}} \\qquad R_N = R_{th}$$

## Practical Applications
Analysis of transistor and amplifier output stages (current-driven models), parallel-connected sources, and sensors that behave as current sources.

## Advantages and Limitations
It is convenient when the circuit has parallel branches or the load is connected in parallel. As with Thevenin's theorem, it applies to linear circuits only, and it is not valid if the circuit has a dependent source controlled by something outside the network (not part of this syllabus).

> [EXAM] Write $I_N = V_{th}/R_{th}$ and $R_N = R_{th}$. Draw the Norton circuit with the arrow of the current source toward terminal a when $V_{th}$ is positive at a."""
    T["mpt"] = """## Definition and Introduction
> [STATEMENT] **Maximum power transfer theorem:** a load receives the maximum power from a linear DC network when its resistance equals the Thevenin resistance of the network as seen from the load terminals, that is $R_L = R_{th}$.

## Working Principle
The load power is $P = I^2R_L$. If $R_L$ is small, the current is large but the load voltage is small. If $R_L$ is large, the voltage is large but the current is small. The product is largest at a particular value in between.

## Derivation
With the network replaced by $V_{th}$ and $R_{th}$:
$$P = I^2R_L = \\frac{V_{th}^2 R_L}{(R_{th}+R_L)^2}$$
Differentiate with respect to $R_L$ and equate to zero:
$$\\frac{dP}{dR_L} = V_{th}^2 \\frac{(R_{th}+R_L)^2 - 2R_L(R_{th}+R_L)}{(R_{th}+R_L)^4} = V_{th}^2 \\frac{R_{th} - R_L}{(R_{th}+R_L)^3} = 0 \\Rightarrow R_L = R_{th}$$
The second derivative is negative at this point, so it is a maximum.

> [FORMULA] $$P_{max} = \\frac{V_{th}^2}{4R_{th}} = \\frac{I_N^2 R_{th}}{4} \\qquad \\eta = \\frac{R_L}{R_{th}+R_L} \\times 100 = 50\\,\\% \\text{ at maximum power}$$

## Practical Applications
Matching a loudspeaker to an amplifier, antenna and radio-frequency matching, and solar cell maximum-power-point trackers. In **power systems** the aim is the opposite: high efficiency, so the load is much larger than the source resistance.

## Advantages and Limitations
It gives the best power in the load for a given source. The efficiency is only 50 %, since an equal amount of power is lost in $R_{th}$, so the condition is used for signal circuits and not for power transmission.

> [EXAM] Derive $R_L = R_{th}$, give $P_{max}$, and state the 50 % efficiency. Mention that the theorem maximizes load power, not efficiency."""
    return T


TOPICS = [("kirchhoff", "Kirchhoff's Laws (KCL and KVL)"), ("vsrc", "Ideal and Practical Voltage Sources"), ("isrc", "Ideal and Practical Current Sources"), ("srctrans", "Source Transformation"), ("mesh", "Mesh Analysis"), ("nodal", "Nodal Analysis"), ("star", "Star-Delta Transformation"), ("delta", "Delta-Star Transformation"), ("superposition", "Superposition Theorem"), ("thevenin", "Thevenin's Theorem"), ("norton", "Norton's Theorem"), ("mpt", "Maximum Power Transfer Theorem")]
