import sys, math, random
sys.path.insert(0, "/home/claude/v2"); sys.path.insert(0, "/home/claude/short")
import cairo
import common as C
from common import W, H, kf, ss, mix, p, eo, eio, back, clamp, YEL, RED, WHITE, GREY, CYAN, GREEN, d2r
import anim2 as A
import knee_flex as L
from anim import rrect

D = "/home/claude/v2/myth_run"
TL = C.Timeline(D + "/timeline.json"); T = TL.T; TOTAL = TL.total
THIT = T["hit"][0]
TIN0, TIN1 = TL.wt("check", "let's") - 0.1, T["check"][1] + 0.3
TOUT0, TOUT1 = T["end"][0] - 0.1, T["end"][0] + 1.7
TDATA0, TDATA1 = T["data"][0] + 0.2, T["risk"][0] + 0.2
TVER = T["verdict"][0]
M0 = 0.27
REF = (520, 900)
GROUND = 1440.0
KW = (540.0, 1120.0)       # world point where the knee model sits


def phase(t):
    return t * 2 * math.pi * 1.45


def leg_pose(hip, ph):
    th = 26 * math.sin(ph) * d2r
    kn = (14 + 85 * max(0.0, math.cos(ph + 0.35)) ** 1.5) * d2r
    K_ = (hip[0] + 300 * math.sin(th), hip[1] + 300 * math.cos(th))
    sa = th - kn
    A_ = (K_[0] + 290 * math.sin(sa), K_[1] + 290 * math.cos(sa))
    return K_, A_, sa - 12 * math.cos(ph) * d2r


def pose(t):
    ph = phase(t)
    lean = 9 * d2r
    hip = (500.0, 800.0 + 14 * abs(math.cos(ph)))
    legs = [leg_pose(hip, ph), leg_pose(hip, ph + math.pi)]
    dy = GROUND - 30 - max(l[1][1] for l in legs)
    hip = (hip[0], hip[1] + dy)
    legs = [((k[0], k[1] + dy), (a[0], a[1] + dy), fa) for k, a, fa in legs]
    sh = (hip[0] + 330 * math.sin(lean), hip[1] - 330 * math.cos(lean))
    head = (sh[0] + 100 * math.sin(lean + 0.1), sh[1] - 100 * math.cos(lean + 0.1))
    arms = []
    for s in (1, -1):
        aa = -30 * s * math.sin(ph) * d2r
        E = (sh[0] + 150 * math.sin(aa), sh[1] + 150 * math.cos(aa))
        ea = aa + 86 * d2r
        arms.append((E, (E[0] + 140 * math.sin(ea), E[1] + 140 * math.cos(ea))))
    return dict(hip=hip, sh=sh, head=head, legs=legs, arms=arms)


def foot(ctx, A_, fa):
    ctx.save(); ctx.translate(*A_); ctx.rotate(-fa)
    ctx.move_to(-44, -14); ctx.line_to(150, 18); ctx.curve_to(170, 24, 170, 44, 150, 46); ctx.line_to(-46, 46)
    ctx.curve_to(-60, 30, -56, -8, -44, -14); ctx.close_path(); ctx.restore()


def figure(ctx, P, which):
    K_, A_, fa = P["legs"][which]
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


def knee_theta(t):
    """running knee flexion of the near leg (deg)"""
    return 14 + 85 * max(0.0, math.cos(phase(t) + 0.35)) ** 1.5


def stance(t):
    """1 when the near foot is loaded (stance phase)"""
    return clamp(-math.cos(phase(t) + 0.35) * 2.5)


PARTS = [(random.Random(i).uniform(-1, 1), random.Random(i + 50).uniform(0, 1), random.Random(i + 99).uniform(0, 6.28)) for i in range(26)]


