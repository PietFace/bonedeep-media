import sys, math
sys.path.insert(0, "/home/claude/v2"); sys.path.insert(0, "/home/claude/short"); sys.path.insert(0, "/home/claude/v2/achilles")
import cairo
import common as C
from common import W, H, kf, ss, mix, p, eo, eio, back, clamp, YEL, RED, WHITE, GREY, CYAN, GREEN, d2r
import anim2 as A
import achilles as AC

D = "/home/claude/v2/achilles"
TL = C.Timeline(D + "/timeline.json"); T = TL.T; TOTAL = TL.total
THIT = T["hit"][0]
TIN0, TIN1 = TL.wt("why", "let's") - 0.1, T["why"][1] + 0.2
TPOP = TL.wt("flags", "pop,")
TOUT0, TOUT1 = T["end"][0] - 0.1, T["end"][0] + 1.8
M0 = 0.27
REF = (520, 900)
GROUND = 1440.0


def run_amp(t):
    return kf(t, [(0, 1), (T["morning"][0] + 0.2, 1), (T["morning"][0] + 1.2, 0), (TOUT1 - 0.2, 0), (TOUT1 + 0.6, 1)], f=ss)


def phase(t):
    return t * 2 * math.pi * 1.45


def leg_pose(hip, ph, amp):
    th = (26 * math.sin(ph)) * amp * d2r                       # thigh angle (+ = forward)
    kn = (8 + (60 * max(0, math.sin(ph - 1.9)) + 18)) * amp * d2r   # knee flexion
    K_ = (hip[0] + 300 * math.sin(th), hip[1] + 300 * math.cos(th))
    sa = th - kn
    A_ = (K_[0] + 290 * math.sin(sa), K_[1] + 290 * math.cos(sa))
    fa = sa + (-10 * math.sin(ph) * amp) * d2r                   # foot angle relative to shin
    return K_, A_, fa


def pose(t):
    amp = run_amp(t); ph = phase(t)
    bob = 14 * abs(math.cos(ph)) * amp
    lean = 9 * amp * d2r
    hip = (500.0, GROUND - 600 - 22 + bob * 0 - (8 * amp) + bob)
    sh = (hip[0] + 330 * math.sin(lean), hip[1] - 330 * math.cos(lean))
    head = (sh[0] + 100 * math.sin(lean + 0.1), sh[1] - 100 * math.cos(lean + 0.1))
    legs = [leg_pose(hip, ph, amp), leg_pose(hip, ph + math.pi, amp)]
    # make the lowest foot touch the ground
    low = max(l[1][1] for l in legs)
    dy = GROUND - 30 - low
    hip = (hip[0], hip[1] + dy); sh = (sh[0], sh[1] + dy); head = (head[0], head[1] + dy)
    legs = [((k[0], k[1] + dy), (a[0], a[1] + dy), fa) for k, a, fa in legs]
    arms = []
    for s in (1, -1):
        aa = (-30 * s * math.sin(ph)) * amp * d2r
        E = (sh[0] + 150 * math.sin(aa), sh[1] + 150 * math.cos(aa))
        ea = aa + (80 * amp + 6) * d2r
        Hd = (E[0] + 140 * math.sin(ea), E[1] + 140 * math.cos(ea))
        arms.append((E, Hd))
    return dict(hip=hip, sh=sh, head=head, legs=legs, arms=arms, lean=lean)


def foot(ctx, A_, fa):
    ctx.save(); ctx.translate(*A_); ctx.rotate(-fa + 0.0)
    ctx.move_to(-44, -14); ctx.line_to(150, 18); ctx.curve_to(170, 24, 170, 44, 150, 46); ctx.line_to(-46, 46)
    ctx.curve_to(-60, 30, -56, -8, -44, -14); ctx.close_path(); ctx.restore()


