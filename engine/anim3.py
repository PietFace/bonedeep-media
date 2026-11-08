"""Bone Deep — English meniscus Short in detailed anatomy style.
Same scene timings/events as anim2 so music2.wav fits."""
import cairo, math, sys, os, subprocess, random
import anim2 as A
from anim2 import (W, H, FPS, SCENES, START, TOTAL, EVENTS, rgba, txt, slam, background, vignette,
                   camera, ringburst, arrow, font, WHITE, GREY, CYAN, RED, YEL, GREEN, BG0,
                   icon_bolt, icon_swell, icon_lock, icon_squat)
from anim import p, eo, eio, back, clamp, rrect, text_w

S = 2  # layer supersampling
HERE = os.path.dirname(os.path.abspath(__file__))
LAYERS = {n: os.path.join(HERE, f"layer_{n}.png") for n in ("back", "men", "fem")}

MED = (682, 1084, 140, 60, -138, 138)   # medial meniscus ellipse (cx, cy, rx, ry, a0, a1)
LAT = (405, 1080, 124, 54, 32, 328)


# ---------------- pre-render static anatomy layers ----------------
def build_layers():
    import knee_still as K
    import cairo as C

    def new():
        s = C.ImageSurface(C.FORMAT_ARGB32, W * S, H * S)
        c = C.Context(s); c.scale(S, S); c.set_antialias(C.ANTIALIAS_BEST)
        return s, c

    # back: muscles + tibia/fibula/plateau
    s, ctx = new()
    K.muscle(ctx, [(60, 80), (120, 400), (170, 700), (250, 860)], [(420, 80), (430, 400), (420, 600), (300, 760)], 46)
    K.muscle(ctx, [(660, 80), (650, 420), (690, 660), (800, 850)], [(1020, 80), (1070, 540), (1020, 820), (850, 900)], 46)
    K.muscle(ctx, [(90, 1280), (150, 1500), (180, 1700), (190, 1940)], [(330, 1270), (420, 1420), (430, 1700), (430, 1940)], 40)
    K.muscle(ctx, [(850, 1200), (900, 1450), (880, 1700), (820, 1940)], [(1050, 1150), (1070, 1450), (1040, 1700), (1000, 1940)], 40)
    ctx.set_operator(C.OPERATOR_ATOP); K.rgba(ctx, (0.02, 0.02, 0.04), 0.38); ctx.paint(); ctx.set_operator(C.OPERATOR_OVER)
    K.soft_shadow(ctx, K.fibula, 10, 10, 0.4, 40)
    K.textured(ctx, K.fibula, K.BONE_L, K.BONE_D, 176, 1300, 262, 1300, pores=60, pore_area=(170, 1160, 290, 1500), cyl=True)
    K.soft_shadow(ctx, K.tibia_body, 12, 14, 0.45, 60)
    K.textured(ctx, K.tibia_body, K.BONE_L, K.BONE_D, 300, 1400, 800, 1400, pores=420,
               pore_area=(230, 1080, 850, 1800), spec=(470, 1230, 230, 0.30), cyl=True)
    ctx.save(); K.tibia_body(ctx); ctx.clip()
    rg = C.RadialGradient(552, 1320, 10, 552, 1320, 120)
    rg.add_color_stop_rgba(0, 1, 0.97, 0.88, 0.40); rg.add_color_stop_rgba(1, 1, 0.97, 0.88, 0)
    ctx.set_source(rg); ctx.paint()
    ctx.save(); ctx.translate(0, 18); K.plateau_top(ctx); ctx.restore()
    K.rgba(ctx, (0.2, 0.1, 0.04), 0.35); ctx.fill()
    ctx.restore()
    K.textured(ctx, K.plateau_top, (0.96, 0.89, 0.74), (0.80, 0.67, 0.47), 300, 980, 800, 1170, pores=120,
               pore_area=(230, 990, 860, 1170), inner=0.3, grain=0.15)
    for cx, cy, rx, ry in ((405, 1082, 100, 42), (680, 1086, 112, 46)):
        K.textured(ctx, lambda c, a=(cx, cy, rx, ry): K.ell(c, *a), K.CART_L, K.CART_D, cx - rx, cy - ry, cx + rx, cy + ry,
                   inner=0.15, grain=0.04, edge=(0.50, 0.55, 0.62), spec=(cx - 25, cy - 15, 70, 0.55))
    ctx.move_to(508, 1096); ctx.curve_to(520, 1064, 528, 1050, 534, 1060)
    ctx.curve_to(540, 1066, 544, 1066, 550, 1058)
    ctx.curve_to(558, 1050, 566, 1066, 576, 1096); ctx.close_path()
    eg = C.LinearGradient(508, 1050, 576, 1096)
    eg.add_color_stop_rgb(0, 0.95, 0.88, 0.72); eg.add_color_stop_rgb(1, 0.70, 0.56, 0.38)
    ctx.set_source(eg); ctx.fill()
    s.write_to_png(LAYERS["back"])

    # menisci + tibial part of PCL
    s, ctx = new()
    K.meniscus(ctx, 405, 1080, 124, 54, 32, 328, w=36)
    K.meniscus(ctx, 682, 1084, 140, 60, -138, 138, w=38)
    K.ligament(ctx, [(550, 1070), (558, 1020), (568, 990), (574, 950)],
               [(592, 1074), (598, 1020), (598, 990), (592, 950)], 12)
    s.write_to_png(LAYERS["men"])

    # femur + cruciates + collaterals
    s, ctx = new()
    ctx.save(); ctx.translate(0, 62)
    K.soft_shadow(ctx, K.femur, 8, 18, 0.55, 60)
    K.textured(ctx, K.femur, K.BONE_L, K.BONE_D, 430, 400, 655, 400, pores=420,
               pore_area=(250, 560, 840, 990), spec=(470, 620, 240, 0.30), cyl=True)
    K.soft_shadow(ctx, K.femur_cart, 0, 6, 0.25, 20)
    K.textured(ctx, K.femur_cart, K.CART_L, K.CART_D, 300, 760, 820, 760, inner=0.30, grain=0.04,
               edge=(0.45, 0.5, 0.58), spec=(420, 860, 120, 0.7), cyl=True)
    ctx.save(); K.femur_cart(ctx); ctx.clip()
    rg = C.RadialGradient(700, 880, 5, 700, 880, 110)
    rg.add_color_stop_rgba(0, 1, 1, 1, 0.45); rg.add_color_stop_rgba(1, 1, 1, 1, 0)
    ctx.set_source(rg); ctx.paint()
    tgv = C.LinearGradient(500, 0, 580, 0)
    tgv.add_color_stop_rgba(0, 0.3, 0.35, 0.45, 0); tgv.add_color_stop_rgba(0.5, 0.3, 0.35, 0.45, 0.35)
    tgv.add_color_stop_rgba(1, 0.3, 0.35, 0.45, 0)
    ctx.set_source(tgv); ctx.rectangle(500, 690, 80, 200); ctx.fill()
    ctx.restore()
    ctx.save(); K.notch(ctx)
    ng = C.LinearGradient(540, 870, 540, 970)
    ng.add_color_stop_rgb(0, 0.10, 0.04, 0.03); ng.add_color_stop_rgb(1, 0.32, 0.13, 0.10)
    ctx.set_source(ng); ctx.fill(); ctx.restore()
    ctx.restore()
    K.ligament(ctx, [(554, 1022), (558, 990), (562, 962), (566, 944)],
               [(580, 1022), (582, 990), (580, 962), (576, 944)], 8)
    K.ligament(ctx, [(516, 1112), (504, 1060), (500, 1000), (512, 946)],
               [(568, 1104), (556, 1050), (538, 1000), (534, 950)], 18)
    K.ligament(ctx, [(806, 826), (792, 960), (798, 1120), (808, 1300)],
               [(830, 826), (868, 960), (868, 1120), (830, 1300)], 22)
    K.ligament(ctx, [(266, 845), (252, 960), (232, 1080), (212, 1190)],
               [(286, 845), (272, 960), (252, 1080), (232, 1190)], 8)
    s.write_to_png(LAYERS["fem"])


