"""Bone Deep — 'Why does your knee crack?' v2. Voice-timed, silhouette -> x-ray zoom -> articulated knee."""
import sys, os, json, math, random, subprocess
sys.path.insert(0, "/home/claude/short")
import cairo, numpy as np, cv2
import anim2 as A
import knee_flex as L
import knee_still as K
from anim import p, eo, eio, back, clamp, rrect

W, H, FPS = 1080, 1920, 30
d2r = math.pi / 180
TL = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "timeline.json")))
TOTAL = TL["total"]
T = {s["id"]: (s["t0"], s["t1"]) for s in TL["segs"]}
WORDS = {s["id"]: s["words"] for s in TL["segs"]}


def wt(seg, word):
    for w in WORDS[seg]:
        if w["w"].lower().strip(",.?!") == word:
            return w["t0"]
    return T[seg][0]


TC = T["crack"][0]                   # crack moment
TPOP = T["pop"][0]
TFLICK = wt("tendon", "flicking") + 0.15
TGIVE = wt("lock", "gives")
TLOCK = wt("lock", "locks")
TCHECK = T["check"][0]
TIN0, TIN1 = T["bad"][0] + 0.15, T["bad"][1] + 0.05          # zoom in
TOUT0, TOUT1 = T["move"][0] - 0.1, T["move"][0] + 1.7          # zoom out
TSTAND0, TSTAND1 = T["move"][0] + 0.7, TOTAL - 0.25

GREEN = (0.25, 0.95, 0.60)
COL_CAPS = A.CYAN
M0 = 0.27                             # model scale inside the figure
ANKLE = (470.0, 1390.0)
LS, LT, LTO = 280.0, 300.0, 330.0


# ---------------- helpers ----------------
def ss(x):
    x = clamp(x); return x * x * (3 - 2 * x)


def kf(t, keys, f=ss):
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            k = f((t - t0) / (t1 - t0)) if t1 > t0 else 1
            if isinstance(v0, tuple):
                return tuple(a + (b - a) * k for a, b in zip(v0, v1))
            return v0 + (v1 - v0) * k
    return keys[-1][1]


def mix(a, b, k):
    return tuple(x + (y - x) * k for x, y in zip(a, b))


# ---------------- figure pose ----------------
def squat_amount(t):
    return kf(t, [(0.25, 0.0), (T["goes"][1] + 0.2, 1.0), (TSTAND0, 1.0), (TSTAND1, 0.0)])


def pose(s):
    psi = (5 + 70 * s) * d2r            # thigh angle from vertical (backwards)
    a_s = (5 + 25 * s) * d2r            # shin lean forward
    tau = (8 + 35 * s) * d2r            # torso lean
    Ax, Ay = ANKLE
    Kx, Ky = Ax + LS * math.sin(a_s), Ay - LS * math.cos(a_s)
    Hx, Hy = Kx - LT * math.sin(psi), Ky - LT * math.cos(psi)
    Sx, Sy = Hx + LTO * math.sin(tau), Hy - LTO * math.cos(tau)
    head = (Sx + 100 * math.sin(tau + 0.1), Sy - 100 * math.cos(tau + 0.1))
    al = (10 + 75 * s) * d2r
    E = (Sx + 150 * math.sin(al), Sy + 150 * math.cos(al))
    al2 = al + 12 * d2r * s + 0.15
    Hd = (E[0] + 140 * math.sin(al2), E[1] + 140 * math.cos(al2))
    phi = -psi
    theta = (a_s + psi) / d2r
    return dict(A=(Ax, Ay), K=(Kx, Ky), H=(Hx, Hy), S=(Sx, Sy), head=head, E=E, Hd=Hd, phi=phi, theta=theta)


PH_LOCK = pose(1.0)


def limb(ctx, a, b, w0, w1):
    ang = math.atan2(b[1] - a[1], b[0] - a[0]); nx, ny = -math.sin(ang), math.cos(ang)
    ctx.move_to(a[0] + nx * w0 / 2, a[1] + ny * w0 / 2)
    ctx.line_to(b[0] + nx * w1 / 2, b[1] + ny * w1 / 2)
    ctx.arc_negative(b[0], b[1], w1 / 2, ang + math.pi / 2, ang - math.pi / 2)
    ctx.line_to(a[0] - nx * w0 / 2, a[1] - ny * w0 / 2)
    ctx.arc_negative(a[0], a[1], w0 / 2, ang - math.pi / 2, ang + math.pi / 2)
    ctx.close_path()


def figure_path(ctx, P, back=False):
    o = (-26, -6) if back else (0, 0)
    sh = lambda q: (q[0] + o[0], q[1] + o[1])
    A_, K_, H_ = sh(P["A"]), sh(P["K"]), sh(P["H"])
    limb(ctx, H_, K_, 110, 84)
    limb(ctx, K_, A_, 80, 46)
    ctx.new_sub_path()
    ctx.move_to(A_[0] - 40, A_[1] - 10); ctx.line_to(A_[0] + 150, A_[1] + 22)
    ctx.line_to(A_[0] + 150, A_[1] + 46); ctx.line_to(A_[0] - 48, A_[1] + 46); ctx.close_path()
    if back:
        return
    limb(ctx, P["H"], P["S"], 150, 160)
    limb(ctx, P["S"], P["E"], 58, 46)
    limb(ctx, P["E"], P["Hd"], 46, 36)
    ctx.new_sub_path(); ctx.arc(P["head"][0], P["head"][1], 64, 0, 2 * math.pi)
    nk = mix(P["S"], P["head"], 0.5)
    limb(ctx, P["S"], nk, 60, 52)


