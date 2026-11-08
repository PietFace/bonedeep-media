"""Bone Deep — 'Is your knee cracking bad?' Same scene timings/EVENTS as anim2 so music2.wav fits."""
import cairo, math, sys, os, subprocess, random
import anim2 as A
import anim3 as F
import anim4 as V
import anim_acl as AC
import knee_flex as L
from anim2 import (W, H, FPS, SCENES, START, TOTAL, EVENTS, rgba, txt, slam, background, vignette,
                   camera, ringburst, arrow, font, WHITE, GREY, CYAN, RED, YEL, GREEN, BG0,
                   icon_bolt, icon_swell, icon_lock, icon_squat)
from anim import p, eo, eio, back, clamp, rrect

d2r = math.pi / 180
R = L.R


def joint_glow(ctx, theta, a):
    if a <= 0:
        return
    ang = (90 + theta * 0.5) * d2r
    cx, cy = (R + 10) * math.cos(ang) * 0.6, (R + 10) * math.sin(ang) * 0.6
    g = cairo.RadialGradient(cx, cy, 20, cx, cy, 300)
    g.add_color_stop_rgba(0, CYAN[0], CYAN[1], CYAN[2], 0.35 * a)
    g.add_color_stop_rgba(1, CYAN[0], CYAN[1], CYAN[2], 0)
    ctx.set_source(g); ctx.arc(cx, cy, 300, 0, 2 * math.pi); ctx.fill()


def bubbles(ctx, t, theta, a, pops=(), seed=2, n=14):
    """Gas bubbles in the joint space; pop times make bubbles burst into rings."""
    if a <= 0:
        return
    r = random.Random(seed)
    base = 90 + theta
    for i in range(n):
        ang = (base + r.uniform(-28, 28)) * d2r
        rad = R + r.uniform(4, 30)
        wob = 3 * math.sin(t * 3 + i)
        x, y = rad * math.cos(ang) + wob, rad * math.sin(ang) + wob * 0.5
        size = r.uniform(10, 24)
        popped = None
        for pt in pops:
            if i % len(pops) == pops.index(pt) and t >= pt:
                popped = t - pt
        if popped is not None:
            if popped < 0.5:
                k = popped / 0.5
                rgba(ctx, WHITE, (1 - k) * a); ctx.set_line_width(3)
                ctx.arc(x, y, size + 70 * eo(k), 0, 2 * math.pi); ctx.stroke()
            continue
        g = cairo.RadialGradient(x - size * 0.3, y - size * 0.3, 1, x, y, size)
        g.add_color_stop_rgba(0, 1, 1, 1, 0.95 * a); g.add_color_stop_rgba(1, CYAN[0], CYAN[1], CYAN[2], 0.35 * a)
        ctx.set_source(g); ctx.arc(x, y, size, 0, 2 * math.pi); ctx.fill()


def burst_word(ctx, word, t, t0, col=YEL, size=200, y=480):
    k = p(t, t0, t0 + 0.25)
    if k <= 0:
        return
    s = 1.6 - 0.6 * eo(k)
    a = clamp(k * 3) * (1 - p(t, t0 + 1.0, t0 + 1.2))
    ctx.save(); ctx.translate(W / 2, y - size * 0.35); ctx.scale(s, s); ctx.rotate(-0.06)
    ctx.translate(-W / 2, -(y - size * 0.35))
    font(ctx, size); e = ctx.text_extents(word)
    for gw, ga in ((30, 0.10), (14, 0.2)):
        ctx.move_to(W / 2 - e.x_advance / 2, y); ctx.text_path(word)
        rgba(ctx, col, ga * a); ctx.set_line_width(gw); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke()
    txt(ctx, word, W / 2, y, size, col, a)
    ctx.restore()


# ---------------- scenes ----------------
def s_cold(ctx, t, d):
    crack = 1.3
    theta = 95 * eio(p(t, 0.1, crack))
    if t > crack:
        theta = 95 - 8 * math.exp(-(t - crack) * 5) * math.sin((t - crack) * 30)
    V.view_side(ctx, theta, glow=0.2, zoom=1.5, cx=700, cy=900,
                extra=lambda c: (joint_glow(c, theta, 0.6),
                                 bubbles(c, t, theta, 1.0, pops=(crack, crack + 0.05, crack + 0.1))))
    vignette(ctx)
    F.text_fade(ctx)
    slam(ctx, ["THAT CRACK", "WHEN YOU SQUAT…"], 420, t, 0.1, 90, out_t=1.2)
    burst_word(ctx, "CRACK!", t, crack, YEL, 210, 470)
    slam(ctx, ["^is ^it ^bad?"], 470, t, 2.4, 130)


def s_titel(ctx, t, d):
    z = 1.0 + 0.08 * t / d
    F.knee(ctx, z, (540, 1060), dim=0.45, glow=0.6 + 0.4 * math.sin(t * 6))
    vignette(ctx); F.text_fade(ctx)
    slam(ctx, ["Why does", "your knee", "^crack?"], 440, t, 0.1, 130, stagger=0.09)


