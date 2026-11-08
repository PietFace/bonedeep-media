"""Articulated lateral-view knee (right knee, anterior = +x). Flexion/extension test clip."""
import cairo, math, os, subprocess, sys, random
import knee_still as K
import anim2 as A
from anim import p, eo, eio, clamp

W, H, FPS = 1080, 1920, 30
S = 2
R = 170          # femoral condyle radius (flexion axis at C = origin)
GAP = 14
Y0 = R + GAP     # tibial plateau height in tibia frame
CX, CY, SC = 720, 800, 0.72
d2r = math.pi / 180


# ---------------- shapes (femur frame / tibia frame, C at origin) ----------------
def femur_path(c):
    c.move_to(-95, -760); c.line_to(-95, -420)
    c.curve_to(-98, -300, -168, -200, -159.7, -58.1)
    c.arc_negative(0, 0, R, 200 * d2r, -20 * d2r)
    c.curve_to(150, -170, 72, -230, 66, -380)
    c.line_to(65, -760); c.close_path()


def femur_artic(c):
    c.move_to(-159.7, -58.1)
    c.arc_negative(0, 0, R, 200 * d2r, -20 * d2r)
    c.curve_to(150, -150, 70, -200, 65, -300)


def tibia_path(c):
    c.move_to(-115, Y0); c.line_to(108, Y0)
    c.curve_to(120, Y0 + 20, 118, Y0 + 60, 135, Y0 + 110)
    c.curve_to(140, Y0 + 150, 95, Y0 + 200, 80, Y0 + 330)
    c.line_to(70, 1000); c.line_to(-60, 1000); c.line_to(-62, Y0 + 330)
    c.curve_to(-70, Y0 + 200, -130, Y0 + 120, -128, Y0 + 50)
    c.curve_to(-127, Y0 + 25, -122, Y0 + 8, -115, Y0)
    c.close_path()


def fibula_path(c):
    c.move_to(-150, Y0 + 100)
    c.curve_to(-150, Y0 + 70, -90, Y0 + 62, -78, Y0 + 95)
    c.curve_to(-70, Y0 + 120, -84, Y0 + 150, -88, Y0 + 190)
    c.curve_to(-92, Y0 + 300, -76, Y0 + 600, -74, 1000)
    c.line_to(-118, 1000)
    c.curve_to(-120, Y0 + 600, -128, Y0 + 300, -128, Y0 + 190)
    c.curve_to(-140, Y0 + 160, -150, Y0 + 130, -150, Y0 + 100)
    c.close_path()


def patella_path(c):
    c.move_to(-66, 0)
    c.curve_to(-66, -36, -20, -40, 12, -35)
    c.curve_to(46, -30, 70, -12, 66, 4)
    c.curve_to(62, 22, 32, 31, 0, 31)
    c.curve_to(-36, 31, -66, 22, -66, 0)
    c.close_path()


# ---------------- sprite builder ----------------
class Sprite:
    def __init__(self, bbox, draw):
        x0, y0, x1, y1 = bbox
        self.x0, self.y0 = x0, y0
        self.surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, int((x1 - x0) * S), int((y1 - y0) * S))
        c = cairo.Context(self.surf); c.scale(S, S); c.translate(-x0, -y0)
        c.set_antialias(cairo.ANTIALIAS_BEST)
        draw(c)

    def paint(self, ctx, a=1.0):
        ctx.save(); ctx.translate(self.x0, self.y0); ctx.scale(1 / S, 1 / S)
        ctx.set_source_surface(self.surf, 0, 0); ctx.get_source().set_filter(cairo.FILTER_GOOD)
        ctx.paint_with_alpha(a); ctx.restore()


