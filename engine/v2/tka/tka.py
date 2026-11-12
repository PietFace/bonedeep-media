"""Lateral knee (anterior = +x) with total knee replacement stages. Origin = flexion axis (condyle centre)."""
import math, random, cairo, sys
sys.path.insert(0, "/home/claude/short"); sys.path.insert(0, "/home/claude/v2")
import knee_still as K
import knee_flex as L
import anim2 as A
import common as C

d2r = math.pi / 180
R, Y0 = L.R, L.Y0
BG = (0.03, 0.04, 0.07)
TCUT = Y0 + 42            # tibial cut level (tibia frame)

# kept femur bone after the box cuts (femur frame)
BOX = [(400, -1100), (400, -260), (110, -260), (110, 30), (70, 112), (-70, 112), (-118, 60), (-118, -90), (-400, -90), (-400, -1100)]
# cut segments, in order: distal, anterior, posterior, chamfers
CUTS = [((-70, 112), (70, 112)), ((110, -260), (110, 30)), ((-118, -90), (-118, 60)), ((70, 112), (110, 30)), ((-70, 112), (-118, 60))]


def box_path(c):
    c.move_to(*BOX[0])
    for q in BOX[1:]: c.line_to(*q)
    c.close_path()


def not_box(c):
    c.rectangle(-1000, -1200, 2000, 2400); box_path(c)


def femur_removed(c):
    """clip current path to removed femur region (femur ∩ ¬box)"""
    L.femur_path(c); c.clip()
    c.set_fill_rule(cairo.FILL_RULE_EVEN_ODD); not_box(c); c.clip(); c.set_fill_rule(cairo.FILL_RULE_WINDING)


def cap_outer(c):
    c.save(); c.scale(1.055, 1.055); L.femur_path(c); c.restore()


def metal(ctx, x0, y0, x1, y1, a=1.0):
    g = cairo.LinearGradient(x0, y0, x1, y1)
    for k, v in ((0, 0.55), (0.25, 0.95), (0.45, 0.70), (0.7, 0.98), (1, 0.60)):
        g.add_color_stop_rgba(k, v * 0.92, v * 0.95, v, a)
    ctx.set_source(g)


def femoral_cap(ctx, k, glow=0.0):
    if k <= 0: return
    ctx.save(); ctx.translate(0, 260 * (1 - eo(k)))
    ctx.save()
    ctx.rectangle(-400, -300, 800, 600); ctx.clip()
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD); not_box(ctx); ctx.clip(); ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
    if glow > 0:
        cap_outer(ctx); A.rgba(ctx, C.CYAN, 0.0); ctx.set_line_width(1)
    cap_outer(ctx); metal(ctx, -200, -100, 200, 200, k); ctx.fill()
    for i in range(6):   # reflections
        ctx.arc(0, 0, R * 1.04 - i * 2, 210 * d2r, 330 * d2r)
    ctx.restore()
    ctx.save(); cap_outer(ctx); ctx.clip()
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD); not_box(ctx); ctx.clip(); ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
    ctx.arc(0, 0, R * 0.97, 15 * d2r, 165 * d2r); A.rgba(ctx, (1, 1, 1), 0.55 * k); ctx.set_line_width(6); ctx.stroke()
    box_path(ctx); A.rgba(ctx, (0.25, 0.27, 0.3), 0.9 * k); ctx.set_line_width(5); ctx.stroke()
    ctx.restore()
    ctx.restore()


def tray(ctx, k):
    if k <= 0: return
    ctx.save(); ctx.translate(0, 300 * (1 - eo(k)))
    ctx.move_to(-28, TCUT); ctx.line_to(28, TCUT); ctx.line_to(14, TCUT + 230); ctx.line_to(-14, TCUT + 230); ctx.close_path()
    metal(ctx, -30, 0, 30, 0, 0.85 * k); ctx.fill()
    from anim import rrect
    rrect(ctx, -122, TCUT - 14, 236, 16, 5); metal(ctx, 0, TCUT - 14, 0, TCUT + 2, k); ctx.fill()
    ctx.restore()


