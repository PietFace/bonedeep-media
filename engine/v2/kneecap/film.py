import sys, math
sys.path.insert(0, "/home/claude/v2"); sys.path.insert(0, "/home/claude/short")
import cairo
import common as C
from common import W, H, kf, ss, mix, p, eo, eio, back, clamp, YEL, RED, WHITE, GREY, CYAN, GREEN, d2r
import anim2 as A
import knee_flex as L
import knee_still as K
from anim import rrect

D = "/home/claude/v2/kneecap"
TL = C.Timeline(D + "/timeline.json"); T = TL.T; TOTAL = TL.total
TIN0, TIN1 = TL.wt("shield", "let's") - 0.1, T["shield"][1] + 0.3
TOUT0, TOUT1 = T["end"][0] - 0.1, T["end"][0] + 1.5
TREM = TL.wt("without", "without")
TBACK = T["baby"][0] - 0.2
M0 = 0.30
REF = (520, 900)
GROUND = 1440.0
ANK = (470.0, 1395.0)
R, Y0 = L.R, L.Y0


def squat(t):
    return 0.5 - 0.5 * math.cos(t * 2 * math.pi * 0.45)


def pose(q):
    s = 28 * q * d2r; f = 85 * q * d2r; lean = (6 + 38 * q) * d2r
    K_ = (ANK[0] + 290 * math.sin(s), ANK[1] - 290 * math.cos(s))
    H_ = (K_[0] - 300 * math.sin(f), K_[1] - 300 * math.cos(f))
    S_ = (H_[0] + 330 * math.sin(lean), H_[1] - 330 * math.cos(lean))
    head = (S_[0] + 100 * math.sin(lean + 0.1), S_[1] - 100 * math.cos(lean + 0.1))
    aa = (70 * q) * d2r
    E = (S_[0] + 150 * math.sin(aa), S_[1] + 150 * math.cos(aa))
    Hd = (E[0] + 140 * math.sin(aa + 0.2), E[1] + 140 * math.cos(aa + 0.2))
    return dict(A=ANK, K=K_, H=H_, S=S_, head=head, E=E, Hd=Hd, thigh=-f, flex=(s + f) / d2r)


def figure(ctx, P, back_=False):
    o = (-26, -6) if back_ else (0, 0)
    sh = lambda q: (q[0] + o[0], q[1] + o[1])
    C.limb(ctx, sh(P["H"]), sh(P["K"]), 106, 80); ctx.fill()
    C.limb(ctx, sh(P["K"]), sh(P["A"]), 78, 44); ctx.fill()
    A_ = sh(P["A"])
    ctx.move_to(A_[0] - 44, A_[1] - 10); ctx.line_to(A_[0] + 150, A_[1] + 22); ctx.line_to(A_[0] + 150, A_[1] + 46)
    ctx.line_to(A_[0] - 48, A_[1] + 46); ctx.close_path(); ctx.fill()
    if back_:
        return
    C.limb(ctx, P["H"], P["S"], 150, 160); ctx.fill()
    C.limb(ctx, P["S"], P["E"], 56, 46); ctx.fill(); C.limb(ctx, P["E"], P["Hd"], 44, 34); ctx.fill()
    C.limb(ctx, P["S"], mix(P["S"], P["head"], 0.5), 60, 52); ctx.fill()
    ctx.arc(P["head"][0], P["head"][1], 64, 0, 2 * math.pi)


def patella_geo(th):
    tub = L.rot((128, Y0 + 100), th * d2r)
    best = None
    for i in range(120):
        s_ = 0.02 + 0.96 * i / 119
        pt, (tx, ty) = L.track_at(s_)
        nx, ny = ty, -tx
        c = (pt[0] + nx * L.PAT_OFF, pt[1] + ny * L.PAT_OFF)
        distal = (c[0] + tx * L.PAT_HALF, c[1] + ty * L.PAT_HALF)
        err = abs(math.dist(distal, tub) - L.LPT)
        if best is None or err < best[0]:
            best = (err, c, (tx, ty), distal, pt)
    _, c, (tx, ty), distal, pt = best
    prox = (c[0] - tx * L.PAT_HALF, c[1] - ty * L.PAT_HALF)
    return c, (tx, ty), prox, distal, tub, pt


