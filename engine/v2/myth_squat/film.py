import sys, math, importlib.util
sys.path.insert(0, "/home/claude/v2"); sys.path.insert(0, "/home/claude/short")
import cairo
import common as C
from common import W, H, kf, ss, mix, p, eo, eio, back, clamp, YEL, RED, WHITE, GREY, CYAN, GREEN, d2r
import anim2 as A
import knee_flex as L
import knee_still as K
from anim import rrect

_spec = importlib.util.spec_from_file_location("kcfilm", "/home/claude/v2/kneecap/film.py")
KC = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(KC)

D = "/home/claude/v2/myth_squat"
TL = C.Timeline(D + "/timeline.json"); T = TL.T; TOTAL = TL.total
THIT = T["hit"][0]
TIN0, TIN1 = TL.wt("check", "let's") - 0.1, T["check"][1] + 0.3
TOUT0, TOUT1 = T["end"][0] - 0.1, T["end"][0] + 1.7
TVER = T["verdict"][0]
TREV0, TREV1 = T["review"][0], T["risk"][0] + 0.1
M0 = 0.30
REF = (520, 900)
GROUND = 1440.0
ANK = (470.0, 1395.0)
R, Y0 = L.R, L.Y0


def squat(t):
    return 0.5 - 0.5 * math.cos(t * 2 * math.pi * 0.42)


def pose(q):
    s = 36 * q * d2r; f = 108 * q * d2r; lean = (6 + 40 * q) * d2r
    K_ = (ANK[0] + 290 * math.sin(s), ANK[1] - 290 * math.cos(s))
    H_ = (K_[0] - 300 * math.sin(f), K_[1] - 300 * math.cos(f))
    S_ = (H_[0] + 330 * math.sin(lean), H_[1] - 330 * math.cos(lean))
    head = (S_[0] + 100 * math.sin(lean + 0.1), S_[1] - 100 * math.cos(lean + 0.1))
    aa = (80 * q + 10) * d2r
    E = (S_[0] + 150 * math.sin(aa), S_[1] + 150 * math.cos(aa))
    Hd = (E[0] + 140 * math.sin(aa + 0.1), E[1] + 140 * math.cos(aa + 0.1))
    return dict(A=ANK, K=K_, H=H_, S=S_, head=head, E=E, Hd=Hd, thigh=-f, flex=(s + f) / d2r)


figure = KC.figure


def draw_knee(ctx, t, st, anchors):
    sp = L.sprites()
    th = min(st["theta"], 125)
    L.band(ctx, (-152, -140), L.rot((-120, Y0 + 70), th * d2r), 30, 24, seed=3, fib=8)
    sp["femur"].paint(ctx)
    ctx.save(); ctx.rotate(th * d2r); sp["tibia"].paint(ctx)
    L.draw_menisci(ctx, -7 * clamp(th / 100), -16 * clamp(th / 100), 0); ctx.restore()
    cg = st.get("calf", 0.0)
    if cg > 0:
        a_ = (-250, -160); b_ = L.rot((-250, Y0 + 230), th * d2r)
        m = mix(a_, b_, 0.5)
        C.glow_blob(ctx, m[0], m[1], 260, GREEN, cg * (0.7 + 0.3 * math.sin(t * 5)))
        anchors["calf"] = ctx.user_to_device(*m)
    c, (tx, ty), prox, distal, tub, pt = KC.patella_geo(th)
    wg = st.get("wrap", 0.0)
    if wg > 0:   # quadriceps tendon pressing on the femur (tendofemoral support)
        for w, a in ((90, 0.12), (50, 0.25)):
            ctx.move_to(128, -380); ctx.line_to(*prox); A.rgba(ctx, GREEN, a * wg); ctx.set_line_width(w)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
        s0 = 0.0; best = None
        for i in range(80):   # contact strip of the tendon on the femur
            q, _ = L.track_at(i / 79)
            d = math.dist(q, prox)
            if best is None or d < best[0]: best = (d, i / 79)
        s1 = best[1]
        ctx.move_to(*L.track_at(max(0.0, s1 - 0.25))[0])
        for i in range(20):
            ctx.line_to(*L.track_at(max(0.0, s1 - 0.25) + 0.25 * i / 19)[0])
        A.rgba(ctx, GREEN, 0.9 * wg); ctx.set_line_width(14); ctx.stroke()
        anchors["wrap"] = ctx.user_to_device(*mix((128, -380), prox, 0.6))
    L.band(ctx, (128, -380), prox, 60, 52, seed=5, fib=12)
    L.band(ctx, distal, tub, 40, 34, seed=7, fib=10)
    ctx.save(); ctx.translate(*c); ctx.rotate(math.atan2(ty, tx)); ctx.scale(L.PAT_SC, L.PAT_SC)
    sp["patella"].paint(ctx)
    ag = st.get("area", 0.0)
    if ag > 0:    # contact patch grows with flexion
        span = 0.25 + 0.75 * clamp(th / 110)
        x0, x1 = -60 * span, 62 * span
        for w, a in ((44, 0.15), (26, 0.3), (12, 0.95)):
            ctx.move_to(x0, 30); ctx.curve_to(x0 * 0.5, 34, x1 * 0.5, 34, x1, 26)
            A.rgba(ctx, CYAN, a * ag); ctx.set_line_width(w / L.PAT_SC * 1.5); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
    ctx.restore()
    anchors["patella"] = ctx.user_to_device(*c)
    pr = st.get("press", 0.0)
    if pr > 0:
        C.glow_blob(ctx, pt[0], pt[1], 140, RED, pr * (0.6 + 0.4 * math.sin(t * 8)))