def silhouette_layer(matrix, P, alpha):
    """Dark figure with cyan rim glow, rendered in screen space via numpy."""
    if alpha <= 0:
        return None
    m = cairo.ImageSurface(cairo.FORMAT_A8, W, H)
    c = cairo.Context(m); c.set_matrix(matrix); c.set_antialias(cairo.ANTIALIAS_GOOD)
    figure_path(c, P); c.set_source_rgba(0, 0, 0, 1); c.fill()
    mb = cairo.ImageSurface(cairo.FORMAT_A8, W, H)
    c2 = cairo.Context(mb); c2.set_matrix(matrix); figure_path(c2, P, back=True); c2.set_source_rgba(0, 0, 0, 1); c2.fill()
    st = m.get_stride()
    mask = np.ndarray((H, st), np.uint8, m.get_data())[:, :W].astype(np.float32) / 255
    maskb = np.ndarray((H, st), np.uint8, mb.get_data())[:, :W].astype(np.float32) / 255
    allm = np.maximum(mask, maskb)
    glow = cv2.GaussianBlur(allm, (0, 0), 14) * 0.9 + cv2.GaussianBlur(allm, (0, 0), 4) * 0.6
    glow = np.clip(glow - allm, 0, 1)
    inner = np.clip(allm - cv2.GaussianBlur(allm, (0, 0), 6), 0, 1)
    gy = np.linspace(1.0, 0.6, H, dtype=np.float32)[:, None]
    body = np.stack([0.30 * gy, 0.20 * gy, 0.12 * gy], -1) * mask[..., None] + \
        np.stack([0.17 * gy, 0.11 * gy, 0.07 * gy], -1) * (maskb * (1 - mask))[..., None]
    cyan = np.array([1.0, 0.85, 0.25], np.float32)         # BGR
    rgb = body + glow[..., None] * cyan * 0.85 + inner[..., None] * cyan * 0.55
    a = np.clip(allm + glow * 0.85, 0, 1)
    out = np.zeros((H, W, 4), np.float32)
    out[..., :3] = np.clip(rgb, 0, 1) * alpha
    out[..., 3] = a * alpha
    out[..., :3] = np.minimum(out[..., :3], out[..., 3:4])
    buf = (out * 255).astype(np.uint8)
    return cairo.ImageSurface.create_for_data(memoryview(np.ascontiguousarray(buf)), cairo.FORMAT_ARGB32, W, H), buf


# ---------------- knee (model frame: condyle centre at origin, femur up, anterior +x) ----------------
Y0 = L.Y0
R = L.R


def caps_path(c, sw):
    c.save(); c.translate(-10, 110); c.scale((235 + 40 * sw) / 100, (265 + 35 * sw) / 100)
    c.arc(0, 0, 100, 0, 2 * math.pi); c.restore()


def tib(pt, th, dx):
    return L.rot((pt[0] + dx, pt[1]), th)


def bubbles(ctx, t, th, vis, grow=1.0, pops=(), n=22, seed=3):
    if vis <= 0:
        return
    r = random.Random(seed)
    base = 90 + th
    for i in range(n):
        ang = (base + r.uniform(-30, 30)) * d2r
        rad = R + r.uniform(0, 30)
        wob = 3 * math.sin(t * 3 + i)
        x, y = rad * math.cos(ang) + wob, rad * math.sin(ang) + wob * 0.6
        size = r.uniform(12, 28) * grow * (0.6 + 0.4 * ss(vis * 1.5 - i / n * 0.5))
        popped = None
        for pt in pops:
            if t >= pt + (i % 4) * 0.03:
                popped = t - pt - (i % 4) * 0.03
        if popped is not None:
            if popped < 0.45:
                k = popped / 0.45
                A.rgba(ctx, A.WHITE, (1 - k) * vis); ctx.set_line_width(4 * (1 - k) + 1)
                ctx.arc(x, y, size + 90 * eo(k), 0, 2 * math.pi); ctx.stroke()
            continue
        gg = cairo.RadialGradient(x, y, size * 0.5, x, y, size * 2.2)
        gg.add_color_stop_rgba(0, A.CYAN[0], A.CYAN[1], A.CYAN[2], 0.35 * vis); gg.add_color_stop_rgba(1, A.CYAN[0], A.CYAN[1], A.CYAN[2], 0)
        ctx.set_source(gg); ctx.arc(x, y, size * 2.2, 0, 2 * math.pi); ctx.fill()
        g = cairo.RadialGradient(x - size * 0.35, y - size * 0.35, 1, x, y, size)
        g.add_color_stop_rgba(0, 1, 1, 1, 0.95 * vis)
        g.add_color_stop_rgba(0.7, 0.6, 0.9, 1, 0.45 * vis)
        g.add_color_stop_rgba(1, A.CYAN[0], A.CYAN[1], A.CYAN[2], 0.15 * vis)
        ctx.set_source(g); ctx.arc(x, y, size, 0, 2 * math.pi); ctx.fill()


