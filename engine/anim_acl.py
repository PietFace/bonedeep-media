"""Bone Deep — ACL tear Short. Same scene timings/EVENTS as anim2 so music2.wav fits."""
import cairo, math, sys, os, subprocess, random
import anim2 as A
import anim3 as F
import anim4 as V
import knee_flex as L
import knee_still as K
from anim2 import (W, H, FPS, SCENES, START, TOTAL, EVENTS, rgba, txt, slam, background, vignette,
                   camera, ringburst, arrow, font, WHITE, GREY, CYAN, RED, YEL, GREEN, BG0,
                   icon_bolt, icon_swell, icon_squat)
from anim import p, eo, eio, back, clamp, rrect

d2r = math.pi / 180
Y0 = L.Y0

# ACL / PCL attachments (lateral view): femur frame / tibia frame
ACL_F, ACL_T = (-62, 34), (46, Y0)
PCL_F, PCL_T = (34, 46), (-96, Y0 + 26)


def tib_pt(pt, th, dx):
    return L.rot((pt[0] + dx, pt[1]), th)


def mix(a, b, k):
    return tuple(x + (y - x) * k for x, y in zip(a, b))


def draw_cruciate(ctx, a, b, w, tension=0.0, torn=0.0, seed=1, sparks_t=None):
    col = mix(K.LIG_L, (1.0, 0.45, 0.40), clamp(tension))
    colD = mix(K.LIG_D, (0.65, 0.12, 0.10), clamp(tension))
    if tension > 0 and torn <= 0:
        for gw, ga in ((w * 3, 0.10), (w * 2, 0.18)):
            ctx.move_to(*a); ctx.line_to(*b)
            rgba(ctx, RED if tension > 0.5 else YEL, ga * tension); ctx.set_line_width(gw)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
    if torn <= 0:
        L.band(ctx, a, b, w, w * 0.85, col=col, colD=colD, seed=seed, fib=10)
        return
    # two frayed stumps retracting
    k = 0.42 - 0.08 * eo(torn)
    ma = mix(a, b, k)
    mb = mix(b, a, k)
    L.band(ctx, a, ma, w, w * 0.7, col=col, colD=colD, seed=seed, fib=8)
    L.band(ctx, b, mb, w, w * 0.7, col=col, colD=colD, seed=seed + 1, fib=8)
    r = random.Random(seed)
    for end, base in ((ma, a), (mb, b)):
        ang = math.atan2(end[1] - base[1], end[0] - base[0])
        for i in range(9):
            aa = ang + r.uniform(-0.8, 0.8)
            ln = r.uniform(10, 26)
            ctx.move_to(*end); ctx.line_to(end[0] + math.cos(aa) * ln, end[1] + math.sin(aa) * ln)
            rgba(ctx, (0.95, 0.85, 0.80), 0.9); ctx.set_line_width(2.5); ctx.stroke()
    if sparks_t is not None and 0 <= sparks_t < 0.7:
        m = mix(a, b, 0.5)
        r = random.Random(4)
        for i in range(30):
            aa = r.uniform(0, 2 * math.pi); sp = r.uniform(200, 520)
            r0 = sp * sparks_t; r1 = r0 + 26 + r.uniform(0, 30)
            rgba(ctx, YEL if i % 3 else WHITE, 1 - sparks_t / 0.7); ctx.set_line_width(4)
            ctx.move_to(m[0] + math.cos(aa) * r0, m[1] + math.sin(aa) * r0)
            ctx.line_to(m[0] + math.cos(aa) * r1, m[1] + math.sin(aa) * r1); ctx.stroke()