_L = {}


def layer(n):
    if n not in _L:
        _L[n] = cairo.ImageSurface.create_from_png(LAYERS[n])
    return _L[n]


def paint_layer(ctx, n, a=1.0):
    ctx.save(); ctx.scale(1 / S, 1 / S)
    ctx.set_source_surface(layer(n), 0, 0)
    ctx.get_source().set_filter(cairo.FILTER_GOOD)
    ctx.paint_with_alpha(a)
    ctx.restore()


def ring_path(ctx, m, drx=0, dry=0):
    cx, cy, rx, ry, a0, a1 = m
    d = math.pi / 180
    ctx.save(); ctx.translate(cx, cy); ctx.scale((rx + drx) / 100, (ry + dry) / 100)
    ctx.arc(0, 0, 100, a0 * d, a1 * d); ctx.restore()


def men_glow(ctx, m, g, col=CYAN):
    if g <= 0:
        return
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for w, a in ((110, 0.06), (75, 0.10), (50, 0.16)):
        ring_path(ctx, m); rgba(ctx, col, a * g); ctx.set_line_width(w); ctx.stroke()
    ring_path(ctx, m); rgba(ctx, col, 0.30 * g); ctx.set_line_width(36); ctx.stroke()


def tear_path(ctx, k):
    cx, cy, rx, ry, _, _ = MED
    d = math.pi / 180
    a0, a1 = 48 * d, 118 * d
    end = a0 + (a1 - a0) * k
    n = 34
    first = True
    for i in range(n + 1):
        ang = a0 + (a1 - a0) * i / n
        if ang > end:
            break
        j = 0.035 * math.sin(i * 2.9) * (1 if i % 2 else -1)
        x = cx + rx * (1 + j) * math.cos(ang)
        y = cy + ry * (1 + j * 1.6) * math.sin(ang) - 2
        if first:
            ctx.move_to(x, y); first = False
        else:
            ctx.line_to(x, y)


