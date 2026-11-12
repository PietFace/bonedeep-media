import sys, math
sys.path.insert(0, "/home/claude/v2"); sys.path.insert(0, "/home/claude/short"); sys.path.insert(0, "/home/claude/v2/ankle")
import cairo
import common as C
from common import W, H, kf, ss, mix, p, eo, eio, back, clamp, YEL, RED, WHITE, GREY, CYAN, GREEN, d2r
import anim2 as A
import ankle as AK

D = "/home/claude/v2/ankle"
TL = C.Timeline(D + "/timeline.json"); T = TL.T; TOTAL = TL.total
TR = TL.wt("roll", "rolls.") + 0.1
TIN0, TIN1 = TL.wt("what", "let's") - 0.1, T["what"][1] + 0.2
TTEAR = TL.wt("grades", "tears")
TMILD = TL.wt("grades", "mild")
TOUT0, TOUT1 = T["end"][0] - 0.1, T["end"][0] + 1.7
ANK = (452.0, 1368.0)
M0 = 0.24
REF = (520, 900)


def fig_dy(t):
    return kf(t, [(0.0, -70), (1.1, -70), (TR - 0.02, 0), (TOTAL - 0.7, 0), (TOTAL - 0.1, -70)], f=lambda x: x * x)


def fig_inv(t):
    return kf(t, [(TR - 0.05, 0), (TR + 0.1, 42), (TR + 0.6, 30), (TOUT1, 0)])


def lift_left(t):
    return kf(t, [(TOUT1 - 0.3, 0), (TOUT1 + 0.2, 1), (TOTAL - 0.8, 1), (TOTAL - 0.4, 0)])


def figure(ctx, t):
    dy = fig_dy(t); inv = fig_inv(t); ll = lift_left(t)
    buck = clamp(inv / 40)
    o = lambda q: (q[0], q[1] + dy)
    kr = (456 - 18 * buck, 1120); kl = (584 + 30 * ll, 1120 - 60 * ll); al = (588 + 10 * ll, 1375 - 150 * ll)
    parts = [((395, 520), (372, 705), 64, 50), ((372, 705), (362, 880), 48, 36),
             ((645, 520), (668, 705), 64, 50), ((668, 705), (678, 880), 48, 36),
             ((466, 870), kr, 96, 72), (kr, (452, 1375), 68, 44), ((574, 870), kl, 96, 72), (kl, al, 68, 44),
             ((520, 500), (520, 445), 60, 54)]
    for a_, b_, w0, w1 in parts:
        C.limb(ctx, o(a_), o(b_), w0, w1); ctx.fill()
    ctx.move_to(*o((372, 492))); ctx.curve_to(*o((450, 470)), *o((590, 470)), *o((668, 492)))
    for q in ((640, 640), (606, 810), (616, 890), (424, 890), (434, 810), (400, 640)):
        ctx.line_to(*o(q))
    ctx.close_path(); ctx.fill()
    for (x, y), r in (((440, 1392), -inv), ((al[0] - 12, al[1] + 17), 0)):
        ctx.save(); ctx.translate(x, y + dy); ctx.rotate(r * d2r); ctx.scale(1, 0.55); ctx.arc(0, 0, 46, 0, 2 * math.pi); ctx.restore(); ctx.fill()
    ctx.arc(520, 390 + dy, 62, 0, 2 * math.pi)


def inside_inv(t):
    if t < T["rest"][0]:
        return kf(t, [(TIN1, 30), (T["ligs"][0] + 0.6, 0), (TL.wt("inward", "rolls"), 0), (TL.wt("inward", "front") + 0.3, 34),
                      (TMILD - 0.2, 30), (TMILD + 0.3, 26), (TTEAR - 0.05, 26), (TTEAR + 0.15, 50), (TTEAR + 0.8, 44),
                      (T["swell"][0] + 0.4, 6)], f=lambda x: ss(x) if x < 1 else 1)
    if t < T["flags"][0]:
        return 6 + 9 * math.sin((t - T["rest"][0]) * 3.0)
    return kf(t, [(T["flags"][0], 6), (T["flags"][0] + 0.5, 4), (TOUT0, 30 * 0 + 4)])


