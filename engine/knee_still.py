import cairo, math, random
import numpy as np

W, H = 1080, 1920
FONT = "Inter"
rnd = random.Random(11)


def rgba(ctx, c, a=1.0):
    ctx.set_source_rgba(c[0], c[1], c[2], a)


# ---------- textures ----------
def grain_pattern(scale, seed):
    rng = np.random.default_rng(seed)
    h, w = H // scale + 2, W // scale + 2
    n = rng.random((h, w))
    arr = np.zeros((h, w, 4), np.uint8)
    arr[..., 3] = (n * 255).astype(np.uint8)
    arr = np.ascontiguousarray(arr)
    surf = cairo.ImageSurface.create_for_data(memoryview(arr), cairo.FORMAT_ARGB32, w, h)
    pat = cairo.SurfacePattern(surf)
    m = cairo.Matrix(); m.scale(1 / scale, 1 / scale)
    pat.set_matrix(m); pat.set_filter(cairo.FILTER_BILINEAR); pat.set_extend(cairo.EXTEND_REPEAT)
    return pat, surf, arr


G_FINE = grain_pattern(2, 1)
G_COARSE = grain_pattern(14, 2)
G_MID = grain_pattern(5, 3)


def textured(ctx, path, light, dark, gx0, gy0, gx1, gy1, pores=0, pore_area=None,
             edge=(0.25, 0.17, 0.10), inner=0.35, grain=0.22, spec=None, cyl=False):
    path(ctx)
    g = cairo.LinearGradient(gx0, gy0, gx1, gy1)
    if cyl:
        g.add_color_stop_rgb(0, *dark)
        g.add_color_stop_rgb(0.38, *light)
        g.add_color_stop_rgb(1, *dark)
    else:
        g.add_color_stop_rgb(0, *light)
        g.add_color_stop_rgb(1, *dark)
    ctx.set_source(g); ctx.fill()
    ctx.save(); path(ctx); ctx.clip()
    rgba(ctx, (0.40, 0.25, 0.10), grain); ctx.mask(G_COARSE[0])
    rgba(ctx, (0.35, 0.22, 0.10), grain * 0.7); ctx.mask(G_MID[0])
    rgba(ctx, (0.30, 0.20, 0.10), grain * 0.4); ctx.mask(G_FINE[0])
    if pores and pore_area:
        x0, y0, x1, y1 = pore_area
        for _ in range(pores):
            x, y = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
            r = rnd.uniform(1.2, 5)
            ctx.save(); ctx.translate(x, y); ctx.scale(1, rnd.uniform(0.5, 1.2))
            ctx.arc(0, 0, r, 0, 2 * math.pi); ctx.restore()
            rgba(ctx, (0.50, 0.32, 0.15), rnd.uniform(0.08, 0.28)); ctx.fill()
    # smooth inner shadow
    for w in range(180, 0, -12):
        path(ctx); rgba(ctx, (0.12, 0.06, 0.03), 0.022 * inner / 0.35); ctx.set_line_width(w); ctx.stroke()
    if spec:
        sx, sy, sr, sa = spec
        rg = cairo.RadialGradient(sx, sy, 0, sx, sy, sr)
        rg.add_color_stop_rgba(0, 1, 1, 0.97, sa)
        rg.add_color_stop_rgba(1, 1, 1, 0.97, 0)
        ctx.set_source(rg); ctx.paint()
    ctx.restore()
    path(ctx); rgba(ctx, edge, 0.6); ctx.set_line_width(2.2); ctx.stroke()


def soft_shadow(ctx, path, dx, dy, a=0.35, spread=40):
    ctx.save(); ctx.translate(dx, dy)
    for w in range(spread, 0, -4):
        path(ctx); rgba(ctx, (0, 0, 0), a / (spread / 4) * 1.4); ctx.set_line_width(w); ctx.stroke_preserve()
        ctx.new_path()
    path(ctx); rgba(ctx, (0, 0, 0), a); ctx.fill()
    ctx.restore()


BONE_L = (0.97, 0.90, 0.74)
BONE_D = (0.78, 0.62, 0.40)
CART_L = (0.93, 0.96, 0.99)
CART_D = (0.66, 0.74, 0.84)
LIG_L = (0.98, 0.96, 0.92)
LIG_D = (0.78, 0.74, 0.68)
MUS_L = (0.82, 0.30, 0.22)
MUS_D = (0.42, 0.09, 0.07)


