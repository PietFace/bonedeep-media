import sys, math
sys.path.insert(0, "/home/claude/v2"); sys.path.insert(0, "/home/claude/short")
import cairo
import common as C
from common import W, H, kf, ss, mix, p, eo, eio, back, clamp, YEL, RED, WHITE, GREY, CYAN, GREEN, d2r
import anim2 as A
import shoulder as SH

D = "/home/claude/v2/shoulder"
TL = C.Timeline(D + "/timeline.json"); T = TL.T; TOTAL = TL.total
TS = T["sting"][0]
TIN0, TIN1 = TL.wt("why", "let's") - 0.1, T["why"][1] + 0.15
TOUT0, TOUT1 = T["check"][0] + 0.9, TOTAL - 0.5
RS = (395.0, 520.0)          # right shoulder joint (viewer left)
M0 = 0.19
REF = (520, 900)


# ---------------- front-view figure ----------------
def arm_alpha_fig(t):
    return kf(t, [(0.4, 0), (TS, 90), (TS + 0.25, 92), (T["why"][0] + 0.4, 165), (TIN0 - 0.2, 30), (TOUT1 - 0.4, 30), (TOTAL - 0.1, 0)])


def figure(ctx, al):
    _figure(ctx, al)


def _figure(ctx0, al):
    class F:   # fill every body part separately so overlaps never cancel out
        def __getattr__(self, n): return getattr(ctx0, n)
    ctx = ctx0
    a = al * d2r
    E = (RS[0] - 175 * math.sin(a), RS[1] + 175 * math.cos(a))
    Hd = (E[0] - 160 * math.sin(a), E[1] + 160 * math.cos(a))
    C.limb(ctx, RS, E, 64, 50); ctx.fill(); C.limb(ctx, E, Hd, 48, 36); ctx.fill()
    C.limb(ctx, (645, 520), (668, 705), 64, 50); ctx.fill(); C.limb(ctx, (668, 705), (678, 880), 48, 36); ctx.fill()
    ctx.new_sub_path()
    ctx.move_to(372, 492); ctx.curve_to(450, 470, 590, 470, 668, 492)
    ctx.line_to(640, 640); ctx.line_to(606, 810); ctx.line_to(616, 890); ctx.line_to(424, 890); ctx.line_to(434, 810)
    ctx.line_to(400, 640); ctx.close_path(); ctx.fill()
    for a_, b_, w0, w1 in (((466, 870), (456, 1120), 96, 72), ((456, 1120), (452, 1375), 68, 44),
                           ((574, 870), (584, 1120), 96, 72), ((584, 1120), (588, 1375), 68, 44), ((520, 500), (520, 445), 60, 54)):
        C.limb(ctx, a_, b_, w0, w1); ctx.fill()
    for x in (440, 600):
        ctx.save(); ctx.translate(x, 1392); ctx.scale(1, 0.55); ctx.arc(0, 0, 46, 0, 2 * math.pi); ctx.restore(); ctx.fill()
    ctx.arc(520, 390, 62, 0, 2 * math.pi)


# ---------------- model state ----------------
def model_alpha(t):
    if t < TIN1:
        return arm_alpha_fig(t)
    keys = [(TIN1, 30), (T["ball"][0] + 0.8, 0), (T["roof"][0] + 0.5, 0), (T["roof"][1], 45), (T["arc"][0] + 0.3, 0),
            (T["arc"][1] - 0.3, 165), (T["irr"][0], 70)]
    if t < T["irr"][0]:
        return kf(t, keys)
    if t < T["signs"][0]:
        k = t - T["irr"][0]
        return 85 + 25 * math.sin(k * 4.0)
    if t < T["good"][0]:
        return kf(t, [(T["signs"][0], 90), (T["signs"][0] + 0.6, 60)])
    if t < T["check"][0]:
        k = t - T["good"][0]
        return 80 - 80 * math.cos(k * 1.6)
    return kf(t, [(T["check"][0], 40), (TOUT0, 30), (TOUT1, 30)])