def figure(ctx, P, which):
    """which: 0 = near side (right leg/arm + torso), 1 = far side"""
    K_, A_, fa = P["legs"][which]
    C.limb(ctx, P["hip"], K_, 106, 80); ctx.fill()
    C.limb(ctx, K_, A_, 78, 44); ctx.fill()
    foot(ctx, A_, fa); ctx.fill()
    E, Hd = P["arms"][which]
    if which == 1:
        C.limb(ctx, P["sh"], E, 56, 46); ctx.fill(); C.limb(ctx, E, Hd, 44, 34); ctx.fill()
        return
    C.limb(ctx, P["hip"], P["sh"], 150, 160); ctx.fill()
    nk = mix(P["sh"], P["head"], 0.5)
    C.limb(ctx, P["sh"], nk, 60, 52); ctx.fill()
    ctx.arc(P["head"][0], P["head"][1], 64, 0, 2 * math.pi); ctx.fill()
    C.limb(ctx, P["sh"], E, 56, 46); ctx.fill(); C.limb(ctx, E, Hd, 44, 34)


PS = pose(T["why"][0])     # standing pose used for the zoom
ANK = PS["legs"][0][1]


def state(t):
    st = {"pf": 0.0}
    if T["morning"][0] + 1.0 <= t < TIN1:
        st["hot"] = p(t, TL.wt("morning", "heel"), TL.wt("morning", "heel") + 0.4); st["thick"] = 0.6 * st["hot"]
    if TIN1 <= t < TOUT0:
        st["hot"] = 0.0
        if t < T["anat"][0] + 0.3:
            st["hot"] = 1 - p(t, TIN1, T["anat"][0] + 0.3); st["thick"] = 0.6 * st["hot"]
        if T["anat"][0] <= t < T["load"][0]:
            st["mglow"] = p(t, TL.wt("anat", "calf"), TL.wt("anat", "calf") + 0.3) * (1 - p(t, TL.wt("anat", "achilles"), TL.wt("anat", "achilles") + 0.3))
            st["tglow"] = p(t, TL.wt("anat", "achilles"), TL.wt("anat", "achilles") + 0.3)
        if T["load"][0] <= t < T["over"][0] + 0.5:     # running steps: rhythmic plantarflexion + load pulses
            k = p(t, T["load"][0], T["load"][0] + 0.5) * (1 - p(t, T["over"][0], T["over"][0] + 0.5))
            w = 0.5 + 0.5 * math.sin((t - T["load"][0]) * 2 * math.pi * 1.4)
            st["pf"] = (-12 + 38 * w) * k; st["con"] = w * k; st["load"] = k
        if T["over"][0] <= t < T["rest"][0]:
            k = p(t, TL.wt("over", "irritated,"), TL.wt("over", "irritated,") + 0.4)
            st["hot"] = k; st["thick"] = p(t, TL.wt("over", "thickens."), TL.wt("over", "thickens.") + 0.6) * 0.5 + 0.5 * k
            st["load"] = p(t, T["over"][0], T["over"][0] + 0.3) * (1 - k); st["lcol"] = RED
            st["pf"] = 10 * math.sin((t - T["over"][0]) * 7) * (1 - k)
        if T["pattern"][0] <= t < T["rest"][0]:
            # morning stiff (hot) -> warm (cool) -> next day (hot)
            a, b, c = TL.wt("pattern", "stiff"), TL.wt("pattern", "better"), TL.wt("pattern", "worse")
            st["hot"] = kf(t, [(a, 1.0), (b, 1.0), (b + 0.4, 0.25), (c, 0.25), (c + 0.3, 1.0)])
            st["thick"] = 0.9
            st["pf"] = kf(t, [(a, 0), (b, 0), (b + 0.5, 20), (c - 0.3, -10), (c, 0)]) if b <= t < c else 0
        if T["rest"][0] <= t < T["fix"][0]:
            calm = p(t, TL.wt("rest", "calms"), TL.wt("rest", "calms") + 0.6)
            back_ = p(t, TL.wt("rest", "comes"), TL.wt("rest", "comes") + 0.4)
            st["hot"] = 1 - calm * 0.85 + back_ * 0.85
            st["thick"] = 0.9
            st["load"] = p(t, TL.wt("rest", "load."), TL.wt("rest", "load.") + 0.3); st["lcol"] = GREEN
        if T["fix"][0] <= t < T["flags"][0]:
            k = p(t, T["fix"][0], T["fix"][0] + 0.6)
            w = 0.5 - 0.5 * math.cos((t - T["fix"][0]) * 2 * math.pi * 0.42)     # slow calf raises
            st["pf"] = (-12 + 42 * w) * k; st["con"] = w * k
            st["green"] = p(t, T["fix"][0] + 0.8, T["fix"][0] + 2.0)
            st["thick"] = 0.9 * (1 - p(t, T["fix"][0] + 1.0, T["fix"][1]))
            st["hot"] = 0.5 * (1 - p(t, T["fix"][0], T["fix"][0] + 1.5))
            st["tglow"] = st["green"]; st["tcol"] = GREEN; st["mglow"] = st["green"] * 0.6; st["mcol"] = GREEN
        if T["flags"][0] <= t < TOUT0:
            st["rupture"] = eo(p(t, TPOP, TPOP + 0.18))
            st["pf"] = -4 * st["rupture"]
    if t >= TOUT0:
        st["green"] = 1 - p(t, TOUT0, TOUT1)
    return st