# ---------- shapes ----------
def femur(c):
    c.move_to(428, 120)
    c.line_to(430, 560)
    c.curve_to(400, 640, 300, 690, 266, 800)
    c.curve_to(240, 880, 290, 965, 380, 978)
    c.curve_to(440, 986, 488, 965, 500, 935)
    c.curve_to(508, 900, 515, 868, 540, 866)
    c.curve_to(566, 868, 574, 900, 580, 935)
    c.curve_to(594, 968, 650, 990, 712, 982)
    c.curve_to(806, 970, 846, 890, 822, 800)
    c.curve_to(796, 692, 684, 640, 652, 560)
    c.line_to(654, 120)
    c.close_path()


def notch(c):
    c.move_to(497, 960)
    c.curve_to(505, 905, 512, 872, 540, 870)
    c.curve_to(568, 872, 575, 905, 583, 960)
    c.curve_to(560, 975, 520, 975, 497, 960)
    c.close_path()


def femur_cart(c):
    c.move_to(350, 770)
    c.curve_to(400, 718, 476, 716, 540, 738)
    c.curve_to(604, 716, 680, 718, 732, 770)
    c.curve_to(786, 826, 800, 900, 752, 948)
    c.curve_to(712, 978, 640, 978, 600, 950)
    c.curve_to(584, 926, 576, 892, 540, 882)
    c.curve_to(504, 892, 496, 926, 480, 950)
    c.curve_to(440, 976, 368, 976, 328, 946)
    c.curve_to(284, 902, 296, 826, 350, 770)
    c.close_path()


PCX, PCY, PRX, PRY = 540, 1075, 318, 98


def tibia_body(c):
    c.move_to(PCX - PRX, PCY)
    c.curve_to(214, 1140, 250, 1215, 330, 1262)
    c.curve_to(400, 1300, 438, 1360, 444, 1460)
    c.line_to(452, 1940)
    c.line_to(628, 1940)
    c.line_to(636, 1460)
    c.curve_to(642, 1360, 690, 1295, 760, 1258)
    c.curve_to(840, 1212, 866, 1140, PCX + PRX, PCY)
    # front half of plateau ellipse back to start
    c.save(); c.translate(PCX, PCY); c.scale(PRX / 100, PRY / 100)
    c.arc(0, 0, 100, 0, math.pi)
    c.restore()
    c.close_path()


def plateau_top(c):
    c.save(); c.translate(PCX, PCY); c.scale(PRX / 100, PRY / 100)
    c.arc(0, 0, 100, 0, 2 * math.pi); c.restore()


def ell(c, cx, cy, rx, ry):
    c.save(); c.translate(cx, cy); c.scale(rx / 100, ry / 100)
    c.arc(0, 0, 100, 0, 2 * math.pi); c.restore()


def fibula(c):
    c.move_to(176, 1215)
    c.curve_to(170, 1170, 230, 1150, 262, 1180)
    c.curve_to(285, 1205, 268, 1250, 246, 1278)
    c.curve_to(238, 1300, 236, 1360, 238, 1420)
    c.line_to(240, 1940)
    c.line_to(198, 1940)
    c.line_to(200, 1420)
    c.curve_to(202, 1340, 196, 1290, 186, 1262)
    c.curve_to(178, 1245, 176, 1230, 176, 1215)
    c.close_path()


def band(pts_l, pts_r):
    def f(c):
        c.move_to(*pts_l[0])
        c.curve_to(*pts_l[1], *pts_l[2], *pts_l[3])
        c.line_to(*pts_r[3])
        c.curve_to(*pts_r[2], *pts_r[1], *pts_r[0])
        c.close_path()
    return f


def fibers(ctx, path, a_pts, b_pts, n, col, alpha, lw=1.6):
    """strokes interpolated between two bezier edges (a, b), clipped to path"""
    ctx.save(); path(ctx); ctx.clip()
    for i in range(n + 1):
        k = i / n + rnd.uniform(-0.3, 0.3) / n
        pts = [(a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k) for a, b in zip(a_pts, b_pts)]
        ctx.move_to(*pts[0]); ctx.curve_to(*pts[1], *pts[2], *pts[3])
        rgba(ctx, col, alpha * rnd.uniform(0.5, 1.0)); ctx.set_line_width(lw * rnd.uniform(0.6, 1.4)); ctx.stroke()
    ctx.restore()


