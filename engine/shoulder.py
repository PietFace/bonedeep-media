"""Right shoulder, anterior view (lateral = viewer's left). Articulated: abduction with
scapulohumeral rhythm, deforming deltoid, supraspinatus tendon under the acromion."""
import cairo, math, random
import knee_still as K
import knee_flex as L
import anim2 as A
from anim import p, eo, eio, clamp

d2r = math.pi / 180
PS = (520, 40)          # scapula rotation centre
HR = 120                # humeral head radius


# ---------------- humerus frame (hanging arm, shaft down +y, head centre at origin) ----------------
def humerus_path(c):
    c.move_to(-150, -30)
    c.curve_to(-160, -90, -110, -125, -51, -109)
    c.arc(0, 0, HR, -115 * d2r, 70 * d2r)
    c.curve_to(55, 170, 52, 230, 48, 300)
    c.line_to(46, 950); c.line_to(-58, 950); c.line_to(-62, 300)
    c.curve_to(-70, 200, -120, 110, -150, 60)
    c.curve_to(-165, 30, -160, 0, -150, -30)
    c.close_path()


def draw_humerus(c):
    K.soft_shadow(c, humerus_path, 10, 12, 0.45, 50)
    K.textured(c, humerus_path, K.BONE_L, K.BONE_D, -160, 0, 120, 0, pores=420,
               pore_area=(-170, -130, 130, 950), spec=(-30, -40, 200, 0.35), cyl=True)
    c.save(); humerus_path(c); c.clip()
    c.arc(0, 0, HR, -100 * d2r, 75 * d2r)
    K.rgba(c, (0.55, 0.62, 0.72)); c.set_line_width(34); c.stroke()
    c.arc(0, 0, HR, -100 * d2r, 75 * d2r)
    K.rgba(c, (0.88, 0.92, 0.97)); c.set_line_width(26); c.stroke()
    rg = cairo.RadialGradient(30, -60, 5, 30, -60, 90)
    rg.add_color_stop_rgba(0, 1, 1, 1, 0.45); rg.add_color_stop_rgba(1, 1, 1, 1, 0)
    c.set_source(rg); c.paint()
    c.restore()


# ---------------- scapula frame (rest = world) ----------------
def scapula_path(c):
    c.move_to(104, -81)
    c.curve_to(150, -110, 200, -140, 260, -150)
    c.line_to(640, -200); c.curve_to(660, 100, 600, 420, 470, 720)
    c.curve_to(400, 600, 250, 320, 170, 150)
    c.curve_to(140, 110, 112, 95, 101, 85)
    c.arc_negative(0, 0, 132, 40 * d2r, -38 * d2r)
    c.close_path()


def acromion_path(c):
    c.move_to(340, -262)
    c.curve_to(200, -252, 40, -232, -110, -206)
    c.curve_to(-152, -200, -165, -176, -142, -160)
    c.curve_to(-60, -168, 60, -184, 150, -194)
    c.curve_to(230, -204, 300, -214, 345, -220)
    c.close_path()


def clavicle_path(c):
    c.move_to(160, -236)
    c.curve_to(350, -302, 620, -300, 1020, -384)
    c.line_to(1020, -318)
    c.curve_to(620, -238, 360, -240, 176, -196)
    c.close_path()


def coracoid_path(c):
    c.move_to(262, -168)
    c.curve_to(270, -120, 236, -88, 192, -80)
    c.curve_to(172, -78, 168, -98, 186, -103)
    c.curve_to(212, -112, 224, -140, 228, -170)
    c.close_path()


def draw_scapula(c):
    # ribs behind (faint)
    for i in range(7):
        y = -140 + i * 130
        c.move_to(300, y + 40); c.curve_to(520, y - 60, 780, y - 40, 1050, y + 70)
        K.rgba(c, (0.85, 0.78, 0.65), 0.10); c.set_line_width(46); c.stroke()
    K.soft_shadow(c, scapula_path, 8, 10, 0.4, 50)
    K.textured(c, scapula_path, (0.90, 0.82, 0.64), (0.62, 0.50, 0.33), 100, -150, 700, 600, pores=300,
               pore_area=(100, -210, 660, 730), inner=0.45, grain=0.2)
    c.arc(0, 0, 128, -38 * d2r, 40 * d2r)
    K.rgba(c, (0.55, 0.62, 0.72)); c.set_line_width(22); c.stroke()
    c.arc(0, 0, 128, -38 * d2r, 40 * d2r)
    K.rgba(c, (0.90, 0.93, 0.98)); c.set_line_width(14); c.stroke()
    for path in (coracoid_path, clavicle_path, acromion_path):
        K.soft_shadow(c, path, 6, 10, 0.45, 36)
        K.textured(c, path, K.BONE_L, K.BONE_D, -150, -260, 400, -150, pores=120,
                   pore_area=(-170, -390, 1020, -70), inner=0.35, grain=0.2, spec=(0, -230, 160, 0.3))