def state(t):
    al = model_alpha(t)
    pinch = SH.pinch_amount(al)
    st = dict(alpha=al, deltoid=0.45, tglow=0.0, irr=0.0, infl=0.0, arc=0.0, green=0.0, nerve=0.0)
    if TS <= t < TIN1:
        st["tglow"] = pinch * 1.2; st["irr"] = pinch; st["infl"] = pinch
    if T["ball"][0] <= t < T["roof"][0]:
        st["deltoid"] = 0.25
    if T["roof"][0] <= t < T["arc"][0]:
        st["tglow"] = 0.7 * p(t, T["roof"][0] + 0.6, T["roof"][0] + 1.2); st["deltoid"] = 0.2
    if T["arc"][0] <= t < T["irr"][0]:
        st["arc"] = p(t, T["arc"][0], T["arc"][0] + 0.4); st["tglow"] = pinch * 1.1; st["irr"] = pinch * 0.6
        st["deltoid"] = 0.25
    if T["irr"][0] <= t < T["good"][0]:
        k = p(t, T["irr"][0], T["irr"][0] + 2.0)
        st["irr"] = max(k, pinch); st["infl"] = k; st["tglow"] = 0.8 + 0.4 * pinch; st["deltoid"] = 0.3
        st["nerve"] = p(t, TL.wt("irr", "tight"), TL.wt("irr", "tight") + 0.3)
    if T["good"][0] <= t < T["check"][0] + 0.5:
        st["green"] = p(t, T["good"][0], T["good"][0] + 0.5); st["deltoid"] = 0.55
    return st


def draw_model(ctx, t, st, anchors):
    beta, Hh, a = SH.shoulder(ctx, st["alpha"], deltoid_a=st["deltoid"], tendon_glow=0 if st["green"] else st["tglow"],
                              irritated=st["irr"] * (1 - st["green"]), inflamed=st["infl"] * (1 - st["green"]))
    if st["green"] > 0:
        SH.supraspinatus(ctx, beta, Hh, a, irritated=0, glow=0)
        tp = SH.S((-20, -150), beta)
        C.glow_blob(ctx, tp[0], tp[1], 160, GREEN, st["green"] * (0.6 + 0.4 * math.sin(t * 5)))
    if st["arc"] > 0:
        SH.painful_arc(ctx, Hh, st["alpha"], st["arc"], R=560)
    if st["nerve"] > 0:
        tp = SH.S((-20, -150), beta)
        C.pulse_path(ctx, [tp, (tp[0] + 200, tp[1] - 150), (tp[0] + 450, tp[1] - 300), (tp[0] + 700, tp[1] - 650)], t, st["nerve"])
    anchors["ball"] = ctx.user_to_device(-30, 40)
    anchors["socket"] = ctx.user_to_device(*SH.S((128, 20), beta))
    anchors["roof"] = ctx.user_to_device(*SH.S((-100, -215), beta))
    anchors["tendon"] = ctx.user_to_device(*SH.S((60, -150), beta))
    return Hh


# ---------------- camera ----------------
def camera(t):
    fig_c = (520.0, 900.0)
    z_in = 0.95 / M0
    if t < TIN0:
        return 1.0, fig_c
    if t < TIN1:
        k = eio(p(t, TIN0, TIN1))
        return 1 + (z_in - 1) * k, mix(fig_c, (RS[0] + 60 * M0, RS[1] + 120 * M0), k)
    if t < TOUT0:
        mv = [(TIN1, (60, 120), 1.0), (T["ball"][1], (60, 60), 1.05), (T["roof"][0] + 0.6, (40, -120), 1.55),
              (T["roof"][1], (40, -120), 1.55), (T["arc"][0] + 0.4, (-150, -60), 0.62), (T["arc"][1], (-150, -60), 0.62),
              (T["irr"][0] + 0.4, (60, -40), 1.15), (T["signs"][0] + 0.3, (60, 140), 0.9),
              (T["good"][0] + 0.3, (-170, -230), 0.55), (T["check"][0] + 0.3, (-170, -230), 0.55), (TOUT0, (60, 120), 1.0)]
        off = kf(t, [(a, b) for a, b, _ in mv]); zm = kf(t, [(a, c) for a, _, c in mv])
        return z_in * zm, (RS[0] + off[0] * M0, RS[1] + off[1] * M0)
    if t < TOUT1:
        k = eio(p(t, TOUT0, TOUT1))
        return z_in + (1 - z_in) * k, mix((RS[0] + 60 * M0, RS[1] + 120 * M0), fig_c, k)
    return 1.0, fig_c


