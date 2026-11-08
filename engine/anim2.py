import cairo, math, sys, subprocess, os, random
from anim import (femur_path, tibia_path, fibula_path, men_wedge, clamp, p, eo, eio, back,
                  rrect, text_w)

W, H, FPS = 1080, 1920, 30
FONT = "Inter"

BG0 = (0.03, 0.04, 0.07)
BG1 = (0.09, 0.12, 0.20)
WHITE = (1, 1, 1)
GREY = (0.70, 0.74, 0.80)
CYAN = (0.25, 0.85, 1.0)
CYAN_D = (0.05, 0.45, 0.62)
RED = (1.0, 0.22, 0.26)
YEL = (1.0, 0.82, 0.18)
GREEN = (0.20, 0.90, 0.65)
BONE_A = (0.96, 0.93, 0.86)
BONE_B = (0.74, 0.68, 0.58)
BONE_E = (0.30, 0.26, 0.22)

SCENES = [("cold", 3.2), ("titel", 3.0), ("anatomie", 6.0), ("functie", 6.0),
          ("scheur", 8.0), ("klachten", 8.0), ("slot", 5.5)]
TOTAL = sum(d for _, d in SCENES)
START = {}
_acc = 0
for n, d in SCENES:
    START[n] = _acc; _acc += d

# local event times per scene: (t, kind) kind in slam/boom/tear
EVENTS = {
    "cold": [(0.1, "slam"), (1.3, "tear")],
    "titel": [(0.1, "slam"), (0.5, "slam"), (1.0, "boom")],
    "anatomie": [(1.3, "boom"), (2.2, "slam")],
    "functie": [(0.6, "boom"), (1.4, "slam"), (2.2, "slam"), (3.0, "slam"), (3.8, "slam"), (4.6, "slam")],
    "scheur": [(0.2, "slam"), (1.6, "slam"), (3.0, "boom"), (4.75, "tear"), (6.4, "slam")],
    "klachten": [(0.05, "boom"), (2.05, "boom"), (4.05, "boom"), (6.05, "boom")],
    "slot": [(0.1, "boom"), (0.9, "slam"), (1.2, "slam")],
}


def global_events():
    out = []
    for n, evs in EVENTS.items():
        for t, k in evs:
            out.append((START[n] + t, k))
    return sorted(out)


def rgba(ctx, c, a=1.0):
    ctx.set_source_rgba(c[0], c[1], c[2], a)


def font(ctx, size, bold=True):
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL,
                         cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)


def txt(ctx, s, x, y, size, col=WHITE, a=1.0, bold=True, align="c", shadow=True):
    font(ctx, size, bold)
    e = ctx.text_extents(s)
    xx = x - e.x_advance / 2 if align == "c" else (x - e.x_advance if align == "r" else x)
    if shadow:
        ctx.move_to(xx, y + size * 0.06)
        rgba(ctx, (0, 0, 0), 0.55 * a); ctx.show_text(s)
    ctx.move_to(xx, y)
    rgba(ctx, col, a); ctx.show_text(s)


COLS = {"*": RED, "^": YEL, "~": CYAN, "+": GREEN}


def slam(ctx, lines, y, t, start, size, stagger=0.08, lh=1.15, base=WHITE, out_t=None):
    """Kinetic text: words punch in big -> normal. Prefix a word with * ^ ~ + to colour it."""
    k = 0
    fo = 1.0
    if out_t is not None:
        fo = 1 - p(t, out_t, out_t + 0.15)
        if fo <= 0:
            return
    font(ctx, size)
    sp = ctx.text_extents(" ").x_advance
    for li, ln in enumerate(lines):
        words = ln.split(" ")
        parsed = []
        for w in words:
            col = base
            if w and w[0] in COLS:
                col = COLS[w[0]]; w = w[1:]
            parsed.append((w, col, ctx.text_extents(w).x_advance))
        total = sum(pw for _, _, pw in parsed) + sp * (len(parsed) - 1)
        x = W / 2 - total / 2
        yy = y + li * size * lh
        for w, col, pw in parsed:
            tk = start + k * stagger
            e = p(t, tk, tk + 0.16)
            k += 1
            if e > 0:
                s = 1.9 - 0.9 * eo(e)
                a = clamp(e * 3) * fo
                cx = x + pw / 2
                ctx.save()
                ctx.translate(cx, yy - size * 0.35); ctx.scale(s, s); ctx.translate(-cx, -(yy - size * 0.35))
                if col != base:
                    # glow
                    for gw, ga in ((14, 0.10), (7, 0.18)):
                        font(ctx, size); ctx.move_to(x, yy); ctx.text_path(w)
                        rgba(ctx, col, ga * a); ctx.set_line_width(gw)
                        ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke()
                txt(ctx, w, x, yy, size, col, a, align="l")
                ctx.restore()
                font(ctx, size)
            x += pw + sp