def menisci_glow(ctx, th, dx, col, g):
    if g <= 0:
        return
    f = clamp(th / 100)
    ctx.save(); ctx.rotate(th * d2r); ctx.translate(dx, 0)
    for (xi, xo) in ((45 - 7 * f, 104 - 7 * f), (-45 - 16 * f, -106 - 16 * f)):
        for w, a in ((40, 0.10), (24, 0.18), (12, 0.30)):
            L.meniscus_poly(ctx, xi, xo); A.rgba(ctx, col, a * g); ctx.set_line_width(w)
            ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke()
    ctx.restore()


def tendon_curve(ctx, a, m, b, w, col=K.LIG_L, colD=K.LIG_D, glow=0.0, gcol=A.CYAN):
    def path(c):
        c.move_to(*a); c.curve_to(m[0], m[1], m[0], m[1], *b)
    if glow > 0:
        for lw, al in ((w * 3.2, 0.10), (w * 2, 0.2)):
            path(ctx); A.rgba(ctx, gcol, al * glow); ctx.set_line_width(lw); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
    path(ctx); A.rgba(ctx, colD); ctx.set_line_width(w); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
    path(ctx); A.rgba(ctx, col); ctx.set_line_width(w * 0.7); ctx.stroke()
    path(ctx); A.rgba(ctx, (1, 1, 1), 0.35); ctx.set_line_width(2); ctx.stroke()


def nerve(ctx, t, a):
    if a <= 0:
        return
    pts = [(-118, 300), (-150, 0), (-175, -500), (-150, -1150)]

    def path(c):
        c.move_to(*pts[0]); c.curve_to(*pts[1], *pts[2], *pts[3])
    path(ctx); A.rgba(ctx, (1.0, 0.85, 0.35), 0.75 * a); ctx.set_line_width(9); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
    # travelling pulses
    for j in range(3):
        k = ((t * 1.6 + j / 3) % 1.0)
        u = 1 - k
        q = (u**3 * pts[0][0] + 3 * u * u * k * pts[1][0] + 3 * u * k * k * pts[2][0] + k**3 * pts[3][0],
             u**3 * pts[0][1] + 3 * u * u * k * pts[1][1] + 3 * u * k * k * pts[2][1] + k**3 * pts[3][1])
        g = cairo.RadialGradient(q[0], q[1], 2, q[0], q[1], 70)
        g.add_color_stop_rgba(0, 1, 1, 1, a); g.add_color_stop_rgba(0.3, 1, 0.3, 0.25, 0.8 * a)
        g.add_color_stop_rgba(1, 1, 0.2, 0.2, 0)
        ctx.set_source(g); ctx.arc(q[0], q[1], 70, 0, 2 * math.pi); ctx.fill()


def knee_side(ctx, t, st, anchors):
    """st: dict of state values. Draws in model frame."""
    sp = L.sprites()
    th, dx = st["theta"], st["dx"]
    f = clamp(th / 100)
    # capsule + fluid (behind)
    sw = st.get("swell", 0)
    fl = st.get("fluid", 0)
    ccol = mix(COL_CAPS, A.RED, clamp(sw * 1.4))
    if fl > 0 or sw > 0:
        caps_path(ctx, sw)
        g = cairo.RadialGradient(-10, 110, 40, -10, 110, 300)
        g.add_color_stop_rgba(0, ccol[0], ccol[1], ccol[2], 0.30 * max(fl, sw))
        g.add_color_stop_rgba(1, ccol[0], ccol[1], ccol[2], 0.08 * max(fl, sw))
        ctx.set_source(g); ctx.fill()
    # hamstring tendon (behind) with flick
    hb = tib((-120, Y0 + 70), th * d2r, dx)
    ha = (-152, -140)
    hm = ((ha[0] + hb[0]) / 2 - 30 + st.get("flick", 0), (ha[1] + hb[1]) / 2)
    tendon_curve(ctx, ha, hm, hb, 26, glow=st.get("tendon_glow", 0))
    anchors["tendon"] = ctx.user_to_device(*hm)
    sp["femur"].paint(ctx)
    ctx.save(); ctx.rotate(th * d2r); ctx.translate(dx, 0)
    sp["tibia"].paint(ctx)
    L.draw_menisci(ctx, -7 * f, -16 * f, 0)
    ctx.restore()
    menisci_glow(ctx, th, dx, st.get("men_col", A.CYAN), st.get("men_glow", 0.3))
    bubbles(ctx, t, th, st.get("gas", 0), st.get("grow", 1), st.get("pops", ()))
    ang = (90 + th) * d2r
    anchors["joint"] = ctx.user_to_device((R + 14) * math.cos(ang), (R + 14) * math.sin(ang))
    # patella + tendons (constant patellar tendon length)
    tub = tib((128, Y0 + 100), th * d2r, dx)
    best = None
    for i in range(160):
        s_ = 0.02 + 0.96 * i / 159
        pt, (tx, ty) = L.track_at(s_)
        nx, ny = ty, -tx
        c = (pt[0] + nx * L.PAT_OFF, pt[1] + ny * L.PAT_OFF)
        distal = (c[0] + tx * L.PAT_HALF, c[1] + ty * L.PAT_HALF)
        err = abs(math.dist(distal, tub) - L.LPT)
        if best is None or err < best[0]:
            best = (err, c, (tx, ty), distal)
    _, c, (tx, ty), distal = best
    prox = (c[0] - tx * L.PAT_HALF, c[1] - ty * L.PAT_HALF)
    qa = st.get("quad", 0)
    if qa > 0:   # quadriceps activation glow
        for w, a in ((130, 0.08), (80, 0.14)):
            ctx.move_to(170, -900); ctx.curve_to(220, -650, 200, -480, prox[0], prox[1])
            A.rgba(ctx, (1.0, 0.55, 0.2), a * qa); ctx.set_line_width(w); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
    L.band(ctx, (128, -380), prox, 60, 52, seed=5, fib=12)
    L.band(ctx, distal, tub, 40, 34, seed=7, fib=10)
    ctx.save(); ctx.translate(*c); ctx.rotate(math.atan2(ty, tx)); ctx.scale(L.PAT_SC, L.PAT_SC)
    sp["patella"].paint(ctx); ctx.restore()
    # capsule outline (in front, subtle)
    if fl > 0 or sw > 0:
        caps_path(ctx, sw); ctx.set_dash([14, 10])
        A.rgba(ctx, ccol, 0.75 * max(fl, sw)); ctx.set_line_width(5); ctx.stroke(); ctx.set_dash([])
    anchors["capsule"] = ctx.user_to_device(-10 + 240 * math.cos(-0.5), 110 + 270 * math.sin(-0.5))
    nerve(ctx, t, st.get("nerve", 0))
    if st.get("bump", 0) > 0:
        g = cairo.RadialGradient(-165, -20, 4, -165, -20, 60)
        g.add_color_stop_rgba(0, 1, 1, 1, 0.8 * st["bump"]); g.add_color_stop_rgba(1, 1, 1, 1, 0)
        ctx.set_source(g); ctx.arc(-165, -20, 60, 0, 2 * math.pi); ctx.fill()


