import cairo, math, sys, subprocess, os

W, H, FPS = 1080, 1920, 30

BG = (0.965, 0.953, 0.933)
INK = (0.11, 0.15, 0.20)
MUTED = (0.42, 0.45, 0.50)
TEAL = (0.05, 0.49, 0.48)
BONE = (0.94, 0.90, 0.83)
BONE_EDGE = (0.50, 0.45, 0.38)
MEN = (0.33, 0.66, 0.76)
MEN_D = (0.16, 0.45, 0.56)
RED = (0.88, 0.31, 0.25)
CARD = (1, 1, 1)
FONT = "Inter"

# scene list: (name, duration)
SCENES = [("hook", 4.5), ("anatomie", 7.5), ("functie", 7.0),
          ("scheur", 8.5), ("klachten", 8.0), ("slot", 7.5)]
TOTAL = sum(d for _, d in SCENES)


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def p(t, a, b):
    return clamp((t - a) / (b - a))


def eo(x):  # ease out cubic
    x = clamp(x)
    return 1 - (1 - x) ** 3


def eio(x):
    x = clamp(x)
    return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2


def back(x):  # ease out back
    x = clamp(x)
    c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def rgba(ctx, c, a=1.0):
    ctx.set_source_rgba(c[0], c[1], c[2], a)


def text(ctx, s, x, y, size, color=INK, a=1.0, bold=True, align="c"):
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL,
                         cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)
    ext = ctx.text_extents(s)
    if align == "c":
        xx = x - ext.x_advance / 2
    elif align == "r":
        xx = x - ext.x_advance
    else:
        xx = x
    ctx.move_to(xx, y)
    rgba(ctx, color, a)
    ctx.show_text(s)
    return ext.x_advance


def text_w(ctx, s, size, bold=True):
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL,
                         cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)
    return ctx.text_extents(s).x_advance


def rrect(ctx, x, y, w, h, r):
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    ctx.close_path()


def caption(ctx, lines, y, t, start, size=64, color=INK, hl=None, lh=1.22):
    """Lines rise + fade in, staggered. hl: dict line_index->color"""
    for i, ln in enumerate(lines):
        k = eo(p(t, start + i * 0.12, start + i * 0.12 + 0.5))
        if k <= 0:
            continue
        c = (hl or {}).get(i, color)
        text(ctx, ln, W / 2, y + i * size * lh + (1 - k) * 30, size, c, k)


def arrow(ctx, x1, y1, x2, y2, color, a=1.0, lw=10, head=28):
    rgba(ctx, color, a)
    ctx.set_line_width(lw)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ang = math.atan2(y2 - y1, x2 - x1)
    ctx.move_to(x1, y1)
    ctx.line_to(x2 - math.cos(ang) * head * 0.6, y2 - math.sin(ang) * head * 0.6)
    ctx.stroke()
    ctx.move_to(x2, y2)
    ctx.line_to(x2 - head * math.cos(ang - 0.45), y2 - head * math.sin(ang - 0.45))
    ctx.line_to(x2 - head * math.cos(ang + 0.45), y2 - head * math.sin(ang + 0.45))
    ctx.close_path()
    ctx.fill()


# ---------------- knee, front view (local units) ----------------
def femur_path(ctx):
    ctx.move_to(-78, -620)
    ctx.line_to(-78, -280)
    ctx.curve_to(-82, -190, -186, -150, -182, -64)
    ctx.curve_to(-180, -14, -150, 8, -104, 8)
    ctx.curve_to(-62, 8, -38, -8, -28, -40)
    ctx.curve_to(-16, -62, 16, -62, 28, -40)
    ctx.curve_to(38, -8, 62, 8, 104, 8)
    ctx.curve_to(150, 8, 180, -14, 182, -64)
    ctx.curve_to(186, -150, 82, -190, 78, -280)
    ctx.line_to(78, -620)
    ctx.close_path()


