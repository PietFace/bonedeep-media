import sys, math
sys.path.insert(0, "/home/claude/v2"); sys.path.insert(0, "/home/claude/short"); sys.path.insert(0, "/home/claude/v2/acl")
import cairo
import common as C
from common import W, H, kf, ss, mix, p, eo, eio, back, clamp, YEL, RED, WHITE, GREY, CYAN, GREEN, d2r
import anim2 as A
import acl as AC
from anim import rrect

D = "/home/claude/v2/acl"
TL = C.Timeline(D + "/timeline.json"); T = TL.T; TOTAL = TL.total
TPOP = TL.wt("tear", "torn.")
THIT = T["hit"][0]
TIN0, TIN1 = T["title"][0] - 0.1, T["title"][1] - 0.2
TOUT0, TOUT1 = T["rehab"][0] - 0.1, T["rehab"][0] + 1.6
M0 = 0.30
REF = (520, 900)
GROUND = 1440.0
METAL = (0.82, 0.86, 0.92)
THV = TL.wt("harvest", "strip")
TTD0, TTD1 = TL.wt("tunnels", "drills"), TL.wt("tunnels", "one") - 0.2
TFD0, TFD1 = TL.wt("tunnels", "one"), T["tunnels"][1] + 0.1
TPL0, TPL1 = T["pull"][0], TL.wt("pull", "fixed") - 0.1
TFIX = TL.wt("pull", "fixed")
TWK = TL.wt("weak", "weaker")
TST = TL.wt("weak", "stronger,")


def run_amp(t):
    if t < TPOP:
        return 1.0
    if t < TOUT0:
        return kf(t, [(TPOP, 1.0), (TPOP + 0.35, 0.0)])
    return kf(t, [(TOUT1 - 0.4, 0.0), (TOUT1 + 0.6, 1.0)])


def phase(t):
    return t * 2 * math.pi * 1.45


def leg_pose(hip, ph, amp, buckle=0.0):
    th = 26 * math.sin(ph) * amp * d2r
    kn = (8 + 85 * amp * max(0.0, math.cos(ph + 0.35)) ** 1.5 + 35 * buckle) * d2r
    K_ = (hip[0] + 300 * math.sin(th), hip[1] + 300 * math.cos(th))
    sa = th - kn
    A_ = (K_[0] + 290 * math.sin(sa), K_[1] + 290 * math.cos(sa))
    return K_, A_, sa, th, kn


def pose(t):
    amp = run_amp(t)
    ph = phase(min(t, TPOP)) if t < TOUT0 else phase(t)
    buckle = math.exp(-(t - TPOP) * 3) if TPOP < t < TOUT0 else 0.0
    lean = (4 + 6 * amp) * d2r
    hip = (500.0, 800.0)
    legs = [leg_pose(hip, ph, amp, buckle), leg_pose(hip, ph + math.pi, amp)]
    dy = GROUND - 30 - max(l[1][1] for l in legs)
    hip = (hip[0], hip[1] + dy)
    legs = [((k[0], k[1] + dy), (a[0], a[1] + dy), fa, th, kn) for k, a, fa, th, kn in legs]
    sh = (hip[0] + 330 * math.sin(lean), hip[1] - 330 * math.cos(lean))
    head = (sh[0] + 100 * math.sin(lean + 0.1), sh[1] - 100 * math.cos(lean + 0.1))
    arms = []
    for s in (1, -1):
        aa = -30 * s * math.sin(ph) * amp * d2r
        E = (sh[0] + 150 * math.sin(aa), sh[1] + 150 * math.cos(aa))
        ea = aa + (30 + 56 * amp) * d2r
        arms.append((E, (E[0] + 140 * math.sin(ea), E[1] + 140 * math.cos(ea))))
    return dict(hip=hip, sh=sh, head=head, legs=legs, arms=arms)