# ---------------- effects ----------------
random.seed(7)
PARTS = [(random.random() * W, random.random() * H, 10 + random.random() * 40,
          1.5 + random.random() * 3.5, random.random() * 6.28) for _ in range(80)]


def background(ctx, tg, tint=None):
    g = cairo.RadialGradient(W / 2, 1050, 50, W / 2, 1050, 1200)
    c1 = tint or BG1
    g.add_color_stop_rgb(0, *c1)
    g.add_color_stop_rgb(1, *BG0)
    ctx.set_source(g); ctx.paint()
    for x0, y0, sp, r, ph in PARTS:
        y = (y0 - sp * tg) % H
        x = x0 + 12 * math.sin(tg * 0.7 + ph)
        a = 0.10 + 0.12 * (0.5 + 0.5 * math.sin(tg * 2 + ph))
        rgba(ctx, CYAN, a); ctx.arc(x, y, r, 0, 2 * math.pi); ctx.fill()


def vignette(ctx, red=0.0):
    g = cairo.RadialGradient(W / 2, H / 2, 500, W / 2, H / 2, 1250)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0, 0, 0, 0.75)
    ctx.set_source(g); ctx.paint()
    if red > 0:
        g = cairo.RadialGradient(W / 2, H / 2, 350, W / 2, H / 2, 1150)
        g.add_color_stop_rgba(0, RED[0], RED[1], RED[2], 0)
        g.add_color_stop_rgba(1, RED[0], RED[1], RED[2], 0.65 * red)
        ctx.set_source(g); ctx.paint()


def camera(name, t):
    zoom, sx, sy, flash, fcol = 1.0, 0.0, 0.0, 0.0, WHITE
    for te, kind in EVENTS[name]:
        dt = t - te
        if dt < 0:
            continue
        amp = {"slam": 0.035, "boom": 0.07, "tear": 0.14}[kind]
        zoom += amp * math.exp(-dt * 9)
        sh = {"slam": 8, "boom": 18, "tear": 42}[kind] * math.exp(-dt * 7)
        sx += sh * math.sin(dt * 71 + te)
        sy += sh * math.cos(dt * 53 + te * 3)
        if kind == "tear":
            f = math.exp(-dt * 6)
            if f > flash:
                flash, fcol = f, (WHITE if dt < 0.06 else RED)
        elif kind == "boom":
            f = 0.25 * math.exp(-dt * 12)
            if f > flash:
                flash, fcol = f, WHITE
    return zoom, sx, sy, flash, fcol


def glow_path(ctx, path_fn, col, a=1.0, widths=((36, 0.06), (22, 0.10), (12, 0.18))):
    for w, ga in widths:
        path_fn(ctx); rgba(ctx, col, ga * a); ctx.set_line_width(w)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke()


def bone_fill(ctx, path_fn, a, y0, y1):
    path_fn(ctx)
    g = cairo.LinearGradient(-200, y0, 200, y1)
    g.add_color_stop_rgba(0, *BONE_A, a)
    g.add_color_stop_rgba(1, *BONE_B, a)
    ctx.set_source(g); ctx.fill_preserve()
    rgba(ctx, BONE_E, a); ctx.set_line_width(5); ctx.stroke()