def draw_tear(ctx, k, sparks_t=None):
    if k <= 0:
        return
    ctx.set_line_join(cairo.LINE_JOIN_MITER); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for w, a, col in ((34, 0.22, RED), (18, 0.45, RED), (7, 1.0, (0.30, 0.0, 0.02)), (2.5, 0.9, (1.0, 0.45, 0.4))):
        tear_path(ctx, k); rgba(ctx, col, a); ctx.set_line_width(w); ctx.stroke()
    if sparks_t is not None and 0 <= sparks_t < 0.7:
        cx, cy, rx, ry, _, _ = MED
        r = random.Random(5)
        for i in range(32):
            ang = r.uniform(50, 116) * math.pi / 180
            x0, y0 = cx + rx * math.cos(ang), cy + ry * math.sin(ang)
            dirx, diry = math.cos(ang + r.uniform(-0.8, 0.8)), math.sin(ang + r.uniform(-0.8, 0.8)) * 1.4
            sp = r.uniform(180, 520)
            r0 = sp * sparks_t; r1 = r0 + 26 + r.uniform(0, 40)
            rgba(ctx, YEL if i % 3 else WHITE, 1 - sparks_t / 0.7)
            ctx.set_line_width(4)
            ctx.move_to(x0 + dirx * r0, y0 + diry * r0); ctx.line_to(x0 + dirx * r1, y0 + diry * r1); ctx.stroke()


def knee(ctx, zoom=1.0, focus=(540, 1000), dim=1.0, fdx=0.0, fdy=0.0, frot=0.0,
         glow=0.0, tear=0.0, sparks_t=None, extra=None):
    ctx.save()
    ctx.translate(W / 2, 1000); ctx.scale(zoom, zoom); ctx.translate(-focus[0], -focus[1])
    paint_layer(ctx, "back", dim)
    paint_layer(ctx, "men", dim)
    men_glow(ctx, LAT, glow * dim); men_glow(ctx, MED, glow * dim)
    draw_tear(ctx, tear, sparks_t)
    ctx.save()
    ctx.translate(540 + fdx, 760 + fdy); ctx.rotate(frot); ctx.translate(-540, -760)
    paint_layer(ctx, "fem", dim)
    ctx.restore()
    if extra:
        extra(ctx)
    ctx.restore()