def s_anatomie(ctx, t, d):
    k = eio(p(t, 0.0, 1.2))
    zoom = 2.4 - 0.9 * k
    theta = 20 + 10 * math.sin(t * 1.5)

    def extra(c):
        joint_glow(c, theta, eo(p(t, 1.2, 1.8)))
        bubbles(c, t, theta, eo(p(t, 3.0, 3.6)), n=16)
    V.view_side(ctx, theta, glow=0.3, zoom=zoom, cx=620 - 40 * (1 - k), cy=960, extra=extra)
    vignette(ctx); F.text_fade(ctx)
    slam(ctx, ["Your knee is filled", "with ~joint ~fluid"], 400, t, 1.2, 76, stagger=0.06)
    slam(ctx, ["and that fluid holds ^dissolved ^gas"], 600, t, 3.0, 52, stagger=0.06)


def s_functie(ctx, t, d):
    hits = [te for te, _ in EVENTS["functie"]]
    theta = 50 - 45 * math.cos(t * 2.0)

    def extra(c):
        joint_glow(c, theta, 0.5)
        bubbles(c, t, theta, 1.0, pops=tuple(hits), n=14)
    V.view_side(ctx, theta, glow=0.3, zoom=1.3, cx=620, cy=980, extra=extra)
    vignette(ctx); F.text_fade(ctx)
    slam(ctx, ["Move it → pressure drops", "→ a gas bubble ^forms: ^pop"], 400, t, 0.4, 62, stagger=0.06)
    slam(ctx, ["tendons sliding over bone", "can ^click too"], 600, t, 3.2, 56, stagger=0.06)


def s_scheur(ctx, t, d):
    verdict = 4.75
    theta = 45 - 40 * math.cos(t * 1.6)
    g = 0.2 if t < verdict else 0.2 + 0.8 * eo(p(t, verdict, verdict + 0.4))

    def extra(c):
        if t >= verdict:
            joint_glow(c, theta, 0.5)
    ctx.push_group()
    V.view_side(ctx, theta, glow=g, zoom=1.1, cx=640, cy=1000, extra=extra)
    ctx.pop_group_to_source(); ctx.paint_with_alpha(0.55 if t < verdict else 1.0)
    vignette(ctx)
    F.text_fade(ctx)
    slam(ctx, ["Many people think…"], 430, t, 0.2, 84, out_t=1.45)
    slam(ctx, ["cracking = *arthritis"], 430, t, 1.6, 92, out_t=2.85)
    slam(ctx, ["but research says…"], 430, t, 3.0, 88, out_t=4.6)
    slam(ctx, ["+MOSTLY", "+HARMLESS"], 420, t, verdict + 0.05, 150, stagger=0.12)
    slam(ctx, ["painless cracking is ^common", "cracking alone ≠ arthritis"], 720, t, 6.2, 52, stagger=0.05)


def s_klachten(ctx, t, d):
    txt(ctx, "get it checked if there's also…", W / 2, 330, 40, GREY, eo(p(t, 0, 0.4)))
    AC.klachten(ctx, t, [("PAIN", "together with", "the cracking", icon_bolt),
                         ("SWELLING", "around or", "inside the knee", icon_swell),
                         ("LOCKING", "your knee catches", "or gets stuck", icon_lock),
                         ("GIVING WAY", "the knee feels", "unstable", icon_squat)])


def s_slot(ctx, t, d):
    th = clamp(50 - 50 * math.cos(max(0, t - 1.0) * 2.4), 0, 100) if t > 1.0 else 0
    ka = eo(p(t, 1.0, 1.5))
    if ka > 0:
        ctx.push_group()
        V.view_side(ctx, th, zoom=0.62, cx=650, cy=820)
        ctx.pop_group_to_source(); ctx.paint_with_alpha(0.9 * ka)
    vignette(ctx)
    slam(ctx, ["BOTTOM LINE"], 400, t, 0.1, 120)
    slam(ctx, ["+painless? +keep +moving"], 540, t, 0.9, 84)
    slam(ctx, ["strong muscles and regular", "movement keep knees +happy"], 1180, t, 1.9, 54, stagger=0.05)
    slam(ctx, ["(exercise is good for your joints)"], 1320, t, 2.8, 40, base=GREY)
    kn = eo(p(t, 3.4, 3.8))
    if kn > 0:
        y = 1390 + (1 - kn) * 40
        rgba(ctx, WHITE, kn); rrect(ctx, 130, y, W - 260, 140, 70); ctx.fill()
        txt(ctx, "Unsure? Ask a physio", W / 2, y + 62, 42, BG0, kn, shadow=False)
        txt(ctx, "Next: your shoulder", W / 2, y + 112, 34, (0.1, 0.45, 0.4), kn, shadow=False)


FN = {"cold": s_cold, "titel": s_titel, "anatomie": s_anatomie, "functie": s_functie,
      "scheur": s_scheur, "klachten": s_klachten, "slot": s_slot}


def frame(name, t, d):
    tg = START[name] + t
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf); ctx.set_antialias(cairo.ANTIALIAS_BEST)
    background(ctx, tg, (0.04, 0.18, 0.17) if name == "slot" else None)
    zoom, sx, sy, flash, fcol = camera(name, t)
    if name == "scheur" and fcol == RED:
        fcol = GREEN            # good-news reveal flashes green, not red
    if name == "cold" and fcol == RED:
        fcol = YEL
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