def draw_knee(ctx, t, st, anchors):
    th = st["theta"]
    L.knee_lateral(ctx, th)
    ang = (90 + th) * d2r
    cp = (L.R * math.cos(ang), L.R * math.sin(ang))
    anchors["joint"] = ctx.user_to_device(*cp)
    anchors["cart"] = ctx.user_to_device(L.R * math.cos(ang - 0.5), L.R * math.sin(ang - 0.5))
    cg = st.get("cart", 0)
    if cg > 0:
        for lw, al in ((40, 0.12), (22, 0.25), (8, 0.8)):
            L.femur_artic(ctx); A.rgba(ctx, CYAN, al * cg); ctx.set_line_width(lw); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
        sq = st.get("squeeze", 0)       # 1 = compressed -> fluid pushed out
        for u, r0, ph0 in PARTS:
            a = ang + u * 0.55
            rr = L.R + 10 + (20 + 120 * sq) * r0 + 8 * math.sin(t * 3 + ph0)
            x, y = rr * math.cos(a), rr * math.sin(a)
            g = cairo.RadialGradient(x, y, 1, x, y, 16)
            g.add_color_stop_rgba(0, 0.8, 0.95, 1, 0.9 * cg); g.add_color_stop_rgba(1, 0.3, 0.8, 1, 0)
            ctx.set_source(g); ctx.arc(x, y, 16, 0, 2 * math.pi); ctx.fill()
    ld = st.get("load", 0)
    if ld > 0:
        C.glow_blob(ctx, cp[0], cp[1], 180, st.get("lcol", YEL), ld)
    rk = st.get("risk", 0)
    if rk > 0:
        C.glow_blob(ctx, cp[0], cp[1], 220, RED, rk * (0.6 + 0.4 * math.sin(t * 6)))


def state(t):
    st = {"theta": knee_theta(t)}
    if T["load"][0] <= t < T["cart"][1] + 0.3:
        s = stance(t)
        st["load"] = s * p(t, T["load"][0], T["load"][0] + 0.5) * (1 - p(t, T["cart"][0], T["cart"][0] + 0.5) * 0.6)
    if T["cart"][0] <= t < TDATA0 + 0.5:
        st["cart"] = p(t, T["cart"][0], T["cart"][0] + 0.5)
        st["squeeze"] = stance(t) if t >= TL.wt("cart", "squeezed") else 0.5
        st["lcol"] = CYAN
    if T["risk"][0] <= t < TVER:
        st["risk"] = p(t, T["risk"][0] + 0.8, T["risk"][0] + 1.4)
    return st


def camera(t):
    fig_c = (520.0, 950.0)
    z_in = 1.15 / M0
    tgt = (KW[0], KW[1] - 120 * M0)
    if t < TIN0:
        return 1.0, fig_c
    if t < TIN1:
        k = eio(p(t, TIN0, TIN1)); return 1 + (z_in - 1) * k, mix(fig_c, tgt, k)
    if t < TOUT0:
        mv = [(TIN1, (0, -120), 1.0), (T["load"][0] + 0.3, (0, -260), 0.85), (T["cart"][0] + 0.3, (-60, 40), 1.5),
              (TDATA0, (-40, 0), 1.2), (T["risk"][0], (0, -120), 0.95), (TOUT0 - 0.3, (0, -120), 1.0)]
        off = kf(t, [(a, b) for a, b, _ in mv]); zm = kf(t, [(a, c) for a, _, c in mv])
        return z_in * zm, (KW[0] + off[0] * M0, KW[1] + off[1] * M0)
    if t < TOUT1:
        k = eio(p(t, TOUT0, TOUT1)); return z_in + (1 - z_in) * k, mix(tgt, fig_c, k)
    return 1.0, fig_c


def window(t):
    if t < TIN0 - 0.4: return 0
    if t < TIN1: return 140 * back(p(t, TIN0 - 0.4, TIN0)) + 1200 * ss(p(t, TIN0 + 0.3, TIN1))
    if t < TOUT0: return 4000
    if t < TOUT1: return 1340 - 1200 * ss(p(t, TOUT0, TOUT1 - 0.2))
    return 140 * (1 - ss(p(t, TOUT1, TOUT1 + 0.4)))