# ---------------- state over time ----------------
def inside_theta(t):
    sq = PH_LOCK["theta"]
    return kf(t, [
        (TIN1, sq), (T["capsule"][0] + 0.8, 25), (T["bend"][0], 20),
        (T["bend"][1], 98), (TPOP + 0.3, 92), (T["tendon"][0] + 0.2, 45),
        (TFLICK - 0.5, 72), (TFLICK, 62), (T["harmless"][0], 35),
    ]) if t < T["harmless"][0] else harmless_theta(t)


def harmless_theta(t):
    if t < T["pain"][0]:
        k = t - T["harmless"][0]
        return 45 - 33 * math.cos(k * 2.2)
    if t < TLOCK:
        return kf(t, [(T["pain"][0], 50), (T["pain"][0] + 0.6, 30)])
    if t < TGIVE:
        return 42 + 1.5 * math.sin(t * 60) * (1 if t < TGIVE - 0.1 else 0)
    if t < TCHECK + 0.3:
        return kf(t, [(TGIVE, 42), (TGIVE + 0.18, 92), (TGIVE + 0.5, 80), (TCHECK + 0.3, 40)], f=eo)
    return kf(t, [(TCHECK + 0.3, 40), (TOUT0, PH_LOCK["theta"])])


def state(t):
    s = squat_amount(t)
    P = pose(s)
    inside = TIN0 <= t <= TOUT1
    st = {"theta": P["theta"], "dx": 18 * clamp(P["theta"] / 100)}
    if TIN1 <= t <= TOUT0:
        th = inside_theta(t)
        st["theta"], st["dx"] = th, 18 * clamp(th / 100)
    # crack moment: bubbles pop inside the x-ray window
    st["gas"] = clamp(p(t, TC - 0.6, TC - 0.2)) * (1 - p(t, TC + 0.6, TC + 0.9))
    st["pops"] = (TC,)
    st["men_glow"] = 0.3
    st["fluid"] = p(t, T["capsule"][0] + 0.5, T["capsule"][0] + 1.4) * (1 - p(t, T["tendon"][0], T["tendon"][0] + 0.6))
    if T["gas"][0] - 0.2 <= t <= TPOP + 0.8:
        st["gas"] = ss(p(t, T["gas"][0], T["gas"][0] + 1.0))
        st["grow"] = 0.7 + 1.0 * ss(p(t, T["bend"][0] + 0.5, T["bend"][1]))
        st["pops"] = (TPOP,)
        st["quad"] = 0.8 * p(t, T["bend"][0], T["bend"][0] + 0.6) * (1 - p(t, TPOP, TPOP + 0.6))
    if T["tendon"][0] <= t <= T["harmless"][0]:
        pull = ss(p(t, T["tendon"][0] + 0.3, TFLICK - 0.05))
        if t < TFLICK:
            st["flick"] = -48 * pull
        else:
            k = t - TFLICK
            st["flick"] = 12 * math.exp(-k * 5) * math.cos(k * 28) - 48 * math.exp(-k * 30)
        st["tendon_glow"] = p(t, T["tendon"][0], T["tendon"][0] + 0.5)
        st["bump"] = math.exp(-max(0, t - TFLICK) * 4) if t >= TFLICK else 0
    if T["harmless"][0] <= t <= T["pain"][0]:
        st["men_col"] = GREEN
        st["men_glow"] = 0.3 + 0.7 * p(t, T["harmless"][0], T["harmless"][0] + 0.6)
    if T["pain"][0] <= t <= TOUT0:
        st["nerve"] = p(t, T["pain"][0], T["pain"][0] + 0.3) * (1 - p(t, T["swell"][0] + 0.3, T["swell"][0] + 0.7))
        st["swell"] = p(t, T["swell"][0], T["swell"][0] + 0.5) * (1 - p(t, TLOCK, TLOCK + 0.4))
    return s, P, st