def foot(ctx, A_, fa):
    ctx.save(); ctx.translate(*A_); ctx.rotate(-fa)
    ctx.move_to(-44, -14); ctx.line_to(150, 18); ctx.curve_to(170, 24, 170, 44, 150, 46); ctx.line_to(-46, 46)
    ctx.curve_to(-60, 30, -56, -8, -44, -14); ctx.close_path(); ctx.restore()


def figure(ctx, P, which):
    K_, A_, fa, _, _ = P["legs"][which]
    C.limb(ctx, P["hip"], K_, 106, 80); ctx.fill()
    C.limb(ctx, K_, A_, 78, 44); ctx.fill()
    foot(ctx, A_, fa); ctx.fill()
    E, Hd = P["arms"][which]
    C.limb(ctx, P["sh"], E, 56, 46); ctx.fill(); C.limb(ctx, E, Hd, 44, 34); ctx.fill()
    if which == 1:
        return
    C.limb(ctx, P["hip"], P["sh"], 150, 160); ctx.fill()
    C.limb(ctx, P["sh"], mix(P["sh"], P["head"], 0.5), 60, 52); ctx.fill()
    ctx.arc(P["head"][0], P["head"][1], 64, 0, 2 * math.pi)


PS = pose(TIN0)
PS["legs"][0] = (PS["legs"][0][0], PS["legs"][0][1], PS["legs"][0][2], 0.0, PS["legs"][0][4])
KW = PS["legs"][0][0]


def state(t, P, inside):
    st = {"theta": 0.0 if inside else P["legs"][0][4] / d2r}
    if t < TPOP:
        st["acl_glow"] = 0.0
    else:
        st["torn"] = eo(p(t, TPOP, TPOP + 0.2))
        st["acl_glow"] = 1.0 if t < T["harvest"][0] else 0.0
        st["acl_col"] = RED
    if t >= THV - 0.6:
        st["acl"] = 1 - p(t, THV - 0.6, THV)
    st["ham_glow"] = p(t, TL.wt("harvest", "hamstring"), TL.wt("harvest", "hamstring") + 0.3) * (1 - p(t, T["tunnels"][0], T["tunnels"][0] + 0.3))
    st["harvest"] = p(t, TL.wt("harvest", "tendon"), TL.wt("harvest", "tendon") + 1.2) if t < T["tunnels"][0] else 0
    st["ttun"] = p(t, TTD0, TTD1)
    if TTD0 <= t < TTD1 + 0.2:
        st["tdrill"] = p(t, TTD0, TTD1)
    st["ftun"] = p(t, TFD0, TFD1)
    if TFD0 <= t < TFD1 + 0.2:
        st["fdrill"] = p(t, TFD0, TFD1)
    st["graft"] = p(t, TPL0, TPL1)
    st["screws"] = p(t, TFIX, TFIX + 0.5)
    st["graft_glow"] = p(t, TL.wt("pull", "new"), TL.wt("pull", "new") + 0.3)
    st["weak"] = p(t, TWK - 0.2, TWK + 0.4) * (1 - p(t, TST, TST + 0.8))
    st["gstrong"] = p(t, TST, TST + 0.8)
    if inside and t >= TST:
        st["theta"] = 30 - 30 * math.cos((t - TST) * 2.0)
    return st


def camera(t):
    fig_c = (520.0, 950.0)
    z_in = 1.05 / M0
    tgt = (KW[0], KW[1] + 120 * M0)
    if t < TIN0:
        return 1.0, fig_c
    if t < TIN1:
        k = eio(p(t, TIN0, TIN1)); return 1 + (z_in - 1) * k, mix(fig_c, tgt, k)
    if t < TOUT0:
        mv = [(TIN1, (0, 120), 1.0), (T["harvest"][0] + 0.3, (-80, 140), 0.9), (TTD0, (40, 300), 1.0), (TFD0, (-40, 130), 1.05),
              (TPL0, (0, 160), 0.95), (T["weak"][0], (0, 150), 1.0), (TOUT0 - 0.2, (0, 120), 1.0)]
        off = kf(t, [(a, b) for a, b, _ in mv]); zm = kf(t, [(a, c) for a, _, c in mv])
        return z_in * zm, (KW[0] + off[0] * M0, KW[1] + off[1] * M0)
    if t < TOUT1:
        k = eio(p(t, TOUT0, TOUT1)); return z_in + (1 - z_in) * k, mix(tgt, fig_c, k)
    return 1.0, fig_c