def tibia_path(ctx):
    ctx.move_to(-192, 44)
    ctx.line_to(-48, 44)
    ctx.curve_to(-30, 44, -22, 22, -10, 22)
    ctx.curve_to(2, 22, 8, 36, 14, 30)
    ctx.curve_to(22, 22, 30, 44, 48, 44)
    ctx.line_to(192, 44)
    ctx.curve_to(198, 70, 192, 124, 150, 168)
    ctx.curve_to(102, 212, 84, 236, 84, 300)
    ctx.line_to(84, 620)
    ctx.line_to(-84, 620)
    ctx.line_to(-84, 300)
    ctx.curve_to(-84, 236, -102, 212, -150, 168)
    ctx.curve_to(-192, 124, -198, 70, -192, 44)
    ctx.close_path()


def fibula_path(ctx):
    ctx.move_to(-236, 170)
    ctx.curve_to(-250, 130, -214, 108, -192, 128)
    ctx.curve_to(-176, 142, -178, 180, -196, 210)
    ctx.line_to(-196, 620)
    ctx.line_to(-232, 620)
    ctx.line_to(-232, 210)
    ctx.close_path()


def men_wedge(ctx, side, squash=0.0):
    s = side
    ctx.move_to(s * 204, 44)
    ctx.line_to(s * (100 - 12 * squash), 44)
    ctx.curve_to(s * 140, 34 + 3 * squash, s * 178, 16 + 4 * squash, s * (200 + 6 * squash), 6 + 4 * squash)
    ctx.curve_to(s * (210 + 6 * squash), 18, s * (210 + 4 * squash), 34, s * 204, 44)
    ctx.close_path()


def knee_front(ctx, cx, cy, sc, bone_a=1.0, men_a=1.0, men_pulse=0.0,
               femur_dy=0.0, squash=0.0, clip_h=None):
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(sc, sc)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    # tibia + fibula
    for path in (fibula_path, tibia_path):
        path(ctx)
        rgba(ctx, BONE, bone_a); ctx.fill_preserve()
        rgba(ctx, BONE_EDGE, bone_a); ctx.set_line_width(5); ctx.stroke()
    # tibial cartilage
    rgba(ctx, (0.80, 0.86, 0.90), bone_a)
    ctx.rectangle(-186, 40, 372, 6); ctx.fill()
    # femur
    ctx.save(); ctx.translate(0, femur_dy)
    femur_path(ctx)
    rgba(ctx, BONE, bone_a); ctx.fill_preserve()
    rgba(ctx, BONE_EDGE, bone_a); ctx.set_line_width(5); ctx.stroke()
    ctx.restore()
    # menisci
    if men_a > 0:
        for side in (-1, 1):
            if men_pulse > 0:
                men_wedge(ctx, side, squash)
                rgba(ctx, MEN, men_a * 0.35 * men_pulse)
                ctx.set_line_width(30); ctx.stroke()
            men_wedge(ctx, side, squash)
            rgba(ctx, MEN, men_a); ctx.fill_preserve()
            rgba(ctx, MEN_D, men_a); ctx.set_line_width(4); ctx.stroke()
    ctx.restore()


