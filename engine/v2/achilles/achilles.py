"""Right lower leg + foot, lateral view (anterior = +x, posterior = -x). Origin = ankle joint centre (talar dome)."""
import math, random, cairo, sys
sys.path.insert(0, "/home/claude/short"); sys.path.insert(0, "/home/claude/v2")
import knee_still as K
import knee_flex as L
import anim2 as A
import common as C

d2r = math.pi / 180
INS = (-188.0, 100.0)          # Achilles insertion on the calcaneal tuber (foot frame)
MTOP = (-150.0, -1000.0)       # top of calf muscles (scaling anchor)
J0 = (-150.0, -430.0)          # musculotendinous junction (leg frame, relaxed)


def tibia(c):
    c.move_to(-45, -1000); c.line_to(-48, -260)
    c.curve_to(-50, -150, -66, -90, -62, -52)
    c.curve_to(-30, -70, 30, -70, 62, -50)
    c.curve_to(70, -42, 74, -36, 70, -30)
    c.curve_to(76, -100, 60, -200, 52, -300)
    c.line_to(42, -1000); c.close_path()


def fibula(c):
    c.move_to(-82, -1000); c.line_to(-86, -260)
    c.curve_to(-92, -150, -104, -70, -90, -10)
    c.curve_to(-80, 30, -56, 52, -40, 44)
    c.curve_to(-22, 36, -18, 0, -24, -60)
    c.curve_to(-32, -140, -44, -220, -52, -300)
    c.line_to(-56, -1000); c.close_path()


def talus(c):
    c.move_to(-56, 8)
    c.arc(0, 0, 56, math.pi * 1.05, math.pi * 1.95)
    c.curve_to(70, 10, 92, 24, 112, 22)
    c.curve_to(142, 24, 148, 62, 124, 74)
    c.curve_to(96, 82, 60, 70, 30, 62)
    c.curve_to(0, 58, -40, 60, -56, 48)
    c.curve_to(-64, 36, -62, 20, -56, 8)
    c.close_path()


def calcaneus(c):
    c.move_to(-40, 58)
    c.curve_to(-90, 50, -150, 44, -180, 58)
    c.curve_to(-204, 72, -206, 140, -186, 170)
    c.curve_to(-160, 190, -90, 186, -40, 178)
    c.curve_to(20, 172, 70, 156, 100, 132)
    c.curve_to(114, 118, 112, 96, 96, 84)
    c.curve_to(60, 72, 10, 66, -40, 58)
    c.close_path()


def midfoot(c):
    c.move_to(118, 30); c.curve_to(150, 18, 196, 22, 214, 40)
    c.curve_to(226, 70, 222, 110, 206, 138)
    c.curve_to(170, 146, 132, 140, 108, 128)
    c.curve_to(124, 100, 132, 70, 118, 30); c.close_path()


def metatarsal(c, y0=0):
    c.move_to(204, 36 + y0); c.curve_to(270, 70 + y0, 330, 110 + y0, 368, 140 + y0)
    c.arc(384, 160 + y0, 28, -math.pi * 0.8, math.pi * 0.55)
    c.curve_to(340, 172 + y0, 270, 146 + y0, 204, 132 + y0); c.close_path()


def toes(c):
    for x0, y0, x1, y1, r in ((404, 160, 446, 170, 22), (452, 172, 486, 184, 18)):
        c.move_to(x0, y0 - r); c.line_to(x1, y1 - r * 0.8); c.arc(x1, y1, r * 0.8, -math.pi / 2, math.pi / 2)
        c.line_to(x0, y0 + r); c.close_path()


def draw_leg(c):
    K.soft_shadow(c, tibia, 8, 10, 0.45, 40)
    K.textured(c, tibia, K.BONE_L, K.BONE_D, -60, 0, 70, 0, pores=360, pore_area=(-70, -1000, 80, -20),
               spec=(10, -400, 160, 0.3), cyl=True)
    c.move_to(-62, -52); c.curve_to(-30, -70, 30, -70, 62, -50)
    K.rgba(c, (0.88, 0.92, 0.97)); c.set_line_width(12); c.stroke()
    K.soft_shadow(c, fibula, 6, 8, 0.4, 30)
    K.textured(c, fibula, (0.95, 0.87, 0.70), (0.72, 0.57, 0.37), -100, 0, -20, 0, pores=160,
               pore_area=(-100, -1000, -20, 50), cyl=True)


def draw_muscles(c):
    # soleus (deep) then gastrocnemius (superficial)
    K.muscle(c, [(-80, -800), (-215, -640), (-205, -400), (-160, -300)], [(-60, -800), (-62, -600), (-80, -400), (-138, -300)], 34)
    K.muscle(c, [(-110, -1000), (-320, -830), (-285, -540), (-165, -420)], [(-70, -1000), (-120, -810), (-180, -560), (-140, -430)], 40)
    c.set_operator(cairo.OPERATOR_ATOP); K.rgba(c, (0.02, 0.02, 0.04), 0.25); c.paint(); c.set_operator(cairo.OPERATOR_OVER)