def camera(t):
    fig_c = (520.0, 950.0)
    z_in = 1.05 / M0
    tgt = (ANK[0] + 20 * M0, ANK[1] - 120 * M0)
    if t < TIN0:
        return 1.0, fig_c
    if t < TIN1:
        k = eio(p(t, TIN0, TIN1)); return 1 + (z_in - 1) * k, mix(fig_c, tgt, k)
    if t < TOUT0:
        mv = [(TIN1, (20, -120), 1.0), (T["anat"][0] + 0.4, (0, -280), 0.85), (TL.wt("anat", "achilles"), (-20, -150), 1.05),
              (T["load"][0] + 0.3, (60, -130), 0.95), (T["over"][0] + 0.3, (-110, -120), 1.45), (T["pattern"][0] + 0.3, (-100, -110), 1.3),
              (T["rest"][0] + 0.3, (-40, -140), 1.05), (T["fix"][0] + 0.3, (60, -140), 0.9), (T["flags"][0] + 0.3, (-100, -130), 1.3),
              (TOUT0 - 0.3, (20, -120), 1.0)]
        off = kf(t, [(a, b) for a, b, _ in mv]); zm = kf(t, [(a, c) for a, _, c in mv])
        return z_in * zm, (ANK[0] + off[0] * M0, ANK[1] + off[1] * M0)
    if t < TOUT1:
        k = eio(p(t, TOUT0, TOUT1)); return z_in + (1 - z_in) * k, mix(tgt, fig_c, k)
    return 1.0, fig_c


def window(t):
    t0 = TL.wt("morning", "heel")
    if t < t0: return 0
    if t < TIN0: return 120 * back(p(t, t0, t0 + 0.3))
    if t < TIN1: return 120 + 1200 * ss(p(t, TIN0 + 0.4, TIN1))
    if t < TOUT0: return 4000
    if t < TOUT1: return 1320 - 1200 * ss(p(t, TOUT0, TOUT1 - 0.2))
    return 120 * (1 - ss(p(t, TOUT1, TOUT1 + 0.4)))


def win_center(P):
    A_ = P["legs"][0][1]
    return (A_[0] - 100 * M0, A_[1] - 250 * M0)


EV = [(THIT, 0.8, True), (TL.wt("over", "irritated,"), 0.35, False), (TPOP, 1.0, True), (TL.wt("flags", "get"), 0.3, False)]


