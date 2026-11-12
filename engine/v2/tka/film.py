import sys, math
sys.path.insert(0, "/home/claude/v2"); sys.path.insert(0, "/home/claude/short"); sys.path.insert(0, "/home/claude/v2/tka")
import cairo
import common as C
from common import W, H, kf, ss, mix, p, eo, eio, back, clamp, YEL, RED, WHITE, GREY, CYAN, GREEN, d2r
import anim2 as A
import tka as TK
from anim import rrect

D = "/home/claude/v2/tka"
TL = C.Timeline(D + "/timeline.json"); T = TL.T; TOTAL = TL.total
THIT = T["hit"][0]
TIN0, TIN1 = T["title"][0] - 0.1, T["title"][1] - 0.2
TOUT0, TOUT1 = T["walk"][0] - 0.1, T["walk"][0] + 1.6
M0 = 0.30
REF = (520, 900)
GROUND = 1440.0
METAL = (0.82, 0.86, 0.92)

# surgery timing
TF0, TF1 = TL.wt("cut", "cuts"), TL.wt("cut", "shin") - 0.5            # femur saw
TFC = (TF1, TF1 + 0.7)                                                   # femur slices fall
TT0, TT1 = TL.wt("cut", "shin"), T["cut"][1] - 0.2                      # tibia saw
TTC = (TT1, TT1 + 0.7)
TCAP = TL.wt("metal", "metal")
TTRAY = TL.wt("metal", "both")
TINS = TL.wt("plastic", "insert")
TGLIDE = TL.wt("plastic", "glides,")


def gait(t):
    """(amplitude, crutches) of the walking figure"""
    if t < TOUT0:
        return 0.45, 0.0
    if t < T["rehab"][0]:
        return 0.35, 1.0
    return kf(t, [(T["rehab"][0], 0.35), (T["rehab"][0] + 1, 0.7)]), 1 - p(t, T["rehab"][0], T["rehab"][0] + 0.8)


def phase(t):
    return t * 2 * math.pi * 0.85


def leg_pose(hip, ph, amp):
    th = 24 * math.sin(ph) * amp * d2r
    kn = (4 + 62 * amp * max(0.0, math.cos(ph + 0.35)) ** 1.5) * d2r
    K_ = (hip[0] + 300 * math.sin(th), hip[1] + 300 * math.cos(th))
    sa = th - kn
    A_ = (K_[0] + 290 * math.sin(sa), K_[1] + 290 * math.cos(sa))
    return K_, A_, sa, th, kn


def pose(t, frozen=False):
    amp, cr = (0.0, 0.0) if frozen else gait(t)
    ph = phase(t)
    lean = (4 + 8 * cr) * d2r
    hip = (500.0, 820.0)
    legs = [leg_pose(hip, ph, amp), leg_pose(hip, ph + math.pi, amp)]
    dy = GROUND - 30 - max(l[1][1] for l in legs)
    hip = (hip[0], hip[1] + dy)
    legs = [((k[0], k[1] + dy), (a[0], a[1] + dy), fa, th, kn) for k, a, fa, th, kn in legs]
    sh = (hip[0] + 330 * math.sin(lean), hip[1] - 330 * math.cos(lean))
    head = (sh[0] + 100 * math.sin(lean + 0.1), sh[1] - 100 * math.cos(lean + 0.1))
    arms = []
    for s in (1, -1):
        aa = (-22 * s * math.sin(ph) * amp * (1 - cr) + 30 * cr) * d2r
        E = (sh[0] + 150 * math.sin(aa), sh[1] + 150 * math.cos(aa))
        ea = aa + (30 + 20 * cr) * d2r
        arms.append((E, (E[0] + 140 * math.sin(ea), E[1] + 140 * math.cos(ea))))
    return dict(hip=hip, sh=sh, head=head, legs=legs, arms=arms, cr=cr)


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
    if P["cr"] > 0.02:   # crutch
        ctx.save(); ctx.set_line_width(16 * P["cr"]); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        top = (Hd[0] - 10, Hd[1] - 60); bot = (Hd[0] + 40, GROUND - 10)
        ctx.move_to(*top); ctx.line_to(*bot); ctx.stroke(); ctx.restore()
    if which == 1:
        return
    C.limb(ctx, P["hip"], P["sh"], 150, 160); ctx.fill()
    C.limb(ctx, P["sh"], mix(P["sh"], P["head"], 0.5), 60, 52); ctx.fill()
    ctx.arc(P["head"][0], P["head"][1], 64, 0, 2 * math.pi)


PS = pose(TIN0, frozen=True)
KW = PS["legs"][0][0]