SPR = {}


def sprites():
    if not SPR:
        SPR["humerus"] = L.Sprite((-220, -180, 140, 980), draw_humerus)
        SPR["scapula"] = L.Sprite((-220, -420, 1040, 800), draw_scapula)
    return SPR


# ---------------- kinematics ----------------
def rot_about(pt, c, a):
    x, y = pt[0] - c[0], pt[1] - c[1]
    return (c[0] + x * math.cos(a) - y * math.sin(a), c[1] + x * math.sin(a) + y * math.cos(a))


def pose(alpha_deg):
    """alpha = arm elevation from hanging (deg). Returns scapula angle, humeral head centre, humerus angle."""
    beta = alpha_deg / 3 * d2r            # ~2:1 scapulohumeral rhythm
    H = rot_about((0, 0), PS, beta)
    return beta, H, alpha_deg * d2r


def S(pt, beta):                           # scapula frame -> world
    return rot_about(pt, PS, beta)


def Hm(pt, H, a):                          # humerus frame -> world
    x, y = pt
    return (H[0] + x * math.cos(a) - y * math.sin(a), H[1] + x * math.sin(a) + y * math.cos(a))


def cubic_band(ctx, Lp, Rp):
    ctx.move_to(*Lp[0]); ctx.curve_to(*Lp[1], *Lp[2], *Lp[3])
    ctx.line_to(*Rp[3]); ctx.curve_to(*Rp[2], *Rp[1], *Rp[0]); ctx.close_path()


def muscle_band(ctx, o1, o2, i1, i2, bulge, alpha=1.0, seed=1, n=34):
    """Muscle between two origin points and two insertion points; bulges outward (to the left of o->i)."""
    def ctrl(a, b, k, out):
        x = a[0] + (b[0] - a[0]) * k; y = a[1] + (b[1] - a[1]) * k
        dx, dy = b[0] - a[0], b[1] - a[1]; ln = math.hypot(dx, dy) or 1
        nx, ny = -dy / ln, dx / ln
        return (x + nx * out, y + ny * out)
    Lp = [o1, ctrl(o1, i1, 0.35, bulge), ctrl(o1, i1, 0.7, bulge * 0.8), i1]
    Rp = [o2, ctrl(o2, i2, 0.35, bulge * 0.35), ctrl(o2, i2, 0.7, bulge * 0.3), i2]
    path = lambda c: cubic_band(c, Lp, Rp)
    ctx.push_group()
    path(ctx)
    g = cairo.LinearGradient(Lp[1][0], Lp[1][1], Rp[1][0], Rp[1][1])
    g.add_color_stop_rgb(0, *K.MUS_D); g.add_color_stop_rgb(0.4, *K.MUS_L); g.add_color_stop_rgb(1, *K.MUS_D)
    ctx.set_source(g); ctx.fill()
    r = random.Random(seed)
    ctx.save(); path(ctx); ctx.clip()
    for i in range(n + 1):
        k = i / n
        P = [(a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k) for a, b in zip(Lp, Rp)]
        ctx.move_to(*P[0]); ctx.curve_to(*P[1], *P[2], *P[3])
        A.rgba(ctx, (1.0, 0.62, 0.52) if i % 2 else (0.25, 0.03, 0.02), 0.30 * r.uniform(0.5, 1))
        ctx.set_line_width(1.8); ctx.stroke()
    # tendinous ends
    for e0, e1 in ((Lp[3], Rp[3]), (Lp[0], Rp[0])):
        g2 = cairo.RadialGradient((e0[0] + e1[0]) / 2, (e0[1] + e1[1]) / 2, 2, (e0[0] + e1[0]) / 2, (e0[1] + e1[1]) / 2, 70)
        g2.add_color_stop_rgba(0, 0.97, 0.94, 0.88, 0.85); g2.add_color_stop_rgba(1, 0.97, 0.94, 0.88, 0)
        ctx.set_source(g2); ctx.paint()
    ctx.restore()
    path(ctx); A.rgba(ctx, (0.25, 0.04, 0.03), 0.7); ctx.set_line_width(2); ctx.stroke()
    ctx.pop_group_to_source(); ctx.paint_with_alpha(alpha)