def knee2(ctx, cx, cy, sc, bone_a=1.0, men_a=1.0, glow=0.0, femur_dy=0.0, squash=0.0, men_col=CYAN):
    ctx.save(); ctx.translate(cx, cy); ctx.scale(sc, sc)
    # rim light
    for f in (fibula_path, tibia_path):
        glow_path(ctx, f, CYAN, 0.35 * bone_a, ((28, 0.05), (14, 0.08)))
        bone_fill(ctx, f, bone_a, 40, 620)
    ctx.save(); ctx.translate(0, femur_dy)
    glow_path(ctx, femur_path, CYAN, 0.35 * bone_a, ((28, 0.05), (14, 0.08)))
    bone_fill(ctx, femur_path, bone_a, -620, 10)
    ctx.restore()
    if men_a > 0:
        for side in (-1, 1):
            fn = lambda c, s=side: men_wedge(c, s, squash)
            if glow > 0:
                glow_path(ctx, fn, men_col, men_a * glow, ((70, 0.08), (44, 0.14), (24, 0.25)))
            fn(ctx); rgba(ctx, men_col, men_a); ctx.fill_preserve()
            rgba(ctx, (1, 1, 1), 0.6 * men_a); ctx.set_line_width(3); ctx.stroke()
    ctx.restore()


def plateau2(ctx, cx, cy, sc, a=1.0, tear=0.0, glow=0.6, femur_rot=None, men_col=CYAN, sparks_t=None):
    d = math.pi / 180
    ctx.save(); ctx.translate(cx, cy); ctx.scale(sc, sc)

    def outline(c):
        c.move_to(-300, 0)
        c.curve_to(-300, -150, -150, -190, 0, -150)
        c.curve_to(150, -190, 300, -150, 300, 0)
        c.curve_to(300, 150, 150, 180, 40, 170)
        c.curve_to(10, 200, -10, 200, -40, 170)
        c.curve_to(-150, 180, -300, 150, -300, 0)
        c.close_path()
    glow_path(ctx, outline, CYAN, 0.3 * a, ((30, 0.05), (14, 0.08)))
    bone_fill(ctx, outline, a, -190, 190)
    for x0 in (-150, 150):
        ctx.save(); ctx.translate(x0, 0); ctx.scale(1, 1.05)
        ctx.arc(0, 0, 105, 0, 2 * math.pi); ctx.restore()
        rgba(ctx, (0.80, 0.86, 0.92), a); ctx.fill()

    def ring(x0, rx, ry, a0, a1, width, col, al):
        ctx.save(); ctx.translate(x0, 0); ctx.scale(rx / 100.0, ry / 100.0)
        ctx.arc(0, 0, 100, a0, a1); ctx.restore()
        rgba(ctx, col, al); ctx.set_line_width(width)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()

    for (x0, rx, ry, a0, a1) in ((-150, 128, 132, 52 * d, 308 * d), (150, 140, 146, -125 * d, 125 * d)):
        for w, ga in ((120, 0.07), (90, 0.12), (70, 0.2)):
            ring(x0, rx, ry, a0, a1, w, men_col, ga * glow * a)
        ring(x0, rx, ry, a0, a1, 54, men_col, a)
        ring(x0, rx, ry, a0, a1, 30, (1, 1, 1), 0.18 * a)

    if tear > 0:
        ctx.save(); ctx.translate(150, 0)
        a0, a1 = -50 * d, 50 * d
        end = a0 + (a1 - a0) * tear
        n = 40
        for w, ga, col in ((40, 0.25, RED), (22, 0.45, RED), (9, 1.0, (0.35, 0.0, 0.02))):
            first = True
            for i in range(n + 1):
                ang = a0 + (a1 - a0) * i / n
                if ang > end:
                    break
                jig = 8 * math.sin(i * 2.7) * (1 if i % 2 else -1)
                r = 143 + jig
                x, y = math.cos(ang) * r, math.sin(ang) * r * 1.03
                if first:
                    ctx.move_to(x, y); first = False
                else:
                    ctx.line_to(x, y)
            rgba(ctx, col, ga * a); ctx.set_line_width(w)
            ctx.set_line_join(cairo.LINE_JOIN_MITER); ctx.stroke()
        if sparks_t is not None and 0 <= sparks_t < 0.7:
            rnd = random.Random(3)
            for i in range(30):
                ang = rnd.uniform(-1.2, 1.2) + (0 if i % 2 else math.pi * 0.0)
                sp = rnd.uniform(250, 650)
                r0 = 143 + sp * sparks_t
                r1 = r0 + 40 + rnd.uniform(0, 50)
                base = rnd.uniform(-45, 45) * d
                x0, y0 = math.cos(base) * 143, math.sin(base) * 147
                dx, dy = math.cos(base + ang * 0.6), math.sin(base + ang * 0.6)
                al = 1 - sparks_t / 0.7
                rgba(ctx, YEL if i % 3 else WHITE, al)
                ctx.set_line_width(5); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
                ctx.move_to(x0 + dx * (r0 - 143), y0 + dy * (r0 - 143))
                ctx.line_to(x0 + dx * (r1 - 143), y0 + dy * (r1 - 143)); ctx.stroke()
        ctx.restore()

    if femur_rot is not None:
        ang, fa = femur_rot
        ctx.save(); ctx.rotate(ang)
        ctx.set_dash([20, 14])
        ctx.save(); ctx.scale(3.3, 1.75); ctx.arc(0, 0, 100, 0, 2 * math.pi); ctx.restore()
        rgba(ctx, WHITE, fa * 0.7); ctx.set_line_width(6); ctx.stroke()
        ctx.set_dash([])
        ctx.restore()
    ctx.restore()


