import sys, math
sys.path.insert(0, "/home/claude/v2"); sys.path.insert(0, "/home/claude/short"); sys.path.insert(0, "/home/claude/v2/back")
import cairo
import common as C
from common import W, H, kf, ss, mix, p, eo, eio, back, clamp, YEL, RED, WHITE, GREY, CYAN, GREEN, d2r
import anim2 as A
import spine as SP

D = "/home/claude/v2/back"
TL = C.Timeline(D + "/timeline.json"); T = TL.T; TOTAL = TL.total
THIT = T["hit"][0]
TIN0, TIN1 = TL.wt("feel", "let's") - 0.1, T["feel"][1] + 0.2
TOUT0, TOUT1 = T["end"][0] - 0.1, T["end"][0] + 1.8
M0 = 0.15
REF = (520, 900)
ANKLE = (430.0, 1390.0)
BOX = (640, 1300, 150, 100)


def bend(t):
    return kf(t, [(0.3, 0.0), (THIT, 0.85), (TOUT1 - 0.2, 0.85), (TOTAL - 0.3, 0.0)])


def pose(b):
    a_s = (5 + 18 * b) * d2r; psi = (5 + 30 * b) * d2r; tau = (6 + 74 * b) * d2r
    Ax, Ay = ANKLE
    K_ = (Ax + 280 * math.sin(a_s), Ay - 280 * math.cos(a_s))
    H_ = (K_[0] - 300 * math.sin(psi), K_[1] - 300 * math.cos(psi))
    S_ = (H_[0] + 330 * math.sin(tau), H_[1] - 330 * math.cos(tau))
    head = (S_[0] + 100 * math.sin(tau + 0.15), S_[1] - 100 * math.cos(tau + 0.15))
    E = (S_[0] + 30 * b, S_[1] + 150)
    Hd = (E[0] + 25 * b, E[1] + 140)
    lum = (H_[0] + 0.32 * 330 * math.sin(tau) - 18 * math.cos(tau), H_[1] - 0.32 * 330 * math.cos(tau) - 18 * math.sin(tau))
    return dict(A=(Ax, Ay), K=K_, H=H_, S=S_, head=head, E=E, Hd=Hd, tau=tau, lum=lum)


PL = pose(0.85)


def figure(ctx, P, back_=False):
    o = (-24, -6) if back_ else (0, 0)
    sh = lambda q: (q[0] + o[0], q[1] + o[1])
    C.limb(ctx, sh(P["H"]), sh(P["K"]), 110, 84); ctx.fill()
    C.limb(ctx, sh(P["K"]), sh(P["A"]), 80, 46); ctx.fill()
    A_ = sh(P["A"])
    ctx.move_to(A_[0] - 40, A_[1] - 10); ctx.line_to(A_[0] + 150, A_[1] + 22); ctx.line_to(A_[0] + 150, A_[1] + 46)
    ctx.line_to(A_[0] - 48, A_[1] + 46); ctx.close_path(); ctx.fill()
    if back_:
        return
    C.limb(ctx, P["H"], P["S"], 150, 160); ctx.fill()
    C.limb(ctx, P["S"], P["E"], 58, 46); ctx.fill()
    C.limb(ctx, P["E"], P["Hd"], 46, 36); ctx.fill()
    nk = mix(P["S"], P["head"], 0.5)
    C.limb(ctx, P["S"], nk, 60, 52); ctx.fill()
    ctx.arc(P["head"][0], P["head"][1], 64, 0, 2 * math.pi)