def pinch_amount(alpha):
    return clamp(1 - abs(alpha - 90) / 32)


def supraspinatus(ctx, beta, H, a, tension=0.0, irritated=0.0, glow=0.0):
    # belly (scapula frame, "x-ray" above the spine)
    Lp = [S(q, beta) for q in [(600, -300), (460, -290), (300, -240), (160, -196)]]
    Rp = [S(q, beta) for q in [(600, -200), (460, -196), (300, -184), (160, -166)]]
    path = lambda c: cubic_band(c, Lp, Rp)
    ctx.push_group()
    path(ctx)
    g = cairo.LinearGradient(Lp[1][0], Lp[1][1], Rp[1][0], Rp[1][1])
    g.add_color_stop_rgb(0, *K.MUS_D); g.add_color_stop_rgb(0.45, *K.MUS_L); g.add_color_stop_rgb(1, *K.MUS_D)
    ctx.set_source(g); ctx.fill()
    ctx.pop_group_to_source(); ctx.paint_with_alpha(0.55)
    # tendon: from the end of the belly, over the head, to the greater tuberosity
    T0 = S((165, -181), beta)
    G = Hm((-128, -74), H, a)
    a0 = math.atan2(T0[1] - H[1], T0[0] - H[0])
    a1 = math.atan2(G[1] - H[1], G[0] - H[0])
    if a1 > a0:
        a1 -= 2 * math.pi
    pts = []
    for i in range(25):
        k = i / 24
        ang = a0 + (a1 - a0) * k
        base = HR + 20
        rr = base + (math.dist(T0, H) - base) * (1 - k) ** 3 + (math.dist(G, H) - base) * k ** 3
        pts.append((H[0] + rr * math.cos(ang), H[1] + rr * math.sin(ang)))

    def tpath(c):
        c.move_to(*pts[0])
        for q in pts[1:]:
            c.line_to(*q)
    hot = max(irritated, glow)
    if hot > 0:
        for w, al in ((70, 0.10), (46, 0.18), (32, 0.3)):
            tpath(ctx); A.rgba(ctx, A.RED, al * hot); ctx.set_line_width(w)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke()
    col = tuple(x + (y - x) * irritated for x, y in zip((0.96, 0.94, 0.90), (1.0, 0.55, 0.5)))
    tpath(ctx); A.rgba(ctx, (0.5, 0.46, 0.42)); ctx.set_line_width(26); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke()
    tpath(ctx); A.rgba(ctx, col); ctx.set_line_width(20); ctx.stroke()
    tpath(ctx); A.rgba(ctx, (1, 1, 1), 0.5); ctx.set_line_width(4); ctx.stroke()


def bursa(ctx, beta, inflamed=0.0):
    c = S((-20, -150), beta)
    ctx.save(); ctx.translate(*c); ctx.rotate(beta); ctx.scale(1, 0.24)
    ctx.arc(0, 0, 70, 0, 2 * math.pi); ctx.restore()
    col = tuple(x + (y - x) * inflamed for x, y in zip((0.55, 0.75, 1.0), (1.0, 0.3, 0.3)))
    A.rgba(ctx, col, 0.75); ctx.fill_preserve(); A.rgba(ctx, (1, 1, 1), 0.5); ctx.set_line_width(2); ctx.stroke()


def shoulder(ctx, alpha, deltoid_a=0.5, tendon_glow=0.0, irritated=0.0, show_bursa=True, inflamed=0.0):
    sp = sprites()
    beta, H, a = pose(alpha)
    ctx.save(); ctx.translate(*PS); ctx.rotate(beta); ctx.translate(-PS[0], -PS[1])
    sp["scapula"].paint(ctx)
    ctx.restore()
    ctx.save(); ctx.translate(*H); ctx.rotate(a)
    sp["humerus"].paint(ctx)
    ctx.restore()
    if show_bursa:
        bursa(ctx, beta, inflamed)
    supraspinatus(ctx, beta, H, a, irritated=irritated, glow=tendon_glow)
    # deltoid: origin on acromion/clavicle, insertion on the deltoid tuberosity
    o1, o2 = S((-150, -185), beta), S((80, -232), beta)
    i1, i2 = Hm((-72, 430), H, a), Hm((-28, 440), H, a)
    length = math.dist(o1, i1)
    rest = 640.0
    bulge = 110 + 150 * clamp((rest - length) / 260)
    if deltoid_a > 0:
        muscle_band(ctx, o1, o2, i1, i2, bulge, deltoid_a, seed=4)
    return beta, H, a