def knee_lateral_acl(ctx, theta, dx=0.0, tension=0.0, torn=0.0, glow=0.0, sparks_t=None, show_pcl=True):
    sp = L.sprites()
    th = theta * d2r
    f = clamp(theta / 100)
    L.band(ctx, (-152, -140), tib_pt((-120, Y0 + 70), th, dx), 30, 24, seed=3, fib=8)
    sp["femur"].paint(ctx)
    ctx.save(); ctx.rotate(th); ctx.translate(dx, 0)
    sp["tibia"].paint(ctx)
    L.draw_menisci(ctx, -7 * f, -16 * f, glow)
    ctx.restore()
    # cruciates drawn "x-ray" style inside the joint
    rg = cairo.RadialGradient(-10, 110, 10, -10, 110, 150)
    rg.add_color_stop_rgba(0, 0.05, 0.03, 0.03, 0.30); rg.add_color_stop_rgba(1, 0.05, 0.03, 0.03, 0)
    ctx.save(); ctx.set_source(rg); ctx.arc(-10, 110, 150, 0, 2 * math.pi); ctx.fill(); ctx.restore()
    if show_pcl:
        draw_cruciate(ctx, PCL_F, tib_pt(PCL_T, th, dx), 34, seed=11)
    draw_cruciate(ctx, ACL_F, tib_pt(ACL_T, th, dx), 30, tension=tension, torn=torn, seed=21, sparks_t=sparks_t)
    # patella + tendons (same solver as knee_flex)
    tub = tib_pt((128, Y0 + 100), th, dx)
    best = None
    for i in range(240):
        s_ = 0.02 + 0.96 * i / 239
        pt, (tx, ty) = L.track_at(s_)
        nx, ny = ty, -tx
        c = (pt[0] + nx * L.PAT_OFF, pt[1] + ny * L.PAT_OFF)
        distal = (c[0] + tx * L.PAT_HALF, c[1] + ty * L.PAT_HALF)
        err = abs(math.dist(distal, tub) - L.LPT)
        if best is None or err < best[0]:
            best = (err, c, (tx, ty), distal)
    _, c, (tx, ty), distal = best
    prox = (c[0] - tx * L.PAT_HALF, c[1] - ty * L.PAT_HALF)
    L.band(ctx, (128, -380), prox, 60, 52, seed=5, fib=12)
    L.band(ctx, distal, tub, 40, 34, seed=7, fib=10)
    ctx.save(); ctx.translate(*c); ctx.rotate(math.atan2(ty, tx)); ctx.scale(L.PAT_SC, L.PAT_SC)
    sp["patella"].paint(ctx); ctx.restore()


def side(ctx, theta, zoom=1.2, cx=620, cy=980, **kw):
    extra = kw.pop("extra", None)
    ctx.save(); ctx.translate(cx, cy); ctx.scale(L.SC * zoom, L.SC * zoom)
    knee_lateral_acl(ctx, theta, **kw)
    if extra:
        extra(ctx)
    ctx.restore()


# front view ACL centre line (anim3 coordinates)
ACL_FRONT = [(542, 1106), (530, 1050), (519, 1000), (523, 948)]


def front_acl_glow(ctx, g, col=RED, torn=0.0):
    if g <= 0 and torn <= 0:
        return
    if g > 0:
        for w, a in ((70, 0.08), (44, 0.16), (26, 0.28)):
            ctx.move_to(*ACL_FRONT[0]); ctx.curve_to(*ACL_FRONT[1], *ACL_FRONT[2], *ACL_FRONT[3])
            rgba(ctx, col, a * g); ctx.set_line_width(w); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
    if torn > 0:
        # jagged rupture across the middle, with frayed fibres
        m = (526, 1028)
        ctx.save(); ctx.translate(*m); ctx.rotate(-0.12)
        gap = 7 + 9 * eo(torn)
        top = [(-27 + i * 6.75, -gap + (4 if i % 2 else -4)) for i in range(9)]
        bot = [(-27 + i * 6.75, gap + (4 if i % 2 == 0 else -4)) for i in range(9)]
        ctx.move_to(*top[0])
        for q in top[1:]:
            ctx.line_to(*q)
        for q in reversed(bot):
            ctx.line_to(*q)
        ctx.close_path()
        rgba(ctx, (0.10, 0.02, 0.02), torn); ctx.fill()
        r = random.Random(8)
        for side_, pts in ((-1, top), (1, bot)):
            for x, y in pts:
                for _ in range(1):
                    ln = r.uniform(4, 9)
                    ctx.move_to(x, y); ctx.line_to(x + r.uniform(-5, 5), y + side_ * -ln * 0 + side_ * ln * 0.2 - side_ * ln)
                    rgba(ctx, (0.96, 0.88, 0.84), 0.85 * torn); ctx.set_line_width(2); ctx.stroke()
        ctx.restore()


def icon_pop(ctx, s, col):
    n = 12
    ctx.move_to(0, -110 * s)
    for i in range(1, 2 * n + 1):
        r = (110 if i % 2 == 0 else 52) * s
        a = -math.pi / 2 + i * math.pi / n
        ctx.line_to(r * math.cos(a), r * math.sin(a))
    ctx.close_path(); rgba(ctx, col, 1); ctx.fill()


