import sys, math, random, importlib.util
sys.path.insert(0, "/home/claude/v2"); sys.path.insert(0, "/home/claude/short"); sys.path.insert(0, "/home/claude/v2/back")
import cairo
import common as C
from common import W, H, kf, ss, mix, p, eo, eio, back, clamp, YEL, RED, WHITE, GREY, CYAN, GREEN, d2r
import anim2 as A
import spine as SP
from anim import rrect

_spec = importlib.util.spec_from_file_location("backfilm", "/home/claude/v2/back/film.py")
BF = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(BF)

D = "/home/claude/v2/taller"
TL = C.Timeline(D + "/timeline.json"); T = TL.T; TOTAL = TL.total
TIN0, TIN1 = TL.wt("how", "let's") - 0.1, T["how"][1] + 0.3
TOUT0, TOUT1 = T["space"][0] - 0.1, T["space"][0] + 1.5
TNIGHT0 = TL.wt("q", "night.")
M0 = 0.15
REF = (520, 900)
P0 = BF.pose(0.0)
GROUND = 1440.0


def shrink(t):
    """0 = morning height, 1 = evening height"""
    if t < TIN0:
        return p(t, TNIGHT0, TNIGHT0 + 0.6)
    if t < T["day"][0]:
        return kf(t, [(TIN0, 1.0), (T["discs"][0], 0.0)])
    if t < T["night"][0]:
        return p(t, TL.wt("day", "squeeze"), T["day"][1])
    if t < TOUT0:
        return 1 - p(t, TL.wt("night", "soak"), T["night"][1] + 0.2)
    return 0.0


def clock(t):
    """'day' or 'night' and blend"""
    if t < TIN0:
        return p(t, TNIGHT0 - 0.2, TNIGHT0 + 0.3)
    if t < T["day"][0]:
        return 0.0
    if t < T["night"][0]:
        return p(t, T["day"][0] + 1.0, T["day"][1])
    if t < TOUT0:
        return 1.0
    return 1 - p(t, TOUT0, TOUT0 + 0.6)


def space_k(t):
    return p(t, TOUT0 + 0.6, TOUT1) * (1 - p(t, T["end"][0] - 0.2, T["end"][0] + 0.4))


def camera(t):
    fig_c = (560.0, 950.0)
    z_in = 0.8 / M0
    if t < TIN0:
        return 1.0, 0.0, fig_c
    if t < TIN1:
        k = eio(p(t, TIN0, TIN1)); return 1 + (z_in - 1) * k, -P0["tau"] * k, mix(fig_c, P0["lum"], k)
    if t < TOUT0:
        lie = ss(p(t, T["night"][0], T["night"][0] + 1.0)) * (1 - ss(p(t, TOUT0 - 0.6, TOUT0)))
        zm = kf(t, [(TIN1, 1.0), (T["discs"][0] + 0.3, 1.1), (T["day"][0] + 0.5, 1.0)])
        return z_in * zm, -P0["tau"] - lie * math.pi / 2, (P0["lum"][0], P0["lum"][1])
    if t < TOUT1:
        k = eio(p(t, TOUT0, TOUT1)); return z_in + (1 - z_in) * k, -P0["tau"] * (1 - k), mix(P0["lum"], fig_c, k)
    return 1.0, 0.0, fig_c


def window(t):
    if t < TIN0 - 0.4: return 0
    if t < TIN1: return 110 * back(p(t, TIN0 - 0.4, TIN0)) + 1100 * ss(p(t, TIN0 + 0.4, TIN1))
    if t < TOUT0: return 4000
    if t < TOUT1: return 1210 - 1100 * ss(p(t, TOUT0, TOUT1 - 0.2))
    return 0


def series_tag(ctx, t):
    a = p(t, 0.1, 0.5) * (1 - p(t, TOTAL - 0.4, TOTAL))
    rrect(ctx, W / 2 - 160, 250, 320, 64, 32); A.rgba(ctx, YEL, 0.14 * a); ctx.fill_preserve()
    A.rgba(ctx, YEL, 0.8 * a); ctx.set_line_width(3); ctx.stroke()
    A.txt(ctx, "BODY FACTS", W / 2, 296, 38, WHITE, a, shadow=False)


def sun_moon(ctx, t, k, x=W / 2, y=400, a=1.0):
    if a <= 0: return
    # sun
    sa = (1 - k) * a
    if sa > 0:
        C.glow_blob(ctx, x, y, 120, YEL, sa)
        ctx.arc(x, y, 44, 0, 2 * math.pi); A.rgba(ctx, YEL, sa); ctx.fill()
        for i in range(10):
            an = i * math.pi / 5 + t * 0.4
            ctx.move_to(x + 60 * math.cos(an), y + 60 * math.sin(an)); ctx.line_to(x + 84 * math.cos(an), y + 84 * math.sin(an))
            A.rgba(ctx, YEL, sa); ctx.set_line_width(7); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
    ma = k * a
    if ma > 0:
        C.glow_blob(ctx, x, y, 110, (0.6, 0.7, 1.0), ma * 0.8)
        ctx.save(); ctx.arc(x, y, 46, 0, 2 * math.pi); ctx.arc_negative(x + 22, y - 12, 40, 2 * math.pi, 0)
        ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD); A.rgba(ctx, (0.85, 0.9, 1.0), ma); ctx.fill(); ctx.restore()
    A.txt(ctx, "7:00" if k < 0.5 else "23:00", x, y + 130, 44, WHITE, a, bold=False)