def draw_femur(c):
    # muscles behind bone: quadriceps (front), hamstrings (back)
    K.muscle(c, [(70, -1000), (80, -700), (110, -450), (112, -300)], [(270, -1000), (290, -650), (225, -420), (150, -300)], 44)
    K.muscle(c, [(-310, -1000), (-340, -650), (-270, -350), (-175, -120)], [(-110, -1000), (-104, -650), (-110, -350), (-132, -120)], 40)
    c.set_operator(cairo.OPERATOR_ATOP); K.rgba(c, (0.02, 0.02, 0.04), 0.30); c.paint(); c.set_operator(cairo.OPERATOR_OVER)
    K.soft_shadow(c, femur_path, 8, 10, 0.45, 50)
    K.textured(c, femur_path, K.BONE_L, K.BONE_D, -95, 0, 160, 0, pores=420,
               pore_area=(-170, -760, 170, 175), spec=(-20, -420, 260, 0.3), cyl=True)
    c.save(); femur_path(c); c.clip()
    femur_artic(c); K.rgba(c, (0.55, 0.62, 0.72)); c.set_line_width(34); c.stroke()
    femur_artic(c); K.rgba(c, (0.88, 0.92, 0.97)); c.set_line_width(26); c.stroke()
    rg = cairo.RadialGradient(90, 40, 5, 90, 40, 120)
    rg.add_color_stop_rgba(0, 1, 1, 1, 0.35); rg.add_color_stop_rgba(1, 1, 1, 1, 0)
    c.set_source(rg); c.paint()
    c.restore()


def draw_tibia(c):
    # gastrocnemius / calf behind
    K.muscle(c, [(-125, Y0 + 40), (-330, Y0 + 260), (-270, Y0 + 600), (-110, 1000)],
             [(-70, Y0 + 60), (-70, Y0 + 300), (-60, Y0 + 600), (-60, 1000)], 40)
    K.muscle(c, [(85, Y0 + 260), (170, Y0 + 420), (150, Y0 + 700), (95, 1000)],
             [(78, Y0 + 300), (82, Y0 + 500), (80, Y0 + 700), (72, 1000)], 20)  # tibialis anterior edge
    c.set_operator(cairo.OPERATOR_ATOP); K.rgba(c, (0.02, 0.02, 0.04), 0.30); c.paint(); c.set_operator(cairo.OPERATOR_OVER)
    K.soft_shadow(c, tibia_path, 8, 10, 0.45, 50)
    K.textured(c, tibia_path, K.BONE_L, K.BONE_D, -130, 0, 140, 0, pores=380,
               pore_area=(-130, Y0, 140, 1000), spec=(10, Y0 + 220, 220, 0.3), cyl=True)
    c.save(); tibia_path(c); c.clip()
    c.move_to(-118, Y0); c.line_to(110, Y0)
    K.rgba(c, (0.55, 0.62, 0.72)); c.set_line_width(26); c.stroke()
    c.move_to(-118, Y0); c.line_to(110, Y0)
    K.rgba(c, (0.88, 0.92, 0.97)); c.set_line_width(18); c.stroke()
    c.restore()
    K.soft_shadow(c, fibula_path, 6, 8, 0.4, 30)
    K.textured(c, fibula_path, K.BONE_L, K.BONE_D, -140, 0, -75, 0, pores=60,
               pore_area=(-150, Y0 + 80, -70, 1000), cyl=True)


def draw_patella(c):
    K.soft_shadow(c, patella_path, 4, 8, 0.45, 26)
    K.textured(c, patella_path, K.BONE_L, K.BONE_D, 0, -40, 0, 31, pores=40,
               pore_area=(-66, -40, 66, 31), inner=0.3)
    c.save(); patella_path(c); c.clip()
    c.move_to(-60, 31); c.curve_to(-30, 34, 30, 34, 62, 22)
    K.rgba(c, (0.88, 0.92, 0.97)); c.set_line_width(26); c.stroke()
    c.restore()


SPR = {}


def sprites():
    if not SPR:
        SPR["femur"] = Sprite((-360, -1010, 320, 200), draw_femur)
        SPR["tibia"] = Sprite((-360, 150, 220, 1010), draw_tibia)
        SPR["patella"] = Sprite((-90, -70, 90, 60), draw_patella)
    return SPR


# ---------------- kinematics helpers ----------------
def rot(pt, th):
    x, y = pt
    return (x * math.cos(th) - y * math.sin(th), x * math.sin(th) + y * math.cos(th))


def bez(p0, p1, p2, p3, t):
    u = 1 - t
    return (u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
            u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1])


