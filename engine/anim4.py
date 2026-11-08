"""Bone Deep — meniscus Short v4: front / side / top views with real motion.
Same scene timings and EVENTS as anim2 so music2.wav fits."""
import cairo, math, sys, os, subprocess, random
import anim2 as A
import anim3 as F            # front view (pre-rendered layers)
import knee_flex as L        # side view (articulated)
import knee_still as K
from anim2 import (W, H, FPS, SCENES, START, TOTAL, EVENTS, rgba, txt, slam, background, vignette,
                   camera, ringburst, arrow, font, WHITE, GREY, CYAN, RED, YEL, GREEN, BG0)
from anim import p, eo, eio, back, clamp, rrect, text_w

d2r = math.pi / 180

# ---------------- TOP VIEW (right tibia from above; anterior = up, medial = viewer's left) ----------------
MED_T = (-150, 6, 140, 146, 72, 288)     # medial meniscus: open C, opening toward the centre
LAT_T = (150, 0, 124, 128, -156, 156)    # lateral meniscus: almost an O


def plateau_top_path(c):
    c.move_to(-300, 0)
    c.curve_to(-300, -140, -150, -178, 0, -160)
    c.curve_to(150, -178, 300, -140, 300, 0)
    c.curve_to(300, 140, 170, 178, 70, 166)
    c.curve_to(40, 162, 25, 138, 0, 138)
    c.curve_to(-25, 138, -40, 162, -70, 166)
    c.curve_to(-170, 178, -300, 140, -300, 0)
    c.close_path()


def draw_top_static(c):
    K.soft_shadow(c, plateau_top_path, 10, 16, 0.5, 60)
    K.textured(c, plateau_top_path, K.BONE_L, K.BONE_D, -300, -180, 300, 180, pores=400,
               pore_area=(-300, -180, 300, 180), inner=0.35, grain=0.18, spec=(-80, -60, 260, 0.25))
    for cx, cy, rx, ry in ((-150, 8, 108, 114), (150, 2, 98, 104)):
        K.textured(c, lambda cc, a=(cx, cy, rx, ry): K.ell(cc, *a), K.CART_L, K.CART_D, cx - rx, cy - ry,
                   cx + rx, cy + ry, inner=0.2, grain=0.04, edge=(0.5, 0.55, 0.62), spec=(cx - 30, cy - 30, 80, 0.5))
    # cruciate footprints
    for (x, y, rx, ry) in ((-14, -78, 34, 22), (6, 112, 30, 22)):
        K.textured(c, lambda cc, a=(x, y, rx, ry): K.ell(cc, *a), K.LIG_L, K.LIG_D, x - rx, y, x + rx, y,
                   inner=0.2, grain=0.05, edge=(0.45, 0.4, 0.35), cyl=True)
    K.meniscus(c, *MED_T[:4], MED_T[4], MED_T[5], w=44, depth=0)
    K.meniscus(c, *LAT_T[:4], LAT_T[4], LAT_T[5], w=40, depth=0)


def condyles_path(c):
    # femoral condyles seen from above (ghost), with intercondylar notch
    c.move_to(-275, -10)
    c.curve_to(-275, -150, -140, -175, -60, -120)
    c.curve_to(-30, -100, 30, -100, 60, -118)
    c.curve_to(140, -168, 265, -140, 265, -10)
    c.curve_to(265, 120, 170, 160, 120, 158)
    c.curve_to(70, 156, 40, 90, 0, 80)
    c.curve_to(-40, 90, -70, 160, -130, 162)
    c.curve_to(-190, 164, -275, 130, -275, -10)
    c.close_path()


def draw_condyles(c):
    K.textured(c, condyles_path, (0.98, 0.93, 0.80), (0.80, 0.66, 0.45), -275, -170, 265, 165, pores=250,
               pore_area=(-275, -170, 265, 165), inner=0.5, grain=0.15, spec=(-120, -60, 200, 0.35))


TOP = {}


def top_sprites():
    if not TOP:
        TOP["plateau"] = L.Sprite((-340, -230, 340, 250), draw_top_static)
        TOP["condyles"] = L.Sprite((-300, -200, 290, 190), draw_condyles)
    return TOP


def med_tear_path(ctx, k):
    cx, cy, rx, ry, _, _ = MED_T
    a0, a1 = 80 * d2r, 150 * d2r        # posterior horn (posterior = down)
    end = a0 + (a1 - a0) * k
    n = 36
    first = True
    for i in range(n + 1):
        ang = a0 + (a1 - a0) * i / n
        if ang > end:
            break
        j = 0.03 * math.sin(i * 2.9) * (1 if i % 2 else -1)
        x = cx + rx * (1 + j) * math.cos(ang)
        y = cy + ry * (1 + j) * math.sin(ang)
        if first:
            ctx.move_to(x, y); first = False
        else:
            ctx.line_to(x, y)


