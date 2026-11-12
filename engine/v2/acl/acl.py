"""Lateral knee (anterior = +x) with ACL, tear and reconstruction stages. Origin = flexion axis."""
import math, random, cairo, sys
sys.path.insert(0, "/home/claude/short"); sys.path.insert(0, "/home/claude/v2")
import knee_still as K
import knee_flex as L
import anim2 as A
import common as C

d2r = math.pi / 180
R, Y0 = L.R, L.Y0
BG = (0.03, 0.04, 0.07)
FA = (-95.0, 25.0)                 # femoral ACL footprint (femur frame)
TA = (40.0, Y0 + 6.0)              # tibial ACL footprint (tibia frame)
FT = (-175.0, -170.0)              # femoral tunnel end
TT = (130.0, Y0 + 260.0)           # tibial tunnel entry (anteromedial cortex)


def tib(pt, th):
    return L.rot(pt, th * d2r)


def lerp(a, b, k):
    return (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k)


def metal(ctx, x0, y0, x1, y1, a=1.0):
    g = cairo.LinearGradient(x0, y0, x1, y1)
    for k, v in ((0, 0.55), (0.3, 0.95), (0.5, 0.7), (0.75, 0.98), (1, 0.6)):
        g.add_color_stop_rgba(k, v * 0.92, v * 0.95, v, a)
    ctx.set_source(g)


def fray(ctx, end, base, seed, a=1.0):
    r = random.Random(seed)
    ang = math.atan2(end[1] - base[1], end[0] - base[0])
    for _ in range(12):
        aa = ang + r.uniform(-0.9, 0.9); ln = r.uniform(10, 30)
        ctx.move_to(*end); ctx.line_to(end[0] + math.cos(aa) * ln, end[1] + math.sin(aa) * ln)
        A.rgba(ctx, (0.98, 0.86, 0.82), 0.9 * a); ctx.set_line_width(2.4); ctx.stroke()


def tunnel(ctx, a, b, k, w=34):
    if k <= 0: return
    e = lerp(a, b, k)
    ctx.move_to(*a); ctx.line_to(*e)
    A.rgba(ctx, (0.25, 0.16, 0.10), 0.85); ctx.set_line_width(w + 8); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
    ctx.move_to(*a); ctx.line_to(*e)
    ctx.set_source_rgba(*BG, 0.95); ctx.set_line_width(w); ctx.stroke()


def drill(ctx, t, a, b, k):
    e = lerp(a, b, k)
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    ctx.save(); ctx.translate(*e); ctx.rotate(ang)
    ctx.rectangle(-420, -13, 420, 26); metal(ctx, 0, -13, 0, 13); ctx.fill()
    for i in range(10):   # spiral flutes
        x = -i * 14 - (t * 300) % 14
        ctx.move_to(x, -13); ctx.line_to(x - 8, 13); A.rgba(ctx, (0.3, 0.32, 0.36), 0.8); ctx.set_line_width(3); ctx.stroke()
    ctx.restore()
    r = random.Random(int(t * 30))
    for _ in range(10):
        aa = r.uniform(0, 2 * math.pi); ln = r.uniform(10, 40)
        ctx.move_to(*e); ctx.line_to(e[0] + math.cos(aa) * ln, e[1] + math.sin(aa) * ln)
        A.rgba(ctx, (1.0, 0.9, 0.6), r.uniform(0.4, 0.9)); ctx.set_line_width(2.5); ctx.stroke()


def graft_path(th):
    return [tib(TT, th), tib(TA, th), FA, FT]


def poly_partial(pts, k):
    """points of the polyline up to fraction k of its length"""
    segs = [math.dist(a, b) for a, b in zip(pts, pts[1:])]
    tot = sum(segs); goal = tot * k; out = [pts[0]]
    for (a, b), s in zip(zip(pts, pts[1:]), segs):
        if goal >= s:
            out.append(b); goal -= s
        else:
            out.append(lerp(a, b, goal / s)); break
    return out