def window(t):
    if t < TS: return 0
    if t < TIN0: return 115 * back(p(t, TS, TS + 0.3))
    if t < TIN1: return 115 + 1100 * ss(p(t, TIN0 + 0.4, TIN1))
    if t < TOUT0: return 4000
    if t < TOUT1: return 1215 - 1100 * ss(p(t, TOUT0, TOUT1 - 0.2))
    return 115 * (1 - ss(p(t, TOUT1, TOUT1 + 0.4)))


def cuff_amt(t):
    return p(t, T["cuff"][0] - 0.1, T["cuff"][0] + 0.25) * (1 - p(t, T["roof"][0] - 0.2, T["roof"][0] + 0.15))


EV = [(TS, 1.0, True)] + [(T["irr"][0] + 0.4 + i * 1.57, 0.25, False) for i in range(3)] + [(T["check"][0], 0.3, False)]


def render(t):
    st = state(t)
    z, foc = camera(t)
    sx, sy, zb, flash = C.shake(t, EV)
    fig_a = (1 - ss(p(t, TIN0 + 0.9, TIN1 - 0.1))) if t < TOUT0 else ss(p(t, TOUT0 + 0.5, TOUT1))
    redk = 0.5 * st["irr"] if T["irr"][0] <= t < T["good"][0] else 0
    tint = mix(mix((0.09, 0.12, 0.20), (0.04, 0.19, 0.15), st["green"]), (0.20, 0.05, 0.06), clamp(redk))
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf); ctx.set_antialias(cairo.ANTIALIAS_GOOD)
    C.background(ctx, t, z, foc, tint, REF)
    ctx.save(); ctx.translate(W / 2 + sx, 900 + sy); ctx.scale(z * (1 + zb), z * (1 + zb)); ctx.translate(-foc[0], -foc[1])
    world = ctx.get_matrix(); ctx.restore()
    al_fig = arm_alpha_fig(t) if t < TIN1 else (arm_alpha_fig(t) if t > TOUT1 else 30)
    sil = C.silhouette_layer(world, lambda c: figure(c, al_fig), fig_a)
    if sil:
        ctx.set_source_surface(sil[0], 0, 0); ctx.paint()
    rw = window(t); anchors = {}
    ca = cuff_amt(t)
    if rw > 0 and ca < 1:
        ctx.save(); ctx.set_matrix(world)
        ctx.arc(RS[0], RS[1], rw, 0, 2 * math.pi)
        if rw < 2000:
            ctx.save(); ctx.clip_preserve(); ctx.set_source_rgb(0.03, 0.04, 0.07); ctx.paint(); ctx.restore()
        ctx.clip()
        ctx.push_group()
        ctx.translate(*RS); ctx.scale(M0, M0)
        draw_model(ctx, t, st, anchors)
        model = ctx.pop_group()
        if ca > 0:   # flip out
            ctx.translate(*foc); ctx.scale(max(0.02, 1 - ca), 1); ctx.translate(-foc[0], -foc[1])
        ctx.set_source(model); ctx.paint()
        C.light_sweep(ctx, t, model)
        ctx.restore()
        if rw < 2000:
            C.window_rim(ctx, world, RS, rw, z)
    if ca > 0:
        ctx.save(); ctx.translate(W / 2, 960); ctx.scale(max(0.02, ca), 1); ctx.scale(0.92, 0.92)
        SH.cuff_view(ctx, t, squeeze=0.4 + 0.6 * (0.5 + 0.5 * math.sin(t * 5)), labels=p(t, T["cuff"][0] + 0.5, T["cuff"][0] + 1.0))
        ctx.restore()
    C.bokeh_front(ctx, t, z, foc, REF)
    A.vignette(ctx, red=clamp(redk) * 0.6 + (0.5 * math.exp(-(t - TS) * 3) if t > TS else 0) * (1 if t < TIN0 else 0))
    C.fades(ctx)
    # labels
    C.label(ctx, "ball", anchors.get("ball"), 260, 1040, p(t, T["ball"][0] + 0.6, T["ball"][0] + 1.0) * (1 - p(t, T["cuff"][0] - 0.3, T["cuff"][0])), WHITE)
    C.label(ctx, "socket", anchors.get("socket"), 820, 1040, p(t, T["ball"][0] + 1.4, T["ball"][0] + 1.8) * (1 - p(t, T["cuff"][0] - 0.3, T["cuff"][0])), WHITE)
    C.label(ctx, "bony roof", anchors.get("roof"), 300, 720, p(t, TL.wt("roof", "bony"), TL.wt("roof", "bony") + 0.4) * (1 - p(t, T["arc"][0], T["arc"][0] + 0.3)), YEL)
    C.label(ctx, "tendon", anchors.get("tendon"), 800, 720, p(t, TL.wt("roof", "tendon"), TL.wt("roof", "tendon") + 0.4) * (1 - p(t, T["arc"][0], T["arc"][0] + 0.3)), CYAN)
    # big words
    C.slam_word(ctx, "OUCH!", t, TS, RED, 200, 600, hold=0.9)
    C.slam_word(ctx, "WHY?", t, TL.wt("why", "why?"), WHITE, 170, 560, hold=1.4, rot=0)
    C.slam_word(ctx, "4 MUSCLES", t, T["cuff"][0] + 0.2, YEL, 120, 440, hold=T["cuff"][1] - T["cuff"][0], rot=0)
    C.slam_word(ctx, "60°–120°", t, T["arc"][0] + 0.3, RED, 140, 470, hold=T["arc"][1] - T["arc"][0] - 0.2, rot=0)
    C.slam_word(ctx, "IRRITATED", t, TL.wt("irr", "irritated,"), RED, 130, 470, hold=2.2)
    C.item_list(ctx, t, [("LIFTING", TL.wt("signs", "lifting")), ("AT NIGHT", TL.wt("signs", "night.")),
                         ("WEAKNESS", TL.wt("signs", "weakness"))], T["signs"][1] + 0.3, col=YEL, mark="•")
    C.slam_word(ctx, "THE RIGHT", t, TL.wt("good", "right"), GREEN, 110, 440, hold=T["good"][1] - TL.wt("good", "right"), rot=0)
    C.slam_word(ctx, "EXERCISES", t, TL.wt("good", "exercises"), GREEN, 140, 580, hold=T["good"][1] - TL.wt("good", "exercises"), rot=0)
    C.stamp(ctx, t, TL.wt("check", "get"), "GET IT CHECKED", TOUT0 + 0.5, y=600)
    C.captions(ctx, t, TL)
    if t > T["check"][0]:
        A.txt(ctx, "General information, not personal medical advice", W / 2, 1440, 26, GREY,
              0.8 * p(t, T["check"][0], T["check"][0] + 0.4) * (1 - p(t, TOTAL - 0.4, TOTAL)), bold=False, shadow=False)
    if flash > 0:
        A.rgba(ctx, RED, flash * 0.6); ctx.paint()
    return surf


BLUR = [(TS - 0.05, TS + 0.35), (TIN0, TIN1), (TOUT0, TOUT1)]
if __name__ == "__main__":
    C.run(render, TOTAL, BLUR, sys.argv)