def state(t):
    st = {"flex": 0.0}
    if t < TIN1 or t > TOUT0:
        st["flex"] = bend(t) * 0.9
        if THIT <= t < TIN1:
            st["spasm"] = 1.0
        return st
    st["flex"] = kf(t, [(TIN1, 0.75), (T["anat"][0] + 0.5, 0.0), (T["move"][0], 0.0)])
    if T["move"][0] <= t < T["flags"][0]:
        st["flex"] = 0.35 - 0.35 * math.cos((t - T["move"][0]) * 2.4)
    if t >= T["flags"][0]:
        st["flex"] = kf(t, [(T["flags"][0], 0.2), (TOUT0, 0.75)])
    if T["anat"][0] <= t < T["nothing"][0]:
        k = (t - T["anat"][0] - 0.6) / 0.35
        st["hl"] = 4 - int(k) if 0 <= k < 5 else -1
        st["disc_glow"] = p(t, TL.wt("anat", "discs"), TL.wt("anat", "discs") + 0.3)
    if T["nothing"][0] <= t < T["strain"][0] + 0.3:
        st["align"] = p(t, T["nothing"][0] + 0.6, T["nothing"][0] + 1.2)
        st["all_glow"] = st["align"] * 0.6
    if T["strain"][0] <= t < T["better"][0] + 1.5:
        st["lig"] = p(t, TL.wt("strain", "ligament"), TL.wt("strain", "ligament") + 0.3) * (1 - p(t, T["better"][0], T["better"][0] + 1.2))
        st["spasm"] = p(t, TL.wt("strain", "lock"), TL.wt("strain", "lock") + 0.4) * (1 - p(t, T["better"][0], T["better"][0] + 1.2))
    if T["hurt"][0] <= t < T["better"][0]:
        st["green_bones"] = p(t, TL.wt("hurt", "damage."), TL.wt("hurt", "damage.") + 0.3)
    if T["better"][0] <= t < T["flags"][0]:
        st["green"] = p(t, T["better"][0] + 0.4, T["better"][0] + 1.0)
    if T["flags"][0] <= t < TOUT0:
        st["nerve"] = p(t, T["flags"][0], T["flags"][0] + 0.4)
    return st


def camera(t):
    fig_c = (520.0, 950.0)
    z_in = 0.72 / M0
    rot_l = -PL["tau"]
    if t < TIN0:
        return 1.0, 0.0, fig_c
    if t < TIN1:
        k = eio(p(t, TIN0, TIN1)); return 1 + (z_in - 1) * k, rot_l * k, mix(fig_c, PL["lum"], k)
    if t < TOUT0:
        mv = [(TIN1, (0, 0), 1.0), (T["anat"][0] + 0.4, (-60, 60), 0.95), (T["strain"][0] + 0.2, (-160, 60), 1.0),
              (T["strain"][1], (-200, 160), 1.35), (T["hurt"][0] + 0.3, (-100, 60), 0.95), (T["flags"][0] + 0.2, (-100, 60), 0.95),
              (TOUT0, (0, 0), 1.0)]
        off = kf(t, [(a, b) for a, b, _ in mv]); zm = kf(t, [(a, c) for a, _, c in mv])
        tau = PL["tau"]
        wo = (M0 * (off[0] * math.cos(tau) - off[1] * math.sin(tau)), M0 * (off[0] * math.sin(tau) + off[1] * math.cos(tau)))
        return z_in * zm, rot_l, (PL["lum"][0] + wo[0], PL["lum"][1] + wo[1])
    if t < TOUT1:
        k = eio(p(t, TOUT0, TOUT1)); return z_in + (1 - z_in) * k, rot_l * (1 - k), mix(PL["lum"], fig_c, k)
    return 1.0, 0.0, fig_c


def window(t):
    if t < THIT: return 0
    if t < TIN0: return 110 * back(p(t, THIT, THIT + 0.3))
    if t < TIN1: return 110 + 1100 * ss(p(t, TIN0 + 0.4, TIN1))
    if t < TOUT0: return 4000
    if t < TOUT1: return 1210 - 1100 * ss(p(t, TOUT0, TOUT1 - 0.2))
    return 110 * (1 - ss(p(t, TOUT1, TOUT1 + 0.4)))


EV = [(THIT, 1.0, True), (TL.wt("strain", "lock"), 0.4, False), (TL.wt("flags", "get"), 0.4, False)]