def ruler(ctx, t, s, a):
    if a <= 0: return
    x = 860; top = 300; bot = GROUND
    ctx.move_to(x, top); ctx.line_to(x, bot); A.rgba(ctx, WHITE, 0.5 * a); ctx.set_line_width(3); ctx.stroke()
    for i in range(0, 46):
        y = bot - i * 25
        if y < top: break
        ctx.move_to(x, y); ctx.line_to(x + (24 if i % 4 == 0 else 12), y); A.rgba(ctx, WHITE, 0.4 * a); ctx.set_line_width(2); ctx.stroke()
    head_y = P0["head"][1] - 64
    hy = GROUND - (GROUND - head_y) * (1 - 0.03 * s)
    ctx.move_to(560, hy); ctx.line_to(x + 30, hy); ctx.set_dash([10, 8]); A.rgba(ctx, YEL, a); ctx.set_line_width(4); ctx.stroke(); ctx.set_dash([])
    cm = 180.0 - 1.5 * s + 3.0 * space_k(t)
    rrect(ctx, x - 150, hy - 80, 220, 64, 14); A.rgba(ctx, (0.05, 0.07, 0.12), 0.85 * a); ctx.fill()
    A.txt(ctx, f"{cm:.1f} cm", x - 40, hy - 34, 40, YEL, a, shadow=False)


def droplets(ctx, t, dcs, mode, a):
    if a <= 0: return
    for j, (x, y) in enumerate(dcs):
        r = random.Random(j)
        for i in range(8):
            ph = (t * 0.5 + r.random()) % 1.0
            u = ph if mode == "out" else 1 - ph
            side = 1 if i % 2 else -1
            dx = side * (60 + 140 * u); dy = r.uniform(-20, 20)
            al = a * (math.sin(math.pi * ph))
            g = cairo.RadialGradient(x + dx, y + dy, 1, x + dx, y + dy, 18)
            g.add_color_stop_rgba(0, 0.7, 0.9, 1, al); g.add_color_stop_rgba(1, 0.3, 0.7, 1, 0)
            ctx.set_source(g); ctx.arc(x + dx, y + dy, 18, 0, 2 * math.pi); ctx.fill()