def state(t):
    st = {}
    inside = TIN1 - 0.5 <= t < TOUT0 + 0.3
    st["theta"] = pose(squat(t))["flex"] if not inside else 0
    if inside:
        if t < T["calf"][0]:
            st["theta"] = 60 - 55 * math.cos((t - TIN1) * 1.6)
        elif t < TREV0:
            st["theta"] = kf(t, [(T["calf"][0], 60 - 55 * math.cos((T["calf"][0] - TIN1) * 1.6)), (T["calf"][0] + 1.2, 125)])
        else:
            st["theta"] = kf(t, [(TREV0, 125), (TREV0 + 1.0, 60)]) if t < T["risk"][0] else 60 - 50 * math.cos((t - T["risk"][0]) * 2.2)
    st["area"] = p(t, TL.wt("area", "bigger"), TL.wt("area", "bigger") + 0.4) * (1 - p(t, T["calf"][1], T["calf"][1] + 0.4))
    st["wrap"] = p(t, TL.wt("wrap", "wraps"), TL.wt("wrap", "wraps") + 0.4) * (1 - p(t, T["calf"][1], T["calf"][1] + 0.4))
    st["calf"] = p(t, TL.wt("calf", "thigh"), TL.wt("calf", "thigh") + 0.5) * (1 - p(t, TREV0, TREV0 + 0.4))
    st["press"] = p(t, TL.wt("risk", "too"), TL.wt("risk", "too") + 0.4) * (1 - p(t, TVER, TVER + 0.3))
    return st


PS = pose(squat(TIN0))
KW = PS["K"]


def camera(t):
    fig_c = (520.0, 950.0)
    z_in = 1.0 / M0
    tgt = (KW[0] + 80 * M0, KW[1] + 20 * M0)
    if t < TIN0:
        return 1.0, fig_c
    if t < TIN1:
        k = eio(p(t, TIN0, TIN1)); return 1 + (z_in - 1) * k, mix(fig_c, tgt, k)
    if t < TOUT0:
        mv = [(TIN1, (80, 20), 0.95), (T["area"][0] + 0.3, (200, 40), 1.25), (T["wrap"][0] + 0.3, (160, -100), 1.0),
              (T["calf"][0] + 0.6, (-160, -160), 0.72), (TREV0, (-100, -60), 0.8), (T["risk"][0], (80, 40), 0.95), (TOUT0 - 0.2, (80, 20), 1.0)]
        off = kf(t, [(a, b) for a, b, _ in mv]); zm = kf(t, [(a, c) for a, _, c in mv])
        return z_in * zm, (KW[0] + off[0] * M0, KW[1] + off[1] * M0)
    if t < TOUT1:
        k = eio(p(t, TOUT0, TOUT1)); return z_in + (1 - z_in) * k, mix(tgt, fig_c, k)
    return 1.0, fig_c