def draw_top(ctx, phi=0.0, ghost=0.75, glow=0.0, pinch=0.0, tear=0.0, sparks_t=None, lift=0.0):
    sp = top_sprites()
    sp["plateau"].paint(ctx)
    # meniscus glow
    for m in (MED_T, LAT_T):
        if glow > 0:
            cx, cy, rx, ry, a0, a1 = m
            for w, a in ((110, 0.06), (80, 0.10), (56, 0.16)):
                ctx.save(); ctx.translate(cx, cy); ctx.scale(rx / 100, ry / 100)
                ctx.arc(0, 0, 100, a0 * d2r, a1 * d2r); ctx.restore()
                rgba(ctx, CYAN, a * glow); ctx.set_line_width(w); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
    # pinch on the medial posterior horn
    if pinch > 0:
        cx, cy, rx, ry, _, _ = MED_T
        for w, a in ((120, 0.10), (80, 0.18), (50, 0.30)):
            ctx.save(); ctx.translate(cx, cy); ctx.scale(rx / 100, ry / 100)
            ctx.arc(0, 0, 100, 76 * d2r, 155 * d2r); ctx.restore()
            rgba(ctx, RED, a * pinch); ctx.set_line_width(w); ctx.stroke()
    # tear
    if tear > 0:
        ctx.set_line_join(cairo.LINE_JOIN_MITER); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        for w, a, col in ((36, 0.22, RED), (18, 0.45, RED), (8, 1.0, (0.30, 0.0, 0.02)), (2.5, 0.9, (1, 0.5, 0.45))):
            med_tear_path(ctx, tear); rgba(ctx, col, a); ctx.set_line_width(w); ctx.stroke()
    if sparks_t is not None and 0 <= sparks_t < 0.7:
        cx, cy, rx, ry, _, _ = MED_T
        r = random.Random(9)
        for i in range(34):
            ang = r.uniform(82, 148) * d2r
            x0, y0 = cx + rx * math.cos(ang), cy + ry * math.sin(ang)
            dx, dy = math.cos(ang + r.uniform(-0.9, 0.9)), math.sin(ang + r.uniform(-0.9, 0.9))
            sp_ = r.uniform(200, 560)
            r0 = sp_ * sparks_t; r1 = r0 + 28 + r.uniform(0, 40)
            rgba(ctx, YEL if i % 3 else WHITE, 1 - sparks_t / 0.7); ctx.set_line_width(4)
            ctx.move_to(x0 + dx * r0, y0 + dy * r0); ctx.line_to(x0 + dx * r1, y0 + dy * r1); ctx.stroke()
    # femoral condyles above (ghost), rotating with the thigh
    if ghost > 0:
        ctx.save(); ctx.translate(0, -lift); ctx.rotate(phi)
        ctx.push_group()
        sp["condyles"].paint(ctx)
        ctx.pop_group_to_source(); ctx.paint_with_alpha(ghost)
        condyles_path(ctx); ctx.set_dash([16, 12]); rgba(ctx, WHITE, 0.8 * ghost / 0.75)
        ctx.set_line_width(4); ctx.stroke(); ctx.set_dash([])
        ctx.restore()


def twist_arrows(ctx, t, a, R=360):
    if a <= 0:
        return
    for side in (1, -1):
        a0 = (-math.pi / 2 if side > 0 else math.pi / 2) + 0.4 * math.sin(t * 5)
        ctx.new_path()
        ctx.arc(0, 0, R, a0 - 0.7, a0 + 0.7)
        rgba(ctx, WHITE, 0.85 * a); ctx.set_line_width(12); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
        ae = a0 + 0.7
        ex, ey = R * math.cos(ae), R * math.sin(ae)
        tx, ty = -math.sin(ae), math.cos(ae)
        arrow(ctx, ex - tx * 24, ey - ty * 24, ex + tx * 18, ey + ty * 18, WHITE, 0.85 * a, lw=2, head=46, glow=False)


def view_top(ctx, zoom, focus, **kw):
    """Place top view: world (0,0) at screen focus mapping."""
    ctx.save()
    ctx.translate(W / 2, 1060); ctx.scale(zoom, zoom); ctx.translate(-focus[0], -focus[1])
    extra = kw.pop("extra", None)
    draw_top(ctx, **kw)
    if extra:
        extra(ctx)
    ctx.restore()


def view_side(ctx, theta, glow=0.0, fdy=0.0, zoom=1.0, cx=L.CX, cy=L.CY, sc=L.SC, extra=None):
    ctx.save()
    ctx.translate(cx, cy); ctx.scale(sc * zoom, sc * zoom)
    L.knee_lateral(ctx, theta, glow=glow, fdy=fdy)
    if extra:
        extra(ctx)
    ctx.restore()