def insert_path(c):
    top = lambda x: math.sqrt((R * 1.06 + 3) ** 2 - x * x)
    c.move_to(-112, TCUT - 14)
    c.line_to(-112, top(-112))
    for i in range(41):
        x = -112 + 222 * i / 40
        c.line_to(x, top(x))
    c.line_to(110, TCUT - 14); c.close_path()


def insert(ctx, k, glow=0.0):
    if k <= 0: return
    ctx.save(); ctx.translate(320 * (1 - eo(k)), 0)
    if glow > 0:
        for lw, al in ((30, 0.12), (14, 0.25)):
            insert_path(ctx); A.rgba(ctx, C.CYAN, al * glow); ctx.set_line_width(lw); ctx.stroke()
    insert_path(ctx)
    g = cairo.LinearGradient(0, R, 0, TCUT)
    g.add_color_stop_rgba(0, 0.97, 0.98, 1.0, k); g.add_color_stop_rgba(1, 0.74, 0.80, 0.90, k)
    ctx.set_source(g); ctx.fill_preserve(); A.rgba(ctx, (0.45, 0.5, 0.6), k); ctx.set_line_width(3); ctx.stroke()
    ctx.restore()


def eo(x):
    x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3


def saw(ctx, t, seg, k):
    """blade travelling along a cut segment, k in 0..1"""
    a, b = seg
    q = C.mix(a, b, k)
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    ctx.move_to(*a); ctx.line_to(*q)
    for lw, al in ((26, 0.15), (10, 0.4), (3, 1.0)):
        ctx.move_to(*a); ctx.line_to(*q); A.rgba(ctx, (1.0, 0.85, 0.4), al); ctx.set_line_width(lw); ctx.stroke()
    ctx.save(); ctx.translate(*q); ctx.rotate(ang + math.pi / 2 + 0.08 * math.sin(t * 60))
    ctx.rectangle(-9, -260, 18, 260); metal(ctx, -9, 0, 9, 0, 0.95); ctx.fill()
    for i in range(10):
        ctx.move_to(-9, -i * 8); ctx.line_to(-15, -i * 8 - 4); ctx.line_to(-9, -i * 8 - 8)
    A.rgba(ctx, (0.8, 0.82, 0.86)); ctx.fill()
    ctx.restore()
    r = random.Random(int(t * 30))
    for _ in range(14):   # bone dust sparks
        aa = r.uniform(0, 2 * math.pi); ln = r.uniform(10, 50)
        ctx.move_to(*q); ctx.line_to(q[0] + math.cos(aa) * ln, q[1] + math.sin(aa) * ln)
        A.rgba(ctx, (1.0, 0.9, 0.6), r.uniform(0.4, 0.9)); ctx.set_line_width(2.5); ctx.stroke()


def patella_mech(ctx, th, worn=0.0):
    sp = L.sprites()
    tub = L.rot((128, Y0 + 100), th * d2r)
    best = None
    for i in range(120):
        s_ = 0.02 + 0.96 * i / 119
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