def arrow(ctx, x1, y1, x2, y2, col, a=1.0, lw=10, head=28, glow=True):
    ang = math.atan2(y2 - y1, x2 - x1)

    def shaft(c):
        c.move_to(x1, y1); c.line_to(x2 - math.cos(ang) * head * 0.6, y2 - math.sin(ang) * head * 0.6)
    if glow:
        glow_path(ctx, shaft, col, a, ((lw * 4, 0.08), (lw * 2.4, 0.15)))
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    shaft(ctx); rgba(ctx, col, a); ctx.set_line_width(lw); ctx.stroke()
    ctx.move_to(x2, y2)
    ctx.line_to(x2 - head * math.cos(ang - 0.45), y2 - head * math.sin(ang - 0.45))
    ctx.line_to(x2 - head * math.cos(ang + 0.45), y2 - head * math.sin(ang + 0.45))
    ctx.close_path(); ctx.fill()


def ringburst(ctx, x, y, dt, col, rmax=260, dur=0.6):
    if 0 <= dt < dur:
        k = dt / dur
        rgba(ctx, col, (1 - k) * 0.9); ctx.set_line_width(14 * (1 - k) + 2)
        ctx.arc(x, y, 30 + rmax * eo(k), 0, 2 * math.pi); ctx.stroke()


# ---------------- scenes ----------------
def s_cold(ctx, t, d):
    cx, cy, sc = W / 2 - 230, 1080, 1.6
    ramp = eo(p(t, 0, 0.4))
    ang = 0.34 * math.sin(t * 9) * ramp * (1 - p(t, 1.3, 1.5))
    tear = eo(p(t, 1.3, 1.55))
    plateau2(ctx, cx, cy, sc, a=1, tear=tear, glow=0.5 + 0.5 * tear,
             femur_rot=(ang, 1 - p(t, 1.3, 1.6)), sparks_t=(t - 1.3) if t >= 1.3 else None)
    slam(ctx, ["ÉÉN VERKEERDE", "DRAAI…"], 430, t, 0.1, 108, out_t=1.2)
    slam(ctx, ["*MENISCUS-", "*SCHEUR"], 430, t, 1.4, 150, stagger=0.12)


def s_titel(ctx, t, d):
    z = 1 + 0.08 * t / d
    knee2(ctx, W / 2, 1300, 0.85 * z, bone_a=0.28, men_a=0.8, glow=0.6 + 0.4 * math.sin(t * 6))
    slam(ctx, ["Wat gebeurt er", "nou ^écht", "in je ~knie?"], 520, t, 0.1, 128, stagger=0.1)