def state(t, P):
    st = {}
    inside = TIN1 - 0.6 <= t < TOUT0 + 0.3
    if not inside:
        _, _, _, th, kn = P["legs"][0]
        st["theta"] = kn / d2r
    else:
        st["theta"] = 0.0
    if t < T["cut"][0]:
        st["worn"] = 1.0
        st["grind"] = p(t, TL.wt("worn", "grinds"), TL.wt("worn", "grinds") + 0.3) * (1 - p(t, TIN1, TIN1 + 0.5)) if t < TIN1 + 0.5 else 0
        if TIN1 - 0.6 <= t < T["cut"][0]:
            st["theta"] = 20 + 20 * math.sin((t - TIN1) * 4) if t < TIN1 + 0.3 else kf(t, [(TIN1 + 0.3, 20 + 20 * math.sin(1.2)), (T["cut"][0], 0)])
    else:
        st["worn"] = 1 - p(t, TFC[0], TFC[1])
    # femur saw
    if TF0 <= t < TF1:
        n = len(TK.CUTS); u = (t - TF0) / (TF1 - TF0) * n
        i = min(n - 1, int(u)); st["saw"] = (TK.CUTS[i], u - i, "femur")
    st["fcut"] = p(t, TFC[0], TFC[1]) if t >= TFC[0] else 0
    if TT0 <= t < TT1:
        st["saw"] = (((-130, TK.TCUT), (120, TK.TCUT)), (t - TT0) / (TT1 - TT0), "tibia")
    st["tcut"] = p(t, TTC[0], TTC[1]) if t >= TTC[0] else 0
    st["cap"] = p(t, TCAP, TCAP + 0.8)
    st["tray"] = p(t, TTRAY, TTRAY + 0.8)
    st["ins"] = p(t, TINS, TINS + 0.7)
    if TGLIDE - 0.8 <= t < TOUT0 and inside:
        st["theta"] = 55 - 55 * math.cos((t - (TGLIDE - 0.8)) * 2.2)
        st["glide"] = p(t, TGLIDE, TGLIDE + 0.4)
        st["ins_glow"] = st["glide"]
    if t >= T["walk"][0]:
        st["glide"] = 0.35
    return st


def camera(t):
    fig_c = (520.0, 950.0)
    z_in = 1.05 / M0
    tgt = (KW[0], KW[1] + 130 * M0)
    if t < TIN0:
        return 1.0, fig_c
    if t < TIN1:
        k = eio(p(t, TIN0, TIN1)); return 1 + (z_in - 1) * k, mix(fig_c, tgt, k)
    if t < TOUT0:
        mv = [(TIN1, (0, 130), 1.0), (TF0, (-20, 170), 1.2), (TT0, (-20, 300), 1.2), (TCAP - 0.2, (0, 200), 1.0),
              (TINS, (40, 260), 1.25), (TGLIDE, (0, 220), 0.95), (TOUT0 - 0.2, (0, 130), 1.0)]
        off = kf(t, [(a, b) for a, b, _ in mv]); zm = kf(t, [(a, c) for a, _, c in mv])
        return z_in * zm, (KW[0] + off[0] * M0, KW[1] + off[1] * M0)
    if t < TOUT1:
        k = eio(p(t, TOUT0, TOUT1)); return z_in + (1 - z_in) * k, mix(tgt, fig_c, k)
    return 1.0, fig_c


def window(t):
    if t < 0.6: return 0
    if t < TIN0: return 135 * back(p(t, 0.6, 0.9))
    if t < TIN1: return 135 + 1200 * ss(p(t, TIN0 + 0.3, TIN1))
    if t < TOUT0: return 4000
    if t < TOUT1: return 1335 - 1200 * ss(p(t, TOUT0, TOUT1 - 0.2))
    return 135 * (1 - ss(p(t, TOTAL - 0.5, TOTAL - 0.1)))


def series_tag(ctx, t):
    a = p(t, 0.2, 0.6) * (1 - p(t, TOTAL - 0.4, TOTAL))
    rrect(ctx, W / 2 - 260, 250, 520, 64, 32); A.rgba(ctx, CYAN, 0.16 * a); ctx.fill_preserve()
    A.rgba(ctx, CYAN, 0.8 * a); ctx.set_line_width(3); ctx.stroke()
    A.txt(ctx, "WHAT THEY ACTUALLY DO", W / 2, 296, 36, WHITE, a, shadow=False)


EV = [(THIT, 0.8, True), (TFC[0], 0.4, False), (TTC[0], 0.4, False), (TCAP + 0.7, 0.35, False), (TTRAY + 0.7, 0.35, False),
      (TINS + 0.6, 0.4, False)]