def window(t):
    if t < TIN0 - 0.4: return 0
    if t < TIN1: return 135 * back(p(t, TIN0 - 0.4, TIN0)) + 1200 * ss(p(t, TIN0 + 0.3, TIN1))
    if t < TOUT0: return 4000
    if t < TOUT1: return 1335 - 1200 * ss(p(t, TOUT0, TOUT1 - 0.2))
    return 135 * (1 - ss(p(t, TOUT1, TOUT1 + 0.4)))


def claim_card(ctx, t, a, strike=0.0):
    if a <= 0: return
    y = 520
    lines = ["DEEP SQUATS ARE", "BAD FOR YOUR KNEES"]
    rrect(ctx, 70, y - 150, W - 140, 300, 34); A.rgba(ctx, (0.05, 0.07, 0.12), 0.82 * a); ctx.fill_preserve()
    A.rgba(ctx, WHITE, 0.25 * a); ctx.set_line_width(3); ctx.stroke()
    A.txt(ctx, "“", 130, y - 40, 150, CYAN, 0.8 * a, shadow=False)
    for i, s in enumerate(lines):
        k = p(t, 0.35 + i * 0.8, 0.6 + i * 0.8)
        A.txt(ctx, s, W / 2, y - 10 + i * 100, 74, WHITE, a * k)
    if strike > 0:
        for i in range(2):
            yy = y - 36 + i * 100
            ctx.move_to(130, yy); ctx.line_to(130 + (W - 260) * eo(clamp(strike * 2 - i * 0.5)), yy + 6)
            A.rgba(ctx, RED, a); ctx.set_line_width(12); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()


def series_tag(ctx, t):
    a = 1 - p(t, TOTAL - 0.4, TOTAL)
    rrect(ctx, W / 2 - 190, 250, 380, 64, 32); A.rgba(ctx, CYAN, 0.16 * a); ctx.fill_preserve()
    A.rgba(ctx, CYAN, 0.8 * a); ctx.set_line_width(3); ctx.stroke()
    A.txt(ctx, "MYTH  or  FACT?", W / 2, 296, 38, WHITE, a, shadow=False)


def review_card(ctx, t):
    a = p(t, TREV0, TREV0 + 0.4) * (1 - p(t, TREV1, TREV1 + 0.4))
    if a <= 0: return
    ctx.rectangle(0, 0, W, H); A.rgba(ctx, (0.03, 0.04, 0.07), 0.65 * a); ctx.fill()
    s = 0.9 + 0.1 * eo(p(t, TREV0, TREV0 + 0.5))
    ctx.save(); ctx.translate(W / 2, 760); ctx.scale(s, s); ctx.translate(-W / 2, -760)
    rrect(ctx, 190, 440, 700, 620, 26); A.rgba(ctx, (0.94, 0.96, 1.0), 0.95 * a); ctx.fill()
    A.txt(ctx, "REVIEW OF STUDIES", W / 2, 530, 44, (0.1, 0.12, 0.18), a, shadow=False)
    for i in range(5):
        rrect(ctx, 250, 580 + i * 50, 580 - (i % 2) * 140, 18, 9); A.rgba(ctx, (0.65, 0.7, 0.8), 0.8 * a); ctx.fill()
    A.txt(ctx, "Hartmann et al., 2013", W / 2, 1010, 34, (0.3, 0.34, 0.42), a, bold=False, shadow=False)
    ctx.restore()
    C.stamp(ctx, t, TL.wt("review", "no"), "NO EVIDENCE OF HARM", TREV1 + 0.2, y=880, col=GREEN)


EV = [(THIT, 0.7, True), (TVER, 0.9, True)]