def claim_card(ctx, t, a, strike=0.0):
    if a <= 0: return
    y = 520
    A.font(ctx, 82)
    lines = ["RUNNING RUINS", "YOUR KNEES"]
    ctx.save()
    rrect(ctx, 90, y - 150, W - 180, 300, 34); A.rgba(ctx, (0.05, 0.07, 0.12), 0.82 * a); ctx.fill_preserve()
    A.rgba(ctx, WHITE, 0.25 * a); ctx.set_line_width(3); ctx.stroke()
    A.txt(ctx, "“", 150, y - 40, 150, CYAN, 0.8 * a, shadow=False)
    for i, s in enumerate(lines):
        k = p(t, 0.35 + i * 0.7, 0.6 + i * 0.7)
        A.txt(ctx, s, W / 2, y - 10 + i * 100, 82, WHITE, a * k)
    if strike > 0:
        for i in range(2):
            yy = y - 38 + i * 100
            ctx.move_to(170, yy); ctx.line_to(170 + (W - 340) * eo(clamp(strike * 2 - i * 0.5)), yy + 6)
            A.rgba(ctx, RED, a); ctx.set_line_width(12); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
    ctx.restore()


def series_tag(ctx, t):
    a = 1 - p(t, TOTAL - 0.4, TOTAL)
    rrect(ctx, W / 2 - 190, 250, 380, 64, 32); A.rgba(ctx, CYAN, 0.16 * a); ctx.fill_preserve()
    A.rgba(ctx, CYAN, 0.8 * a); ctx.set_line_width(3); ctx.stroke()
    A.txt(ctx, "MYTH  or  FACT?", W / 2, 296, 38, WHITE, a, shadow=False)


def bars(ctx, t):
    a = p(t, TDATA0, TDATA0 + 0.4) * (1 - p(t, TDATA1, TDATA1 + 0.4))
    if a <= 0: return
    ctx.rectangle(0, 0, W, H); A.rgba(ctx, (0.03, 0.04, 0.07), 0.72 * a); ctx.fill()
    base, scale = 1000, 36
    data = [("NON-RUNNERS", 10.2, (0.80, 0.84, 0.92), TL.wt("data", "people")),
            ("RECREATIONAL", 3.5, GREEN, TL.wt("data", "recreational")),
            ("ELITE", 13.3, RED, TL.wt("elite", "years"))]
    A.txt(ctx, "knee & hip arthritis", W / 2, 410, 52, WHITE, a)
    for i, (lab, v, col, t0) in enumerate(data):
        k = eo(p(t, t0, t0 + 0.8))
        if k <= 0: continue
        x = 160 + i * 290; w = 200
        h = v * scale * k
        g = cairo.LinearGradient(0, base - h, 0, base)
        g.add_color_stop_rgba(0, col[0], col[1], col[2], 0.95 * a); g.add_color_stop_rgba(1, col[0], col[1], col[2], 0.35 * a)
        rrect(ctx, x, base - h, w, h + 1, 14); ctx.set_source(g); ctx.fill()
        for lw, al in ((22, 0.10), (10, 0.2)):
            rrect(ctx, x, base - h, w, h + 1, 14); A.rgba(ctx, col, al * a * k); ctx.set_line_width(lw); ctx.stroke()
        A.txt(ctx, f"{v * k:.1f}%", x + w / 2, base - h - 30, 64, col, a * k)
        A.txt(ctx, lab, x + w / 2, base + 56, 34, WHITE, a * k)
    A.txt(ctx, "Alentorn-Geli et al., 2017 (meta-analysis)", W / 2, base + 108, 26, GREY, 0.85 * a, bold=False, shadow=False)


EV = [(THIT, 0.7, True), (TVER, 0.9, True)]