def render(t):
    s = shrink(t); ck = clock(t); sk = space_k(t)
    z, rot, foc = camera(t)
    fig_a = (1 - ss(p(t, TIN0 + 0.9, TIN1 - 0.1))) if t < TOUT0 else ss(p(t, TOUT0 + 0.5, TOUT1))
    tint = mix(mix((0.09, 0.12, 0.20), (0.05, 0.05, 0.14), ck * 0.8), (0.02, 0.02, 0.05), sk)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf); ctx.set_antialias(cairo.ANTIALIAS_GOOD)
    C.background(ctx, t, z, foc, tint, REF)
    if sk > 0:   # stars
        r = random.Random(7)
        for _ in range(140):
            x, y, sz = r.uniform(0, W), r.uniform(0, H), r.uniform(1, 3.5)
            A.rgba(ctx, WHITE, sk * r.uniform(0.3, 1) * (0.7 + 0.3 * math.sin(t * 3 + x))); ctx.arc(x, y, sz, 0, 2 * math.pi); ctx.fill()
    ctx.save(); ctx.translate(W / 2, 950); ctx.scale(z, z); ctx.rotate(rot); ctx.translate(-foc[0], -foc[1])
    world = ctx.get_matrix()
    if fig_a > 0 and sk < 1:
        g = cairo.RadialGradient(520, GROUND, 10, 520, GROUND, 400)
        g.add_color_stop_rgba(0, CYAN[0], CYAN[1], CYAN[2], 0.22 * fig_a * (1 - sk)); g.add_color_stop_rgba(1, CYAN[0], CYAN[1], CYAN[2], 0)
        ctx.save(); ctx.translate(0, GROUND); ctx.scale(1, 0.1); ctx.translate(0, -GROUND); ctx.set_source(g)
        ctx.arc(520, GROUND, 400, 0, 2 * math.pi); ctx.fill(); ctx.restore()
    ctx.restore()
    # figure (slightly compressed in the evening, floats in space)
    fl = sk * (-60 + 20 * math.sin(t * 1.5))
    m = cairo.Matrix(*world)
    fm = cairo.Matrix(1, 0, 0, 1 - 0.03 * s, 0, GROUND * 0.03 * s + fl)
    fm = fm.multiply(m)
    sil = C.silhouette_layer(fm, lambda c: BF.figure(c, P0), fig_a, lambda c: BF.figure(c, P0, True))
    if sil:
        ctx.set_source_surface(sil[0], 0, 0); ctx.paint()
    rw = window(t); anchors = {}
    dcs = []
    if rw > 0:
        st = {"flex": 0.0, "ds": 1 - 0.28 * s}
        st["disc_glow"] = p(t, TL.wt("discs", "discs,"), TL.wt("discs", "discs,") + 0.3) * (1 - p(t, TOUT0 - 0.3, TOUT0))
        ctx.save(); ctx.set_matrix(fm)
        ctx.arc(P0["lum"][0], P0["lum"][1], rw, 0, 2 * math.pi)
        if rw < 2000:
            ctx.save(); ctx.clip_preserve(); ctx.set_source_rgb(0.03, 0.04, 0.07); ctx.paint(); ctx.restore()
        ctx.clip()
        ctx.push_group()
        ctx.translate(*P0["lum"]); ctx.rotate(P0["tau"]); ctx.scale(M0, M0)
        SP.spine(ctx, t, st, anchors)
        _, _, dc = SP.chain(0.0, st["ds"])
        dcs = [ctx.user_to_device(d[0], d[1]) for d in dc]
        model = ctx.pop_group()
        ctx.set_source(model); ctx.paint()
        C.light_sweep(ctx, t, model)
        ctx.restore()
        if rw < 2000:
            C.window_rim(ctx, fm, P0["lum"], rw, z)
    if T["day"][0] <= t < T["night"][0]:
        droplets(ctx, t, dcs, "out", p(t, TL.wt("day", "squeeze"), TL.wt("day", "squeeze") + 0.4) * (1 - p(t, T["day"][1], T["day"][1] + 0.3)))
    if T["night"][0] <= t < TOUT0:
        droplets(ctx, t, dcs, "in", p(t, TL.wt("night", "soak"), TL.wt("night", "soak") + 0.4) * (1 - p(t, TOUT0 - 0.4, TOUT0)))
    C.bokeh_front(ctx, t, z, foc, REF)
    A.vignette(ctx, red=0)
    C.fades(ctx)
    series_tag(ctx, t)
    outside = t < TIN0 + 0.3 or t > TOUT1 - 0.4
    ra = (1 - p(t, TIN0, TIN0 + 0.4)) if t < TIN1 else p(t, TOUT1 - 0.4, TOUT1)
    ruler(ctx, t, s, ra * (1 if outside else 0))
    sm_a = (1 - p(t, TIN0, TIN0 + 0.3)) if t < TIN1 else (p(t, T["day"][0], T["day"][0] + 0.4) * (1 - p(t, TOUT0, TOUT0 + 0.3)) if t < TOUT1 else p(t, T["end"][0], T["end"][0] + 0.4))
    sun_moon(ctx, t, ck, x=200, y=470, a=sm_a)
    C.label(ctx, "disc", anchors.get("disc"), 860, 1060,
            p(t, TL.wt("discs", "discs,"), TL.wt("discs", "discs,") + 0.4) * (1 - p(t, T["day"][0], T["day"][0] + 0.3)), CYAN)
    C.slam_word(ctx, "1–2 CM", t, TL.wt("how", "one"), YEL, 180, 600, hold=TIN0 - TL.wt("how", "one") + 0.3, rot=0)
    C.slam_word(ctx, "WATER CUSHIONS", t, TL.wt("discs", "water"), CYAN, 104, 440, hold=T["discs"][1] - TL.wt("discs", "water") + 0.2, rot=0)
    C.slam_word(ctx, "SQUEEZED OUT", t, TL.wt("day", "squeeze"), YEL, 120, 440, hold=T["day"][1] - TL.wt("day", "squeeze") + 0.2, rot=0)
    C.slam_word(ctx, "SOAKED BACK UP", t, TL.wt("night", "soak"), CYAN, 104, 440, hold=T["night"][1] - TL.wt("night", "soak") + 0.2, rot=0)
    C.slam_word(ctx, "+ A FEW CM IN SPACE", t, TL.wt("space", "grow"), WHITE, 84, 560, hold=T["space"][1] - TL.wt("space", "grow") + 0.2, rot=0)
    C.slam_word(ctx, "MEASURE IN THE MORNING", t, TL.wt("end", "do"), GREEN, 80, 600, hold=TOTAL - TL.wt("end", "do") - 0.6, rot=0)
    if TIN1 - 0.3 < t < TOUT0:
        A.txt(ctx, "disc changes exaggerated for clarity", W / 2, 1440, 26, GREY, 0.8 * p(t, T["day"][0], T["day"][0] + 0.5) * (1 - p(t, TOUT0 - 0.4, TOUT0)), bold=False, shadow=False)
    C.captions(ctx, t, TL)
    return surf


BLUR = [(TIN0, TIN1), (TOUT0, TOUT1)]
if __name__ == "__main__":
    C.run(render, TOTAL, BLUR, sys.argv)