# ---------------- tibial plateau, top view ----------------
def plateau(ctx, cx, cy, sc, a=1.0, tear=0.0, glow=0.0, femur_rot=None, shake=0.0):
    ctx.save()
    ctx.translate(cx + shake, cy)
    ctx.scale(sc, sc)
    # plateau outline (kidney-ish)
    ctx.move_to(-300, 0)
    ctx.curve_to(-300, -150, -150, -190, 0, -150)
    ctx.curve_to(150, -190, 300, -150, 300, 0)
    ctx.curve_to(300, 150, 150, 180, 40, 170)
    ctx.curve_to(10, 200, -10, 200, -40, 170)
    ctx.curve_to(-150, 180, -300, 150, -300, 0)
    ctx.close_path()
    rgba(ctx, BONE, a); ctx.fill_preserve()
    rgba(ctx, BONE_EDGE, a); ctx.set_line_width(5); ctx.stroke()
    # cartilage zones
    for x0 in (-150, 150):
        ctx.save(); ctx.translate(x0, 0); ctx.scale(1, 1.05)
        ctx.arc(0, 0, 105, 0, 2 * math.pi); ctx.restore()
        rgba(ctx, (0.84, 0.89, 0.92), a); ctx.fill()

    def ring(x0, rx, ry, a0, a1, width, col):
        ctx.save(); ctx.translate(x0, 0); ctx.scale(rx / 100.0, ry / 100.0)
        ctx.arc(0, 0, 100, a0, a1)
        ctx.restore()
        rgba(ctx, col, a)
        ctx.set_line_width(width)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke()

    d = math.pi / 180
    # lateral (left, more O-shaped): opening to the right
    ring(-150, 128, 132, 52 * d, 308 * d, 64, MEN_D)
    ring(-150, 128, 132, 52 * d, 308 * d, 50, MEN)
    # medial (right, C-shaped, bigger): opening to the left
    ring(150, 140, 146, -125 * d, 125 * d, 64, MEN_D)
    ring(150, 140, 146, -125 * d, 125 * d, 50, MEN)

    if glow > 0:
        ctx.save(); ctx.translate(150, 0); ctx.scale(1.4, 1.46)
        ctx.arc(0, 0, 100, -55 * d, 55 * d); ctx.restore()
        rgba(ctx, RED, a * 0.28 * glow); ctx.set_line_width(80); ctx.stroke()

    if tear > 0:
        # jagged longitudinal tear along the medial meniscus
        n = 40
        a0, a1 = -50 * d, 50 * d
        end = a0 + (a1 - a0) * tear
        ctx.save(); ctx.translate(150, 0)
        first = True
        for i in range(n + 1):
            ang = a0 + (a1 - a0) * i / n
            if ang > end:
                break
            jig = 7 * math.sin(i * 2.7) * (1 if i % 2 else -1)
            r = 143 + jig
            x, y = math.cos(ang) * r, math.sin(ang) * r * 1.03
            if first:
                ctx.move_to(x, y); first = False
            else:
                ctx.line_to(x, y)
        ctx.restore()
        rgba(ctx, RED, a); ctx.set_line_width(9)
        ctx.set_line_join(cairo.LINE_JOIN_MITER); ctx.stroke()

    if femur_rot is not None:
        ang, fa = femur_rot
        ctx.save(); ctx.rotate(ang)
        ctx.set_dash([18, 14])
        ctx.save(); ctx.scale(3.3, 1.75); ctx.arc(0, 0, 100, 0, 2 * math.pi); ctx.restore()
        rgba(ctx, INK, fa * 0.45); ctx.set_line_width(5); ctx.stroke()
        ctx.set_dash([])
        ctx.restore()
    ctx.restore()


def label(ctx, s, tx, ty, lx, ly, k, color=INK, size=40, align="l"):
    if k <= 0:
        return
    # dot at target, line to label
    rgba(ctx, color, k)
    ctx.arc(tx, ty, 9, 0, 2 * math.pi); ctx.fill()
    ex = tx + (lx - tx) * eo(k)
    ey = ty + (ly - ty) * eo(k)
    ctx.set_line_width(4); ctx.move_to(tx, ty); ctx.line_to(ex, ey); ctx.stroke()
    kk = p(k, 0.5, 1)
    if kk > 0:
        if align == "above":
            text(ctx, s, lx, ly - 22, size, color, kk, align="c")
        else:
            off = 14 if align == "l" else -14
            text(ctx, s, lx + off, ly + size * 0.35, size, color, kk, align=align)


# ---------------- chrome ----------------
def chrome(ctx, tg):
    # progress bar
    rgba(ctx, INK, 0.08); rrect(ctx, 60, 120, W - 120, 10, 5); ctx.fill()
    rgba(ctx, TEAL, 1); rrect(ctx, 60, 120, max(10, (W - 120) * tg / TOTAL), 10, 5); ctx.fill()
    # series tag
    s = "WAT GEBEURT ER IN JE…"
    w = text_w(ctx, s, 34)
    rgba(ctx, TEAL, 1); rrect(ctx, W / 2 - w / 2 - 28, 170, w + 56, 64, 32); ctx.fill()
    text(ctx, s, W / 2, 214, 34, (1, 1, 1))