def render(t):
    st = state(t)
    z, foc = camera(t)
    sx, sy, zb, flash = C.shake(t, EV)
    fig_a = (1 - ss(p(t, TIN0 + 0.8, TIN1 - 0.1))) if t < TOUT0 else ss(p(t, TOUT0 + 0.5, TOUT1))
    redk = 0.45 * st.get("risk", 0)
    green = p(t, T["end"][0] + 0.2, T["end"][0] + 0.9) * (1 - p(t, TOTAL - 1, TOTAL))
    tint = mix(mix((0.09, 0.12, 0.20), (0.04, 0.19, 0.15), green), (0.20, 0.05, 0.06), clamp(redk))
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
        for i in range(7):
            x = 900 - ((t * 900 + i * 260) % 1500); y = GROUND + 6 + (i % 3) * 14
            ctx.move_to(x, y); ctx.line_to(x + 120, y); A.rgba(ctx, CYAN, 0.35 * fig_a); ctx.set_line_width(3); ctx.stroke()
    ctx.restore()
    P = pose(t)
    sil = C.silhouette_layer(world, lambda c: figure(c, P, 0), fig_a, lambda c: figure(c, P, 1))
    if sil:
        ctx.set_source_surface(sil[0], 0, 0); ctx.paint()
    rw = window(t); anchors = {}
    if rw > 0:
        wc = P["legs"][0][0] if t < TIN0 or t > TOUT1 else KW
        if TIN0 <= t < TIN1:
            wc = mix(P["legs"][0][0], KW, ss(p(t, TIN0, TIN0 + 0.5)))
        elif TOUT0 <= t <= TOUT1:
            wc = mix(KW, P["legs"][0][0], ss(p(t, TOUT1 - 0.6, TOUT1)))
        ctx.save(); ctx.set_matrix(world)
        ctx.arc(wc[0], wc[1], rw, 0, 2 * math.pi)
        if rw < 2000:
            ctx.save(); ctx.clip_preserve(); ctx.set_source_rgb(0.03, 0.04, 0.07); ctx.paint(); ctx.restore()
        ctx.clip()
        ctx.push_group()
        ctx.translate(*wc); ctx.scale(M0, M0)
        draw_knee(ctx, t, st, anchors)
        model = ctx.pop_group()
        ctx.set_source(model); ctx.paint()
        C.light_sweep(ctx, t, model)
        ctx.restore()
        if rw < 2000:
            C.window_rim(ctx, world, wc, rw, z)
    C.bokeh_front(ctx, t, z, foc, REF)
    A.vignette(ctx, red=clamp(redk) * 0.6 + (0.4 * math.exp(-(t - THIT) * 3) if THIT < t < TIN0 else 0))
    C.fades(ctx)
    bars(ctx, t)
    series_tag(ctx, t)
    # claim card: intro + verdict
    ca = (1 - p(t, TIN0 - 0.2, TIN0 + 0.2)) + p(t, TVER - 0.2, TVER + 0.1) * (1 - p(t, TOUT0 + 0.2, TOUT0 + 0.5))
    claim_card(ctx, t if t < TIN0 else 2.0, clamp(ca), strike=p(t, TL.wt("verdict", "myth."), TL.wt("verdict", "myth.") + 0.4))
    if THIT <= t < TIN0 + 0.2:
        C.slam_word(ctx, "?", t, THIT, YEL, 260, 900, hold=TIN0 - THIT - 0.2, rot=0.08)
    C.label(ctx, "cartilage", anchors.get("cart"), 230, 760,
            p(t, TL.wt("cart", "cartilage"), TL.wt("cart", "cartilage") + 0.4) * (1 - p(t, TDATA0 - 0.3, TDATA0)), CYAN)
    C.slam_word(ctx, "SEVERAL × BODY WEIGHT", t, TL.wt("load", "several"), YEL, 84, 470, hold=T["load"][1] - TL.wt("load", "several") + 0.2, rot=0)
    C.slam_word(ctx, "NO BLOOD SUPPLY", t, TL.wt("cart", "no"), WHITE, 100, 470, hold=TL.wt("cart", "it") - TL.wt("cart", "no") - 0.1, rot=0)
    C.slam_word(ctx, "LIKE A SPONGE", t, TL.wt("cart", "squeezed"), CYAN, 110, 470, hold=T["cart"][1] - TL.wt("cart", "squeezed") + 0.2, rot=0)
    C.item_list(ctx, t, [("OLD KNEE INJURY", TL.wt("risk", "old")), ("EXTRA WEIGHT", TL.wt("risk", "extra")),
                         ("TOO MUCH, TOO FAST", TL.wt("risk", "ramping"))], TVER - 0.2, size=66)
    C.stamp(ctx, t, TL.wt("verdict", "myth."), "MYTH", TOUT0 + 0.4, y=830, col=RED)
    C.slam_word(ctx, "BUILD UP GRADUALLY", t, T["end"][0], GREEN, 86, 470, hold=TOTAL - T["end"][0] - 0.7, rot=0)
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