def camera(t, P):
    """returns zoom, rotation, focus(world), and the x-ray window radius (world)."""
    Kp = P["K"]
    fig_c = (520.0, 900.0)
    z_in = 0.55 / M0
    # inside camera targets in model coords (converted to world below)
    if t < TIN0:
        z, rot, foc = 1.0, 0.0, fig_c
    elif t < TIN1 + 0.01:
        k = eio(p(t, TIN0, TIN1))
        z = 1.0 + (z_in - 1.0) * k
        rot = -PH_LOCK["phi"] * k
        foc = mix(fig_c, PH_LOCK["K"], k)
    elif t < TOUT0:
        z, rot, foc = z_in, -PH_LOCK["phi"], PH_LOCK["K"]
        # local moves (in model coords)
        mv = [(TIN1, (0, 0), 1.0), (T["capsule"][0] + 0.6, (-150, 120), 1.0), (T["gas"][0], (-90, 140), 1.0),
              (T["gas"][0] + 0.8, (0, 0), 1.6), (TPOP + 0.4, (0, 0), 1.8), (T["tendon"][0] + 0.5, (-150, 40), 1.25),
              (T["harmless"][0] + 0.3, (-60, 150), 1.0), (T["pain"][0] + 0.2, (-80, -260), 0.75),
              (T["swell"][0] + 0.2, (-60, 140), 1.05), (TCHECK + 0.9, (-60, 140), 1.0), (TOUT0, (0, 0), 1.0)]
        keys_off = [(a, b) for a, b, _ in mv]
        keys_z = [(a, c) for a, _, c in mv]
        off = kf(t, keys_off); zm = kf(t, keys_z)
        jw = kf(t, [(T["gas"][0], 0.0), (T["gas"][0] + 0.8, 1.0), (TPOP + 0.4, 1.0), (T["tendon"][0] + 0.5, 0.0)])
        if jw > 0:
            th = inside_theta(t); ang = (90 + th) * d2r
            off = (off[0] + jw * 0.9 * (R + 14) * math.cos(ang), off[1] + jw * 0.9 * (R + 14) * math.sin(ang))
        z *= zm
        ph = PH_LOCK["phi"]
        wo = (M0 * (off[0] * math.cos(ph) - off[1] * math.sin(ph)), M0 * (off[0] * math.sin(ph) + off[1] * math.cos(ph)))
        foc = (foc[0] + wo[0], foc[1] + wo[1])
    elif t < TOUT1:
        k = eio(p(t, TOUT0, TOUT1))
        z = z_in + (1.0 - z_in) * k
        rot = -PH_LOCK["phi"] * (1 - k)
        foc = mix(PH_LOCK["K"], fig_c, k)
    else:
        z, rot, foc = 1.0, 0.0, fig_c
    # x-ray window radius (world units)
    if t < TC:
        rw = 0
    elif t < TIN0:
        rw = 125 * back(p(t, TC, TC + 0.3))
    elif t < TIN1:
        rw = 125 + 900 * ss(p(t, TIN0 + 0.4, TIN1))
    elif t < TOUT0:
        rw = 2000
    elif t < TOUT1:
        rw = 1025 - 900 * ss(p(t, TOUT0, TOUT1 - 0.2))
    else:
        rw = 125 * (1 - ss(p(t, TOUT1, TOUT1 + 0.5)))
    fig_a = 1 - ss(p(t, TIN0 + 0.9, TIN1 - 0.1)) if t < TOUT0 else ss(p(t, TOUT0 + 0.5, TOUT1))
    return z, rot, foc, rw, fig_a


# ---------------- shake / flash ----------------
EVENTS = [(TC, 1.0, "big"), (TPOP, 0.5, "small"), (TFLICK, 0.35, "small"), (TGIVE, 0.9, "big"),
          (TCHECK + 0.05, 0.3, "small")]


def shake(t):
    sx = sy = 0; zb = 0; fl = 0
    for te, amp, kind in EVENTS:
        dt = t - te
        if dt < 0:
            continue
        e = math.exp(-dt * 7)
        sx += 30 * amp * e * math.sin(dt * 71 + te)
        sy += 30 * amp * e * math.cos(dt * 53 + te)
        zb += 0.06 * amp * math.exp(-dt * 9)
        if kind == "big":
            fl = max(fl, 0.7 * math.exp(-dt * 7))
    return sx, sy, zb, fl


# ---------------- background with parallax & bokeh ----------------
rnd = random.Random(7)
FAR = [(rnd.uniform(-300, W + 300), rnd.uniform(-300, H + 300), rnd.uniform(2, 5), rnd.uniform(0, 6.28)) for _ in range(90)]
NEAR = [(rnd.uniform(-200, W + 200), rnd.uniform(-200, H + 200), rnd.uniform(40, 110), rnd.uniform(0, 6.28)) for _ in range(9)]