def knee(ctx, t, st, anchors):
    sp = L.sprites()
    th = st.get("theta", 0.0)
    worn = st.get("worn", 0.0)
    fcut = st.get("fcut", 0.0)        # 0..1 removal of femur slices
    tcut = st.get("tcut", 0.0)
    # hamstring tendon behind
    L.band(ctx, (-152, -140), L.rot((-120, Y0 + 70), th * d2r), 30, 24, seed=3, fib=8)
    # --- femur ---
    if fcut <= 0:
        sp["femur"].paint(ctx)
    else:
        ctx.save(); box_path(ctx); ctx.clip(); sp["femur"].paint(ctx); ctx.restore()
    if worn > 0:   # thinned, rough cartilage + spurs
        L.femur_artic(ctx); A.rgba(ctx, K.BONE_D, 0.9 * worn); ctx.set_line_width(14); ctx.stroke()
        for x, y in ((-150, -95), (150, -100), (-128, 105), (125, 100)):
            ctx.arc(x * 1.08, y * 1.08, 16, 0, 2 * math.pi); A.rgba(ctx, K.BONE_D, worn); ctx.fill()
    if fcut > 0:
        if fcut < 1:   # slices falling away
            off = (60 * fcut, 380 * fcut ** 2)
            ctx.save(); ctx.translate(*off); ctx.rotate(0.3 * fcut)
            femur_removed(ctx); sp["femur"].paint(ctx, 1 - fcut); ctx.restore()
    femoral_cap(ctx, st.get("cap", 0.0))
    # --- tibia ---
    ctx.save(); ctx.rotate(th * d2r)
    if tcut <= 0:
        sp["tibia"].paint(ctx)
    else:
        ctx.save(); ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        ctx.rectangle(-1000, -1000, 2000, 3000); ctx.rectangle(-300, Y0 - 30, 600, TCUT - Y0 + 30); ctx.clip()
        ctx.set_fill_rule(cairo.FILL_RULE_WINDING); sp["tibia"].paint(ctx); ctx.restore()
    if worn > 0:
        ctx.move_to(-118, Y0); ctx.line_to(110, Y0); A.rgba(ctx, K.BONE_D, 0.9 * worn); ctx.set_line_width(18); ctx.stroke()
    if tcut <= 0 and st.get("men", 1.0) > 0:
        L.draw_menisci(ctx, 0, 0, 0)
    if tcut > 0:
        if tcut < 1:
            ctx.save(); ctx.translate(-80 * tcut, 380 * tcut ** 2 * 0 - 300 * tcut); ctx.rotate(-0.25 * tcut)
            L.tibia_path(ctx); ctx.clip(); ctx.rectangle(-300, Y0 - 30, 600, TCUT - Y0 + 30); ctx.clip()
            sp["tibia"].paint(ctx, 1 - tcut); L.draw_menisci(ctx, 0, 0, 0); ctx.restore()
    tray(ctx, st.get("tray", 0.0))
    insert(ctx, st.get("ins", 0.0), st.get("ins_glow", 0.0))
    ctx.restore()
    # grinding contact
    ang = (90 + th) * d2r
    cp = (R * math.cos(ang), R * math.sin(ang))
    gr = st.get("grind", 0.0)
    if gr > 0:
        C.glow_blob(ctx, cp[0], cp[1], 200, C.RED, gr * (0.6 + 0.4 * math.sin(t * 11)))
        r = random.Random(int(t * 24))
        for _ in range(int(16 * gr)):
            aa = r.uniform(0, 2 * math.pi); ln = r.uniform(20, 70)
            ctx.move_to(*cp); ctx.line_to(cp[0] + math.cos(aa) * ln, cp[1] + math.sin(aa) * ln)
            A.rgba(ctx, (1.0, 0.75, 0.4), r.uniform(0.5, 1.0) * gr); ctx.set_line_width(3); ctx.stroke()
    gl = st.get("glide", 0.0)
    if gl > 0:
        C.glow_blob(ctx, cp[0], cp[1], 160, C.CYAN, gl * 0.7)
    sw = st.get("saw")
    if sw is not None:
        seg, k, frame = sw
        if frame == "tibia":
            ctx.save(); ctx.rotate(th * d2r); saw(ctx, t, seg, k); ctx.restore()
        else:
            saw(ctx, t, seg, k)
    patella_mech(ctx, th)
    anchors["joint"] = ctx.user_to_device(*cp)
    anchors["cap"] = ctx.user_to_device(150, 40)
    anchors["insert"] = ctx.user_to_device(*L.rot((60, TCUT - 30), th * d2r))
    anchors["tray"] = ctx.user_to_device(*L.rot((-10, TCUT + 140), th * d2r))
    anchors["femur"] = ctx.user_to_device(-30, -230)
    anchors["tibia"] = ctx.user_to_device(*L.rot((0, Y0 + 420), th * d2r))
