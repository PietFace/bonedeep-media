"""Bone Deep — shoulder Short (painful arc / rotator cuff). Same timings/EVENTS as anim2 -> music2.wav."""
import cairo, math, sys, os, subprocess
import anim2 as A
import anim3 as F
import anim_acl as AC
import shoulder as SH
from anim2 import (W, H, FPS, SCENES, START, TOTAL, EVENTS, rgba, txt, slam, background, vignette,
                   camera, ringburst, arrow, font, WHITE, GREY, CYAN, RED, YEL, GREEN, BG0, icon_bolt)
from anim import p, eo, eio, back, clamp, rrect

d2r = math.pi / 180


def view(ctx, alpha, zoom=1.0, focus=(60, 60), cx=W / 2, cy=1050, extra=None, **kw):
    ctx.save()
    ctx.translate(cx, cy); ctx.scale(zoom, zoom); ctx.translate(-focus[0], -focus[1])
    beta, Hh, a = SH.shoulder(ctx, alpha, **kw)
    if extra:
        extra(ctx, beta, Hh, a)
    ctx.restore()


def flipx(ctx, k):
    ctx.translate(W / 2, 1050); ctx.scale(0.25 + 0.75 * k, 1); ctx.translate(-W / 2, -1050)


def tendon_point(beta, Hh):
    return SH.S((-20, -150), beta)


def lbl(c, s, tx, ty, lx, ly, k, col=CYAN):
    if k <= 0:
        return
    rgba(c, col, k); c.arc(tx, ty, 8, 0, 2 * math.pi); c.fill()
    c.set_line_width(4); c.move_to(tx, ty)
    c.line_to(tx + (lx - tx) * eo(k), ty + (ly - ty) * eo(k)); c.stroke()
    txt(c, s, lx, ly + (-16 if ly < ty else 50), 44, col, p(k, 0.5, 1))


# ---------------- icons ----------------
def icon_moon(ctx, s, col):
    ctx.push_group()
    ctx.arc(0, 0, 100 * s, 0, 2 * math.pi); rgba(ctx, col, 1); ctx.fill()
    ctx.set_operator(cairo.OPERATOR_CLEAR)
    ctx.arc(48 * s, -38 * s, 88 * s, 0, 2 * math.pi); ctx.fill()
    ctx.set_operator(cairo.OPERATOR_OVER)
    ctx.pop_group_to_source(); ctx.paint()
    for x, y, r in ((75, 50, 10), (40, 92, 6), (100, 0, 7)):
        ctx.arc(x * s, y * s, r * s, 0, 2 * math.pi); rgba(ctx, col, 1); ctx.fill()


def icon_dumbbell(ctx, s, col):
    rgba(ctx, col, 1)
    rrect(ctx, -70 * s, -12 * s, 140 * s, 24 * s, 10 * s); ctx.fill()
    for x in (-100, 70):
        rrect(ctx, x * s, -55 * s, 30 * s, 110 * s, 10 * s); ctx.fill()
    for x in (-125, 100):
        rrect(ctx, x * s, -35 * s, 25 * s, 70 * s, 8 * s); ctx.fill()


def icon_up(ctx, s, col):
    rgba(ctx, col, 1)
    ctx.move_to(0, -115 * s); ctx.line_to(80 * s, -20 * s); ctx.line_to(28 * s, -20 * s)
    ctx.line_to(28 * s, 110 * s); ctx.line_to(-28 * s, 110 * s); ctx.line_to(-28 * s, -20 * s)
    ctx.line_to(-80 * s, -20 * s); ctx.close_path(); ctx.fill()