# ---------------- scenes ----------------
def s_hook(ctx, t, d):
    title = ["Wat gebeurt er", "in je knie bij een", "meniscusscheur?"]
    for i, ln in enumerate(title):
        k = back(p(t, 0.15 + i * 0.25, 0.75 + i * 0.25))
        if k <= 0:
            continue
        size = 104 if i < 2 else 112
        col = INK if i < 2 else RED
        ctx.save()
        y = 430 + i * 130
        ctx.translate(W / 2, y); ctx.scale(k, k); ctx.translate(-W / 2, -y)
        text(ctx, ln, W / 2, y, size, col, clamp(k))
        ctx.restore()
    kk = eo(p(t, 1.0, 1.8))
    pulse = 0.5 + 0.5 * math.sin(t * 6)
    knee_front(ctx, W / 2, 1180 + (1 - kk) * 80, 0.62, bone_a=kk, men_a=kk,
               men_pulse=pulse * kk)
    # red alert ring at medial joint line
    if t > 1.8:
        r = 40 + 50 * ((t - 1.8) % 1.0)
        a = 1 - ((t - 1.8) % 1.0)
        rgba(ctx, RED, a * 0.8); ctx.set_line_width(8)
        ctx.arc(W / 2 + 0.62 * 160, 1180 + 0.62 * 26, r, 0, 2 * math.pi); ctx.stroke()


def s_anatomie(ctx, t, d):
    caption(ctx, ["Tussen je bovenbeen en", "scheenbeen zitten 2 menisci"], 380, t, 0.1, 62)
    caption(ctx, ["stevige schokdempers van kraakbeen"], 560, t, 2.4, 50, color=TEAL)
    kb = eo(p(t, 0.0, 0.8))
    km = eo(p(t, 1.4, 2.1))
    pulse = (0.5 + 0.5 * math.sin((t - 1.4) * 5)) if t > 1.4 else 0
    cx, cy, sc = W / 2, 1150, 0.78
    knee_front(ctx, cx, cy, sc, bone_a=kb, men_a=km, men_pulse=pulse * km)
    label(ctx, "bovenbeen", cx + 78 * sc, cy - 420 * sc, cx + 250, cy - 420 * sc, p(t, 0.8, 1.4))
    label(ctx, "scheenbeen", cx + 84 * sc, cy + 400 * sc, cx + 250, cy + 400 * sc, p(t, 1.0, 1.6))
    label(ctx, "meniscus", cx - 165 * sc, cy + 30 * sc, 230, cy - 190, p(t, 1.9, 2.6), MEN_D, align="above")
    label(ctx, "meniscus", cx + 165 * sc, cy + 30 * sc, W - 230, cy - 190, p(t, 2.0, 2.7), MEN_D, align="above")


def s_functie(ctx, t, d):
    caption(ctx, ["Ze vangen de druk op", "en verdelen die"], 380, t, 0.1, 66)
    caption(ctx, ["Ze dragen zo'n helft van de belasting,", "bij een gebogen knie nog meer"],
            580, t, 3.2, 42, color=TEAL)
    cyc = 0.5 - 0.5 * math.cos(max(0, t - 0.8) * 2 * math.pi / 1.6) if t > 0.8 else 0
    cx, cy, sc = W / 2, 1180, 0.78
    knee_front(ctx, cx, cy, sc, femur_dy=10 * cyc, squash=cyc, men_pulse=cyc)
    # load arrow down
    ka = eo(p(t, 0.6, 1.1))
    if ka > 0:
        arrow(ctx, cx, cy - 560 * sc - 40 - 20 * cyc, cx, cy - 330 * sc + 10 * cyc,
              RED, ka, lw=16, head=46)
    # spread arrows along joint line
    if t > 1.0:
        a = clamp(cyc * 1.6) * eo(p(t, 1.0, 1.4))
        y = cy + 60 * sc
        for s in (-1, 1):
            arrow(ctx, cx + s * 60, y + 70, cx + s * (190 + 50 * cyc), y + 70, TEAL, a, lw=10, head=28)