def top_labels(ctx, k):
    if k <= 0:
        return
    for s_, tx, ty, lx, ly in (("inner meniscus", -250, 100, -230, 290), ("outer meniscus", 250, 90, 230, 290)):
        rgba(ctx, CYAN, k); ctx.arc(tx, ty, 8, 0, 2 * math.pi); ctx.fill()
        ex, ey = tx + (lx - tx) * eo(k), ty + (ly - ty) * eo(k)
        ctx.set_line_width(3.5); ctx.move_to(tx, ty); ctx.line_to(ex, ey); ctx.stroke()
        txt(ctx, s_, lx, ly + 46, 36, CYAN, p(k, 0.5, 1))
    txt(ctx, "FRONT", 0, -205, 30, GREY, 0.8 * k, shadow=False)


# ---------------- scenes ----------------
def s_cold(ctx, t, d):
    ramp = eo(p(t, 0, 0.35)) * (1 - p(t, 1.3, 1.45))
    phi = 0.20 * math.sin(t * 9) * ramp
    tear = eo(p(t, 1.3, 1.55))
    pinch = clamp(abs(phi) / 0.2) * (1 - p(t, 1.3, 1.6)) + 0.6 * tear * (0.6 + 0.4 * math.sin(t * 7))
    zoom = 1.9 + 0.2 * eo(p(t, 1.3, 3.2))
    view_top(ctx, zoom, (-130, 90), phi=phi, ghost=0.55 * (1 - p(t, 1.3, 1.8)) + 0.12,
             pinch=pinch, tear=tear, sparks_t=(t - 1.3) if t >= 1.3 else None, glow=0.3)
    vignette(ctx, red=0.5 * p(t, 0, 1.3) * (1 - p(t, 1.5, 3)))
    F.text_fade(ctx)
    slam(ctx, ["ONE WRONG", "TWIST…"], 420, t, 0.1, 130, out_t=1.2)
    slam(ctx, ["*MENISCUS", "*TEAR"], 420, t, 1.4, 150, stagger=0.12)


def s_titel(ctx, t, d):
    z = 1.0 + 0.08 * t / d
    F.knee(ctx, z, (540, 1060), dim=0.45, glow=0.6 + 0.4 * math.sin(t * 6))
    vignette(ctx); F.text_fade(ctx)
    slam(ctx, ["What *really", "happens inside", "your ~knee?"], 440, t, 0.1, 120, stagger=0.09)


def s_anatomie(ctx, t, d):
    # front view first, then a quick flip to the top view to show the C and the O
    if t < 3.4:
        k = eio(p(t, 0.0, 1.3))
        ig = p(t, 1.3, 1.6)
        pulse = (0.6 + 0.4 * math.sin((t - 1.3) * 6)) if t > 1.3 else 0

        def extra(c):
            ringburst(c, F.LAT[0], F.LAT[1], t - 1.3, CYAN, 220)
            ringburst(c, F.MED[0], F.MED[1], t - 1.3, CYAN, 220)
        F.knee(ctx, 2.3 - 1.3 * k, (540, 1090 - 70 * k), glow=pulse * ig, extra=extra)
    else:
        k = eo(p(t, 3.4, 4.0))
        ctx.save(); ctx.translate(W / 2, 1060); ctx.scale(1, 0.3 + 0.7 * k); ctx.translate(-W / 2, -1060)
        view_top(ctx, 1.2, (0, 40), ghost=0.0, glow=0.6 + 0.3 * math.sin(t * 6),
                 extra=lambda c: top_labels(c, p(t, 4.0, 4.6)))
        ctx.restore()
    vignette(ctx); F.text_fade(ctx)
    slam(ctx, ["^2 menisci"], 420, t, 1.4, 140)
    slam(ctx, ["your knee's ~shock ~absorbers"], 560, t, 2.2, 66, stagger=0.07)


def s_functie(ctx, t, d):
    hits = [te for te, _ in EVENTS["functie"]]
    comp = 0
    for te in hits:
        if t >= te:
            comp = max(comp, math.exp(-(t - te) * 6))
    theta = 70 * eio(p(t, 3.2, 4.4))
    zoom = 1.25

    def extra(c):
        # load arrow coming down the thigh
        if t >= hits[0] - 0.2:
            last = max([te for te in hits if te <= t + 0.2] or [hits[0]])
            drop = eo(p(t - last, -0.2, 0.0))
            off = (1 - drop) * -150
            arrow(c, 0, -620 + off, 0, -360 + off + 14 * comp, RED, 1, lw=34, head=90)
        for te in hits:
            ringburst(c, 0, L.R + 6, t - te, RED, 240, 0.5)
    view_side(ctx, theta, glow=0.3 + 0.7 * comp, fdy=10 * comp, zoom=zoom, cx=600, cy=1000, extra=extra)
    vignette(ctx); F.text_fade(ctx)
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
    if t > 4.4:
        txt(ctx, "menisci glide back", W / 2, 1640, 40, CYAN, eo(p(t, 4.4, 4.8)))