def knee(ctx, t, st, anchors):
    sp = L.sprites()
    th = st.get("theta", 0.0)
    hv = st.get("harvest", 0.0)
    # hamstring tendon (harvest source)
    hb = L.rot((-120, Y0 + 70), th * d2r)
    hg = st.get("ham_glow", 0.0)
    if hg > 0:
        for w, a in ((80, 0.12), (46, 0.25)):
            ctx.move_to(-152, -140); ctx.line_to(*hb); A.rgba(ctx, C.YEL, a * hg); ctx.set_line_width(w); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
    L.band(ctx, (-152, -140), hb, 30, 24, seed=3, fib=8)
    anchors["ham"] = ctx.user_to_device(*lerp((-152, -140), hb, 0.5))
    sp["femur"].paint(ctx)
    ctx.save(); ctx.rotate(th * d2r); sp["tibia"].paint(ctx)
    L.draw_menisci(ctx, -7 * min(1, th / 100), -16 * min(1, th / 100), 0)
    tunnel(ctx, TA, TT, st.get("ttun", 0.0))
    ctx.restore()
    tunnel(ctx, FA, FT, st.get("ftun", 0.0))
    # harvested strip flying out
    if 0 < hv < 1:
        off = (-260 * hv, -80 * hv)
        ctx.save(); ctx.translate(*off)
        L.band(ctx, (-152, -140), hb, 22, 18, col=(1.0, 0.95, 0.75), colD=(0.85, 0.7, 0.4), seed=11, fib=6)
        ctx.restore()
    # native ACL (intact / torn)
    a_, b_ = FA, tib(TA, th)
    na = st.get("acl", 1.0)
    if na > 0:
        ag = st.get("acl_glow", 0.0)
        if ag > 0:
            for w, al in ((90, 0.12), (54, 0.25)):
                ctx.move_to(*a_); ctx.line_to(*b_); A.rgba(ctx, st.get("acl_col", C.RED), al * ag); ctx.set_line_width(w); ctx.stroke()
        tr = st.get("torn", 0.0)
        if tr <= 0:
            L.band(ctx, a_, b_, 42, 38, seed=21, fib=8)
        else:
            k = 0.45 - 0.12 * tr
            m1 = lerp(a_, b_, k); m2 = lerp(b_, a_, k * 0.8)
            ctx.save(); ctx.push_group()
            L.band(ctx, a_, m1, 30, 22, seed=22, fib=6); L.band(ctx, b_, m2, 30, 22, seed=23, fib=6)
            fray(ctx, m1, a_, 5); fray(ctx, m2, b_, 6)
            ctx.pop_group_to_source(); ctx.paint_with_alpha(na); ctx.restore()
        anchors["acl"] = ctx.user_to_device(*lerp(a_, b_, 0.5))
    # drills
    if st.get("tdrill") is not None:
        ctx.save(); ctx.rotate(th * d2r); drill(ctx, t, TT, TA, st["tdrill"]); ctx.restore()
    if st.get("fdrill") is not None:
        drill(ctx, t, TA_world(th), FT, st["fdrill"])
    # graft
    gk = st.get("graft", 0.0)
    if gk > 0:
        pts = poly_partial(graft_path(th), gk)
        wk = st.get("weak", 0.0); gr = st.get("gstrong", 0.0)
        col = C.mix(C.mix((1.0, 0.96, 0.82), (1.0, 0.55, 0.45), wk), (0.75, 1.0, 0.85), gr)
        colD = C.mix(C.mix((0.85, 0.72, 0.45), (0.7, 0.2, 0.15), wk), (0.3, 0.65, 0.45), gr)
        gg = st.get("graft_glow", 0.0)
        if gg > 0:
            ctx.move_to(*pts[0])
            for q in pts[1:]: ctx.line_to(*q)
            gc = C.GREEN if gr > 0.3 else (C.RED if wk > 0.3 else C.CYAN)
            A.rgba(ctx, gc, 0.25 * gg); ctx.set_line_width(80); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
        wdt = 28 * (1 - 0.35 * wk * (0.6 + 0.4 * math.sin(t * 6)))
        for a, b in zip(pts, pts[1:]):
            L.band(ctx, a, b, wdt, wdt, col=col, colD=colD, seed=31, fib=7)
        anchors["graft"] = ctx.user_to_device(*lerp(FA, tib(TA, th), 0.5))
    # interference screws
    sc = st.get("screws", 0.0)
    if sc > 0:
        for (pt, ang) in ((lerp(FA, FT, 0.55), math.atan2(FT[1] - FA[1], FT[0] - FA[0])),
                          (tib(lerp(TA, TT, 0.45), th), math.atan2(tib(TT, th)[1] - tib(TA, th)[1], tib(TT, th)[0] - tib(TA, th)[0]))):
            ctx.save(); ctx.translate(*pt); ctx.rotate(ang); ctx.translate(0, 26 + 40 * (1 - sc))
            ctx.rectangle(-60, -12, 120, 24); metal(ctx, 0, -12, 0, 12, sc); ctx.fill()
            for i in range(8):
                ctx.move_to(-56 + i * 15, -12); ctx.line_to(-50 + i * 15, 12); A.rgba(ctx, (0.35, 0.37, 0.4), 0.8 * sc); ctx.set_line_width(2.5); ctx.stroke()
            ctx.restore()
        anchors["screw"] = ctx.user_to_device(*lerp(FA, FT, 0.55))
    L_patella(ctx, th)
    anchors["femur"] = ctx.user_to_device(-30, -260)
    anchors["tibia"] = ctx.user_to_device(*tib((0, Y0 + 420), th))


def TA_world(th):
    return tib(TA, th)


def L_patella(ctx, th):
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