def draw_foot(c):
    for fn, light, dark, box, pores in ((calcaneus, K.BONE_L, K.BONE_D, (-210, 40, 120, 190), 200),
                                        (midfoot, (0.95, 0.88, 0.72), (0.74, 0.60, 0.42), (105, 15, 230, 150), 70)):
        K.soft_shadow(c, fn, 5, 8, 0.4, 26)
        K.textured(c, fn, light, dark, box[0], box[1], box[2], box[3], pores=pores, pore_area=box, inner=0.35)
    for y0, sh in ((-14, 0.82), (0, 1.0)):
        fn = lambda cc, y0=y0: metatarsal(cc, y0)
        K.soft_shadow(c, fn, 4, 6, 0.35, 18)
        K.textured(c, fn, tuple(v * sh for v in (0.97, 0.90, 0.74)), tuple(v * sh for v in K.BONE_D), 200, 40, 400, 190,
                   pores=80, pore_area=(200, 30, 410, 190), inner=0.3, cyl=True)
    K.textured(c, toes, (0.95, 0.88, 0.72), (0.74, 0.60, 0.42), 390, 140, 490, 200, inner=0.3, grain=0.1)


def draw_talus(c):
    K.soft_shadow(c, talus, 4, 8, 0.4, 22)
    K.textured(c, talus, K.BONE_L, K.BONE_D, -60, -56, 150, 80, pores=90, pore_area=(-60, -56, 150, 80), inner=0.3,
               spec=(-10, -20, 60, 0.4))
    c.arc(0, 0, 56, math.pi * 1.08, math.pi * 1.92); K.rgba(c, (0.88, 0.92, 0.97)); c.set_line_width(12); c.stroke()


SPR = {}


def sprites():
    if not SPR:
        SPR["leg"] = L.Sprite((-120, -1010, 90, 70), draw_leg)
        SPR["mus"] = L.Sprite((-340, -1010, -40, -280), draw_muscles)
        SPR["foot"] = L.Sprite((-220, 0, 500, 210), draw_foot)
        SPR["talus"] = L.Sprite((-70, -70, 160, 95), draw_talus)
    return SPR


def rot(pt, a):
    return (pt[0] * math.cos(a) - pt[1] * math.sin(a), pt[0] * math.sin(a) + pt[1] * math.cos(a))


def bez(p0, p1, p2, u):
    return ((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0],
            (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1])


def tendon_geom(pf, con):
    """centreline control points: junction J, control M, insertion I."""
    sx, sy = 1 + 0.08 * con, 1 - 0.07 * con
    J = (MTOP[0] + (J0[0] - MTOP[0]) * sx, MTOP[1] + (J0[1] - MTOP[1]) * sy)
    I = rot(INS, pf * d2r)
    M = (-158 + 0.3 * (I[0] + 188), -60 + 0.4 * I[1])
    return J, M, I


def width_at(u, thick):
    base = 60 - 30 * min(1, u / 0.55) + 16 * max(0, (u - 0.8) / 0.2)
    return base + 52 * thick * math.exp(-((u - 0.66) / 0.11) ** 2)


def tendon_path(ctx, J, M, I, thick, u0=0.0, u1=1.0, n=40):
    left, right = [], []
    for i in range(n + 1):
        u = u0 + (u1 - u0) * i / n
        q = bez(J, M, I, u); q2 = bez(J, M, I, min(1, u + 0.01)); q1 = bez(J, M, I, max(0, u - 0.01))
        ang = math.atan2(q2[1] - q1[1], q2[0] - q1[0]); nx, ny = -math.sin(ang), math.cos(ang)
        w = width_at(u, thick) / 2
        left.append((q[0] + nx * w, q[1] + ny * w)); right.append((q[0] - nx * w, q[1] - ny * w))
    ctx.move_to(*left[0])
    for q in left[1:]: ctx.line_to(*q)
    for q in reversed(right): ctx.line_to(*q)
    ctx.close_path()
    return left, right