def render(t):
    st = state(t)
    z, foc = camera(t)
    sx, sy, zb, flash = C.shake(t, EV)
    fig_a = (1 - ss(p(t, TIN0 + 0.8, TIN1 - 0.1))) if t < TOUT0 else ss(p(t, TOUT0 + 0.5, TOUT1))
    redk = 0.45 * st["press"]
    green = max(0.7 * max(st["wrap"], st["calf"]) * (1 if t > T["wrap"][0] else 0), p(t, T["end"][0] + 0.2, T["end"][0] + 0.9) * (1 - p(t, TOTAL - 1, TOTAL)))
    tint = mix(mix((0.09, 0.12, 0.20), (0.04, 0.19, 0.15), clamp(green)), (0.20, 0.05, 0.06), clamp(redk))
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
    outside = t < TIN0 or t > TOUT1 - 0.3
    P = pose(squat(t)) if outside else PS
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
        ctx.translate(*wc)
        if outside:
            ctx.rotate(P["thigh"])
        elif t < TOUT0:
            ctx.rotate(PS["thigh"] * (1 - ss(p(t, TIN0, TIN1))))
        else:
            ctx.rotate(PS["thigh"] * ss(p(t, TOUT0, TOUT1)))
        ctx.scale(M0, M0)
        draw_knee(ctx, t, st, anchors)
        model = ctx.pop_group()
        ctx.set_source(model); ctx.paint()
        C.light_sweep(ctx, t, model)
        ctx.restore()
        if rw < 2000:
            C.window_rim(ctx, world, (wc[0] + 40 * M0, wc[1]), rw, z)
    C.bokeh_front(ctx, t, z, foc, REF)
    A.vignette(ctx, red=clamp(redk) * 0.6 + (0.4 * math.exp(-(t - THIT) * 3) if THIT < t < TIN0 else 0))
    C.fades(ctx)
    review_card(ctx, t)
    series_tag(ctx, t)
    ca = (1 - p(t, TIN0 - 0.2, TIN0 + 0.2)) + p(t, TVER - 0.2, TVER + 0.1) * (1 - p(t, TOUT0 + 0.2, TOUT0 + 0.5))
    claim_card(ctx, t if t < TIN0 else 3.0, clamp(ca), strike=p(t, TL.wt("verdict", "myth."), TL.wt("verdict", "myth.") + 0.4))
    if THIT <= t < TIN0 + 0.2:
        C.slam_word(ctx, "?", t, THIT, YEL, 260, 900, hold=TIN0 - THIT - 0.2, rot=0.08)
    lk = lambda a_, b_: p(t, a_, a_ + 0.4) * (1 - p(t, b_, b_ + 0.3))
    C.label(ctx, "kneecap", anchors.get("patella"), 880, 660, lk(T["area"][0] + 0.3, T["wrap"][0]), WHITE)
    C.label(ctx, "tendon", anchors.get("wrap"), 880, 640, lk(TL.wt("wrap", "tendon"), T["calf"][0]), GREEN)
    C.label(ctx, "thigh on calf", anchors.get("calf"), 230, 680, lk(TL.wt("calf", "calf,"), TREV0), GREEN)
    C.slam_word(ctx, "BIGGER CONTACT AREA", t, TL.wt("area", "bigger"), CYAN, 84, 440, hold=T["area"][1] - TL.wt("area", "bigger") + 0.2, rot=0)
    C.slam_word(ctx, "TENDON TAKES LOAD", t, TL.wt("wrap", "wraps"), GREEN, 90, 440, hold=T["wrap"][1] - TL.wt("wrap", "wraps") + 0.2, rot=0)
    C.slam_word(ctx, "LESS LOAD ON THE JOINT", t, TL.wt("calf", "taking"), GREEN, 78, 440, hold=T["calf"][1] - TL.wt("calf", "taking") + 0.2, rot=0)
    C.item_list(ctx, t, [("TOO MUCH WEIGHT", TL.wt("risk", "too")), ("TOO SOON", TL.wt("risk", "soon,")),
                         ("POOR TECHNIQUE", TL.wt("risk", "poor"))], TVER - 0.2, size=66)
    C.stamp(ctx, t, TL.wt("verdict", "myth."), "MYTH", TOUT0 + 0.4, y=830, col=RED)
    C.slam_word(ctx, "SQUAT DEEP", t, T["end"][0], GREEN, 130, 440, hold=TL.wt("end", "if") - T["end"][0] - 0.2, rot=0)
    C.slam_word(ctx, "PAIN? ADJUST DEPTH", t, TL.wt("end", "if"), YEL, 88, 440, hold=TOTAL - TL.wt("end", "if") - 0.6, rot=0)
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