def painful_arc(ctx, H, alpha, a=1.0, R=560):
    if a <= 0:
        return
    # arc measured from hanging (down = 90 deg screen) towards lateral (left) and up
    def ang(deg):
        return (90 + deg) * d2r
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.arc(H[0], H[1], R, ang(0), ang(170)); A.rgba(ctx, A.WHITE, 0.25 * a); ctx.set_line_width(8); ctx.stroke()
    for w, al in ((60, 0.12), (34, 0.25)):
        ctx.arc(H[0], H[1], R, ang(60), ang(120)); A.rgba(ctx, A.RED, al * a); ctx.set_line_width(w); ctx.stroke()
    ctx.arc(H[0], H[1], R, ang(60), ang(120)); A.rgba(ctx, A.RED, a); ctx.set_line_width(14); ctx.stroke()
    for deg in (60, 120):
        x, y = H[0] + (R + 70) * math.cos(ang(deg)), H[1] + (R + 70) * math.sin(ang(deg))
        A.txt(ctx, f"{deg}°", x, y + 16, 44, A.WHITE, a)
    x, y = H[0] + R * math.cos(ang(alpha)), H[1] + R * math.sin(ang(alpha))
    hot = pinch_amount(alpha)
    A.rgba(ctx, A.RED if hot > 0.3 else A.WHITE, a); ctx.arc(x, y, 18, 0, 2 * math.pi); ctx.fill()


# ---------------- lateral (face-on) view of the socket with the 4 cuff tendons ----------------
CUFF = [("subscapularis", 125, 235, (0.30, 0.75, 1.0)), ("supraspinatus", 245, 300, (1.0, 0.80, 0.25)),
        ("infraspinatus", 308, 368, (0.35, 0.95, 0.65)), ("teres minor", 376, 420, (0.85, 0.55, 1.0))]


def cuff_view(ctx, t, squeeze=0.0, labels=1.0, highlight=None):
    # glenoid (pear-shaped) with cartilage
    def glen(c):
        c.move_to(0, -200)
        c.curve_to(90, -200, 120, -90, 110, 0)
        c.curve_to(110, 120, 80, 210, 0, 215)
        c.curve_to(-80, 210, -110, 120, -110, 0)
        c.curve_to(-120, -90, -90, -200, 0, -200)
        c.close_path()
    K.soft_shadow(ctx, glen, 6, 10, 0.4, 40)
    K.textured(ctx, glen, K.CART_L, K.CART_D, -110, -200, 110, 215, inner=0.25, grain=0.05,
               edge=(0.45, 0.5, 0.58), spec=(-30, -60, 120, 0.5))
    # humeral head (ghost) sitting in the socket
    ctx.save(); ctx.arc(0, 10, 230, 0, 2 * math.pi)
    A.rgba(ctx, (0.95, 0.88, 0.72), 0.22); ctx.fill_preserve()
    ctx.set_dash([18, 12]); A.rgba(ctx, A.WHITE, 0.6); ctx.set_line_width(4); ctx.stroke(); ctx.set_dash([])
    ctx.restore()
    R = 300 - 26 * squeeze
    for i, (name, a0, a1, col) in enumerate(CUFF):
        on = 1.0 if highlight is None else (1.0 if highlight == i else 0.35)
        pulse = 0.5 + 0.5 * math.sin(t * 5 + i)
        for w, al in ((110, 0.08), (80, 0.14)):
            ctx.arc(0, 10, R, a0 * d2r, a1 * d2r); A.rgba(ctx, col, al * on * (0.6 + 0.4 * squeeze * pulse))
            ctx.set_line_width(w); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
        ctx.arc(0, 10, R, a0 * d2r, a1 * d2r); A.rgba(ctx, col, on); ctx.set_line_width(56); ctx.stroke()
        ctx.arc(0, 10, R - 14, a0 * d2r, a1 * d2r); A.rgba(ctx, (1, 1, 1), 0.35 * on); ctx.set_line_width(5); ctx.stroke()
        # pull arrows towards the centre
        if squeeze > 0:
            m = (a0 + a1) / 2 * d2r
            x0, y0 = (R + 90) * math.cos(m), 10 + (R + 90) * math.sin(m)
            x1, y1 = (R + 40) * math.cos(m), 10 + (R + 40) * math.sin(m)
            A.arrow(ctx, x0, y0, x1, y1, col, squeeze * on, lw=8, head=24, glow=False)
        if labels > 0:
            m = (a0 + a1) / 2 * d2r
            lx, ly = (R + 130) * math.cos(m), 10 + (R + 130) * math.sin(m)
            A.txt(ctx, name, lx, ly + 14, 40, col, labels * on)