def text_fade(ctx):
    tg = cairo.LinearGradient(0, 0, 0, 760)
    tg.add_color_stop_rgba(0, 0.02, 0.02, 0.04, 0.92); tg.add_color_stop_rgba(0.55, 0.02, 0.02, 0.04, 0.6)
    tg.add_color_stop_rgba(1, 0.02, 0.02, 0.04, 0)
    ctx.set_source(tg); ctx.rectangle(0, 0, W, 760); ctx.fill()
    bg = cairo.LinearGradient(0, 1500, 0, 1920)
    bg.add_color_stop_rgba(0, 0.02, 0.02, 0.04, 0); bg.add_color_stop_rgba(1, 0.02, 0.02, 0.04, 0.95)
    ctx.set_source(bg); ctx.rectangle(0, 1500, W, 420); ctx.fill()


def label(ctx, s, tx, ty, lx, ly, k, col=WHITE):
    if k <= 0:
        return
    rgba(ctx, col, k); ctx.arc(tx, ty, 8, 0, 2 * math.pi); ctx.fill()
    ex, ey = tx + (lx - tx) * eo(k), ty + (ly - ty) * eo(k)
    ctx.set_line_width(3.5); ctx.move_to(tx, ty); ctx.line_to(ex, ey); ctx.stroke()
    kk = p(k, 0.5, 1)
    if kk > 0:
        font(ctx, 40); e = ctx.text_extents(s)
        x = min(max(lx - e.x_advance / 2, 40), W - 40 - e.x_advance)
        txt(ctx, s, x, ly + 50, 40, col, kk, align="l")


# ---------------- scenes ----------------
def s_cold(ctx, t, d):
    ramp = eo(p(t, 0, 0.4)) * (1 - p(t, 1.3, 1.5))
    fdx = 9 * math.sin(t * 10) * ramp
    frot = 0.02 * math.sin(t * 10 + 0.5) * ramp
    tear = eo(p(t, 1.3, 1.55))
    zoom = 2.0 + 0.15 * eo(p(t, 1.3, 3.2))
    knee(ctx, zoom, (700, 1105), fdx=fdx, frot=frot, glow=0.35 + 0.5 * tear * (0.6 + 0.4 * math.sin(t * 7)),
         tear=tear, sparks_t=(t - 1.3) if t >= 1.3 else None)
    vignette(ctx, red=0.5 * p(t, 0, 1.3) * (1 - p(t, 1.5, 3)))
    text_fade(ctx)
    slam(ctx, ["ONE WRONG", "TWIST…"], 420, t, 0.1, 130, out_t=1.2)
    slam(ctx, ["*MENISCUS", "*TEAR"], 420, t, 1.4, 150, stagger=0.12)


def s_titel(ctx, t, d):
    z = 1.0 + 0.08 * t / d
    knee(ctx, z, (540, 1060), dim=0.45, glow=0.6 + 0.4 * math.sin(t * 6))
    vignette(ctx); text_fade(ctx)
    slam(ctx, ["What *really", "happens inside", "your ~knee?"], 440, t, 0.1, 120, stagger=0.09)


def s_anatomie(ctx, t, d):
    k = eio(p(t, 0.0, 1.3))
    zoom = 2.3 - 1.3 * k
    fx, fy = 540, 1090 - 70 * k
    ig = p(t, 1.3, 1.6)
    pulse = (0.6 + 0.4 * math.sin((t - 1.3) * 6)) if t > 1.3 else 0

    def extra(c):
        ringburst(c, LAT[0], LAT[1], t - 1.3, CYAN, 220)
        ringburst(c, MED[0], MED[1], t - 1.3, CYAN, 220)
        label(c, "outer meniscus", 300, 1130, 250, 1430, p(t, 3.0, 3.6), CYAN)
        label(c, "inner meniscus", 790, 1132, 800, 1430, p(t, 3.2, 3.8), CYAN)
    knee(ctx, zoom, (fx, fy), glow=pulse * ig, extra=extra)
    vignette(ctx); text_fade(ctx)
    slam(ctx, ["^2 menisci"], 420, t, 1.4, 140)
    slam(ctx, ["your knee's ~shock ~absorbers"], 560, t, 2.2, 66, stagger=0.07)