def render(t):
    P = pose(t) if (t < TIN0 or t > TOUT1 - 0.3) else PS
    st = state(t, P)
    z, foc = camera(t)
    sx, sy, zb, flash = C.shake(t, EV)
    fig_a = (1 - ss(p(t, TIN0 + 0.8, TIN1 - 0.1))) if t < TOUT0 else ss(p(t, TOUT0 + 0.5, TOUT1))
    redk = 0.5 * st.get("grind", 0)
    green = max(p(t, TGLIDE, TGLIDE + 0.5) * (1 - p(t, TOUT0, TOUT0 + 0.5)), p(t, T["last"][0], T["last"][0] + 0.6) * (1 - p(t, TOTAL - 1, TOTAL)))
    surg = p(t, T["cut"][0] - 0.3, T["cut"][0] + 0.3) * (1 - p(t, T["plastic"][0], T["plastic"][0] + 0.5))
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
        TK.knee(ctx, t, st, anchors)
        model = ctx.pop_group()
        ctx.set_source(model); ctx.paint()
        C.light_sweep(ctx, t, model)
        ctx.restore()
        if rw < 2000:
            C.window_rim(ctx, world, wc, rw, z)
    C.bokeh_front(ctx, t, z, foc, REF)
    A.vignette(ctx, red=clamp(redk) * 0.6 + (0.5 * math.exp(-(t - THIT) * 3) if THIT < t < TIN0 else 0))
    C.fades(ctx)
    series_tag(ctx, t)
    # labels
    lk = lambda a_, b_: p(t, a_, a_ + 0.4) * (1 - p(t, b_, b_ + 0.3))
    C.label(ctx, "thigh bone", anchors.get("femur"), 230, 620, lk(TL.wt("cut", "thigh"), TT0), WHITE)
    C.label(ctx, "shin bone", anchors.get("tibia"), 820, 1120, lk(TL.wt("cut", "shin"), TCAP), WHITE)
    C.label(ctx, "metal", anchors.get("cap"), 860, 700, lk(TCAP + 0.5, T["plastic"][0]), METAL)
    C.label(ctx, "metal", anchors.get("tray"), 240, 1150, lk(TTRAY + 0.5, T["plastic"][0]), METAL)
    C.label(ctx, "plastic", anchors.get("insert"), 860, 1060, lk(TINS + 0.5, TGLIDE + 1.2), CYAN)
    # slams
    C.slam_word(ctx, "BONE ON BONE", t, TL.wt("worn", "grinds"), RED, 110, 600, hold=T["worn"][1] - TL.wt("worn", "grinds") + 0.6)
    if TIN0 - 0.2 <= t < T["cut"][0] + 0.2:
        a = p(t, T["title"][0], T["title"][0] + 0.3) * (1 - p(t, T["cut"][0] - 0.2, T["cut"][0] + 0.1))
        s = 1.4 - 0.4 * eo(p(t, T["title"][0], T["title"][0] + 0.35))
        ctx.save(); ctx.translate(W / 2, 520); ctx.scale(s, s); ctx.translate(-W / 2, -520)
        A.txt(ctx, "NEW KNEE", W / 2, 540, 150, WHITE, a)
        A.txt(ctx, "total knee replacement", W / 2, 620, 46, CYAN, a * 0.9, bold=False)
        ctx.restore()
    C.slam_word(ctx, "A FEW MM", t, TL.wt("cut", "few"), YEL, 130, 470, hold=TT0 - TL.wt("cut", "few") - 0.2, rot=0)
    C.slam_word(ctx, "METAL", t, TCAP, METAL, 160, 470, hold=TL.wt("metal", "cement,") - TCAP - 0.1, rot=0)
    C.slam_word(ctx, "BONE CEMENT", t, TL.wt("metal", "cement,"), WHITE, 110, 440, hold=TL.wt("metal", "growing") - TL.wt("metal", "cement,") - 0.1, rot=0)
    C.slam_word(ctx, "OR BONE GROWS IN", t, TL.wt("metal", "growing"), WHITE, 92, 440, hold=T["metal"][1] - TL.wt("metal", "growing") + 0.2, rot=0)
    C.slam_word(ctx, "PLASTIC", t, TINS, CYAN, 150, 440, hold=TGLIDE - TINS - 0.2, rot=0)
    C.slam_word(ctx, "GLIDES", t, TGLIDE, GREEN, 160, 440, hold=T["plastic"][1] - TGLIDE + 0.2, rot=0)
    C.slam_word(ctx, "DAY 1", t, TL.wt("walk", "walking,"), YEL, 170, 560, hold=T["walk"][1] - TL.wt("walk", "walking,") + 0.2, rot=0)
    C.slam_word(ctx, "MONTHS OF REHAB", t, TL.wt("rehab", "months"), YEL, 100, 560, hold=T["rehab"][1] - TL.wt("rehab", "months") + 0.2, rot=0)
    C.slam_word(ctx, "20+ YEARS", t, TL.wt("last", "twenty"), GREEN, 150, 560, hold=T["last"][1] - TL.wt("last", "twenty") + 0.2, rot=0)
    C.slam_word(ctx, "METAL + PLASTIC + REHAB", t, TL.wt("end", "metal,"), GREEN, 78, 560, hold=TOTAL - TL.wt("end", "metal,") - 0.6, rot=0)
    C.captions(ctx, t, TL)
    if t > T["end"][0]:
        A.txt(ctx, "General information, not personal medical advice", W / 2, 1440, 26, GREY,
              0.8 * p(t, T["end"][0], T["end"][0] + 0.4) * (1 - p(t, TOTAL - 0.4, TOTAL)), bold=False, shadow=False)
    if flash > 0:
        A.rgba(ctx, WHITE, flash * 0.5); ctx.paint()
    return surf


BLUR = [(THIT - 0.05, THIT + 0.3), (TIN0, TIN1), (TOUT0, TOUT1)]
if __name__ == "__main__":
    C.run(render, TOTAL, BLUR, sys.argv)