# ---------------- scenes ----------------
def s_cold(ctx, t, d):
    hit = 1.3
    alpha = 100 * eio(p(t, 0.0, 1.2))
    pinch = SH.pinch_amount(alpha)
    zoom = 1.35 + 0.15 * eo(p(t, hit, 3.2))

    def extra(c, beta, Hh, a):
        tp = tendon_point(beta, Hh)
        ringburst(c, tp[0], tp[1], t - hit, RED, 300, 0.7)
    view(ctx, alpha, zoom=zoom, focus=(-10, -130), irritated=pinch, inflamed=pinch,
         tendon_glow=pinch * (1.3 if t > hit else 0.8), extra=extra)
    vignette(ctx, red=0.6 * pinch * (1 - p(t, 1.6, 3)))
    F.text_fade(ctx)
    slam(ctx, ["THAT PINCH WHEN", "YOU LIFT YOUR ARM…"], 420, t, 0.1, 90, out_t=1.2)
    slam(ctx, ["*SHOULDER", "*PAIN?"], 420, t, 1.4, 150, stagger=0.12)


def s_titel(ctx, t, d):
    alpha = 20 + 40 * eio(p(t, 0, d))
    ctx.push_group()
    view(ctx, alpha, zoom=1.0 + 0.06 * t / d, focus=(80, 100))
    ctx.pop_group_to_source(); ctx.paint_with_alpha(0.5)
    vignette(ctx); F.text_fade(ctx)
    slam(ctx, ["What *really", "happens inside", "your ~shoulder?"], 440, t, 0.1, 116, stagger=0.09)


def s_anatomie(ctx, t, d):
    k = eio(p(t, 0.0, 1.3))
    zoom = 2.4 - 1.35 * k
    focus = (-10 + 100 * k, -60 + 140 * k)

    def extra(c, beta, Hh, a):
        kk = p(t, 3.0, 3.6); kk2 = p(t, 3.3, 3.9); kk3 = p(t, 3.6, 4.2); kk4 = p(t, 3.9, 4.5)
        lbl(c, "ball", -30, 40, -330, 260, kk, WHITE)
        lbl(c, "socket", 128, 20, 420, 300, kk2, WHITE)
        lbl(c, "acromion", -100, -215, -230, -270, kk3, YEL)
        tp = SH.S((60, -145), beta)
        lbl(c, "rotator cuff tendon", tp[0], tp[1], 330, -270, kk4, CYAN)
    view(ctx, 0, zoom=zoom, focus=focus, tendon_glow=0.6 * p(t, 2.2, 2.6) * (0.6 + 0.4 * math.sin(t * 6)),
         deltoid_a=0.5 * (1 - p(t, 1.0, 2.0)) + 0.15, extra=extra)
    vignette(ctx); F.text_fade(ctx)
    slam(ctx, ["A ^ball in a ^shallow ^socket"], 420, t, 1.4, 84, stagger=0.07)
    slam(ctx, ["held by your ~rotator ~cuff"], 540, t, 2.2, 66, stagger=0.07)


def s_functie(ctx, t, d):
    hits = [te for te, _ in EVENTS["functie"]]
    comp = 0
    for te in hits:
        if t >= te:
            comp = max(comp, math.exp(-(t - te) * 5))
    if t < 3.1:
        ctx.save(); ctx.translate(W / 2, 1100); ctx.scale(0.92, 0.92)
        SH.cuff_view(ctx, t, squeeze=0.3 + 0.7 * comp, labels=eo(p(t, 0.6, 1.2)))
        ctx.restore()
    else:
        alpha = 150 * eio(p(t, 3.2, 5.8))
        ctx.save(); flipx(ctx, eo(p(t, 3.1, 3.4)))
        view(ctx, alpha, zoom=1.0, focus=(60, 30), tendon_glow=0.7, deltoid_a=0.35)
        ctx.restore()
    vignette(ctx); F.text_fade(ctx)
    if t > 0.5:
        ka = eo(p(t, 0.5, 0.7)) * (1 - p(t, 2.9, 3.1))
        ctx.save(); s = 1 + 0.2 * comp
        ctx.translate(W / 2, 440); ctx.scale(s, s); ctx.translate(-W / 2, -440)
        txt(ctx, "4", W / 2, 520, 220, YEL, ka)
        ctx.restore()
    slam(ctx, ["muscles keep the ball ~centred"], 610, t, 1.0, 56, stagger=0.06, out_t=2.95)
    slam(ctx, ["as you lift, the tendon", "glides ^under ^the ^roof"], 420, t, 3.2, 70, stagger=0.06)