def window(t):
    if t < TPOP - 0.1: return 0
    if t < TIN0: return 135 * back(p(t, TPOP - 0.1, TPOP + 0.2))
    if t < TIN1: return 135 + 1200 * ss(p(t, TIN0 + 0.3, TIN1))
    if t < TOUT0: return 4000
    if t < TOUT1: return 1335 - 1200 * ss(p(t, TOUT0, TOUT1 - 0.2))
    return 135 * (1 - ss(p(t, TOTAL - 0.5, TOTAL - 0.1)))


def series_tag(ctx, t):
    a = p(t, 0.2, 0.6) * (1 - p(t, TOTAL - 0.4, TOTAL))
    rrect(ctx, W / 2 - 260, 250, 520, 64, 32); A.rgba(ctx, CYAN, 0.16 * a); ctx.fill_preserve()
    A.rgba(ctx, CYAN, 0.8 * a); ctx.set_line_width(3); ctx.stroke()
    A.txt(ctx, "WHAT THEY ACTUALLY DO", W / 2, 296, 36, WHITE, a, shadow=False)


def strength_chart(ctx, t):
    a = p(t, T["weak"][0] + 0.2, T["weak"][0] + 0.6) * (1 - p(t, T["weak"][1] + 0.1, T["weak"][1] + 0.4))
    if a <= 0: return
    x0, y0, w, h = 150, 860, 780, 330
    rrect(ctx, x0 - 40, y0 - h - 90, w + 80, h + 170, 26); A.rgba(ctx, (0.03, 0.04, 0.07), 0.82 * a); ctx.fill()
    A.txt(ctx, "graft strength", x0 + w / 2, y0 - h - 30, 42, WHITE, a)
    ctx.move_to(x0, y0); ctx.line_to(x0 + w, y0); A.rgba(ctx, GREY, a); ctx.set_line_width(3); ctx.stroke()
    for m in (0, 3, 6, 9, 12):
        x = x0 + w * m / 12
        A.txt(ctx, f"{m}", x, y0 + 46, 32, GREY, a, bold=False, shadow=False)
    A.txt(ctx, "months", x0 + w / 2, y0 + 86, 30, GREY, a, bold=False, shadow=False)
    f = lambda m: 0.75 - 0.42 * math.exp(-((m - 2) / 1.3) ** 2) + 0.18 * clamp((m - 2) / 10)   # dip, then recovery
    prog = eo(p(t, T["weak"][0] + 0.4, TST + 1.2))
    n = 60
    for lw, al in ((16, 0.15), (6, 1.0)):
        ctx.move_to(x0, y0 - h * f(0))
        for i in range(1, int(n * prog) + 1):
            m = 12 * i / n
            ctx.line_to(x0 + w * m / 12, y0 - h * f(m))
        A.rgba(ctx, YEL, al * a); ctx.set_line_width(lw); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke()
    if prog > 0.25:
        xd = x0 + w * 2 / 12; yd = y0 - h * f(2)
        ctx.arc(xd, yd, 12, 0, 2 * math.pi); A.rgba(ctx, RED, a); ctx.fill()
        A.txt(ctx, "weakest", xd + 20, yd + 60, 34, RED, a * p(t, TWK, TWK + 0.3), shadow=False)


EV = [(TPOP, 1.0, True), (TFIX + 0.4, 0.4, False)]