def klachten(ctx, t, items):
    i = min(3, int(t // 2.0))
    lt = t - i * 2.0
    big, l1, l2, ic = items[i]
    k = back(p(lt, 0.05, 0.4))
    cx, cy = W / 2, 1120
    ctx.save(); ctx.translate(cx, cy); s = 1.3 - 0.3 * eo(p(lt, 0.05, 0.4)); ctx.scale(s * k, s * k)
    for r, a in ((290, 0.06), (250, 0.10), (215, 0.16)):
        rgba(ctx, RED, a); ctx.arc(0, 0, r, 0, 2 * math.pi); ctx.fill()
    rgba(ctx, RED, 1); ctx.arc(0, 0, 185, 0, 2 * math.pi); ctx.fill()
    if ic is icon_swell:
        ic(ctx, 1.1, WHITE, lt)
    else:
        ctx.save()
        if ic in (icon_bolt, icon_pop):
            ctx.rotate(0.06 * math.sin(lt * 30) * math.exp(-lt * 2))
        ic(ctx, 1.15, WHITE); ctx.restore()
    ctx.restore()
    ringburst(ctx, cx, cy, lt - 0.05, RED, 420, 0.7)
    vignette(ctx)
    slam(ctx, [big], 470, lt, 0.05, 170 if len(big) < 9 else 140, base=RED)
    slam(ctx, [l1, l2], 600, lt, 0.35, 56, base=GREY)
    for j in range(4):
        rgba(ctx, RED if j <= i else (0.3, 0.32, 0.38), 1)
        ctx.arc(W / 2 - 75 + j * 50, 1500, 10, 0, 2 * math.pi); ctx.fill()


# ---------------- scenes ----------------
def s_cold(ctx, t, d):
    snap = 1.3
    dx = 34 * eio(p(t, 0.1, snap)) + (10 * eo(p(t, snap, snap + 0.2)) if t > snap else 0)
    tension = p(t, 0.2, snap) if t < snap else 0
    torn = eo(p(t, snap, snap + 0.3))
    zoom = 2.1 + 0.15 * eo(p(t, snap, 3.2))
    side(ctx, 12, zoom=zoom, cx=640, cy=900, dx=dx, tension=tension, torn=torn,
         sparks_t=(t - snap) if t >= snap else None)
    vignette(ctx, red=0.6 * p(t, 0, snap) * (1 - p(t, 1.5, 3)))
    F.text_fade(ctx)
    slam(ctx, ["ONE BAD", "LANDING…"], 420, t, 0.1, 130, out_t=1.2)
    slam(ctx, ["*ACL", "*TEAR"], 420, t, 1.4, 160, stagger=0.12)


def s_titel(ctx, t, d):
    z = 1.0 + 0.08 * t / d
    F.knee(ctx, z, (540, 1060), dim=0.45, extra=lambda c: front_acl_glow(c, 0.6 + 0.4 * math.sin(t * 6)))
    vignette(ctx); F.text_fade(ctx)
    slam(ctx, ["What *really", "happens when", "your ~ACL tears?"], 440, t, 0.1, 116, stagger=0.09)


def s_anatomie(ctx, t, d):
    k = eio(p(t, 0.0, 1.4))
    zoom = 2.8 - 1.2 * k
    fx, fy = 530, 1020 - 20 * k
    ig = p(t, 1.3, 1.6)
    pulse = (0.6 + 0.4 * math.sin((t - 1.3) * 6)) if t > 1.3 else 0.3

    def extra(c):
        front_acl_glow(c, pulse * max(ig, 0.3), CYAN)
        if t > 3.0:
            kk = p(t, 3.0, 3.6)
            for s_, tx, ty, lx, ly in (("ACL", 510, 990, 330, 900), ("PCL", 572, 975, 760, 900)):
                rgba(c, CYAN if s_ == "ACL" else GREY, kk); c.arc(tx, ty, 6, 0, 2 * math.pi); c.fill()
                c.set_line_width(3); c.move_to(tx, ty)
                c.line_to(tx + (lx - tx) * eo(kk), ty + (ly - ty) * eo(kk)); c.stroke()
                txt(c, s_, lx, ly - 14, 44, CYAN if s_ == "ACL" else GREY, p(kk, 0.5, 1))
    F.knee(ctx, zoom, (fx, fy), extra=extra)
    vignette(ctx); F.text_fade(ctx)
    slam(ctx, ["Your ^ACL"], 420, t, 1.4, 140)
    slam(ctx, ["a ~rope deep inside your knee"], 560, t, 2.2, 62, stagger=0.07)


def s_functie(ctx, t, d):
    hits = [te for te, _ in EVENTS["functie"]]
    comp = 0
    for te in hits:
        if t >= te:
            comp = max(comp, math.exp(-(t - te) * 6))

    def extra(c):
        if t > 3.2:
            a = eo(p(t, 3.2, 3.6))
            tb = tib_pt((150, Y0 + 170), 18 * d2r, 16 * comp)
            arrow(c, tb[0] + 20, tb[1], tb[0] + 200, tb[1], YEL, a, lw=22, head=60)
    side(ctx, 18, zoom=1.35, cx=600, cy=980, dx=16 * comp, tension=0.6 * comp, glow=0.2, extra=extra)
    vignette(ctx); F.text_fade(ctx)
    if t > 0.5:
        n = int(round(200 * eo(p(t, 0.5, 1.5))))
        ka = eo(p(t, 0.5, 0.7))
        ctx.save(); s = 1 + 0.2 * comp
        ctx.translate(W / 2, 440); ctx.scale(s, s); ctx.translate(-W / 2, -440)
        lbl = f"± {n} kg"
        for gw, ga in ((24, 0.08), (12, 0.15)):
            font(ctx, 170); e = ctx.text_extents(lbl)
            ctx.move_to(W / 2 - e.x_advance / 2, 500); ctx.text_path(lbl)
            rgba(ctx, YEL, ga * ka); ctx.set_line_width(gw); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke()
        txt(ctx, lbl, W / 2, 500, 170, YEL, ka)
        ctx.restore()
    slam(ctx, ["of force before a young ACL snaps"], 600, t, 1.0, 52, stagger=0.06)
    slam(ctx, ["it stops your shin sliding ^forward"], 680, t, 3.2, 52, stagger=0.06)


def s_scheur(ctx, t, d):
    pop = 4.75
    if t < 3.0:
        theta = 45 - 30 * eio(p(t, 0.2, 2.6))
        side(ctx, theta, zoom=1.2, cx=640, cy=960, glow=0.3, tension=0.2 * p(t, 1.6, 3.0))
        vignette(ctx)
    else:
        k = p(t, 3.0, pop)
        fdx = 22 * eio(k) + 6 * math.sin((t - 3) * 18) * k
        frot = 0.035 * eio(k)
        torn = eo(p(t, pop, pop + 0.25))
        zoom = 1.25 + 0.9 * eio(p(t, 3.0, 4.6)) + (0.15 * eo(p(t, pop, 7)) if t > pop else 0)

        def extra(c):
            c.save(); c.translate(540 + fdx, 760); c.rotate(frot); c.translate(-540, -760)
            front_acl_glow(c, (0.3 + 0.7 * k) if t < pop else 0.9 * math.exp(-(t - pop) * 1.5), RED, torn)
            c.restore()
            if t >= pop and t - pop < 0.7:
                st = t - pop; r = random.Random(4)
                for i in range(30):
                    aa = r.uniform(0, 2 * math.pi); sp_ = r.uniform(150, 420)
                    r0 = sp_ * st; r1 = r0 + 22 + r.uniform(0, 26)
                    rgba(c, YEL if i % 3 else WHITE, 1 - st / 0.7); c.set_line_width(3.5)
                    c.move_to(526 + math.cos(aa) * r0, 1028 + math.sin(aa) * r0)
                    c.line_to(526 + math.cos(aa) * r1, 1028 + math.sin(aa) * r1); c.stroke()
            if 3.1 < t < pop:
                a = eo(p(t, 3.1, 3.4)) * (1 - p(t, 4.5, pop))
                arrow(c, 300, 1020, 420, 1020, WHITE, a, lw=12, head=40)
                c.save(); c.translate(540, 1500); c.scale(1, 0.25)
                c.arc(0, 0, 320, 0.3 + (t - 3) * 3, 1.8 + (t - 3) * 3); c.restore()
                rgba(c, WHITE, 0.8 * a); c.set_line_width(10); c.stroke()
        flip = eo(p(t, 3.0, 3.3))
        ctx.save(); ctx.translate(W / 2, 1060); ctx.scale(0.3 + 0.7 * flip, 1); ctx.translate(-W / 2, -1060)
        F.knee(ctx, zoom, (530, 1030), fdx=fdx, frot=frot, glow=0.2, extra=extra)
        ctx.restore()
        red = 0.8 * k * (1 - p(t, pop + 0.3, pop + 1.5)) + (0.6 * math.exp(-(t - pop) * 3) if t >= pop else 0)
        vignette(ctx, red=red)
    F.text_fade(ctx)
    slam(ctx, ["You ^land or ^stop suddenly…"], 430, t, 0.2, 70, out_t=1.45)
    slam(ctx, ["knee almost ^straight…"], 430, t, 1.6, 82, out_t=2.85)
    slam(ctx, ["it *caves *in and *twists"], 430, t, 3.0, 82, out_t=4.6)
    slam(ctx, ["*POP"], 480, t, pop + 0.05, 240)
    slam(ctx, ["many people ^feel or ^hear it"], 610, t, 6.2, 56, stagger=0.06)


def s_klachten(ctx, t, d):
    klachten(ctx, t, [("POP", "felt or heard", "at the moment of injury", icon_pop),
                      ("SWELLING", "usually within", "a few hours", icon_swell),
                      ("GIVING WAY", "the knee feels", "unstable when you turn", icon_squat),
                      ("PAIN", "hard to keep", "playing or walking", icon_bolt)])


def s_slot(ctx, t, d):
    th = clamp(50 - 50 * math.cos(max(0, t - 1.0) * 2.4), 0, 100) if t > 1.0 else 0
    ka = eo(p(t, 1.0, 1.5))
    if ka > 0:
        ctx.push_group()
        V.view_side(ctx, th, zoom=0.62, cx=650, cy=820)
        ctx.pop_group_to_source(); ctx.paint_with_alpha(0.9 * ka)
    vignette(ctx)
    slam(ctx, ["BUT…"], 400, t, 0.1, 140)
    slam(ctx, ["+good +news"], 540, t, 0.9, 110)
    slam(ctx, ["many people get back to sport", "with +solid +rehab"], 1180, t, 1.9, 54, stagger=0.05)
    slam(ctx, ["(with or without surgery)"], 1320, t, 2.8, 40, base=GREY)
    kn = eo(p(t, 3.4, 3.8))
    if kn > 0:
        y = 1390 + (1 - kn) * 40
        rgba(ctx, WHITE, kn); rrect(ctx, 130, y, W - 260, 140, 70); ctx.fill()
        txt(ctx, "Not sure? Get your knee checked", W / 2, y + 62, 42, BG0, kn, shadow=False)
        txt(ctx, "Next: your cracking knee", W / 2, y + 112, 34, (0.1, 0.45, 0.4), kn, shadow=False)


FN = {"cold": s_cold, "titel": s_titel, "anatomie": s_anatomie, "functie": s_functie,
      "scheur": s_scheur, "klachten": s_klachten, "slot": s_slot}


def frame(name, t, d):
    tg = START[name] + t
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf); ctx.set_antialias(cairo.ANTIALIAS_BEST)
    background(ctx, tg, (0.04, 0.18, 0.17) if name == "slot" else None)
    zoom, sx, sy, flash, fcol = camera(name, t)
    drift = 1 + 0.03 * t / d
    ctx.save()
    ctx.translate(W / 2 + sx, 1000 + sy); ctx.scale(zoom * drift, zoom * drift); ctx.translate(-W / 2, -1000)
    ctx.push_group(); FN[name](ctx, t, d); ctx.pop_group_to_source()
    fin = p(t, 0, 0.08) if name != "cold" else 1
    ctx.paint_with_alpha(min(fin, 1 - p(t, d - 0.08, d)))
    ctx.restore()
    F.chrome(ctx, tg, name)
    if flash > 0:
        rgba(ctx, fcol, flash * (0.85 if fcol == WHITE else 0.5)); ctx.paint()
    return surf


def render_scene(idx, outdir):
    name, d = SCENES[idx]
    n = int(round(d * FPS))
    tmp = os.path.join(outdir, f"tmp_{idx}_{name}.mp4"); fin = os.path.join(outdir, f"{idx}_{name}.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
           "-pix_fmt", "yuv420p", "-r", str(FPS), tmp]
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