def s_scheur(ctx, t, d):
    tear_t = 4.75
    if t < 3.0:
        # side view: planted foot, knee bends
        theta = 15 + 45 * eio(p(t, 1.6, 2.8))
        view_side(ctx, theta, glow=0.4, zoom=1.15, cx=640, cy=960)
        vignette(ctx)
    else:
        zin = eio(p(t, 3.0, 4.7))
        zoom = 1.25 + 0.6 * zin + (0.15 * eo(p(t, tear_t, 6.8)) if t > tear_t else 0)
        fx, fy = -120 * zin, 90 * zin
        phi = 0.0
        if t < tear_t:
            k = p(t, 3.0, 4.6)
            phi = (0.06 + 0.22 * k) * math.sin((t - 3.0) * (7 + 10 * k))
        tear = eo(p(t, tear_t, tear_t + 0.25))
        pinch = (clamp(abs(phi) / 0.25) if t < tear_t else 0) + 0.7 * tear * (0.6 + 0.4 * math.sin(t * 7))
        flip = eo(p(t, 3.0, 3.35))
        ctx.save(); ctx.translate(W / 2, 1060); ctx.scale(1, 0.25 + 0.75 * flip); ctx.translate(-W / 2, -1060)
        view_top(ctx, zoom, (fx, fy), phi=phi, ghost=0.7 * (1 - p(t, tear_t, tear_t + 0.6)) + 0.1,
                 pinch=pinch, tear=tear, glow=0.3, sparks_t=(t - tear_t) if t >= tear_t else None,
                 extra=lambda c: twist_arrows(c, t, eo(p(t, 3.2, 3.5)) * (1 - p(t, 4.5, tear_t)), 380))
        ctx.restore()
        red = 0.8 * p(t, 3.0, 4.7) * (1 - p(t, tear_t + 0.3, tear_t + 1.5))
        if t >= tear_t:
            red += 0.6 * math.exp(-(t - tear_t) * 3)
        vignette(ctx, red=red)
    F.text_fade(ctx)
    slam(ctx, ["Your foot is ^planted…"], 430, t, 0.2, 80, out_t=1.45)
    slam(ctx, ["your knee is ^bent…"], 430, t, 1.6, 84, out_t=2.85)
    slam(ctx, ["and then you *TWIST"], 430, t, 3.0, 88, out_t=4.6)
    slam(ctx, ["*TEAR"], 470, t, tear_t + 0.05, 230)
    slam(ctx, ["after 40, often from", "^wear ^and ^tear too"], 600, t, 6.4, 56, stagger=0.06)


def s_slot(ctx, t, d):
    theta = 50 - 50 * math.cos(max(0, t - 1.0) * 2.4) / 1 if t > 1.0 else 0
    theta = clamp(theta, 0, 100)
    ka = eo(p(t, 1.0, 1.5))
    if ka > 0:
        ctx.push_group()
        view_side(ctx, theta, glow=0.0, zoom=0.62, cx=650, cy=820)
        ctx.pop_group_to_source(); ctx.paint_with_alpha(0.9 * ka)
    vignette(ctx)
    slam(ctx, ["BUT…"], 400, t, 0.1, 140)
    slam(ctx, ["+good +news"], 540, t, 0.9, 110)
    slam(ctx, ["symptoms often improve", "with targeted +exercise +therapy"], 1180, t, 1.9, 54, stagger=0.05)
    slam(ctx, ["(especially wear-related tears)"], 1320, t, 2.8, 40, base=GREY)
    kn = eo(p(t, 3.4, 3.8))
    if kn > 0:
        y = 1390 + (1 - kn) * 40
        rgba(ctx, WHITE, kn); rrect(ctx, 130, y, W - 260, 140, 70); ctx.fill()
        txt(ctx, "Not sure? Get your knee checked", W / 2, y + 62, 42, BG0, kn, shadow=False)
        txt(ctx, "Next: your ACL", W / 2, y + 112, 34, (0.1, 0.45, 0.4), kn, shadow=False)


FN = {"cold": s_cold, "titel": s_titel, "anatomie": s_anatomie, "functie": s_functie,
      "scheur": s_scheur, "klachten": F.s_klachten, "slot": s_slot}


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
    F.chrome(ctx, tg, name)
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
        frame(name, t, dict(SCENES)[name]).write_to_png(sys.argv[4])
    else:
        render_scene(int(sys.argv[2]), sys.argv[3])