# patellar track along the anterior femur (trochlea -> distal condyle)
TRACK = []
for i in range(60):
    TRACK.append(bez((66, -380), (72, -230), (150, -170), (159.7, -58.1), i / 59))
for i in range(1, 50):
    a = -20 + 100 * i / 49
    TRACK.append((R * math.cos(a * d2r), R * math.sin(a * d2r)))
_L = [0.0]
for i in range(1, len(TRACK)):
    _L.append(_L[-1] + math.dist(TRACK[i - 1], TRACK[i]))


def track_at(s):
    target = s * _L[-1]
    for i in range(1, len(_L)):
        if _L[i] >= target:
            f = (target - _L[i - 1]) / (_L[i] - _L[i - 1] + 1e-9)
            a, b = TRACK[i - 1], TRACK[i]
            pt = (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
            tx, ty = b[0] - a[0], b[1] - a[1]
            n = math.hypot(tx, ty)
            return pt, (tx / n, ty / n)
    return TRACK[-1], (0, 1)


def band(ctx, a, b, w0, w1, col=K.LIG_L, colD=K.LIG_D, seed=1, fib=10):
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    nx, ny = -math.sin(ang), math.cos(ang)
    pts = [(a[0] + nx * w0 / 2, a[1] + ny * w0 / 2), (b[0] + nx * w1 / 2, b[1] + ny * w1 / 2),
           (b[0] - nx * w1 / 2, b[1] - ny * w1 / 2), (a[0] - nx * w0 / 2, a[1] - ny * w0 / 2)]

    def path(c):
        c.move_to(*pts[0])
        for q in pts[1:]:
            c.line_to(*q)
        c.close_path()
    # shadow
    ctx.save(); ctx.translate(4, 6); path(ctx); K.rgba(ctx, (0, 0, 0), 0.35); ctx.fill(); ctx.restore()
    path(ctx)
    g = cairo.LinearGradient(pts[0][0], pts[0][1], pts[3][0], pts[3][1])
    g.add_color_stop_rgb(0, *colD); g.add_color_stop_rgb(0.4, *col); g.add_color_stop_rgb(1, *colD)
    ctx.set_source(g); ctx.fill()
    r = random.Random(seed)
    ctx.save(); path(ctx); ctx.clip()
    for i in range(fib):
        k = (i + 0.5) / fib + r.uniform(-0.02, 0.02)
        sa = (pts[3][0] + (pts[0][0] - pts[3][0]) * k, pts[3][1] + (pts[0][1] - pts[3][1]) * k)
        sb = (pts[2][0] + (pts[1][0] - pts[2][0]) * k, pts[2][1] + (pts[1][1] - pts[2][1]) * k)
        ctx.move_to(*sa); ctx.line_to(*sb)
        K.rgba(ctx, (0.5, 0.46, 0.42) if i % 2 else (1, 1, 1), 0.35); ctx.set_line_width(1.6); ctx.stroke()
    ctx.restore()


def meniscus_poly(ctx, x_in, x_out):
    """Wedge sitting on the plateau, top surface hugging the condyle circle (tibia frame)."""
    n = 24
    ctx.move_to(x_in, Y0 - 2)
    ctx.line_to(x_out, Y0 - 2)
    for i in range(n + 1):
        x = x_out + (x_in - x_out) * i / n
        y = math.sqrt(max(R * R - x * x, 0)) + 2.5
        if i == n:
            y = max(y, Y0 - 7)
        ctx.line_to(x, y)
    ctx.close_path()


def draw_menisci(ctx, shift_a, shift_p, glow=0.0):
    for (xi, xo) in ((45 + shift_a, 104 + shift_a), (-45 + shift_p, -106 + shift_p)):
        if glow > 0:
            for w, a in ((40, 0.08), (24, 0.15), (12, 0.25)):
                meniscus_poly(ctx, xi, xo); K.rgba(ctx, A.CYAN, a * glow); ctx.set_line_width(w)
                ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke()
        meniscus_poly(ctx, xi, xo)
        g = cairo.LinearGradient(xo, Y0, xi, Y0 - 20)
        g.add_color_stop_rgb(0, 0.62, 0.67, 0.75); g.add_color_stop_rgb(1, 0.94, 0.96, 0.99)
        ctx.set_source(g); ctx.fill_preserve()
        K.rgba(ctx, (0.40, 0.45, 0.55), 0.8); ctx.set_line_width(2); ctx.stroke()


def knee_lateral(ctx, theta, glow=0.0, fdy=0.0):
    """theta = flexion in degrees. Draws in world coords (C at origin)."""
    sp = sprites()
    th = theta * d2r
    f = clamp(theta / 100)
    # hamstring tendon (behind)
    band(ctx, (-152, -140), rot((-120, Y0 + 70), th), 30, 24, seed=3, fib=8)
    ctx.save(); ctx.translate(0, fdy); sp["femur"].paint(ctx); ctx.restore()
    ctx.save(); ctx.rotate(th)
    sp["tibia"].paint(ctx)
    draw_menisci(ctx, -7 * f, -16 * f, glow)
    ctx.restore()
    # patella + tendons (patellar tendon length kept constant)
    tub = rot((128, Y0 + 100), th)
    best = None
    for i in range(240):
        s_ = 0.02 + 0.96 * i / 239
        pt, (tx, ty) = track_at(s_)
        nx, ny = ty, -tx
        c = (pt[0] + nx * PAT_OFF, pt[1] + ny * PAT_OFF)
        distal = (c[0] + tx * PAT_HALF, c[1] + ty * PAT_HALF)
        err = abs(math.dist(distal, tub) - LPT)
        if best is None or err < best[0]:
            best = (err, c, (tx, ty), distal)
    _, c, (tx, ty), distal = best
    prox = (c[0] - tx * PAT_HALF, c[1] - ty * PAT_HALF)
    band(ctx, (128, -380), prox, 60, 52, seed=5, fib=12)          # quadriceps tendon
    band(ctx, distal, tub, 40, 34, seed=7, fib=10)                 # patellar tendon
    ctx.save(); ctx.translate(*c); ctx.rotate(math.atan2(ty, tx)); ctx.scale(PAT_SC, PAT_SC)
    sp["patella"].paint(ctx)
    ctx.restore()


PAT_SC = 1.6
PAT_HALF = 58 * PAT_SC
PAT_OFF = 31 * PAT_SC
LPT = 250


def test_frame(t):
    D = 7.0
    if t < 0.5:
        th = 0
    elif t < 3.0:
        th = 100 * eio(p(t, 0.5, 3.0))
    elif t < 3.6:
        th = 100
    elif t < 6.1:
        th = 100 * (1 - eio(p(t, 3.6, 6.1)))
    else:
        th = 0
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf); ctx.set_antialias(cairo.ANTIALIAS_BEST)
    A.background(ctx, t)
    ctx.save(); ctx.translate(CX, CY); ctx.scale(SC, SC)
    knee_lateral(ctx, th, glow=0.4 + 0.6 * clamp(th / 100))
    ctx.restore()
    A.vignette(ctx)
    tg = cairo.LinearGradient(0, 0, 0, 520)
    tg.add_color_stop_rgba(0, 0.02, 0.02, 0.04, 0.9); tg.add_color_stop_rgba(1, 0.02, 0.02, 0.04, 0)
    ctx.set_source(tg); ctx.rectangle(0, 0, W, 520); ctx.fill()
    A.txt(ctx, f"{int(round(th))}°", W / 2, 380, 170, A.YEL)
    A.txt(ctx, "knee bend", W / 2, 450, 46, A.GREY, bold=False)
    a = clamp(th / 40)
    A.txt(ctx, "menisci glide backward", 330, 1500, 40, A.CYAN, a, align="c")
    return surf


if __name__ == "__main__":
    if sys.argv[1] == "still":
        test_frame(float(sys.argv[2])).write_to_png(sys.argv[3])
    else:
        out = sys.argv[2]
        tmp = out.replace(".mp4", ".tmp.mp4")
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
               "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
               "-pix_fmt", "yuv420p", tmp]
        pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for i in range(int(7.0 * FPS)):
            pr.stdin.write(bytes(test_frame(i / FPS).get_data()))
        pr.stdin.close()
        if pr.wait() == 0:
            os.replace(tmp, out)
        print("ok")