def s_scheur(ctx, t, d):
    cx, cy, sc = W / 2, 1150, 1.25
    if t < 3.0:
        caption(ctx, ["Van bovenaf gezien:", "twee ringen op je scheenbeen"], 380, t, 0.1, 60)
    else:
        fade = 1 - eo(p(t, 2.7, 3.0))
    tt = t - 3.0
    if t >= 3.0:
        caption(ctx, ["Draaien met gebogen knie,", "terwijl je voet stilstaat…"], 380, tt, 0.0, 60)
    if t >= 5.4:
        caption(ctx, ["…kan een scheur geven"], 560, t - 5.4, 0.0, 66, color=RED)
    ka = eo(p(t, 0.0, 0.8))
    rot = None
    if t > 3.0:
        k = p(t, 3.0, 5.6)
        ang = 0.22 * math.sin(k * math.pi * 2.5) * eo(p(t, 3.0, 3.4))
        rot = (ang, eo(p(t, 3.0, 3.4)) * (1 - p(t, 5.6, 6.2)))
    tear = eo(p(t, 5.3, 5.9))
    shake = 0
    if 5.3 < t < 6.0:
        shake = 10 * math.sin(t * 90) * (1 - p(t, 5.3, 6.0))
    glow = (0.6 + 0.4 * math.sin(t * 6)) * tear
    plateau(ctx, cx, cy, sc * 0.8, a=ka, tear=tear, glow=glow, femur_rot=rot, shake=shake)
    # rotation arrows
    if 3.2 < t < 5.8:
        a = eo(p(t, 3.2, 3.6)) * (1 - p(t, 5.4, 5.8))
        rgba(ctx, INK, a * 0.75)
        ctx.set_line_width(10); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        R = 340
        a0 = math.pi * 1.15; a1 = math.pi * 1.85
        ctx.arc(cx, cy, R, a0, a1); ctx.stroke()
        ex, ey = cx + R * math.cos(a1), cy + R * math.sin(a1)
        arrow(ctx, ex - 1, ey - 18, ex + 6, ey + 6, INK, a * 0.75, lw=1, head=34)
    # labels
    k1 = p(t, 0.9, 1.5) * (1 - p(t, 2.7, 3.0))
    label(ctx, "binnenkant", cx + 150 * sc * 0.8 + 140, cy - 160, cx + 330, cy - 330, k1, MEN_D, size=38, align="r")
    label(ctx, "buitenkant", cx - 150 * sc * 0.8 - 128, cy - 160, cx - 330, cy - 330, k1, MEN_D, size=38)


def s_klachten(ctx, t, d):
    caption(ctx, ["Herkenbare klachten"], 380, t, 0.1, 72)
    items = [("Pijn aan de binnen- of", "buitenkant van je knie"),
             ("Zwelling, vaak pas", "na een paar uur"),
             ("Haken of op slot", "schieten van de knie"),
             ("Pijn bij hurken", "en draaien")]
    for i, (l1, l2) in enumerate(items):
        k = eo(p(t, 0.7 + i * 0.9, 1.25 + i * 0.9))
        if k <= 0:
            continue
        y = 520 + i * 230
        x = 80 + (1 - k) * 200
        ctx.save()
        rgba(ctx, INK, 0.06 * k); rrect(ctx, x + 4, y + 8, W - 160, 196, 36); ctx.fill()
        rgba(ctx, CARD, k); rrect(ctx, x, y, W - 160, 196, 36); ctx.fill()
        rgba(ctx, RED if i == 2 else TEAL, k)
        ctx.arc(x + 98, y + 98, 52, 0, 2 * math.pi); ctx.fill()
        text(ctx, str(i + 1), x + 98, y + 118, 56, (1, 1, 1), k)
        text(ctx, l1, x + 180, y + 86, 46, INK, k, align="l")
        text(ctx, l2, x + 180, y + 144, 46, MUTED, k, bold=False, align="l")
        ctx.restore()