def background(ctx, t, cam, tint):
    g = cairo.RadialGradient(W / 2, 950, 60, W / 2, 950, 1250)
    g.add_color_stop_rgb(0, *tint); g.add_color_stop_rgb(1, 0.02, 0.025, 0.045)
    ctx.set_source(g); ctx.paint()
    z, foc = cam
    px, py = -(foc[0] - 520) * z * 0.08, -(foc[1] - 900) * z * 0.08
    for x, y, r, ph in FAR:
        xx = (x + px - 6 * t) % (W + 600) - 300
        yy = (y + py - 10 * t) % (H + 600) - 300
        A.rgba(ctx, A.CYAN, 0.10 + 0.08 * math.sin(t * 2 + ph)); ctx.arc(xx, yy, r, 0, 2 * math.pi); ctx.fill()


def bokeh_front(ctx, t, cam):
    z, foc = cam
    px, py = -(foc[0] - 520) * z * 0.5, -(foc[1] - 900) * z * 0.5
    for x, y, r, ph in NEAR:
        xx = (x + px + 14 * math.sin(t * 0.4 + ph)) % (W + 400) - 200
        yy = (y + py - 22 * t) % (H + 400) - 200
        g = cairo.RadialGradient(xx, yy, r * 0.2, xx, yy, r)
        g.add_color_stop_rgba(0, A.CYAN[0], A.CYAN[1], A.CYAN[2], 0.10)
        g.add_color_stop_rgba(0.75, A.CYAN[0], A.CYAN[1], A.CYAN[2], 0.07)
        g.add_color_stop_rgba(1, A.CYAN[0], A.CYAN[1], A.CYAN[2], 0)
        ctx.set_source(g); ctx.arc(xx, yy, r, 0, 2 * math.pi); ctx.fill()


# ---------------- text ----------------
YEL, RED, WHITE, GREY = A.YEL, A.RED, A.WHITE, A.GREY
NO_CAP = {"crack", "pop"}


def captions(ctx, t):
    seg = None
    for s in TL["segs"]:
        if s["t0"] - 0.05 <= t <= s["t1"] + 0.25:
            seg = s
    if seg is None or seg["id"] in NO_CAP:
        return
    words = seg["words"]
    size = 58
    A.font(ctx, size)
    sp = size * 0.30
    lines, cur, wsum = [], [], 0
    for w in words:
        ww = ctx.text_extents(w["w"]).x_advance
        if cur and wsum + sp + ww > 880:
            lines.append(cur); cur, wsum = [], 0
        cur.append((w, ww)); wsum += (sp if len(cur) > 1 else 0) + ww
    lines.append(cur)
    a_in = clamp((t - seg["t0"] + 0.05) / 0.12) * (1 - clamp((t - seg["t1"] - 0.1) / 0.15))
    y0 = 1300 - (len(lines) - 1) * size * 0.6
    for li, line in enumerate(lines):
        tw = sum(ww for _, ww in line) + sp * (len(line) - 1)
        x = W / 2 - tw / 2
        y = y0 + li * size * 1.2
        for w, ww in line:
            active = w["t0"] <= t < w["t1"]
            said = t >= w["t0"]
            col = YEL if active else (WHITE if said else (0.62, 0.66, 0.72))
            s_ = 1.12 if active else 1.0
            ctx.save(); ctx.translate(x + ww / 2, y - size * 0.35); ctx.scale(s_, s_); ctx.translate(-(x + ww / 2), -(y - size * 0.35))
            A.font(ctx, size); ctx.move_to(x, y); ctx.text_path(w["w"])
            A.rgba(ctx, (0, 0, 0), 0.85 * a_in); ctx.set_line_width(10); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke()
            A.txt(ctx, w["w"], x, y, size, col, a_in, align="l", shadow=False)
            ctx.restore()
            x += ww + sp


def slam_word(ctx, word, t, t0, col, size, y, hold=1.0, rot=-0.05):
    k = p(t, t0, t0 + 0.2)
    if k <= 0:
        return
    a = clamp(k * 3) * (1 - p(t, t0 + hold, t0 + hold + 0.2))
    if a <= 0:
        return
    s = 1.7 - 0.7 * eo(k)
    ctx.save(); ctx.translate(W / 2, y - size * 0.35); ctx.scale(s, s); ctx.rotate(rot); ctx.translate(-W / 2, -(y - size * 0.35))
    A.font(ctx, size); e = ctx.text_extents(word)
    for gw, ga in ((34, 0.10), (16, 0.22)):
        ctx.move_to(W / 2 - e.x_advance / 2, y); ctx.text_path(word)
        A.rgba(ctx, col, ga * a); ctx.set_line_width(gw); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke()
    A.txt(ctx, word, W / 2, y, size, col, a)
    ctx.restore()


def label(ctx, s, anchor, lx, ly, k, col=A.CYAN):
    if k <= 0 or anchor is None:
        return
    tx, ty = anchor
    A.rgba(ctx, col, k); ctx.arc(tx, ty, 8, 0, 2 * math.pi); ctx.fill()
    ctx.set_line_width(3.5); ctx.move_to(tx, ty)
    ctx.line_to(tx + (lx - tx) * eo(k), ty + (ly - ty) * eo(k)); ctx.stroke()
    A.txt(ctx, s, lx, ly - 14, 44, col, p(k, 0.5, 1))


