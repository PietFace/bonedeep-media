"""Lumbar spine, lateral view (anterior = +x, posterior = -x). Origin = centre of L3 body."""
import math, cairo, sys
sys.path.insert(0, "/home/claude/short"); sys.path.insert(0, "/home/claude/v2")
import knee_still as K
import knee_flex as L
import anim2 as A
import common as C

d2r = math.pi / 180
BH, DH = 70, 24            # half body height, half disc height
LORD = [22, 10, 0, -9, -16]  # angle of L5..L1 'up' direction (deg, + = tilted forward), neutral lordosis


def body(c):
    c.move_to(-92, -62); c.curve_to(-60, -74, 60, -74, 94, -64)
    c.curve_to(86, -20, 86, 20, 96, 64)
    c.curve_to(60, 74, -60, 74, -92, 62)
    c.curve_to(-84, 20, -84, -20, -92, -62); c.close_path()


def arch(c):
    # pedicle + lamina + spinous process + articular processes, one outline
    c.move_to(-92, -40)
    c.curve_to(-120, -48, -140, -70, -150, -96)          # superior articular process
    c.curve_to(-160, -110, -180, -104, -182, -80)
    c.curve_to(-186, -50, -200, -36, -230, -40)          # lamina to spinous process
    c.line_to(-330, -46); c.curve_to(-352, -40, -352, 36, -330, 42)
    c.line_to(-236, 40)
    c.curve_to(-210, 46, -196, 70, -200, 96)              # inferior articular process
    c.curve_to(-204, 118, -176, 120, -168, 98)
    c.curve_to(-160, 70, -140, 40, -120, 34)
    c.curve_to(-104, 30, -94, 22, -92, 10)
    c.close_path()


def disc_shape(c):
    c.move_to(-88, -DH); c.curve_to(-30, -DH - 6, 40, -DH - 6, 92, -DH)
    c.curve_to(100, -8, 100, 8, 92, DH)
    c.curve_to(40, DH + 6, -30, DH + 6, -88, DH)
    c.curve_to(-96, 8, -96, -8, -88, -DH); c.close_path()


def draw_vert(c):
    K.soft_shadow(c, arch, 5, 8, 0.4, 26)
    K.textured(c, arch, (0.92, 0.84, 0.66), (0.70, 0.57, 0.38), -350, -100, -90, 100, pores=90,
               pore_area=(-350, -110, -90, 120), inner=0.4, grain=0.2)
    K.soft_shadow(c, body, 6, 10, 0.45, 30)
    K.textured(c, body, K.BONE_L, K.BONE_D, -95, -70, 95, 70, pores=160, pore_area=(-95, -72, 95, 72),
               inner=0.35, spec=(-20, -30, 80, 0.35))


def draw_disc(c):
    K.textured(c, disc_shape, (0.88, 0.92, 0.97), (0.60, 0.68, 0.80), -90, -DH, 90, DH, inner=0.25, grain=0.04,
               edge=(0.45, 0.5, 0.58))
    c.save(); disc_shape(c); c.clip()
    for i in range(6):   # annulus rings
        y = -DH + 8 + i * 7
        c.move_to(-90, y); c.curve_to(-30, y - 2, 40, y - 2, 95, y)
        K.rgba(c, (1, 1, 1), 0.25); c.set_line_width(1.5); c.stroke()
    g = cairo.RadialGradient(-12, 0, 2, -12, 0, 40)
    g.add_color_stop_rgba(0, 0.75, 0.9, 1.0, 0.9); g.add_color_stop_rgba(1, 0.75, 0.9, 1.0, 0)
    c.set_source(g); c.paint()
    c.restore()


def sacrum(c):
    c.move_to(-92, -30); c.curve_to(-40, -44, 50, -44, 96, -32)
    c.curve_to(90, 60, 60, 200, 0, 330)
    c.curve_to(-30, 380, -80, 380, -110, 320)
    c.curve_to(-170, 220, -230, 120, -300, 40)
    c.curve_to(-320, 10, -300, -40, -250, -36)
    c.curve_to(-180, -32, -130, -26, -92, -30); c.close_path()


def draw_sacrum(c):
    K.soft_shadow(c, sacrum, 6, 10, 0.45, 40)
    K.textured(c, sacrum, (0.92, 0.84, 0.66), (0.66, 0.53, 0.36), -300, -40, 100, 380, pores=250,
               pore_area=(-300, -40, 100, 380), inner=0.4)


SPR = {}


def sprites():
    if not SPR:
        SPR["vert"] = L.Sprite((-370, -130, 120, 140), draw_vert)
        SPR["disc"] = L.Sprite((-110, -40, 115, 40), draw_disc)
        SPR["sac"] = L.Sprite((-330, -60, 120, 400), draw_sacrum)
    return SPR


def chain(flex=0.0, ds=1.0):
    """returns list of frames (cx, cy, ang) for sacrum-top, L5..L1 and disc centres, with L3 at origin."""
    ang = LORD[0]
    pos = (0.0, 0.0)
    sac = (pos[0], pos[1], ang + 10)           # sacral plate
    frames, discs = [], []
    cur = pos; a_prev = ang + 10
    for i in range(5):
        a = LORD[i] + flex * 7
        am = (a_prev + a) / 2 * d2r
        dh = DH * ds
        dc = (cur[0] + math.sin(am) * dh, cur[1] - math.cos(am) * dh)
        discs.append((dc[0], dc[1], (a_prev + a) / 2))
        ar = a * d2r
        vc = (dc[0] + math.sin(ar) * (dh + BH), dc[1] - math.cos(ar) * (dh + BH))
        frames.append((vc[0], vc[1], a))
        cur = (vc[0] + math.sin(ar) * BH, vc[1] - math.cos(ar) * BH); a_prev = a
    ox, oy = frames[2][0], frames[2][1]
    sh = lambda f: (f[0] - ox, f[1] - oy, f[2])
    return sh(sac), [sh(f) for f in frames], [sh(d) for d in discs]