def ligament(ctx, L, R, n=14):
    path = band(L, R)
    soft_shadow(ctx, path, 6, 8, 0.25, 24)
    textured(ctx, path, LIG_L, LIG_D, L[1][0], L[1][1], R[1][0], R[1][1], inner=0.15, grain=0.06,
             edge=(0.45, 0.40, 0.35), cyl=True)
    fibers(ctx, path, L, R, n, (0.55, 0.50, 0.45), 0.35)
    fibers(ctx, path, L, R, n // 2, (1, 1, 1), 0.35, 1.2)


def muscle(ctx, L, R, n=40):
    path = band(L, R)
    textured(ctx, path, MUS_L, MUS_D, L[1][0], L[1][1], R[1][0], R[1][1], inner=0.5, grain=0.08,
             edge=(0.25, 0.04, 0.03), cyl=True)
    fibers(ctx, path, L, R, n, (1.0, 0.62, 0.52), 0.35, 1.8)
    fibers(ctx, path, L, R, n, (0.25, 0.03, 0.02), 0.35, 1.4)


def meniscus(ctx, cx, cy, rx, ry, a0, a1, w=40, depth=14):
    d = math.pi / 180

    def ring(c, drx=0.0, dry=0.0, dy=0.0):
        c.save(); c.translate(cx, cy + dy); c.scale((rx + drx) / 100, (ry + dry) / 100)
        c.arc(0, 0, 100, a0 * d, a1 * d); c.restore()

    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    # contact shadow on the plateau
    for k in range(6):
        ring(ctx, 4, 2, depth + 6); rgba(ctx, (0.1, 0.06, 0.03), 0.06)
        ctx.set_line_width(w + 30 - k * 5); ctx.stroke()
    # outer side wall (thick, peripheral edge of the wedge)
    ring(ctx, 2, 1, depth); rgba(ctx, (0.55, 0.58, 0.64)); ctx.set_line_width(w); ctx.stroke()
    ring(ctx, 2, 1, depth * 0.55); rgba(ctx, (0.70, 0.73, 0.78)); ctx.set_line_width(w); ctx.stroke()
    # sloping top surface: outer (high, lit) -> inner (thin, falling away)
    n = 9
    for i in range(n):
        f = i / (n - 1)
        off = (0.5 - f) * w * 0.92
        col = tuple(a + (b - a) * f for a, b in zip((0.95, 0.96, 0.98), (0.72, 0.77, 0.85)))
        ring(ctx, off, off * ry / rx, 0)
        rgba(ctx, col); ctx.set_line_width(w / n * 1.6); ctx.stroke()
    # specular rim
    ring(ctx, w * 0.36, w * 0.36 * ry / rx, -1)
    rgba(ctx, (1, 1, 1), 0.85); ctx.set_line_width(3); ctx.stroke()
    ring(ctx, -w * 0.48, -w * 0.48 * ry / rx, 0)
    rgba(ctx, (0.40, 0.45, 0.55), 0.6); ctx.set_line_width(2); ctx.stroke()


def label(ctx, s, tx, ty, lx, ly):
    rgba(ctx, (1, 1, 1), 0.95)
    ctx.arc(tx, ty, 7, 0, 2 * math.pi); ctx.fill()
    ctx.set_line_width(3); ctx.move_to(tx, ty); ctx.line_to(lx, ly); ctx.stroke()
    ctx.arc(lx, ly, 4, 0, 2 * math.pi); ctx.fill()
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(36)
    e = ctx.text_extents(s)
    x = min(max(lx - e.x_advance / 2, 40), W - 40 - e.x_advance)
    y = ly - 18 if ly < ty else ly + 46
    for dy, col, a in ((3, (0, 0, 0), 0.85), (0, (1, 1, 1), 1)):
        ctx.move_to(x, y + dy); rgba(ctx, col, a); ctx.show_text(s)


def draw():
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)
    ctx.set_antialias(cairo.ANTIALIAS_BEST)
    g = cairo.RadialGradient(540, 1000, 50, 540, 1000, 1200)
    g.add_color_stop_rgb(0, 0.10, 0.12, 0.17)
    g.add_color_stop_rgb(1, 0.02, 0.02, 0.04)
    ctx.set_source(g); ctx.paint()

    # ---- muscles (behind) ----
    muscle(ctx, [(60, 80), (120, 400), (170, 700), (250, 860)], [(420, 80), (430, 400), (420, 600), (300, 760)], 46)  # vastus lateralis
    muscle(ctx, [(660, 80), (650, 420), (690, 660), (800, 850)], [(1020, 80), (1070, 540), (1020, 820), (850, 900)], 46)  # vastus medialis
    muscle(ctx, [(90, 1280), (150, 1500), (180, 1700), (190, 1940)], [(330, 1270), (420, 1420), (430, 1700), (430, 1940)], 40)  # tibialis anterior
    muscle(ctx, [(850, 1200), (900, 1450), (880, 1700), (820, 1940)], [(1050, 1150), (1070, 1450), (1040, 1700), (1000, 1940)], 40)  # gastrocnemius med.

    # push muscles back (depth)
    rgba(ctx, (0.02, 0.02, 0.04), 0.38); ctx.paint()
    # ---- fibula + tibia ----
    soft_shadow(ctx, fibula, 10, 10, 0.4, 40)
    textured(ctx, fibula, BONE_L, BONE_D, 176, 1300, 262, 1300, pores=60, pore_area=(170, 1160, 290, 1500), cyl=True)
    soft_shadow(ctx, tibia_body, 12, 14, 0.45, 60)
    textured(ctx, tibia_body, BONE_L, BONE_D, 300, 1400, 800, 1400, pores=420,
             pore_area=(230, 1080, 850, 1800), spec=(470, 1230, 230, 0.30), cyl=True)
    ctx.save(); tibia_body(ctx); ctx.clip()
    rg = cairo.RadialGradient(552, 1320, 10, 552, 1320, 120)
    rg.add_color_stop_rgba(0, 1, 0.97, 0.88, 0.40); rg.add_color_stop_rgba(1, 1, 0.97, 0.88, 0)
    ctx.set_source(rg); ctx.paint()
    # plateau rim shadow under the top surface
    ctx.save(); ctx.translate(0, 18); plateau_top(ctx); ctx.restore()
    rgba(ctx, (0.2, 0.1, 0.04), 0.35); ctx.fill()
    ctx.restore()
    textured(ctx, plateau_top, (0.96, 0.89, 0.74), (0.80, 0.67, 0.47), 300, 980, 800, 1170, pores=120,
             pore_area=(230, 990, 860, 1170), inner=0.3, grain=0.15)
    for cx, cy, rx, ry in ((405, 1082, 100, 42), (680, 1086, 112, 46)):
        textured(ctx, lambda c, a=(cx, cy, rx, ry): ell(c, *a), CART_L, CART_D, cx - rx, cy - ry, cx + rx, cy + ry,
                 inner=0.15, grain=0.04, edge=(0.50, 0.55, 0.62), spec=(cx - 25, cy - 15, 70, 0.55))
    # intercondylar eminence (tibial spines)
    ctx.move_to(508, 1096); ctx.curve_to(520, 1064, 528, 1050, 534, 1060)
    ctx.curve_to(540, 1066, 544, 1066, 550, 1058)
    ctx.curve_to(558, 1050, 566, 1066, 576, 1096); ctx.close_path()
    eg = cairo.LinearGradient(508, 1050, 576, 1096)
    eg.add_color_stop_rgb(0, 0.95, 0.88, 0.72); eg.add_color_stop_rgb(1, 0.70, 0.56, 0.38)
    ctx.set_source(eg); ctx.fill()

    # ---- menisci ----
    meniscus(ctx, 405, 1080, 124, 54, 32, 328, w=36)    # lateral: almost an O, horns close together
    meniscus(ctx, 682, 1084, 140, 60, -138, 138, w=38)  # medial: open C, wider

    # ---- PCL (posterior, behind ACL) ----
    ligament(ctx, [(550, 1070), (558, 1020), (568, 990), (574, 950)],
             [(592, 1074), (598, 1020), (598, 990), (592, 950)], 12)

    # ---- femur (sits on the back half of the menisci) ----
    ctx.save(); ctx.translate(0, 62)
    soft_shadow(ctx, femur, 8, 18, 0.55, 60)
    textured(ctx, femur, BONE_L, BONE_D, 430, 400, 655, 400, pores=420,
             pore_area=(250, 560, 840, 990), spec=(470, 620, 240, 0.30), cyl=True)
    soft_shadow(ctx, femur_cart, 0, 6, 0.25, 20)
    textured(ctx, femur_cart, CART_L, CART_D, 300, 760, 820, 760, inner=0.30, grain=0.04,
             edge=(0.45, 0.5, 0.58), spec=(420, 860, 120, 0.7), cyl=True)
    ctx.save(); femur_cart(ctx); ctx.clip()
    rg = cairo.RadialGradient(700, 880, 5, 700, 880, 110)
    rg.add_color_stop_rgba(0, 1, 1, 1, 0.45); rg.add_color_stop_rgba(1, 1, 1, 1, 0)
    ctx.set_source(rg); ctx.paint()
    # trochlear groove
    tgv = cairo.LinearGradient(500, 0, 580, 0)
    tgv.add_color_stop_rgba(0, 0.3, 0.35, 0.45, 0); tgv.add_color_stop_rgba(0.5, 0.3, 0.35, 0.45, 0.35)
    tgv.add_color_stop_rgba(1, 0.3, 0.35, 0.45, 0)
    ctx.set_source(tgv); ctx.rectangle(500, 690, 80, 200); ctx.fill()
    ctx.restore()
    ctx.save(); notch(ctx)
    ng = cairo.LinearGradient(540, 870, 540, 970)
    ng.add_color_stop_rgb(0, 0.10, 0.04, 0.03); ng.add_color_stop_rgb(1, 0.32, 0.13, 0.10)
    ctx.set_source(ng); ctx.fill(); ctx.restore()
    ctx.restore()

    # PCL femoral part in the notch (lateral wall of medial condyle = viewer right)
    ligament(ctx, [(554, 1022), (558, 990), (562, 962), (566, 944)],
             [(580, 1022), (582, 990), (580, 962), (576, 944)], 8)
    # ACL: anterior intercondylar area -> medial wall of lateral condyle (viewer left), twisting
    ligament(ctx, [(516, 1112), (504, 1060), (500, 1000), (512, 946)],
             [(568, 1104), (556, 1050), (538, 1000), (534, 950)], 18)

    # ---- collateral ligaments ----
    ligament(ctx, [(806, 826), (792, 960), (798, 1120), (808, 1300)],
             [(830, 826), (868, 960), (868, 1120), (830, 1300)], 22)   # MCL: broad, tapering
    ligament(ctx, [(266, 845), (252, 960), (232, 1080), (212, 1190)],
             [(286, 845), (272, 960), (252, 1080), (232, 1190)], 8)  # LCL -> fibular head

    # ---- grading / vignette ----
    vg = cairo.RadialGradient(540, 1050, 380, 540, 1050, 1150)
    vg.add_color_stop_rgba(0, 0, 0, 0, 0); vg.add_color_stop_rgba(1, 0, 0, 0, 0.85)
    ctx.set_source(vg); ctx.paint()
    tg = cairo.LinearGradient(0, 0, 0, 520)
    tg.add_color_stop_rgba(0, 0.02, 0.02, 0.04, 0.95); tg.add_color_stop_rgba(1, 0.02, 0.02, 0.04, 0)
    ctx.set_source(tg); ctx.rectangle(0, 0, W, 520); ctx.fill()
    bg = cairo.LinearGradient(0, 1500, 0, 1920)
    bg.add_color_stop_rgba(0, 0.02, 0.02, 0.04, 0); bg.add_color_stop_rgba(1, 0.02, 0.02, 0.04, 0.95)
    ctx.set_source(bg); ctx.rectangle(0, 1500, W, 420); ctx.fill()

    # ---- labels ----
    label(ctx, "voorste kruisband", 520, 1040, 250, 700)
    label(ctx, "binnenband", 830, 960, 880, 700)
    label(ctx, "buitenband", 252, 1000, 140, 1420)
    label(ctx, "buitenste meniscus", 315, 1125, 330, 1540)
    label(ctx, "binnenste meniscus", 790, 1130, 760, 1540)

    # ---- title ----
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(140)
    s = "MENISCUS"
    e = ctx.text_extents(s)
    for w_, a in ((22, 0.10), (10, 0.18)):
        ctx.move_to(540 - e.x_advance / 2, 330); ctx.text_path(s)
        rgba(ctx, (0.25, 0.85, 1.0), a); ctx.set_line_width(w_); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke()
    ctx.move_to(540 - e.x_advance / 2, 336); rgba(ctx, (0, 0, 0), 0.6); ctx.show_text(s)
    ctx.move_to(540 - e.x_advance / 2, 330); rgba(ctx, (1, 1, 1)); ctx.show_text(s)
    ctx.set_font_size(34); ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    s2 = "rechterknie van voren · licht gebogen · knieschijf weggelaten"
    e = ctx.text_extents(s2)
    ctx.move_to(540 - e.x_advance / 2, 400); rgba(ctx, (0.75, 0.78, 0.84)); ctx.show_text(s2)
    return surf


if __name__ == "__main__":
    draw().write_to_png("/home/claude/short/knee_still.png")
    print("ok")