def flag_list(ctx, t):
    items = [("PAIN", T["pain"][0] + 0.7), ("SWELLING", T["swell"][0]), ("LOCKING", TLOCK), ("GIVING WAY", TGIVE)]
    end = TCHECK + 1.2
    a_all = 1 - p(t, end, end + 0.25)
    if t < items[0][1] or a_all <= 0:
        return
    for i, (w, t0) in enumerate(items):
        k = p(t, t0, t0 + 0.18)
        if k <= 0:
            continue
        y = 400 + i * 96
        x = 150 + (1 - eo(k)) * -120
        a = clamp(k * 2) * a_all
        A.rgba(ctx, RED, a); ctx.arc(x, y - 20, 22, 0, 2 * math.pi); ctx.fill()
        A.txt(ctx, "!", x, y - 4, 34, WHITE, a, shadow=False)
        A.txt(ctx, w, x + 48, y, 74, RED, a, align="l")
    # stamp
    k = p(t, TCHECK, TCHECK + 0.18)
    if k > 0:
        s = 1.8 - 0.8 * eo(k); a = clamp(k * 3) * a_all
        ctx.save(); ctx.translate(W / 2, 830); ctx.rotate(-0.07); ctx.scale(s, s)
        A.font(ctx, 78); e = ctx.text_extents("GET IT CHECKED")
        rrect(ctx, -e.x_advance / 2 - 34, -70, e.x_advance + 68, 104, 18)
        A.rgba(ctx, WHITE, a); ctx.set_line_width(8); ctx.stroke()
        A.txt(ctx, "GET IT CHECKED", 0, 6, 78, WHITE, a)
        ctx.restore()