def s_anatomie(ctx, t, d):
    k = eio(p(t, 0.0, 1.2))
    zz = 2.2 - 1.2 * k
    cy = 1230
    ctx.save()
    ctx.translate(W / 2, cy); ctx.scale(zz, zz); ctx.translate(-W / 2, -cy)
    ig = p(t, 1.3, 1.6)
    pulse = 0.6 + 0.4 * math.sin((t - 1.3) * 6) if t > 1.3 else 0
    knee2(ctx, W / 2, cy, 0.74, men_a=0.25 + 0.75 * ig, glow=pulse * ig)
    ctx.restore()
    ringburst(ctx, W / 2 - 120, cy + 25, t - 1.3, CYAN)
    ringburst(ctx, W / 2 + 120, cy + 25, t - 1.3, CYAN)
    slam(ctx, ["^2 menisci"], 420, t, 1.4, 140)
    slam(ctx, ["jouw ~schokdempers"], 560, t, 2.2, 84)
    la = eo(p(t, 3.0, 3.5))
    if la > 0:
        txt(ctx, "bovenbeen", W / 2 + 120, cy - 300, 40, GREY, la, align="l")
        txt(ctx, "scheenbeen", W / 2 + 120, cy + 330, 40, GREY, la, align="l")


def s_functie(ctx, t, d):
    cx, cy, sc = W / 2, 1270, 0.72
    hits = [te for te, _ in EVENTS["functie"]]
    comp = 0
    for te in hits:
        dt = t - te
        if dt >= 0:
            comp = max(comp, math.exp(-dt * 6))
    knee2(ctx, cx, cy, sc, femur_dy=18 * comp, squash=comp, glow=0.4 + 0.6 * comp,
          men_col=CYAN)
    # slamming arrow
    if t >= hits[0] - 0.2:
        last = max([te for te in hits if te <= t + 0.2] or [hits[0]])
        dt = t - last
        drop = eo(p(dt, -0.2, 0.0))
        y2 = cy - 420 * sc + 20 + 30 * comp
        y1 = y2 - 170
        off = (1 - drop) * -120
        arrow(ctx, cx, y1 + off, cx, y2 + off, RED, 1, lw=22, head=60)
    for te in hits:
        ringburst(ctx, cx - 120, cy + 25, t - te, RED, 200, 0.5)
        ringburst(ctx, cx + 120, cy + 25, t - te, RED, 200, 0.5)
    n = int(round(50 * eo(p(t, 0.5, 1.5))))
    if t > 0.5:
        ka = eo(p(t, 0.5, 0.7))
        ctx.save(); s = 1 + 0.25 * comp
        ctx.translate(W / 2, 440); ctx.scale(s, s); ctx.translate(-W / 2, -440)
        for gw, ga in ((24, 0.08), (12, 0.15)):
            font(ctx, 190); e = ctx.text_extents(f"± {n}%")
            ctx.move_to(W / 2 - e.x_advance / 2, 500); ctx.text_path(f"± {n}%")
            rgba(ctx, YEL, ga * ka); ctx.set_line_width(gw); ctx.stroke()
        txt(ctx, f"± {n}%", W / 2, 500, 190, YEL, ka)
        ctx.restore()
    slam(ctx, ["van de druk vangen ze op"], 600, t, 1.0, 58)
    slam(ctx, ["bij een gebogen knie: ^nog ^meer"], 690, t, 3.2, 52)