def render(t):
    st = state(t)
    z, foc = camera(t)
    sx, sy, zb, flash = C.shake(t, EV)
    fig_a = (1 - ss(p(t, TIN0 + 0.9, TIN1 - 0.1))) if t < TOUT0 else ss(p(t, TOUT0 + 0.5, TOUT1))
    redk = 0.5 * st.get("hot", 0) * (1 if TIN1 < t < TOUT0 else 0.4) + 0.5 * st.get("rupture", 0)
    green = max(st.get("green", 0) * (1 if t < TOUT0 else 0), p(t, T["end"][0] + 0.3, T["end"][0] + 1.0) * (1 - p(t, TOTAL - 1, TOTAL)))
    tint = mix(mix((0.09, 0.12, 0.20), (0.04, 0.19, 0.15), green), (0.20, 0.05, 0.06), clamp(redk))
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf); ctx.set_antialias(cairo.ANTIALIAS_GOOD)
    C.background(ctx, t, z, foc, tint, REF)
    ctx.save(); ctx.translate(W / 2 + sx, 950 + sy); ctx.scale(z * (1 + zb), z * (1 + zb)); ctx.translate(-foc[0], -foc[1])
    world = ctx.get_matrix()
    if fig_a > 0:   # ground + speed lines while running
        g = cairo.RadialGradient(520, GROUND, 10, 520, GROUND, 420)
        g.add_color_stop_rgba(0, CYAN[0], CYAN[1], CYAN[2], 0.22 * fig_a); g.add_color_stop_rgba(1, CYAN[0], CYAN[1], CYAN[2], 0)
        ctx.save(); ctx.translate(0, GROUND); ctx.scale(1, 0.1); ctx.translate(0, -GROUND); ctx.set_source(g)
        ctx.arc(520, GROUND, 420, 0, 2 * math.pi); ctx.fill(); ctx.restore()
        amp = run_amp(t)
        for i in range(7):
            x = 900 - ((t * 900 + i * 260) % 1500)
            y = GROUND + 6 + (i % 3) * 14
            ctx.move_to(x, y); ctx.line_to(x + 120, y); A.rgba(ctx, CYAN, 0.35 * amp * fig_a); ctx.set_line_width(3); ctx.stroke()
    ctx.restore()
    P = pose(t) if (t < TIN0 or t > TOUT1) else PS
    sil = C.silhouette_layer(world, lambda c: figure(c, P, 0), fig_a, lambda c: figure(c, P, 1))
    if sil:
        ctx.set_source_surface(sil[0], 0, 0); ctx.paint()
    rw = window(t); anchors = {}
    A_ = P["legs"][0][1]
    if rw > 0:
        wc = win_center(P)
        ctx.save(); ctx.set_matrix(world)
        ctx.arc(wc[0], wc[1], rw, 0, 2 * math.pi)
        if rw < 2000:
            ctx.save(); ctx.clip_preserve(); ctx.set_source_rgb(0.03, 0.04, 0.07); ctx.paint(); ctx.restore()
        ctx.clip()
        ctx.push_group()
        ctx.translate(*A_); ctx.scale(M0, M0)
        AC.leg(ctx, t, st, anchors)
        model = ctx.pop_group()
        ctx.set_source(model); ctx.paint()
        C.light_sweep(ctx, t, model)
        ctx.restore()
        if rw < 2000:
            C.window_rim(ctx, world, wc, rw, z)
    C.bokeh_front(ctx, t, z, foc, REF)
    A.vignette(ctx, red=clamp(redk) * 0.6 + (0.5 * math.exp(-(t - THIT) * 3) if THIT < t < TIN0 else 0)
               + (0.6 * math.exp(-(t - TPOP) * 3) if t > TPOP else 0))
    C.fades(ctx)
    C.label(ctx, "calf muscles", anchors.get("calf"), 230, 640,
            p(t, TL.wt("anat", "calf"), TL.wt("anat", "calf") + 0.4) * (1 - p(t, T["load"][0], T["load"][0] + 0.3)), WHITE)
    C.label(ctx, "Achilles tendon", anchors.get("tendon"), 250, 980,
            p(t, TL.wt("anat", "achilles"), TL.wt("anat", "achilles") + 0.4) * (1 - p(t, T["load"][0], T["load"][0] + 0.3)), CYAN)
    C.label(ctx, "heel bone", anchors.get("heel"), 820, 1060,
            p(t, TL.wt("anat", "achilles") + 0.6, TL.wt("anat", "achilles") + 1.0) * (1 - p(t, T["load"][0], T["load"][0] + 0.3)), WHITE)
    C.slam_word(ctx, "OUCH!", t, THIT, RED, 190, 600, hold=0.9)
    C.slam_word(ctx, "WHY?", t, T["why"][0], WHITE, 180, 560, hold=1.0, rot=0)
    C.slam_word(ctx, "STRONGEST TENDON", t, TL.wt("anat", "strongest"), YEL, 92, 440, hold=T["anat"][1] - TL.wt("anat", "strongest") + 0.2, rot=0)
    C.slam_word(ctx, "SEVERAL × BODY WEIGHT", t, TL.wt("load", "several"), YEL, 84, 440, hold=T["load"][1] - TL.wt("load", "several") + 0.2, rot=0)
    C.slam_word(ctx, "TOO FAST", t, TL.wt("over", "too"), RED, 140, 440, hold=TL.wt("over", "irritated,") - TL.wt("over", "too") - 0.1)
    C.slam_word(ctx, "IRRITATED", t, TL.wt("over", "irritated,"), RED, 130, 440, hold=T["over"][1] - TL.wt("over", "irritated,") + 0.2)
    C.item_list(ctx, t, [("STIFF IN THE MORNING", TL.wt("pattern", "stiff")), ("BETTER ONCE WARM", TL.wt("pattern", "better")),
                         ("WORSE NEXT DAY", TL.wt("pattern", "worse"))], T["rest"][0] - 0.1, size=60, mark="•", col=YEL)
    C.slam_word(ctx, "JUST REST?", t, T["rest"][0], WHITE, 130, 440, hold=TL.wt("rest", "tendons") - T["rest"][0] - 0.2, rot=0)
    C.slam_word(ctx, "TENDONS NEED LOAD", t, TL.wt("rest", "tendons"), GREEN, 92, 440, hold=T["rest"][1] - TL.wt("rest", "tendons") + 0.2, rot=0)
    C.slam_word(ctx, "HEAVY & SLOW", t, TL.wt("fix", "slow,"), GREEN, 120, 440, hold=TL.wt("fix", "build") - TL.wt("fix", "slow,") - 0.1, rot=0)
    C.slam_word(ctx, "BUILD UP GRADUALLY", t, TL.wt("fix", "build"), GREEN, 86, 440, hold=T["fix"][1] - TL.wt("fix", "build") + 0.2, rot=0)
    C.slam_word(ctx, "POP!", t, TPOP, RED, 220, 520, hold=TL.wt("flags", "get") - TPOP - 0.1)
    C.stamp(ctx, t, TL.wt("flags", "get"), "SAME DAY", TOUT0 + 0.3, y=640, col=RED)
    C.slam_word(ctx, "LOAD IT SMART", t, TL.wt("end", "load"), GREEN, 116, 560, hold=TOTAL - TL.wt("end", "load") - 0.7, rot=0)
    C.captions(ctx, t, TL)
    if t > T["end"][0]:
        A.txt(ctx, "General information, not personal medical advice", W / 2, 1440, 26, GREY,
              0.8 * p(t, T["end"][0], T["end"][0] + 0.4) * (1 - p(t, TOTAL - 0.4, TOTAL)), bold=False, shadow=False)
    if flash > 0:
        A.rgba(ctx, WHITE, flash * 0.6); ctx.paint()
    return surf


BLUR = [(THIT - 0.05, THIT + 0.35), (TIN0, TIN1), (TPOP - 0.05, TPOP + 0.35), (TOUT0, TOUT1)]
if __name__ == "__main__":
    C.run(render, TOTAL, BLUR, sys.argv)