def state(t):
    st = {"inv": fig_inv(t) if t < TIN1 else inside_inv(t)}
    if t >= TOUT0:
        st["inv"] = fig_inv(t)
    if TR <= t < TIN1:
        st["atfl_glow"] = 1.0; st["atfl_col"] = RED
    if T["ligs"][0] <= t < T["inward"][0]:
        st["lig_glow"] = p(t, T["ligs"][0] + 0.8, T["ligs"][0] + 1.4)
    if T["inward"][0] <= t < T["swell"][0]:
        st["atfl_glow"] = p(t, TL.wt("inward", "front"), TL.wt("inward", "front") + 0.3)
        st["atfl_col"] = YEL if t < TTEAR else RED
    if t >= TTEAR:
        st["torn"] = (eo(p(t, TTEAR, TTEAR + 0.2))) * (1 - p(t, T["rest"][0] + 2.0, T["rest"][0] + 3.5))
    sw = p(t, T["swell"][0], T["swell"][1]) * (1 - 0.6 * p(t, T["rest"][0] + 1, T["rest"][1]))
    if t >= T["flags"][0]:
        sw *= 1 - p(t, T["flags"][0], T["flags"][0] + 1)
    st["swell"] = sw if t >= T["swell"][0] else 0
    st["green"] = p(t, T["rest"][0] + 0.6, T["rest"][0] + 1.1) * (1 - p(t, T["flags"][0], T["flags"][0] + 0.3))
    if st["green"] > 0:
        st["lig_glow"] = st["green"] * 0.8; st["gcol"] = GREEN
    st["bone"] = p(t, TL.wt("flags", "bone?"), TL.wt("flags", "bone?") + 0.3) * (1 - p(t, TOUT0 - 0.3, TOUT0))
    return st


def camera(t):
    fig_c = (520.0, 900.0)
    z_in = 1.7 / M0
    tgt = (ANK[0], ANK[1] + 70 * M0)
    if t < TIN0:
        return 1.0, fig_c
    if t < TIN1:
        k = eio(p(t, TIN0, TIN1)); return 1 + (z_in - 1) * k, mix(fig_c, tgt, k)
    if t < TOUT0:
        mv = [(TIN1, (0, 70), 1.0), (T["ligs"][0] + 0.5, (-50, 160), 1.1), (T["inward"][0] + 0.3, (-30, 170), 1.0),
              (T["grades"][0] + 0.3, (-80, 150), 1.3), (T["swell"][0] + 0.3, (-40, 160), 1.0),
              (T["rest"][0] + 0.3, (0, 170), 0.9), (T["flags"][0] + 0.3, (-50, 150), 1.05), (TOUT0 - 0.4, (0, 70), 1.0)]
        off = kf(t, [(a, b) for a, b, _ in mv]); zm = kf(t, [(a, c) for a, _, c in mv])
        return z_in * zm, (ANK[0] + off[0] * M0, ANK[1] + off[1] * M0)
    if t < TOUT1:
        k = eio(p(t, TOUT0, TOUT1)); return z_in + (1 - z_in) * k, mix(tgt, fig_c, k)
    return 1.0, fig_c


def window(t):
    if t < TR: return 0
    if t < TIN0: return 105 * back(p(t, TR, TR + 0.3))
    if t < TIN1: return 105 + 1100 * ss(p(t, TIN0 + 0.4, TIN1))
    if t < TOUT0: return 4000
    if t < TOUT1: return 1205 - 1100 * ss(p(t, TOUT0, TOUT1 - 0.2))
    return 105 * (1 - ss(p(t, TOUT1, TOUT1 + 0.4)))


EV = [(TR, 1.0, True), (TTEAR, 0.8, True), (TL.wt("flags", "get"), 0.3, False)]