def s_scheur(ctx, t, d):
    cx, cy = W / 2, 1150
    zin = eio(p(t, 3.0, 4.7))
    tear_t = 4.75
    # camera push toward medial meniscus
    zz = 1 + 0.35 * zin + (0.15 * eo(p(t, tear_t, 6.0)) if t > tear_t else 0)
    fx = cx + 150 * 1.0 * zin
    ctx.save()
    ctx.translate(cx, cy); ctx.scale(zz, zz); ctx.translate(-fx, -cy)
    spin_in = eo(p(t, 0, 0.6))
    ctx.save(); ctx.translate(cx, cy); ctx.rotate((1 - spin_in) * -1.2)
    ctx.scale(0.4 + 0.6 * spin_in, 0.4 + 0.6 * spin_in); ctx.translate(-cx, -cy)
    rot = None
    if t > 3.0:
        k = p(t, 3.0, 4.6)
        amp = 0.08 + 0.3 * k
        ang = amp * math.sin((t - 3.0) * (6 + 10 * k))
        rot = (ang * (1 - p(t, tear_t, tear_t + 0.2)), 1 - p(t, tear_t, tear_t + 0.4))
    tear = eo(p(t, tear_t, tear_t + 0.25))
    plateau2(ctx, cx, cy, 1.0, tear=tear, glow=0.5 + 0.5 * tear, femur_rot=rot,
             sparks_t=(t - tear_t) if t >= tear_t else None)
    ctx.restore()
    if 3.1 < t < tear_t:
        a = eo(p(t, 3.1, 3.4))
        R = 330
        for s in (1, -1):
            a0 = math.pi * (1.2 if s > 0 else 0.2) + (t - 3) * 2.5
            ctx.set_line_width(12); rgba(ctx, WHITE, a * 0.85)
            ctx.arc(cx, cy, R, a0, a0 + 1.6); ctx.stroke()
            ex, ey = cx + R * math.cos(a0 + 1.6), cy + R * math.sin(a0 + 1.6)
            tx, ty = -math.sin(a0 + 1.6), math.cos(a0 + 1.6)
            arrow(ctx, ex - tx * 20, ey - ty * 20, ex + tx * 14, ey + ty * 14, WHITE, a * 0.85, lw=2, head=40, glow=False)
    ctx.restore()
    vignette(ctx, red=0.8 * p(t, 3.0, 4.7) * (1 - p(t, tear_t + 0.3, tear_t + 1.5)) + 0.6 * math.exp(-max(0, t - tear_t) * 3) * (t >= tear_t))
    slam(ctx, ["Je voet staat ^stil…"], 430, t, 0.2, 84, out_t=1.45)
    slam(ctx, ["je knie is ^gebogen…"], 430, t, 1.6, 84, out_t=2.85)
    slam(ctx, ["en dan: *DRAAIEN"], 430, t, 3.0, 96, out_t=4.6)
    slam(ctx, ["*SCHEUR"], 470, t, tear_t + 0.05, 210)
    slam(ctx, ["na je 40e ook vaak", "door ^slijtage"], 600, t, 6.4, 58)


def icon_bolt(ctx, s, col):
    pts = [(20, -120), (-60, 15), (-5, 15), (-25, 120), (60, -20), (5, -20), (30, -120)]
    ctx.move_to(pts[0][0] * s, pts[0][1] * s)
    for x, y in pts[1:]:
        ctx.line_to(x * s, y * s)
    ctx.close_path(); rgba(ctx, col, 1); ctx.fill()


def icon_swell(ctx, s, col, t):
    for i in range(3):
        k = ((t * 0.8 + i / 3) % 1)
        rgba(ctx, col, (1 - k) * 0.9); ctx.set_line_width(10)
        ctx.arc(0, 0, (40 + 90 * k) * s, 0, 2 * math.pi); ctx.stroke()
    rgba(ctx, col, 1); ctx.arc(0, 0, (45 + 8 * math.sin(t * 8)) * s, 0, 2 * math.pi); ctx.fill()


def icon_lock(ctx, s, col):
    rgba(ctx, col, 1)
    rrect(ctx, -70 * s, -10 * s, 140 * s, 110 * s, 18 * s); ctx.fill()
    ctx.set_line_width(22 * s); ctx.arc(0, -10 * s, 48 * s, math.pi, 2 * math.pi); ctx.stroke()
    rgba(ctx, BG0, 1); ctx.arc(0, 35 * s, 14 * s, 0, 2 * math.pi); ctx.fill()
    ctx.rectangle(-6 * s, 35 * s, 12 * s, 35 * s); ctx.fill()


def icon_squat(ctx, s, col):
    rgba(ctx, col, 1); ctx.set_line_width(20 * s); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.arc(-14 * s, -112 * s, 26 * s, 0, 2 * math.pi); ctx.fill()
    ctx.move_to(-22 * s, -78 * s); ctx.line_to(-48 * s, 10 * s); ctx.line_to(38 * s, 18 * s)
    ctx.line_to(22 * s, 100 * s); ctx.line_to(62 * s, 100 * s); ctx.stroke()
    ctx.move_to(-28 * s, -56 * s); ctx.line_to(58 * s, -40 * s); ctx.stroke()
    ctx.set_line_width(8 * s)
    for ang in (-1.2, -0.5, 0.2):
        x, y = 38 * s + math.cos(ang) * 34 * s, 18 * s + math.sin(ang) * 34 * s
        ctx.move_to(x, y); ctx.line_to(x + math.cos(ang) * 26 * s, y + math.sin(ang) * 26 * s); ctx.stroke()


