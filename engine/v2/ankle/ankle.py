"""Right ankle, anterior view (lateral = viewer's left). Origin = top of the talar dome."""
import math, random, cairo, sys
sys.path.insert(0, "/home/claude/short"); sys.path.insert(0, "/home/claude/v2")
import knee_still as K
import knee_flex as L
import anim2 as A
import common as C

d2r = math.pi / 180
PIV = (0.0, 120.0)            # subtalar pivot (foot rotates about this)


def tibia(c):
    c.move_to(-72, -1000); c.line_to(-80, -320)
    c.curve_to(-88, -170, -125, -90, -110, -20)
    c.curve_to(-104, -2, -95, 2, -88, 2)
    c.curve_to(-40, -10, 30, -10, 82, 2)
    c.curve_to(92, 30, 92, 62, 104, 74)
    c.curve_to(122, 86, 140, 70, 142, 40)
    c.curve_to(146, -40, 150, -120, 120, -230)
    c.curve_to(96, -320, 82, -420, 82, -1000)
    c.close_path()


def fibula(c):
    c.move_to(-152, -1000); c.line_to(-150, -300)
    c.curve_to(-156, -150, -182, -40, -178, 40)
    c.curve_to(-176, 100, -160, 132, -140, 130)
    c.curve_to(-118, 128, -108, 96, -106, 40)
    c.curve_to(-104, -40, -108, -150, -118, -300)
    c.line_to(-120, -1000); c.close_path()


def talus(c):
    c.move_to(-100, 8)
    c.curve_to(-60, -6, 40, -6, 84, 8)
    c.curve_to(92, 50, 88, 90, 70, 112)
    c.curve_to(30, 126, -40, 126, -86, 112)
    c.curve_to(-104, 90, -108, 40, -100, 8)
    c.close_path()


def talus_head(c):
    c.save(); c.translate(-8, 128); c.scale(70 / 100, 40 / 100); c.arc(0, 0, 100, 0, 2 * math.pi); c.restore()


def calcaneus(c):
    c.move_to(-118, 120)
    c.curve_to(-60, 106, 60, 106, 104, 122)
    c.curve_to(118, 170, 112, 230, 86, 252)
    c.curve_to(30, 268, -50, 268, -100, 250)
    c.curve_to(-126, 220, -130, 160, -118, 120)
    c.close_path()


def forefoot(c):
    c.move_to(-95, 150)
    c.curve_to(-40, 136, 60, 136, 100, 150)
    c.curve_to(150, 210, 175, 270, 168, 320)
    c.arc(128, 330, 40, 0, math.pi)                       # big toe (medial = viewer right)
    for x, r in ((66, 24), (20, 22), (-24, 20), (-64, 18)):
        c.arc(x, 334, r, 0, math.pi)
    c.curve_to(-120, 330, -160, 300, -150, 260)
    c.curve_to(-140, 210, -120, 170, -95, 150)
    c.close_path()


def draw_leg(c):
    K.muscle(c, [(-300, -1000), (-320, -600), (-260, -330), (-180, -220)], [(-150, -1000), (-140, -600), (-140, -350), (-140, -250)], 30)
    K.muscle(c, [(110, -1000), (130, -600), (150, -380), (130, -260)], [(300, -1000), (330, -620), (280, -380), (170, -240)], 30)
    c.set_operator(cairo.OPERATOR_ATOP); K.rgba(c, (0.02, 0.02, 0.04), 0.35); c.paint(); c.set_operator(cairo.OPERATOR_OVER)
    for fn, x0, x1, pores in ((fibula, -185, -100, 120), (tibia, -125, 150, 420)):
        K.soft_shadow(c, fn, 8, 10, 0.45, 40)
        K.textured(c, fn, K.BONE_L, K.BONE_D, x0, 0, x1, 0, pores=pores, pore_area=(x0, -1000, x1, 140),
                   spec=((x0 + x1) / 2 - 20, -300, 200, 0.3), cyl=True)
    # cartilage of the mortise
    c.move_to(-88, 2); c.curve_to(-40, -10, 30, -10, 82, 2)
    K.rgba(c, (0.88, 0.92, 0.97)); c.set_line_width(12); c.stroke()


def draw_foot(c):
    K.soft_shadow(c, calcaneus, 6, 10, 0.4, 30)
    K.textured(c, calcaneus, K.BONE_L, K.BONE_D, -120, 120, 110, 260, pores=150, pore_area=(-130, 110, 120, 270), inner=0.4)
    c.push_group()
    K.textured(c, forefoot, (0.95, 0.88, 0.72), (0.72, 0.60, 0.42), -200, 150, 170, 340, pores=200,
               pore_area=(-200, 140, 170, 345), inner=0.35)
    c.save(); forefoot(c); c.clip()
    for x in (128, 66, 20, -24, -64):   # metatarsal shafts
        c.move_to(x * 0.45, 165); c.line_to(x, 318)
        K.rgba(c, (0.45, 0.33, 0.20), 0.40); c.set_line_width(3); c.stroke()
    g = cairo.LinearGradient(0, 150, 0, 360)
    g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0.05, 0.03, 0.02, 0.35)
    c.set_source(g); c.paint()
    c.restore()
    c.pop_group_to_source(); c.paint_with_alpha(0.92)


def draw_talus(c):
    K.soft_shadow(c, talus, 4, 8, 0.4, 24)
    K.textured(c, talus, K.BONE_L, K.BONE_D, -100, 0, 90, 120, pores=80, pore_area=(-100, 0, 90, 120), inner=0.3,
               spec=(-20, 30, 70, 0.4))
    c.move_to(-100, 8); c.curve_to(-60, -6, 40, -6, 84, 8)
    K.rgba(c, (0.88, 0.92, 0.97)); c.set_line_width(12); c.stroke()
    K.textured(c, talus_head, (0.97, 0.91, 0.76), (0.78, 0.66, 0.47), -80, 90, 60, 170, inner=0.25, grain=0.1)