def draw_tendon(ctx, t, J, M, I, thick, hot, green, u0=0.0, u1=1.0, fray=None):
    col = C.mix(C.mix((0.97, 0.95, 0.90), (1.0, 0.55, 0.45), hot), (0.75, 1.0, 0.85), green * 0.6)
    colD = C.mix(C.mix((0.74, 0.70, 0.62), (0.70, 0.15, 0.12), hot), (0.30, 0.65, 0.45), green * 0.6)
    ctx.save(); ctx.translate(5, 7); tendon_path(ctx, J, M, I, thick, u0, u1); A.rgba(ctx, (0, 0, 0), 0.35); ctx.fill(); ctx.restore()
    left, right = tendon_path(ctx, J, M, I, thick, u0, u1)
    g = cairo.LinearGradient(left[len(left) // 2][0], left[len(left) // 2][1], right[len(right) // 2][0], right[len(right) // 2][1])
    g.add_color_stop_rgb(0, *colD); g.add_color_stop_rgb(0.42, *col); g.add_color_stop_rgb(1, *colD)
    ctx.set_source(g); ctx.fill_preserve()
    ctx.save(); ctx.clip()
    for k in range(9):   # fibres
        f = (k + 0.5) / 9
        ctx.move_to(*C.mix(right[0], left[0], f))
        for a_, b_ in zip(left[1:], right[1:]):
            ctx.line_to(*C.mix(b_, a_, f + 0.03 * math.sin(k * 7.1 + a_[1] * 0.02)))
        A.rgba(ctx, (1, 1, 1) if k % 2 else (0.45, 0.40, 0.36), 0.35); ctx.set_line_width(1.8); ctx.stroke()
    ctx.restore()
    if fray is not None:   # frayed stump end
        r = random.Random(fray)
        end = bez(J, M, I, fray); base = bez(J, M, I, fray + (0.04 if fray < 0.6 else -0.04))
        ang = math.atan2(end[1] - base[1], end[0] - base[0])
        for _ in range(14):
            aa = ang + r.uniform(-0.8, 0.8); ln = r.uniform(10, 30); o = r.uniform(-14, 14)
            s = (end[0] - math.sin(ang) * o, end[1] + math.cos(ang) * o)
            ctx.move_to(*s); ctx.line_to(s[0] + math.cos(aa) * ln, s[1] + math.sin(aa) * ln)
            A.rgba(ctx, (0.98, 0.85, 0.80), 0.9); ctx.set_line_width(2.4); ctx.stroke()


def kager(ctx, I):
    ctx.move_to(-130, -330); ctx.curve_to(-90, -200, -66, -100, -66, -50)
    ctx.line_to(I[0] + 40, I[1] - 40); ctx.curve_to(-150, -60, -150, -200, -130, -330); ctx.close_path()
    g = cairo.LinearGradient(-140, -300, -80, 0)
    g.add_color_stop_rgba(0, 0.98, 0.86, 0.45, 0.55); g.add_color_stop_rgba(1, 0.92, 0.74, 0.32, 0.65)
    ctx.set_source(g); ctx.fill()


def leg(ctx, t, st, anchors):
    sp = sprites()
    pf = st.get("pf", 0.0); con = st.get("con", 0.0)
    thick = st.get("thick", 0.0); hot = st.get("hot", 0.0); green = st.get("green", 0.0)
    rup = st.get("rupture", 0.0)
    J, M, I = tendon_geom(pf, con)
    a = pf * d2r
    # heat glow behind thickened part
    if hot > 0:
        q = bez(J, M, I, 0.66)
        C.glow_blob(ctx, q[0], q[1], 150 + 60 * thick, C.RED, hot * (0.55 + 0.45 * math.sin(t * 7)))
    ctx.save(); ctx.rotate(a); sp["foot"].paint(ctx); ctx.restore()
    ctx.save(); ctx.rotate(a * 0.25); sp["talus"].paint(ctx); ctx.restore()
    kager(ctx, I)
    sp["leg"].paint(ctx)
    # calf muscles (contract = shorter + fatter)
    sx, sy = 1 + 0.08 * con, 1 - 0.07 * con
    gm = st.get("mglow", 0.0)
    if gm > 0:
        C.glow_blob(ctx, -190, -660, 260, st.get("mcol", C.CYAN), gm * 0.7)
    ctx.save(); ctx.translate(*MTOP); ctx.scale(sx, sy); ctx.translate(-MTOP[0], -MTOP[1]); sp["mus"].paint(ctx); ctx.restore()
    tg = st.get("tglow", 0.0)
    if tg > 0:
        for lw, al in ((90, 0.10), (55, 0.2)):
            ctx.move_to(*J); ctx.curve_to(*C.mix(J, M, 0.66), *C.mix(I, M, 0.66), *I)
            A.rgba(ctx, st.get("tcol", C.CYAN), al * tg); ctx.set_line_width(lw); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
    if rup <= 0:
        draw_tendon(ctx, t, J, M, I, thick, hot, green)
    else:
        gap = 0.17 * rup
        Jr = (J[0], J[1] - 90 * rup)   # proximal part recoils upward
        draw_tendon(ctx, t, Jr, M, I, thick, 0.6 * rup, 0, 0.0, 0.62 - gap, fray=0.62 - gap)
        draw_tendon(ctx, t, J, M, I, thick, 0.6 * rup, 0, 0.68, 1.0, fray=0.68)
        q = bez(J, M, I, 0.64)
        C.glow_blob(ctx, q[0], q[1], 140, C.RED, rup * (0.6 + 0.4 * math.sin(t * 9)))
    lp = st.get("load", 0.0)
    if lp > 0:
        C.pulse_path(ctx, [J, C.mix(J, M, 0.5), C.mix(M, I, 0.5), I], t, lp, col=st.get("lcol", C.YEL), speed=2.2)
    anchors["tendon"] = ctx.user_to_device(*bez(J, M, I, 0.62))
    anchors["calf"] = ctx.user_to_device(-230, -700)
    anchors["heel"] = ctx.user_to_device(*rot((-150, 150), a))
    anchors["ins"] = ctx.user_to_device(*I)
    return J, M, I