def s_functie(ctx, t, d):
    hits = [te for te, _ in EVENTS["functie"]]
    comp = 0
    for te in hits:
        if t >= te:
            comp = max(comp, math.exp(-(t - te) * 6))

    def extra(c):
        for te in hits:
            ringburst(c, LAT[0], LAT[1] + 10, t - te, RED, 180, 0.5)
            ringburst(c, MED[0], MED[1] + 10, t - te, RED, 180, 0.5)
        if t >= hits[0] - 0.2:
            last = max([te for te in hits if te <= t + 0.2] or [hits[0]])
            drop = eo(p(t - last, -0.2, 0.0))
            y2 = 900 + 14 * comp
            off = (1 - drop) * -120
            arrow(c, 540, y2 - 190 + off, 540, y2 + off, RED, 1, lw=24, head=64)
    knee(ctx, 1.0, (540, 1040), fdy=12 * comp, glow=0.3 + 0.7 * comp, extra=extra)
    vignette(ctx); text_fade(ctx)
    if t > 0.5:
        n = int(round(50 * eo(p(t, 0.5, 1.5))))
        ka = eo(p(t, 0.5, 0.7))
        ctx.save(); s = 1 + 0.25 * comp
        ctx.translate(W / 2, 440); ctx.scale(s, s); ctx.translate(-W / 2, -440)
        for gw, ga in ((24, 0.08), (12, 0.15)):
            font(ctx, 190); e = ctx.text_extents(f"± {n}%")
            ctx.move_to(W / 2 - e.x_advance / 2, 500); ctx.text_path(f"± {n}%")
            rgba(ctx, YEL, ga * ka); ctx.set_line_width(gw); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke()
        txt(ctx, f"± {n}%", W / 2, 500, 190, YEL, ka)
        ctx.restore()
    slam(ctx, ["of the load goes through them"], 600, t, 1.0, 56, stagger=0.06)
    slam(ctx, ["with a bent knee: ^even ^more"], 680, t, 3.2, 56, stagger=0.06)


def s_scheur(ctx, t, d):
    tear_t = 4.75
    zin = eio(p(t, 3.0, 4.7))
    zoom = 1.0 + 0.75 * zin + (0.12 * eo(p(t, tear_t, 6.5)) if t > tear_t else 0)
    fx = 540 + 160 * zin
    fy = 1040 + 70 * zin
    tw = 0.0
    if 3.0 < t < tear_t:
        k = p(t, 3.0, 4.6)
        tw = (0.25 + 0.75 * k) * math.sin((t - 3.0) * (8 + 12 * k))
    fdx = 10 * tw
    frot = 0.025 * tw
    tear = eo(p(t, tear_t, tear_t + 0.25))

    def extra(c):
        if 3.1 < t < tear_t:
            a = eo(p(t, 3.1, 3.4))
            # twisting arrows around the joint (rotation about the leg's long axis)
            for side, ph in ((1, 0.0), (-1, math.pi)):
                c.save(); c.translate(540, 1060); c.scale(1, 0.24)
                a0 = ph + 0.3 + (t - 3.0) * 3.0 * side
                c.arc(0, 0, 450, a0, a0 + 1.5) if side > 0 else c.arc_negative(0, 0, 450, a0, a0 - 1.5)
                c.restore()
                rgba(c, WHITE, 0.85 * a); c.set_line_width(12); c.set_line_cap(cairo.LINE_CAP_ROUND); c.stroke()
                ae = a0 + (1.5 if side > 0 else -1.5)
                ex, ey = 540 + 450 * math.cos(ae), 1060 + 108 * math.sin(ae)
                tx, ty = -math.sin(ae) * side, math.cos(ae) * 0.24 * side
                nrm = math.hypot(tx, ty) or 1
                tx, ty = tx / nrm, ty / nrm
                arrow(c, ex - tx * 24, ey - ty * 24, ex + tx * 16, ey + ty * 16, WHITE, 0.85 * a, lw=2, head=44, glow=False)
    knee(ctx, zoom, (fx, fy), fdx=fdx, frot=frot, glow=0.3 + 0.6 * tear, tear=tear,
         sparks_t=(t - tear_t) if t >= tear_t else None, extra=extra)
    red = 0.8 * p(t, 3.0, 4.7) * (1 - p(t, tear_t + 0.3, tear_t + 1.5))
    if t >= tear_t:
        red += 0.6 * math.exp(-(t - tear_t) * 3)
    vignette(ctx, red=red); text_fade(ctx)
    slam(ctx, ["Your foot is ^planted…"], 430, t, 0.2, 80, out_t=1.45)
    slam(ctx, ["your knee is ^bent…"], 430, t, 1.6, 84, out_t=2.85)
    slam(ctx, ["and then you *TWIST"], 430, t, 3.0, 88, out_t=4.6)
    slam(ctx, ["*TEAR"], 470, t, tear_t + 0.05, 230)
    slam(ctx, ["after 40, often from", "^wear ^and ^tear too"], 600, t, 6.4, 56, stagger=0.06)