def render(t):
    inside = TIN1 - 0.6 <= t < TOUT0 + 0.3
    P = PS if TIN0 <= t <= TOUT1 - 0.3 else pose(t)
    st = state(t, P, inside)
    z, foc = camera(t)
    sx, sy, zb, flash = C.shake(t, EV)
    fig_a = (1 - ss(p(t, TIN0 + 0.8, TIN1 - 0.1))) if t < TOUT0 else ss(p(t, TOUT0 + 0.5, TOUT1))
    redk = 0.5 * (st.get("torn", 0) if t < T["harvest"][0] else 0) * (1 - p(t, TIN1, TIN1 + 0.5)) + 0.35 * st["weak"]
    green = max(st["gstrong"] * (1 - p(t, TOUT0, TOUT0 + 0.5)), p(t, T["end"][0], T["end"][0] + 0.6) * (1 - p(t, TOTAL - 1, TOTAL)))
    surg = p(t, T["harvest"][0] - 0.3, T["harvest"][0] + 0.3) * (1 - p(t, T["weak"][0], T["weak"][0] + 0.5))
    tint = mix(mix(mix((0.09, 0.12, 0.20), (0.05, 0.16, 0.18), surg), (0.04, 0.19, 0.15), green), (0.20, 0.05, 0.06), clamp(redk))
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf); ctx.set_antialias(cairo.ANTIALIAS_GOOD)
    C.background(ctx, t, z, foc, tint, REF)
    ctx.save(); ctx.translate(W / 2 + sx, 950 + sy); ctx.scale(z * (1 + zb), z * (1 + zb)); ctx.translate(-foc[0], -foc[1])
    world = ctx.get_matrix()
    if fig_a > 0:
        g = cairo.RadialGradient(520, GROUND, 10, 520, GROUND, 420)
        g.add_color_stop_rgba(0, CYAN[0], CYAN[1], CYAN[2], 0.22 * fig_a); g.add_color_stop_rgba(1, CYAN[0], CYAN[1], CYAN[2], 0)
        ctx.save(); ctx.translate(0, GROUND); ctx.scale(1, 0.1); ctx.translate(0, -GROUND); ctx.set_source(g)
        ctx.arc(520, GROUND, 420, 0, 2 * math.pi); ctx.fill(); ctx.restore()
        amp = run_amp(t)
        for i in range(7):
            x = 900 - ((t * 900 + i * 260) % 1500); y = GROUND + 6 + (i % 3) * 14
            ctx.move_to(x, y); ctx.line_to(x + 120, y); A.rgba(ctx, CYAN, 0.35 * amp * fig_a); ctx.set_line_width(3); ctx.stroke()
    ctx.restore()
    sil = C.silhouette_layer(world, lambda c: figure(c, P, 0), fig_a, lambda c: figure(c, P, 1))
    if sil:
        ctx.set_source_surface(sil[0], 0, 0); ctx.paint()
    rw = window(t); anchors = {}
    if rw > 0:
        K_, _, _, th, _ = P["legs"][0]
        wc = K_
        ctx.save(); ctx.set_matrix(world)
        ctx.arc(wc[0], wc[1], rw, 0, 2 * math.pi)
        if rw < 2000:
            ctx.save(); ctx.clip_preserve(); ctx.set_source_rgb(0.03, 0.04, 0.07); ctx.paint(); ctx.restore()
        ctx.clip()
        ctx.push_group()
        ctx.translate(*wc); ctx.rotate(-th); ctx.scale(M0, M0)
        AC.knee(ctx, t, st, anchors)
        model = ctx.pop_group()
        ctx.set_source(model); ctx.paint()
        C.light_sweep(ctx, t, model)
        ctx.restore()
        if rw < 2000:
            C.window_rim(ctx, world, wc, rw, z)
    C.bokeh_front(ctx, t, z, foc, REF)
    A.vignette(ctx, red=clamp(redk) * 0.6 + (0.6 * math.exp(-(t - TPOP) * 3) if t > TPOP else 0))
    C.fades(ctx)
    series_tag(ctx, t)
    strength_chart(ctx, t)
    lk = lambda a_, b_: p(t, a_, a_ + 0.4) * (1 - p(t, b_, b_ + 0.3))
    C.label(ctx, "torn ACL", anchors.get("acl"), 230, 700, lk(TIN1, T["harvest"][0]), RED)
    C.label(ctx, "hamstring tendon", anchors.get("ham"), 260, 640, lk(TL.wt("harvest", "hamstring"), T["tunnels"][0]), YEL)
    C.label(ctx, "screw", anchors.get("screw"), 230, 620, lk(TFIX + 0.3, T["weak"][0]), METAL)
    C.label(ctx, "new ACL", anchors.get("graft"), 860, 720, lk(TL.wt("pull", "new"), T["weak"][0]), GREEN)
    C.slam_word(ctx, "POP!", t, TPOP, RED, 220, 600, hold=0.9)
    C.slam_word(ctx, "RARELY HEALS", t, TL.wt("tear", "rarely"), RED, 120, 600, hold=T["tear"][1] - TL.wt("tear", "rarely") + 0.3)
    if TIN0 - 0.2 <= t < T["harvest"][0] + 0.2:
        a = p(t, T["title"][0], T["title"][0] + 0.3) * (1 - p(t, T["harvest"][0] - 0.2, T["harvest"][0] + 0.1))
        s = 1.4 - 0.4 * eo(p(t, T["title"][0], T["title"][0] + 0.35))
        ctx.save(); ctx.translate(W / 2, 520); ctx.scale(s, s); ctx.translate(-W / 2, -520)
        A.txt(ctx, "NEW ACL", W / 2, 540, 150, WHITE, a)
        A.txt(ctx, "ACL reconstruction", W / 2, 620, 46, CYAN, a * 0.9, bold=False)
        ctx.restore()
    C.slam_word(ctx, "YOUR OWN TENDON", t, TL.wt("harvest", "own"), YEL, 100, 440, hold=T["harvest"][1] - TL.wt("harvest", "own") + 0.2, rot=0)
    C.slam_word(ctx, "2 TUNNELS", t, TTD0, WHITE, 140, 440, hold=T["tunnels"][1] - TTD0 + 0.2, rot=0)
    C.slam_word(ctx, "NEW ACL", t, TL.wt("pull", "new"), GREEN, 150, 440, hold=T["pull"][1] - TL.wt("pull", "new") + 0.2, rot=0)
    C.slam_word(ctx, "9+ MONTHS", t, TL.wt("rehab", "nine"), YEL, 150, 560, hold=TL.wt("rehab", "going") - TL.wt("rehab", "nine") - 0.1, rot=0)
    C.slam_word(ctx, "TOO EARLY = RE-TEAR RISK", t, TL.wt("rehab", "going"), RED, 74, 560, hold=T["rehab"][1] - TL.wt("rehab", "going") + 0.2, rot=0)
    C.slam_word(ctx, "WORTH IT", t, TL.wt("end", "worth"), GREEN, 160, 560, hold=TOTAL - TL.wt("end", "worth") - 0.6, rot=0)
    C.captions(ctx, t, TL)
    if t > T["end"][0]:
        A.txt(ctx, "General information, not personal medical advice", W / 2, 1440, 26, GREY,
              0.8 * p(t, T["end"][0], T["end"][0] + 0.4) * (1 - p(t, TOTAL - 0.4, TOTAL)), bold=False, shadow=False)
    if flash > 0:
        A.rgba(ctx, WHITE, flash * 0.5); ctx.paint()
    return surf


BLUR = [(TPOP - 0.05, TPOP + 0.3), (TIN0, TIN1), (TOUT0, TOUT1)]
if __name__ == "__main__":
    C.run(render, TOTAL, BLUR, sys.argv)