def s_scheur(ctx, t, d):
    arc_t = 4.75
    if t < 3.0:
        alpha = 75 + 55 * math.sin(t * 7) * eo(p(t, 0, 0.3))
        irr = 0.2 + 0.8 * eo(p(t, 1.6, 3.0))
        view(ctx, alpha, zoom=1.15, focus=(20, 0), irritated=irr, inflamed=irr * 0.8,
             tendon_glow=irr * 0.6, deltoid_a=0.35)
        vignette(ctx, red=0.3 * irr)
    else:
        if t < arc_t:
            alpha = 25 + 65 * eio(p(t, 3.0, arc_t))
        else:
            alpha = 90 + 65 * eio(p(t, arc_t + 0.4, 7.6))
        pinch = SH.pinch_amount(alpha)

        def extra(c, beta, Hh, a):
            SH.painful_arc(c, Hh, alpha, eo(p(t, 3.0, 3.4)), R=540)
        view(ctx, alpha, zoom=0.82, focus=(-120, -70), irritated=max(pinch, 0.4), inflamed=pinch,
             tendon_glow=pinch * 1.2, deltoid_a=0.3, extra=extra)
        vignette(ctx, red=0.7 * pinch)
    F.text_fade(ctx)
    slam(ctx, ["Too much, ^too ^soon…"], 430, t, 0.2, 84, out_t=1.45)
    slam(ctx, ["the tendon gets ^irritated…"], 430, t, 1.6, 74, out_t=2.85)
    slam(ctx, ["and lifting starts to *HURT"], 430, t, 3.0, 74, out_t=4.6)
    slam(ctx, ["*PAINFUL", "*ARC"], 420, t, arc_t + 0.05, 150, stagger=0.12)
    slam(ctx, ["it hurts most between ^60° and ^120°"], 1720, t, 6.2, 50, stagger=0.05)


def s_klachten(ctx, t, d):
    AC.klachten(ctx, t, [("PAIN", "lifting your arm", "out to the side", icon_bolt),
                         ("NIGHT PAIN", "lying on", "that shoulder", icon_moon),
                         ("WEAKNESS", "reaching or", "carrying things", icon_dumbbell),
                         ("OVERHEAD", "reaching up", "hurts most", icon_up)])


def s_slot(ctx, t, d):
    alpha = clamp(75 - 75 * math.cos(max(0, t - 1.0) * 2.0), 0, 150) if t > 1.0 else 0
    ka = eo(p(t, 1.0, 1.5))
    if ka > 0:
        ctx.push_group()
        view(ctx, alpha, zoom=0.55, cx=600, cy=880, focus=(60, 60), deltoid_a=0.4)
        ctx.pop_group_to_source(); ctx.paint_with_alpha(0.9 * ka)
    vignette(ctx)
    slam(ctx, ["BUT…"], 400, t, 0.1, 140)
    slam(ctx, ["+good +news"], 540, t, 0.9, 110)
    slam(ctx, ["for most people, +targeted", "+exercise is the first step"], 1180, t, 1.9, 54, stagger=0.05)
    slam(ctx, ["(surgery often isn't needed)"], 1320, t, 2.8, 40, base=GREY)
    kn = eo(p(t, 3.4, 3.8))
    if kn > 0:
        y = 1390 + (1 - kn) * 40
        rgba(ctx, WHITE, kn); rrect(ctx, 110, y, W - 220, 140, 70); ctx.fill()
        txt(ctx, "Not sure? Get your shoulder checked", W / 2, y + 62, 40, BG0, kn, shadow=False)
        txt(ctx, "Next: your ankle", W / 2, y + 112, 34, (0.1, 0.45, 0.4), kn, shadow=False)


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