def perp_foot(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    u = -(a[0] * dx + a[1] * dy) / (dx * dx + dy * dy)
    return (a[0] + u * dx, a[1] + u * dy)


def cartilage_patella(c):
    L.patella_path(c)


def draw_knee(ctx, t, st, anchors):
    sp = L.sprites()
    th = st["theta"]
    rem = st.get("removed", 0.0)
    L.band(ctx, (-152, -140), L.rot((-120, Y0 + 70), th * d2r), 30, 24, seed=3, fib=8)
    sp["femur"].paint(ctx)
    ctx.save(); ctx.rotate(th * d2r); sp["tibia"].paint(ctx); L.draw_menisci(ctx, -7 * clamp(th / 100), -16 * clamp(th / 100), 0); ctx.restore()
    c, (tx, ty), prox, distal, tub, pt = patella_geo(th)
    # without patella the tendon hugs the femur
    c2 = mix(c, pt, rem)
    prox2 = mix(prox, (pt[0] - tx * 40, pt[1] - ty * 40), rem); distal2 = mix(distal, (pt[0] + tx * 40, pt[1] + ty * 40), rem)
    mg = st.get("muscle", 0.0)
    if mg > 0:
        for w, a in ((150, 0.08), (90, 0.16)):
            ctx.move_to(170, -900); ctx.curve_to(220, -650, 200, -480, prox2[0], prox2[1])
            A.rgba(ctx, st.get("mcol", RED), a * mg * (0.7 + 0.3 * math.sin(t * 9))); ctx.set_line_width(w)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
    tg = st.get("tendon", 0.0)
    if tg > 0:
        ctx.move_to(128, -380); ctx.line_to(*prox2); ctx.line_to(*c2); ctx.line_to(*distal2); ctx.line_to(*tub)
        for w, a in ((110, 0.10), (70, 0.18)):
            ctx.move_to(128, -380); ctx.line_to(*prox2); ctx.line_to(*c2); ctx.line_to(*distal2); ctx.line_to(*tub)
            A.rgba(ctx, CYAN, a * tg); ctx.set_line_width(w); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke()
    L.band(ctx, (128, -380), prox2, 60, 52, seed=5, fib=12)
    L.band(ctx, distal2, tub, 40, 34, seed=7, fib=10)
    if rem > 0:
        L.band(ctx, prox2, distal2, 50, 44, seed=9, fib=10)
    pa = 1 - rem
    if pa > 0:
        ctx.save(); ctx.translate(*c); ctx.rotate(math.atan2(ty, tx))
        bs = st.get("baby", 0.0)   # 1 = cartilage baby kneecap
        sc = L.PAT_SC * (1 - 0.35 * bs)
        ctx.scale(sc, sc)
        if bs > 0:
            ctx.push_group(); sp["patella"].paint(ctx); pg = ctx.pop_group()
            ctx.set_source(pg); ctx.paint_with_alpha(pa * (1 - bs))
            L.patella_path(ctx)
            g = cairo.LinearGradient(0, -40, 0, 31)
            g.add_color_stop_rgba(0, 0.90, 0.95, 1.0, pa * bs); g.add_color_stop_rgba(1, 0.62, 0.72, 0.86, pa * bs)
            ctx.set_source(g); ctx.fill()
        else:
            sp["patella"].paint(ctx, pa)
        cg = st.get("thick", 0.0)
        if cg > 0:
            for w, a in ((40, 0.15), (24, 0.3), (10, 0.9)):
                ctx.move_to(-60, 31); ctx.curve_to(-30, 34, 30, 34, 62, 22)
                A.rgba(ctx, CYAN, a * cg); ctx.set_line_width(w / sc * 1.6); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
        ctx.restore()
    # lever arm
    lv = st.get("lever", 0.0)
    if lv > 0:
        foot = perp_foot(distal2, tub)
        foot0 = perp_foot(distal, tub)
        for w, a in ((26, 0.15), (9, 1.0)):
            ctx.move_to(0, 0); ctx.line_to(*foot); A.rgba(ctx, YEL, a * lv); ctx.set_line_width(w); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
        if rem > 0:   # ghost of the original lever
            ctx.set_dash([14, 10]); ctx.move_to(0, 0); ctx.line_to(*foot0); A.rgba(ctx, YEL, 0.5 * lv * rem); ctx.set_line_width(5); ctx.stroke(); ctx.set_dash([])
        ctx.arc(0, 0, 16, 0, 2 * math.pi); A.rgba(ctx, WHITE, lv); ctx.fill()
        anchors["lever"] = ctx.user_to_device(*mix((0, 0), foot, 0.5))
    anchors["patella"] = ctx.user_to_device(*c)
    anchors["pcart"] = ctx.user_to_device(*mix(c, pt, 0.6))
    anchors["tendon"] = ctx.user_to_device(*mix(distal, tub, 0.5))


def state(t):
    st = {}
    inside = TIN1 - 0.5 <= t < TOUT0 + 0.3
    if not inside:
        st["theta"] = pose(squat(t))["flex"]
    else:
        st["theta"] = 45 - 45 * math.cos((t - TIN1) * 1.7)
        if T["baby"][0] <= t < T["end"][0]:
            st["theta"] = kf(t, [(T["baby"][0], st["theta"]), (T["baby"][0] + 0.8, 20)]) if t < T["baby"][0] + 0.8 else 20
    st["tendon"] = p(t, TL.wt("sesamoid", "tendon."), TL.wt("sesamoid", "tendon.") + 0.4) * (1 - p(t, T["lever"][0] + 0.8, T["lever"][0] + 1.3))
    st["lever"] = p(t, TL.wt("lever", "forward,"), TL.wt("lever", "forward,") + 0.4) * (1 - p(t, TBACK, TBACK + 0.3))
    st["removed"] = p(t, TREM, TREM + 0.8) * (1 - p(t, TBACK - 0.5, TBACK))
    st["muscle"] = max(p(t, TL.wt("lever", "thigh"), TL.wt("lever", "thigh") + 0.4) * (1 - p(t, TREM, TREM + 0.3)),
                       p(t, TL.wt("without", "force."), TL.wt("without", "force.") + 0.3) * (1 - p(t, TBACK - 0.5, TBACK)))
    st["mcol"] = GREEN if t < TREM else RED
    st["baby"] = p(t, TL.wt("baby", "babies"), TL.wt("baby", "babies") + 0.5) * (1 - p(t, TL.wt("baby", "turns"), TL.wt("baby", "turns") + 1.6))
    st["thick"] = p(t, TL.wt("thick", "thickest"), TL.wt("thick", "thickest") + 0.4) * (1 - p(t, TOUT0, TOUT0 + 0.4))
    return st


PS = pose(squat(TIN0))
KW = PS["K"]


def camera(t):
    fig_c = (520.0, 950.0)
    z_in = 1.0 / M0
    tgt = (KW[0] + 60 * M0, KW[1] + 20 * M0)
    if t < TIN0:
        return 1.0, fig_c
    if t < TIN1:
        k = eio(p(t, TIN0, TIN1)); return 1 + (z_in - 1) * k, mix(fig_c, tgt, k)
    if t < TOUT0:
        mv = [(TIN1, (110, 20), 0.95), (T["sesamoid"][0] + 0.3, (160, -20), 0.9), (T["lever"][0] + 0.5, (120, 60), 0.85),
              (T["baby"][0] + 0.3, (230, 40), 1.4), (T["thick"][0] + 0.3, (240, 30), 1.6), (TOUT0 - 0.2, (60, 20), 1.0)]
        off = kf(t, [(a, b) for a, b, _ in mv]); zm = kf(t, [(a, c) for a, _, c in mv])
        return z_in * zm, (KW[0] + off[0] * M0, KW[1] + off[1] * M0)
    if t < TOUT1:
        k = eio(p(t, TOUT0, TOUT1)); return z_in + (1 - z_in) * k, mix(tgt, fig_c, k)
    return 1.0, fig_c


def window(t):
    if t < 0.5: return 0
    if t < TIN0: return 130 * back(p(t, 0.5, 0.8))
    if t < TIN1: return 130 + 1200 * ss(p(t, TIN0 + 0.3, TIN1))
    if t < TOUT0: return 4000
    if t < TOUT1: return 1330 - 1200 * ss(p(t, TOUT0, TOUT1 - 0.2))
    return 130 * (1 - ss(p(t, TOTAL - 0.5, TOTAL - 0.1)))


def series_tag(ctx, t):
    a = p(t, 0.1, 0.5) * (1 - p(t, TOTAL - 0.4, TOTAL))
    rrect(ctx, W / 2 - 160, 250, 320, 64, 32); A.rgba(ctx, YEL, 0.14 * a); ctx.fill_preserve()
    A.rgba(ctx, YEL, 0.8 * a); ctx.set_line_width(3); ctx.stroke()
    A.txt(ctx, "BODY FACTS", W / 2, 296, 38, WHITE, a, shadow=False)


EV = [(TREM + 0.4, 0.5, False), (TL.wt("end", "big"), 0.5, False)]


def render(t):
    st = state(t)
    z, foc = camera(t)
    sx, sy, zb, flash = C.shake(t, EV)
    fig_a = (1 - ss(p(t, TIN0 + 0.8, TIN1 - 0.1))) if t < TOUT0 else ss(p(t, TOUT0 + 0.5, TOUT1))
    redk = 0.45 * st["removed"]
    green = p(t, T["end"][0], T["end"][0] + 0.6) * (1 - p(t, TOTAL - 1, TOTAL)) + 0.6 * st["lever"] * (1 - st["removed"]) * (1 if t < TREM else 0)
    tint = mix(mix((0.09, 0.12, 0.20), (0.04, 0.19, 0.15), clamp(green)), (0.20, 0.05, 0.06), clamp(redk))
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf); ctx.set_antialias(cairo.ANTIALIAS_GOOD)
    C.background(ctx, t, z, foc, tint, REF)
    ctx.save(); ctx.translate(W / 2 + sx, 950 + sy); ctx.scale(z * (1 + zb), z * (1 + zb)); ctx.translate(-foc[0], -foc[1])
    world = ctx.get_matrix()
    if fig_a > 0:
        g = cairo.RadialGradient(520, GROUND, 10, 520, GROUND, 420)
        g.add_color_stop_rgba(0, YEL[0], YEL[1], YEL[2], 0.14 * fig_a); g.add_color_stop_rgba(1, YEL[0], YEL[1], YEL[2], 0)
        ctx.save(); ctx.translate(0, GROUND); ctx.scale(1, 0.1); ctx.translate(0, -GROUND); ctx.set_source(g)
        ctx.arc(520, GROUND, 420, 0, 2 * math.pi); ctx.fill(); ctx.restore()
    ctx.restore()
    P = pose(squat(t)) if (t < TIN0 or t > TOUT1 - 0.3) else PS
    sil = C.silhouette_layer(world, lambda c: figure(c, P), fig_a, lambda c: figure(c, P, True))
    if sil:
        ctx.set_source_surface(sil[0], 0, 0); ctx.paint()
    rw = window(t); anchors = {}
    if rw > 0:
        wc = P["K"]
        ctx.save(); ctx.set_matrix(world)
        ctx.arc(wc[0] + 40 * M0, wc[1], rw, 0, 2 * math.pi)
        if rw < 2000:
            ctx.save(); ctx.clip_preserve(); ctx.set_source_rgb(0.03, 0.04, 0.07); ctx.paint(); ctx.restore()
        ctx.clip()
        ctx.push_group()
        ctx.translate(*wc); ctx.rotate(P["thigh"] if (t < TIN0 or t > TOUT1 - 0.3) else PS["thigh"] * (1 - ss(p(t, TIN0, TIN1))) if t < TOUT0 else PS["thigh"] * ss(p(t, TOUT0, TOUT1)))
        ctx.scale(M0, M0)
        draw_knee(ctx, t, st, anchors)
        model = ctx.pop_group()
        ctx.set_source(model); ctx.paint()
        C.light_sweep(ctx, t, model)
        ctx.restore()
        if rw < 2000:
            C.window_rim(ctx, world, (wc[0] + 40 * M0, wc[1]), rw, z)
    C.bokeh_front(ctx, t, z, foc, REF)
    A.vignette(ctx, red=clamp(redk) * 0.6)
    C.fades(ctx)
    series_tag(ctx, t)
    lk = lambda a_, b_: p(t, a_, a_ + 0.4) * (1 - p(t, b_, b_ + 0.3))
    C.label(ctx, "kneecap", anchors.get("patella"), 880, 640, lk(T["sesamoid"][0] + 0.2, T["lever"][0] + 0.5), WHITE)
    C.label(ctx, "tendon", anchors.get("tendon"), 880, 1100, lk(TL.wt("sesamoid", "tendon."), T["lever"][0] + 0.5), CYAN)
    C.label(ctx, "leverage", anchors.get("lever"), 230, 1080, lk(TL.wt("lever", "leverage."), TREM), YEL)
    if t < TIN0 + 0.3:
        a = p(t, 0.3, 0.6) * (1 - p(t, TIN0, TIN0 + 0.3))
        s = 1.3 - 0.3 * eo(p(t, 0.3, 0.7))
        ctx.save(); ctx.translate(W / 2, 520); ctx.scale(s, s); ctx.translate(-W / 2, -520)
        A.txt(ctx, "WHY DO YOU HAVE", W / 2, 470, 86, WHITE, a)
        A.txt(ctx, "A KNEECAP?", W / 2, 580, 120, YEL, a)
        ctx.restore()
    C.slam_word(ctx, "BONE IN A TENDON", t, TL.wt("sesamoid", "bone"), CYAN, 96, 440, hold=T["sesamoid"][1] - TL.wt("sesamoid", "bone") + 0.2, rot=0)
    C.slam_word(ctx, "MORE LEVERAGE", t, TL.wt("lever", "leverage."), GREEN, 116, 440, hold=T["lever"][1] - TL.wt("lever", "leverage.") + 0.2, rot=0)
    C.slam_word(ctx, "NO KNEECAP?", t, TREM, RED, 130, 440, hold=TL.wt("without", "much") - TREM - 0.1, rot=0)
    C.slam_word(ctx, "MUCH MORE FORCE", t, TL.wt("without", "much"), RED, 100, 440, hold=T["without"][1] - TL.wt("without", "much") + 0.2, rot=0)
    # age counter
    if T["baby"][0] <= t < T["thick"][0] + 0.2:
        ta, tb = TL.wt("baby", "turns"), TL.wt("baby", "turns") + 1.6
        age = 0 if t < ta else min(6, int(6 * p(t, ta, tb)) + 0)
        a = p(t, T["baby"][0], T["baby"][0] + 0.3) * (1 - p(t, T["thick"][0] - 0.2, T["thick"][0] + 0.1))
        A.txt(ctx, "AGE", W / 2, 400, 50, WHITE, a)
        A.txt(ctx, f"{age}", W / 2, 540, 150, YEL if age < 3 else GREEN, a)
        A.txt(ctx, "cartilage" if age < 3 else "bone", W / 2, 610, 46, CYAN if age < 3 else K.BONE_L, a, bold=False)
    C.slam_word(ctx, "THICKEST CARTILAGE", t, TL.wt("thick", "thickest"), CYAN, 92, 440, hold=T["thick"][1] - TL.wt("thick", "thickest") + 0.3, rot=0)
    C.slam_word(ctx, "SMALL BONE.", t, T["end"][0], WHITE, 120, 470, hold=TOTAL - T["end"][0] - 0.6, rot=0)
    C.slam_word(ctx, "BIG JOB.", t, TL.wt("end", "big"), GREEN, 150, 600, hold=TOTAL - TL.wt("end", "big") - 0.6, rot=0)
    C.captions(ctx, t, TL)
    if flash > 0:
        A.rgba(ctx, WHITE, flash * 0.5); ctx.paint()
    return surf


BLUR = [(TIN0, TIN1), (TOUT0, TOUT1)]
if __name__ == "__main__":
    C.run(render, TOTAL, BLUR, sys.argv)