def s_klachten(ctx, t, d):
    items = [("PIJN", "aan de binnen- of", "buitenkant van je knie", icon_bolt),
             ("ZWELLING", "vaak pas na", "een paar uur", icon_swell),
             ("OP SLOT", "de knie blijft haken", "of zit even vast", icon_lock),
             ("AU!", "bij hurken", "en draaien", icon_squat)]
    i = min(3, int(t // 2.0))
    lt = t - i * 2.0
    big, l1, l2, ic = items[i]
    k = back(p(lt, 0.05, 0.4))
    cx, cy = W / 2, 1120
    # icon disc
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
    slam(ctx, [big], 470, lt, 0.05, 170, base=RED)
    slam(ctx, [l1, l2], 600, lt, 0.35, 56, base=GREY)
    # counter dots
    for j in range(4):
        rgba(ctx, RED if j <= i else (0.3, 0.32, 0.38), 1)
        ctx.arc(W / 2 - 75 + j * 50, 1500, 10, 0, 2 * math.pi); ctx.fill()


def s_slot(ctx, t, d):
    slam(ctx, ["MAAR…"], 400, t, 0.1, 140)
    slam(ctx, ["+goed +nieuws"], 540, t, 0.9, 110)
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
    slam(ctx, ["klachten worden vaak minder", "met gerichte +oefentherapie"], 1140, t, 1.9, 56, stagger=0.05)
    slam(ctx, ["(zeker bij slijtage)"], 1290, t, 2.8, 42, base=GREY)
    kn = eo(p(t, 3.4, 3.8))
    if kn > 0:
        y = 1380 + (1 - kn) * 40
        rgba(ctx, WHITE, kn); rrect(ctx, 130, y, W - 260, 140, 70); ctx.fill()
        txt(ctx, "Twijfel? Laat je knie checken", W / 2, y + 62, 44, BG0, kn, shadow=False)
        txt(ctx, "Volgende: je schouder", W / 2, y + 112, 34, (0.1, 0.45, 0.4), kn, shadow=False)


FN = {"cold": s_cold, "titel": s_titel, "anatomie": s_anatomie, "functie": s_functie,
      "scheur": s_scheur, "klachten": s_klachten, "slot": s_slot}


def chrome(ctx, tg, name, t):
    rgba(ctx, WHITE, 0.12); rrect(ctx, 60, 110, W - 120, 10, 5); ctx.fill()
    rgba(ctx, RED if name != "slot" else GREEN, 1)
    rrect(ctx, 60, 110, max(10, (W - 120) * tg / TOTAL), 10, 5); ctx.fill()
    a = eo(p(tg, 3.2, 3.6))
    if a > 0:
        s = "WAT GEBEURT ER IN JE…"
        w = text_w(ctx, s, 30)
        rgba(ctx, WHITE, 0.12 * a); rrect(ctx, W / 2 - w / 2 - 26, 150, w + 52, 58, 29); ctx.fill()
        txt(ctx, s, W / 2, 190, 30, WHITE, 0.9 * a, shadow=False)
    if name == "slot":
        txt(ctx, "Algemene informatie, geen persoonlijk advies", W / 2, 262, 26, GREY, 0.8, bold=False, shadow=False)


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
    # quick in/out
    fin = p(t, 0, 0.08) if name != "cold" else 1
    fout = 1 - p(t, d - 0.08, d)
    ctx.paint_with_alpha(min(fin, fout))
    ctx.restore()
    if name != "scheur":
        vignette(ctx)
    chrome(ctx, tg, name, t)
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
    if sys.argv[1] == "still":
        name, t = sys.argv[2], float(sys.argv[3])
        d = dict(SCENES)[name]
        frame(name, t, d).write_to_png(sys.argv[4])
    else:
        render_scene(int(sys.argv[2]), sys.argv[3])