SPR = {}


def sprites():
    if not SPR:
        SPR["leg"] = L.Sprite((-340, -1010, 340, 150), draw_leg)
        SPR["foot"] = L.Sprite((-220, 90, 200, 400), draw_foot)
        SPR["talus"] = L.Sprite((-120, -20, 110, 180), draw_talus)
    return SPR


def rot(pt, c, a):
    x, y = pt[0] - c[0], pt[1] - c[1]
    return (c[0] + x * math.cos(a) - y * math.sin(a), c[1] + x * math.sin(a) + y * math.cos(a))


REST = {}
LIGS = {  # name: (proximal point (leg), distal point (frame), distal frame, width)
    "ATFL": ((-128, 88), (-58, 150), "talus", 30),
    "CFL": ((-150, 126), (-138, 252), "foot", 26),
    "PTFL": ((-156, 104), (-100, 70), "talus", 18),
    "DELT1": ((112, 66), (70, 112), "talus", 26),
    "DELT2": ((120, 72), (96, 206), "foot", 22),
}


def lig_points(name, inv):
    a = -inv * d2r
    pa, pb, fr, w = LIGS[name]
    b = rot(pb, PIV, a) if fr == "foot" else rot(pb, (0, 40), a * 0.35)
    return pa, b, w


def strain(name, inv):
    pa, pb, _ = lig_points(name, 0)
    rest = math.dist(pa, pb)
    a, b, _ = lig_points(name, inv)
    return math.dist(a, b) / rest - 1


def ligament(ctx, name, inv, glow=0.0, gcol=C.CYAN, torn=0.0, t=0.0):
    a, b, w = lig_points(name, inv)
    s = max(0.0, strain(name, inv))
    hot = clamp01(s * 5)
    col = C.mix(K.LIG_L, (1.0, 0.5, 0.42), hot); colD = C.mix(K.LIG_D, (0.7, 0.12, 0.1), hot)
    ww = w * (1 - 0.35 * clamp01(s * 3))   # thinner when stretched
    if glow > 0:
        for lw, al in ((ww * 4, 0.10), (ww * 2.4, 0.2)):
            ctx.move_to(*a); ctx.line_to(*b); A.rgba(ctx, gcol, al * glow); ctx.set_line_width(lw)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
    if torn <= 0:
        L.band(ctx, a, b, ww, ww * 0.9, col=col, colD=colD, seed=hash(name) % 97, fib=8)
        return
    k = 0.42 - 0.1 * torn
    ma = C.mix(a, b, k); mb = C.mix(b, a, k)
    L.band(ctx, a, ma, ww, ww * 0.7, col=col, colD=colD, seed=3, fib=6)
    L.band(ctx, b, mb, ww, ww * 0.7, col=col, colD=colD, seed=4, fib=6)
    r = random.Random(5)
    for end, base in ((ma, a), (mb, b)):
        ang = math.atan2(end[1] - base[1], end[0] - base[0])
        for _ in range(8):
            aa = ang + r.uniform(-0.9, 0.9); ln = r.uniform(6, 16)
            ctx.move_to(*end); ctx.line_to(end[0] + math.cos(aa) * ln, end[1] + math.sin(aa) * ln)
            A.rgba(ctx, (0.96, 0.88, 0.84), 0.9); ctx.set_line_width(2); ctx.stroke()


def clamp01(x):
    return max(0.0, min(1.0, x))


def ankle(ctx, t, st, anchors):
    sp = sprites()
    inv = st.get("inv", 0.0)
    a = -inv * d2r
    sw = st.get("swell", 0.0)
    # swelling behind, around the lateral malleolus
    if sw > 0:
        C.glow_blob(ctx, -150, 110, 120 + 120 * sw, (0.75, 0.15, 0.35), sw)
        C.glow_blob(ctx, -150, 110, 70 + 80 * sw, (0.95, 0.25, 0.25), sw * 0.8)
    ctx.save(); ctx.translate(*PIV); ctx.rotate(a); ctx.translate(-PIV[0], -PIV[1])
    sp["foot"].paint(ctx)
    ctx.restore()
    ctx.save(); ctx.translate(0, 40); ctx.rotate(a * 0.35); ctx.translate(0, -40)
    sp["talus"].paint(ctx)
    ctx.restore()
    sp["leg"].paint(ctx)
    lg = st.get("lig_glow", 0.0)
    for nm in ("PTFL", "DELT1", "DELT2", "CFL"):
        ligament(ctx, nm, inv, glow=lg if nm in ("PTFL", "CFL") else 0, gcol=st.get("gcol", C.CYAN), t=t)
    ligament(ctx, "ATFL", inv, glow=max(lg, st.get("atfl_glow", 0)), gcol=st.get("atfl_col", st.get("gcol", C.CYAN)),
             torn=st.get("torn", 0), t=t)
    if sw > 0.3:   # bruise tint over the lateral side
        C.glow_blob(ctx, -170, 200, 160, (0.45, 0.15, 0.55), (sw - 0.3) * 0.8)
    for nm in ("ATFL", "CFL", "PTFL"):
        pa, pb, _ = lig_points(nm, inv)
        anchors[nm] = ctx.user_to_device((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2)
    anchors["fibula"] = ctx.user_to_device(-140, 60)
    anchors["bone"] = ctx.user_to_device(-142, 110)