# ---------------- frame ----------------
def render(t):
    s, P, st = state(t)
    z, rot, foc, rw, fig_a = camera(t, P)
    sx, sy, zb, flash = shake(t)
    green = p(t, T["harmless"][0], T["harmless"][0] + 0.5) * (1 - p(t, T["pain"][0], T["pain"][0] + 0.3))
    green = max(green, p(t, T["move"][0] + 0.3, T["move"][0] + 1.0) * (1 - p(t, TOTAL - 1.0, TOTAL)))
    redk = st.get("nerve", 0) * 0.6 + st.get("swell", 0) * 0.5
    tint = mix(mix((0.09, 0.12, 0.20), (0.04, 0.19, 0.15), green), (0.20, 0.05, 0.06), clamp(redk))
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf); ctx.set_antialias(cairo.ANTIALIAS_GOOD)
    background(ctx, t, (z, foc), tint)
    # world camera
    ctx.save()
    ctx.translate(W / 2 + sx, 900 + sy)
    ctx.scale(z * (1 + zb), z * (1 + zb))
    ctx.rotate(rot)
    ctx.translate(-foc[0], -foc[1])
    world = ctx.get_matrix()
    # floor glow
    if fig_a > 0:
        g = cairo.RadialGradient(ANKLE[0] + 40, ANKLE[1] + 50, 10, ANKLE[0] + 40, ANKLE[1] + 50, 360)
        g.add_color_stop_rgba(0, A.CYAN[0], A.CYAN[1], A.CYAN[2], 0.25 * fig_a); g.add_color_stop_rgba(1, A.CYAN[0], A.CYAN[1], A.CYAN[2], 0)
        ctx.save(); ctx.translate(0, ANKLE[1] + 50); ctx.scale(1, 0.12); ctx.translate(0, -(ANKLE[1] + 50))
        ctx.set_source(g); ctx.arc(ANKLE[0] + 40, ANKLE[1] + 50, 360, 0, 2 * math.pi); ctx.fill(); ctx.restore()
    ctx.restore()
    sil = silhouette_layer(world, P, fig_a)
    if sil:
        ctx.set_source_surface(sil[0], 0, 0); ctx.paint()
    anchors = {}
    if rw > 0:
        ctx.save(); ctx.set_matrix(world)
        Kp = P["K"] if not (TIN1 <= t <= TOUT0) else PH_LOCK["K"]
        phi = P["phi"] if not (TIN1 <= t <= TOUT0) else PH_LOCK["phi"]
        if TIN0 <= t <= TIN1:
            Kp, phi = PH_LOCK["K"], PH_LOCK["phi"]
        ctx.arc(Kp[0], Kp[1], rw, 0, 2 * math.pi)
        if rw < 1500:
            ctx.save(); ctx.clip_preserve()
            ctx.set_source_rgb(0.03, 0.04, 0.07); ctx.paint(); ctx.restore()
        ctx.clip()
        ctx.push_group()
        ctx.translate(*Kp); ctx.rotate(phi); ctx.scale(M0, M0)
        knee_side(ctx, t, st, anchors)
        model = ctx.pop_group()
        ctx.set_source(model); ctx.paint()
        # light sweep across the anatomy
        sw = ((t * 0.45) % 1.6) - 0.3
        dev = ctx.device_to_user
        x0, y0 = dev(-200 + sw * W * 1.6, 0); x1, y1 = dev(200 + sw * W * 1.6, 400)
        lg = cairo.LinearGradient(x0, y0, x1, y1)
        lg.add_color_stop_rgba(0, 1, 1, 1, 0); lg.add_color_stop_rgba(0.5, 1, 0.98, 0.92, 0.22); lg.add_color_stop_rgba(1, 1, 1, 1, 0)
        ctx.set_source(lg); ctx.mask(model)
        ctx.restore()
        if rw < 1500:   # window rim
            ctx.save(); ctx.set_matrix(world)
            for w_, a_ in ((26, 0.10), (12, 0.25), (4, 0.9)):
                ctx.arc(Kp[0], Kp[1], rw, 0, 2 * math.pi); A.rgba(ctx, A.CYAN, a_)
                ctx.set_line_width(w_ / z); ctx.stroke()
            ctx.restore()
    bokeh_front(ctx, t, (z, foc))
    A.vignette(ctx, red=clamp(redk) * 0.6 + (0.5 * math.exp(-(t - TGIVE) * 3) if t > TGIVE else 0))
    # top fade for text
    tg = cairo.LinearGradient(0, 0, 0, 900)
    tg.add_color_stop_rgba(0, 0.02, 0.02, 0.04, 0.55); tg.add_color_stop_rgba(1, 0.02, 0.02, 0.04, 0)
    ctx.set_source(tg); ctx.rectangle(0, 0, W, 900); ctx.fill()
    bg = cairo.LinearGradient(0, 1150, 0, 1500)
    bg.add_color_stop_rgba(0, 0.02, 0.02, 0.04, 0); bg.add_color_stop_rgba(1, 0.02, 0.02, 0.04, 0.6)
    ctx.set_source(bg); ctx.rectangle(0, 1150, W, H - 1150); ctx.fill()
    # labels
    label(ctx, "joint capsule", anchors.get("capsule"), 800, 760,
          p(t, T["capsule"][0] + 1.0, T["capsule"][0] + 1.5) * (1 - p(t, T["gas"][0], T["gas"][0] + 0.3)))
    label(ctx, "gas bubbles", anchors.get("joint"), 300, 760,
          p(t, T["gas"][0] + 0.9, T["gas"][0] + 1.4) * (1 - p(t, T["bend"][0] + 0.6, T["bend"][0] + 0.9)))
    label(ctx, "tendon", anchors.get("tendon"), 270, 780,
          p(t, T["tendon"][0] + 0.8, T["tendon"][0] + 1.3) * (1 - p(t, T["harmless"][0], T["harmless"][0] + 0.3)), WHITE)
    # big words
    slam_word(ctx, "CRACK!", t, TC, YEL, 210, 600, hold=1.0)
    slam_word(ctx, "IS IT BAD?", t, T["bad"][0], WHITE, 130, 560, hold=1.6, rot=0)
    slam_word(ctx, "POP", t, TPOP, YEL, 220, 600, hold=0.7)
    slam_word(ctx, "CLICK", t, TFLICK, WHITE, 120, 560, hold=0.6)
    slam_word(ctx, "USUALLY", t, wt("harmless", "usually"), GREEN, 120, 470, hold=T["pain"][0] - wt("harmless", "usually") - 0.3, rot=0)
    slam_word(ctx, "HARMLESS", t, wt("harmless", "harmless"), GREEN, 150, 610, hold=T["pain"][0] - wt("harmless", "harmless") - 0.3, rot=0)
    flag_list(ctx, t)
    slam_word(ctx, "KEEP MOVING", t, wt("move", "keep"), GREEN, 116, 560, hold=TOTAL - wt("move", "keep") - 0.6, rot=0)
    captions(ctx, t)
    if t > T["move"][0]:
        A.txt(ctx, "General information, not personal medical advice", W / 2, 1440, 26, GREY,
              0.8 * p(t, T["move"][0], T["move"][0] + 0.4) * (1 - p(t, TOTAL - 0.4, TOTAL)), bold=False, shadow=False)
    if flash > 0:
        A.rgba(ctx, WHITE, flash); ctx.paint()
    return surf


BLUR = [(TC - 0.05, TC + 0.35), (TIN0, TIN1), (TPOP - 0.05, TPOP + 0.3), (TFLICK - 0.1, TFLICK + 0.3),
        (TGIVE - 0.05, TGIVE + 0.4), (TOUT0, TOUT1)]


def frame_bytes(i):
    t = i / FPS
    if any(a <= t <= b for a, b in BLUR):
        acc = None
        for j in range(4):
            sf = render(t + (j - 1.5) / (4 * FPS) * 0.6)
            arr = np.ndarray((H, W, 4), np.uint8, sf.get_data()).astype(np.uint16)
            acc = arr if acc is None else acc + arr
        return (acc // 4).astype(np.uint8).tobytes()
    return bytes(render(t).get_data())


if __name__ == "__main__":
    if sys.argv[1] == "still":
        sf = render(float(sys.argv[2])); sf.write_to_png(sys.argv[3])
    else:
        i0, i1, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        tmp = out.replace(".mp4", ".tmp.mp4")
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
               "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
               "-pix_fmt", "yuv420p", "-r", str(FPS), tmp]
        pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for i in range(i0, i1):
            pr.stdin.write(frame_bytes(i))
        pr.stdin.close()
        if pr.wait() == 0:
            os.replace(tmp, out)
        print("done", out, flush=True)