def s_klachten(ctx, t, d):
    items = [("PAIN", "on the inner or", "outer side of your knee", icon_bolt),
             ("SWELLING", "often appearing", "hours later", icon_swell),
             ("LOCKING", "your knee catches", "or gets stuck", icon_lock),
             ("OUCH!", "when squatting", "and twisting", icon_squat)]
    i = min(3, int(t // 2.0))
    lt = t - i * 2.0
    big, l1, l2, ic = items[i]
    k = back(p(lt, 0.05, 0.4))
    cx, cy = W / 2, 1120
    ctx.save(); ctx.translate(cx, cy); s = 1.3 - 0.3 * eo(p(lt, 0.05, 0.4))
    ctx.scale(s * k, s * k)
    for r, a in ((290, 0.06), (250, 0.10), (215, 0.16)):
        rgba(ctx, RED, a); ctx.arc(0, 0, r, 0, 2 * math.pi); ctx.fill()
    rgba(ctx, RED, 1); ctx.arc(0, 0, 185, 0, 2 * math.pi); ctx.fill()
    if ic is icon_swell:
        ic(ctx, 1.1, WHITE, lt)
    else:
        ctx.save()
        if ic is icon_bolt:
            ctx.rotate(0.05 * math.sin(lt * 30) * math.exp(-lt * 2))
        ic(ctx, 1.15, WHITE)
        ctx.restore()
    ctx.restore()
    ringburst(ctx, cx, cy, lt - 0.05, RED, 420, 0.7)
    vignette(ctx)
    slam(ctx, [big], 470, lt, 0.05, 170, base=RED)
    slam(ctx, [l1, l2], 600, lt, 0.35, 56, base=GREY)
    for j in range(4):
        rgba(ctx, RED if j <= i else (0.3, 0.32, 0.38), 1)
        ctx.arc(W / 2 - 75 + j * 50, 1500, 10, 0, 2 * math.pi); ctx.fill()


def s_slot(ctx, t, d):
    vignette(ctx)
    slam(ctx, ["BUT…"], 400, t, 0.1, 140)
    slam(ctx, ["+good +news"], 540, t, 0.9, 110)
    k = back(p(t, 1.2, 1.6))
    cx, cy = W / 2, 860
    if k > 0:
        ctx.save(); ctx.translate(cx, cy); ctx.scale(k, k)
        for r, a in ((190, 0.07), (160, 0.12), (138, 0.2)):
            rgba(ctx, GREEN, a); ctx.arc(0, 0, r, 0, 2 * math.pi); ctx.fill()
        rgba(ctx, GREEN, 1); ctx.arc(0, 0, 120, 0, 2 * math.pi); ctx.fill()
        kc = eo(p(t, 1.4, 1.8))
        pts = [(-52, 4), (-14, 42), (58, -36)]
        rgba(ctx, BG0, 1); ctx.set_line_width(26)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        L1 = math.dist(pts[0], pts[1]); L2 = math.dist(pts[1], pts[2]); L = (L1 + L2) * kc
        if L > 0:
            ctx.move_to(*pts[0])
            if L <= L1:
                f = L / L1
                ctx.line_to(pts[0][0] + (pts[1][0] - pts[0][0]) * f, pts[0][1] + (pts[1][1] - pts[0][1]) * f)
            else:
                ctx.line_to(*pts[1]); f = (L - L1) / L2
                ctx.line_to(pts[1][0] + (pts[2][0] - pts[1][0]) * f, pts[1][1] + (pts[2][1] - pts[1][1]) * f)
            ctx.stroke()
        ctx.restore()
        ringburst(ctx, cx, cy, t - 1.2, GREEN, 300, 0.7)
    slam(ctx, ["symptoms often improve", "with targeted +exercise +therapy"], 1140, t, 1.9, 54, stagger=0.05)
    slam(ctx, ["(especially wear-related tears)"], 1290, t, 2.8, 40, base=GREY)
    kn = eo(p(t, 3.4, 3.8))
    if kn > 0:
        y = 1380 + (1 - kn) * 40
        rgba(ctx, WHITE, kn); rrect(ctx, 130, y, W - 260, 140, 70); ctx.fill()
        txt(ctx, "Not sure? Get your knee checked", W / 2, y + 62, 42, BG0, kn, shadow=False)
        txt(ctx, "Next: your shoulder", W / 2, y + 112, 34, (0.1, 0.45, 0.4), kn, shadow=False)


FN = {"cold": s_cold, "titel": s_titel, "anatomie": s_anatomie, "functie": s_functie,
      "scheur": s_scheur, "klachten": s_klachten, "slot": s_slot}


def chrome(ctx, tg, name):
    rgba(ctx, WHITE, 0.12); rrect(ctx, 60, 110, W - 120, 10, 5); ctx.fill()
    rgba(ctx, RED if name != "slot" else GREEN, 1)
    rrect(ctx, 60, 110, max(10, (W - 120) * tg / TOTAL), 10, 5); ctx.fill()
    a = eo(p(tg, 3.2, 3.6))
    if a > 0:
        s = "WHAT HAPPENS INSIDE YOUR…"
        w = text_w(ctx, s, 30)
        rgba(ctx, WHITE, 0.12 * a); rrect(ctx, W / 2 - w / 2 - 26, 150, w + 52, 58, 29); ctx.fill()
        txt(ctx, s, W / 2, 190, 30, WHITE, 0.9 * a, shadow=False)
    if name == "slot":
        txt(ctx, "General information, not personal medical advice", W / 2, 262, 26, GREY, 0.8, bold=False, shadow=False)
    # brand bug
    txt(ctx, "BONE DEEP", W - 60, 1560, 30, WHITE, 0.55, align="r", shadow=False)


def frame(name, t, d):
    tg = START[name] + t
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)
    ctx.set_antialias(cairo.ANTIALIAS_BEST)
    tint = (0.04, 0.18, 0.17) if name == "slot" else None
    background(ctx, tg, tint)
    zoom, sx, sy, flash, fcol = camera(name, t)
    drift = 1 + 0.03 * t / d
    ctx.save()
    ctx.translate(W / 2 + sx, 1000 + sy); ctx.scale(zoom * drift, zoom * drift); ctx.translate(-W / 2, -1000)
    ctx.push_group()
    FN[name](ctx, t, d)
    ctx.pop_group_to_source()
    fin = p(t, 0, 0.08) if name != "cold" else 1
    fout = 1 - p(t, d - 0.08, d)
    ctx.paint_with_alpha(min(fin, fout))
    ctx.restore()
    chrome(ctx, tg, name)
    if flash > 0:
        rgba(ctx, fcol, flash * (0.85 if fcol == WHITE else 0.5)); ctx.paint()
    return surf


def render_scene(idx, outdir):
    name, d = SCENES[idx]
    n = int(round(d * FPS))
    tmp = os.path.join(outdir, f"tmp_{idx}_{name}.mp4")
    fin = os.path.join(outdir, f"{idx}_{name}.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast",
           "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS), tmp]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(n):
        pr.stdin.write(bytes(frame(name, i / FPS, d).get_data()))
    pr.stdin.close()
    if pr.wait() == 0:
        os.replace(tmp, fin)
    print("done", fin, flush=True)


if __name__ == "__main__":
    if sys.argv[1] == "layers":
        build_layers()
    elif sys.argv[1] == "still":
        name, t = sys.argv[2], float(sys.argv[3])
        frame(name, t, dict(SCENES)[name]).write_to_png(sys.argv[4])
    else:
        render_scene(int(sys.argv[2]), sys.argv[3])