def render(t):
    st = state(t)
    z, foc = camera(t)
    sx, sy, zb, flash = C.shake(t, EV)
    fig_a = (1 - ss(p(t, TIN0 + 0.9, TIN1 - 0.1))) if t < TOUT0 else ss(p(t, TOUT0 + 0.5, TOUT1))
    redk = st["swell"] * 0.5 + (0.4 if TTEAR <= t < T["swell"][0] else 0)
    tint = mix(mix((0.09, 0.12, 0.20), (0.04, 0.19, 0.15), st["green"]), (0.20, 0.05, 0.06), clamp(redk))
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf); ctx.set_antialias(cairo.ANTIALIAS_GOOD)
    C.background(ctx, t, z, foc, tint, REF)
    ctx.save(); ctx.translate(W / 2 + sx, 900 + sy); ctx.scale(z * (1 + zb), z * (1 + zb)); ctx.translate(-foc[0], -foc[1])
    world = ctx.get_matrix()
    # curb + ground glow
    if fig_a > 0:
        cy = 1420 - 70
        ctx.rectangle(250, cy, 560, 34); A.rgba(ctx, CYAN, 0.10 * fig_a); ctx.fill()
        ctx.move_to(250, cy); ctx.line_to(810, cy); A.rgba(ctx, CYAN, 0.5 * fig_a); ctx.set_line_width(3); ctx.stroke()
        g = cairo.RadialGradient(520, 1420, 10, 520, 1420, 380)
        g.add_color_stop_rgba(0, CYAN[0], CYAN[1], CYAN[2], 0.22 * fig_a); g.add_color_stop_rgba(1, CYAN[0], CYAN[1], CYAN[2], 0)
        ctx.save(); ctx.translate(0, 1420); ctx.scale(1, 0.1); ctx.translate(0, -1420); ctx.set_source(g)
        ctx.arc(520, 1420, 380, 0, 2 * math.pi); ctx.fill(); ctx.restore()
    ctx.restore()
    sil = C.silhouette_layer(world, lambda c: figure(c, t), fig_a)
    if sil:
        ctx.set_source_surface(sil[0], 0, 0); ctx.paint()
    rw = window(t); anchors = {}
    ank = (ANK[0], ANK[1] + fig_dy(t)) if (t < TIN0 or t > TOUT1) else ANK
    if rw > 0:
        ctx.save(); ctx.set_matrix(world)
        ctx.arc(ank[0], ank[1] + 40 * M0, rw, 0, 2 * math.pi)
        if rw < 2000:
            ctx.save(); ctx.clip_preserve(); ctx.set_source_rgb(0.03, 0.04, 0.07); ctx.paint(); ctx.restore()
        ctx.clip()
        ctx.push_group()
        ctx.translate(*ank); ctx.scale(M0, M0)
        AK.ankle(ctx, t, st, anchors)
        if st["bone"] > 0:
            C.glow_blob(ctx, -142, 100, 110, RED, st["bone"] * (0.6 + 0.4 * math.sin(t * 8)))
        model = ctx.pop_group()
        ctx.set_source(model); ctx.paint()
        C.light_sweep(ctx, t, model)
        ctx.restore()
        if rw < 2000:
            C.window_rim(ctx, world, (ank[0], ank[1] + 40 * M0), rw, z)
    C.bokeh_front(ctx, t, z, foc, REF)
    A.vignette(ctx, red=clamp(redk) * 0.6 + (0.5 * math.exp(-(t - TR) * 3) if TR < t < TIN0 else 0))
    C.fades(ctx)
    lk = p(t, T["ligs"][0] + 1.0, T["ligs"][0] + 1.5) * (1 - p(t, T["inward"][0] + 0.5, T["inward"][0] + 0.8))
    C.label(ctx, "ATFL", anchors.get("ATFL"), 230, 760, lk, CYAN)
    C.label(ctx, "CFL", anchors.get("CFL"), 170, 1060, lk, CYAN)
    C.label(ctx, "PTFL", anchors.get("PTFL"), 300, 640, lk * 0.9, CYAN)
    fk = p(t, TL.wt("inward", "front"), TL.wt("inward", "front") + 0.4) * (1 - p(t, T["grades"][0], T["grades"][0] + 0.3))
    C.label(ctx, "front ligament", anchors.get("ATFL"), 260, 700, fk, YEL)
    C.slam_word(ctx, "ROLLED!", t, TR, RED, 190, 600, hold=0.9)
    C.slam_word(ctx, "WHAT HAPPENED?", t, T["what"][0], WHITE, 100, 560, hold=1.3, rot=0)
    C.slam_word(ctx, "3 LIGAMENTS", t, TL.wt("ligs", "three"), YEL, 120, 440, hold=T["ligs"][1] - TL.wt("ligs", "three"), rot=0)
    C.slam_word(ctx, "STRETCHED", t, TMILD + 0.4, YEL, 130, 470, hold=TTEAR - TMILD - 0.7)
    C.slam_word(ctx, "TORN", t, TTEAR, RED, 220, 520, hold=T["grades"][1] - TTEAR + 0.3)
    C.slam_word(ctx, "SWELLING", t, TL.wt("swell", "swells,"), RED, 130, 470, hold=T["swell"][1] - TL.wt("swell", "swells,"))
    C.slam_word(ctx, "MOVE EARLY", t, TL.wt("rest", "move"), GREEN, 120, 440, hold=T["rest"][1] - TL.wt("rest", "move"), rot=0)
    C.slam_word(ctx, "TRAIN BALANCE", t, TL.wt("rest", "train"), GREEN, 110, 580, hold=T["rest"][1] - TL.wt("rest", "train"), rot=0)
    C.item_list(ctx, t, [("CAN'T WALK", TL.wt("flags", "can't")), ("BONE PAIN", TL.wt("flags", "bone?"))], TOUT0 + 0.3)
    C.stamp(ctx, t, TL.wt("flags", "get"), "GET IT CHECKED", TOUT0 + 0.3, y=700)
    C.slam_word(ctx, "TRAIN IT", t, TL.wt("end", "train"), GREEN, 140, 560, hold=TOTAL - TL.wt("end", "train") - 0.7, rot=0)
    C.captions(ctx, t, TL)
    if t > T["end"][0]:
        A.txt(ctx, "General information, not personal medical advice", W / 2, 1440, 26, GREY,
              0.8 * p(t, T["end"][0], T["end"][0] + 0.4) * (1 - p(t, TOTAL - 0.4, TOTAL)), bold=False, shadow=False)
    if flash > 0:
        A.rgba(ctx, WHITE, flash * 0.7); ctx.paint()
    return surf


BLUR = [(TR - 0.1, TR + 0.35), (TIN0, TIN1), (TTEAR - 0.05, TTEAR + 0.35), (TOUT0, TOUT1)]
if __name__ == "__main__":
    C.run(render, TOTAL, BLUR, sys.argv)