def render(t):
    st = state(t)
    z, rot, foc = camera(t)
    sx, sy, zb, flash = C.shake(t, EV)
    fig_a = (1 - ss(p(t, TIN0 + 0.9, TIN1 - 0.1))) if t < TOUT0 else ss(p(t, TOUT0 + 0.5, TOUT1))
    redk = 0.5 * st.get("spasm", 0) * (1 if t > TIN1 else 0) + 0.4 * st.get("nerve", 0)
    green = max(st.get("green", 0), p(t, T["end"][0] + 0.3, T["end"][0] + 1.0) * (1 - p(t, TOTAL - 1, TOTAL)))
    tint = mix(mix((0.09, 0.12, 0.20), (0.04, 0.19, 0.15), green), (0.20, 0.05, 0.06), clamp(redk))
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf); ctx.set_antialias(cairo.ANTIALIAS_GOOD)
    C.background(ctx, t, z, foc, tint, REF)
    ctx.save(); ctx.translate(W / 2 + sx, 950 + sy); ctx.scale(z * (1 + zb), z * (1 + zb)); ctx.rotate(rot); ctx.translate(-foc[0], -foc[1])
    world = ctx.get_matrix()
    if fig_a > 0:   # box + floor
        bx, by, bw, bh = BOX
        ctx.rectangle(bx, by, bw, bh); A.rgba(ctx, (0.25, 0.75, 0.95), 0.10 * fig_a); ctx.fill_preserve()
        A.rgba(ctx, CYAN, 0.6 * fig_a); ctx.set_line_width(3); ctx.stroke()
        ctx.move_to(bx, by + bh * 0.35); ctx.line_to(bx + bw, by + bh * 0.35); A.rgba(ctx, CYAN, 0.35 * fig_a); ctx.stroke()
        g = cairo.RadialGradient(520, 1440, 10, 520, 1440, 400)
        g.add_color_stop_rgba(0, CYAN[0], CYAN[1], CYAN[2], 0.22 * fig_a); g.add_color_stop_rgba(1, CYAN[0], CYAN[1], CYAN[2], 0)
        ctx.save(); ctx.translate(0, 1440); ctx.scale(1, 0.1); ctx.translate(0, -1440); ctx.set_source(g)
        ctx.arc(520, 1440, 400, 0, 2 * math.pi); ctx.fill(); ctx.restore()
    ctx.restore()
    P = pose(bend(t)) if (t < TIN0 or t > TOUT1) else PL
    sil = C.silhouette_layer(world, lambda c: figure(c, P), fig_a, lambda c: figure(c, P, True))
    if sil:
        ctx.set_source_surface(sil[0], 0, 0); ctx.paint()
    rw = window(t); anchors = {}
    if rw > 0:
        ctx.save(); ctx.set_matrix(world)
        ctx.arc(P["lum"][0], P["lum"][1], rw, 0, 2 * math.pi)
        if rw < 2000:
            ctx.save(); ctx.clip_preserve(); ctx.set_source_rgb(0.03, 0.04, 0.07); ctx.paint(); ctx.restore()
        ctx.clip()
        ctx.push_group()
        ctx.translate(*P["lum"]); ctx.rotate(P["tau"]); ctx.scale(M0, M0)
        st2 = dict(st)
        if st.get("green_bones"):
            st2["all_glow"] = st["green_bones"]; st2["green"] = 0.001
        SP.spine(ctx, t, st2, anchors)
        model = ctx.pop_group()
        ctx.set_source(model); ctx.paint()
        C.light_sweep(ctx, t, model)
        ctx.restore()
        if rw < 2000:
            C.window_rim(ctx, world, P["lum"], rw, z)
    C.bokeh_front(ctx, t, z, foc, REF)
    A.vignette(ctx, red=clamp(redk) * 0.6 + (0.5 * math.exp(-(t - THIT) * 3) if THIT < t < TIN0 else 0))
    C.fades(ctx)
    C.label(ctx, "vertebra", anchors.get("vert"), 820, 700, p(t, TL.wt("anat", "vertebrae,"), TL.wt("anat", "vertebrae,") + 0.4) * (1 - p(t, T["nothing"][0], T["nothing"][0] + 0.3)), WHITE)
    C.label(ctx, "disc", anchors.get("disc"), 860, 1040, p(t, TL.wt("anat", "discs"), TL.wt("anat", "discs") + 0.4) * (1 - p(t, T["nothing"][0], T["nothing"][0] + 0.3)), CYAN)
    C.label(ctx, "ligament", anchors.get("lig"), 260, 700, p(t, TL.wt("strain", "ligament"), TL.wt("strain", "ligament") + 0.4) * (1 - p(t, T["hurt"][0], T["hurt"][0] + 0.3)), RED)
    C.label(ctx, "muscles", anchors.get("muscle"), 220, 1080, p(t, TL.wt("strain", "muscles"), TL.wt("strain", "muscles") + 0.4) * (1 - p(t, T["hurt"][0], T["hurt"][0] + 0.3)), RED)
    C.slam_word(ctx, "LOCKED!", t, THIT, RED, 190, 600, hold=1.6)
    C.slam_word(ctx, "SLIPPED?", t, TL.wt("feel", "slipped"), WHITE, 150, 560, hold=1.6, rot=0)
    C.slam_word(ctx, "NOTHING SLIPPED", t, TL.wt("nothing", "nothing"), GREEN, 100, 470, hold=T["nothing"][1] - TL.wt("nothing", "nothing"), rot=0)
    C.slam_word(ctx, "MUSCLE SPASM", t, TL.wt("strain", "lock"), RED, 92, 470, hold=T["strain"][1] - TL.wt("strain", "lock"))
    C.slam_word(ctx, "PAIN", t, TL.wt("hurt", "pain"), RED, 150, 430, hold=T["hurt"][1] - TL.wt("hurt", "pain"), rot=0)
    C.slam_word(ctx, "≠ DAMAGE", t, TL.wt("hurt", "damage."), GREEN, 130, 580, hold=T["hurt"][1] - TL.wt("hurt", "damage."), rot=0)
    C.slam_word(ctx, "A FEW WEEKS", t, TL.wt("better", "few"), GREEN, 120, 470, hold=T["better"][1] - TL.wt("better", "few"), rot=0)
    C.slam_word(ctx, "BED REST? NO.", t, T["move"][0], RED, 110, 440, hold=TL.wt("move", "gentle") - T["move"][0] - 0.2, rot=0)
    C.slam_word(ctx, "MOVE GENTLY", t, TL.wt("move", "gentle"), GREEN, 120, 470, hold=T["move"][1] - TL.wt("move", "gentle"), rot=0)
    C.item_list(ctx, t, [("GROIN NUMBNESS", TL.wt("flags", "numbness")), ("TROUBLE PEEING", TL.wt("flags", "trouble")),
                         ("WEAK LEGS", TL.wt("flags", "weak"))], TOUT0 + 0.3, size=66)
    C.stamp(ctx, t, TL.wt("flags", "get"), "GET HELP NOW", TOUT0 + 0.3, y=760, col=RED)
    C.slam_word(ctx, "KEEP MOVING", t, TL.wt("end", "keep"), GREEN, 116, 560, hold=TOTAL - TL.wt("end", "keep") - 0.7, rot=0)
    C.captions(ctx, t, TL)
    if t > T["end"][0]:
        A.txt(ctx, "General information, not personal medical advice", W / 2, 1440, 26, GREY,
              0.8 * p(t, T["end"][0], T["end"][0] + 0.4) * (1 - p(t, TOTAL - 0.4, TOTAL)), bold=False, shadow=False)
    if flash > 0:
        A.rgba(ctx, RED, flash * 0.6); ctx.paint()
    return surf


BLUR = [(THIT - 0.05, THIT + 0.35), (TIN0, TIN1), (TOUT0, TOUT1)]
if __name__ == "__main__":
    C.run(render, TOTAL, BLUR, sys.argv)