def to_world(f, pt):
    a = f[2] * d2r
    return (f[0] + pt[0] * math.cos(a) - pt[1] * math.sin(a), f[1] + pt[0] * math.sin(a) + pt[1] * math.cos(a))


def spine(ctx, t, st, anchors):
    sp = sprites()
    ds = st.get("ds", 1.0)
    sac, fr, dc = chain(st.get("flex", 0), ds)
    spasm = st.get("spasm", 0); green = st.get("green", 0)
    # erector spinae behind (posterior), follows spinous tips
    pts = [to_world(sac, (-280, 120))] + [to_world(f, (-370, 0)) for f in fr] + [to_world(fr[-1], (-380, -260))]
    def mpath(c, off=0.0):
        c.move_to(*pts[0])
        for q0, q1 in zip(pts[:-1], pts[1:]):
            m = ((q0[0] + q1[0]) / 2, (q0[1] + q1[1]) / 2)
            c.curve_to(q0[0], q0[1], m[0], m[1], m[0], m[1])
        c.line_to(*pts[-1])
    w = 115 * (1 + 0.3 * spasm)
    col_hot = C.mix(K.MUS_L, (1.0, 0.25, 0.2), spasm)
    if spasm > 0 or green > 0:
        gc = C.mix(C.RED, C.GREEN, green)
        for lw, al in ((w * 1.8, 0.10), (w * 1.35, 0.16)):
            mpath(ctx); A.rgba(ctx, gc, al * max(spasm * (0.6 + 0.4 * math.sin(t * 9)), green)); ctx.set_line_width(lw)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke()
    mpath(ctx); A.rgba(ctx, K.MUS_D); ctx.set_line_width(w); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
    mpath(ctx); A.rgba(ctx, col_hot, 0.9); ctx.set_line_width(w * 0.8); ctx.stroke()
    for k in range(9):   # fibres
        ctx.save(); ctx.translate((k - 4) * 9 * math.cos(0.3), 0)
        mpath(ctx); A.rgba(ctx, (1, 0.6, 0.5) if k % 2 else (0.3, 0.05, 0.04), 0.35); ctx.set_line_width(2.2); ctx.stroke()
        ctx.restore()
    anchors["muscle"] = ctx.user_to_device(*pts[3])
    ctx.save(); ctx.translate(sac[0], sac[1]); ctx.rotate(sac[2] * d2r); sp["sac"].paint(ctx); ctx.restore()
    hl = st.get("hl", -1)
    for i, d in enumerate(dc):
        ctx.save(); ctx.translate(d[0], d[1]); ctx.rotate(d[2] * d2r); ctx.scale(1, ds); sp["disc"].paint(ctx)
        if green > 0 or st.get("disc_glow", 0) > 0:
            disc_shape(ctx); A.rgba(ctx, C.GREEN if green > 0 else C.CYAN, 0.8 * max(green, st.get("disc_glow", 0)))
            ctx.set_line_width(5); ctx.stroke()
        ctx.restore()
    for i, f in enumerate(fr):
        ctx.save(); ctx.translate(f[0], f[1]); ctx.rotate(f[2] * d2r); sp["vert"].paint(ctx)
        if hl == i or st.get("all_glow", 0) > 0:
            g = st.get("all_glow", 0) if hl != i else 1.0
            body(ctx); A.rgba(ctx, C.CYAN if green <= 0 else C.GREEN, 0.7 * g); ctx.set_line_width(6); ctx.stroke()
        ctx.restore()
    # interspinous ligaments between spinous tips
    lig = st.get("lig", 0)
    for i in range(4):
        a = to_world(fr[i], (-300, -44)); b = to_world(fr[i + 1], (-300, 40))
        hot = lig if i == 0 else lig * 0.3
        L.band(ctx, a, b, 22, 22, col=C.mix(K.LIG_L, (1, 0.45, 0.4), hot), colD=C.mix(K.LIG_D, (0.7, 0.1, 0.1), hot), seed=i, fib=6)
        if hot > 0:
            C.glow_blob(ctx, (a[0] + b[0]) / 2, (a[1] + b[1]) / 2, 90, C.RED, hot * (0.6 + 0.4 * math.sin(t * 8)))
    # alignment line (posterior body walls)
    al = st.get("align", 0)
    if al > 0:
        ps = [to_world(f, (-92, 0)) for f in fr]
        ctx.move_to(*to_world(sac, (-100, -30)))
        for q in ps: ctx.line_to(*q)
        ctx.set_dash([18, 12]); A.rgba(ctx, C.GREEN, al); ctx.set_line_width(7); ctx.stroke(); ctx.set_dash([])
    # nerve roots / cauda equina (canal behind bodies)
    nv = st.get("nerve", 0)
    if nv > 0:
        top = to_world(fr[-1], (-130, -120)); mid = to_world(fr[2], (-130, 0)); bot = to_world(sac, (-150, 200))
        C.pulse_path(ctx, [top, mid, to_world(fr[0], (-130, 60)), bot], t, nv, speed=-1.4)
    anchors["disc"] = ctx.user_to_device(*to_world(dc[1], (60, 0)))
    anchors["vert"] = ctx.user_to_device(*to_world(fr[3], (60, 0)))
    anchors["lig"] = ctx.user_to_device(*to_world(fr[0], (-300, -60)))
    return fr