def s_slot(ctx, t, d):
    k = back(p(t, 0.1, 0.7))
    cx, cy = W / 2, 560
    if k > 0:
        ctx.save(); ctx.translate(cx, cy); ctx.scale(k, k)
        rgba(ctx, TEAL, 1); ctx.arc(0, 0, 120, 0, 2 * math.pi); ctx.fill()
        # check draw
        kc = eo(p(t, 0.5, 1.0))
        pts = [(-52, 4), (-14, 42), (58, -36)]
        rgba(ctx, (1, 1, 1), 1); ctx.set_line_width(26)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        L1 = math.dist(pts[0], pts[1]); L2 = math.dist(pts[1], pts[2]); L = (L1 + L2) * kc
        if L > 0:
            ctx.move_to(*pts[0])
            if L <= L1:
                f = L / L1
                ctx.line_to(pts[0][0] + (pts[1][0] - pts[0][0]) * f, pts[0][1] + (pts[1][1] - pts[0][1]) * f)
            else:
                ctx.line_to(*pts[1])
                f = (L - L1) / L2
                ctx.line_to(pts[1][0] + (pts[2][0] - pts[1][0]) * f, pts[1][1] + (pts[2][1] - pts[1][1]) * f)
            ctx.stroke()
        ctx.restore()
    caption(ctx, ["Goed nieuws"], 790, t, 0.6, 84, color=TEAL)
    caption(ctx, ["Bij veel meniscusklachten,", "zeker door slijtage, is gericht", "oefenen de eerste stap"],
            900, t, 1.2, 54)
    caption(ctx, ["Twijfel je? Laat je knie", "onderzoeken door een fysiotherapeut"], 1160, t, 3.0, 42, color=MUTED)
    kn = eo(p(t, 4.6, 5.2))
    if kn > 0:
        y = 1330 + (1 - kn) * 30
        rgba(ctx, INK, kn); rrect(ctx, 110, y, W - 220, 150, 40); ctx.fill()
        text(ctx, "Volgende: je schouder", W / 2, y + 66, 46, (1, 1, 1), kn)
        text(ctx, "Volg voor de hele reeks", W / 2, y + 116, 34, (0.75, 0.9, 0.88), kn, bold=False)
    text(ctx, "Algemene informatie, geen persoonlijk advies", W / 2, 1560, 28, MUTED, eo(p(t, 1.0, 1.6)), bold=False)


FN = {"hook": s_hook, "anatomie": s_anatomie, "functie": s_functie,
      "scheur": s_scheur, "klachten": s_klachten, "slot": s_slot}


def frame(name, t, d, offset):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)
    ctx.set_antialias(cairo.ANTIALIAS_BEST)
    rgba(ctx, BG); ctx.paint()
    # soft backdrop circle
    rgba(ctx, TEAL, 0.05); ctx.arc(W / 2, 1150, 470, 0, 2 * math.pi); ctx.fill()
    ctx.push_group()
    FN[name](ctx, t, d)
    ctx.pop_group_to_source()
    fade = min(p(t, 0, 0.25), 1 - p(t, d - 0.25, d))
    ctx.paint_with_alpha(fade)
    chrome(ctx, offset + t)
    return surf


def render_scene(idx, outdir):
    name, d = SCENES[idx]
    offset = sum(dd for _, dd in SCENES[:idx])
    n = int(round(d * FPS))
    tmp = os.path.join(outdir, f"tmp_{idx}_{name}.mp4")
    fin = os.path.join(outdir, f"{idx}_{name}.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast",
           "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS), tmp]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(n):
        s = frame(name, i / FPS, d, offset)
        pr.stdin.write(bytes(s.get_data()))
    pr.stdin.close()
    if pr.wait() == 0:
        os.replace(tmp, fin)
    print("done", fin)


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "still":
        # name t
        name, t = sys.argv[2], float(sys.argv[3])
        idx = [n for n, _ in SCENES].index(name)
        d = SCENES[idx][1]
        off = sum(dd for _, dd in SCENES[:idx])
        frame(name, t, d, off).write_to_png(sys.argv[4])
    elif mode == "scene":
        render_scene(int(sys.argv[2]), sys.argv[3])
