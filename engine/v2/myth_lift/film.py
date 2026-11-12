import sys, math, importlib.util
sys.path.insert(0, "/home/claude/v2"); sys.path.insert(0, "/home/claude/short"); sys.path.insert(0, "/home/claude/v2/back")
import cairo
import common as C
from common import W, H, kf, ss, mix, p, eo, eio, back, clamp, YEL, RED, WHITE, GREY, CYAN, GREEN, d2r
import anim2 as A
import spine as SP
from anim import rrect

_spec = importlib.util.spec_from_file_location("backfilm", "/home/claude/v2/back/film.py")
BF = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(BF)

D = "/home/claude/v2/myth_lift"
TL = C.Timeline(D + "/timeline.json"); T = TL.T; TOTAL = TL.total
THIT = T["hit"][0]
TIN0, TIN1 = TL.wt("check", "let's") - 0.1, T["check"][1] + 0.3
TOUT0, TOUT1 = T["end"][0] - 0.1, T["end"][0] + 1.8
TVER = T["verdict"][0]
TREV0, TREV1 = T["review"][0], T["stiff"][1] + 0.1
M0 = 0.15
REF = (520, 900)
PL = BF.PL


def lift(t):
    """bend amount and whether the box is held, for a looping lift"""
    ph = (t * 0.45) % 1.0
    b = 0.85 * (0.5 - 0.5 * math.cos(ph * 2 * math.pi))
    held = 0.5 <= ph < 1.0
    return b, held


def box_rect(P, held):
    bx, by, bw, bh = BF.BOX
    if held:
        hd = P["Hd"]
        return (hd[0] - bw / 2 + 20, hd[1] - 30, bw, bh)
    return BF.BOX


def state(t):
    st = {"flex": 0.0}
    inside = TIN1 - 0.3 <= t < TOUT0 + 0.2
    if not inside:
        st["flex"] = lift(t)[0] * 0.9
        return st
    st["flex"] = 0.45 - 0.45 * math.cos((t - TIN1) * 1.5)
    if T["built"][0] <= t < T["discs"][0] + 1.0:
        st["flex"] = kf(t, [(T["built"][0], st["flex"]), (TL.wt("built", "tilts"), 1.0), (T["discs"][0], 1.0), (T["discs"][0] + 1.0, 0.45 - 0.45 * math.cos((T["discs"][0] + 1.0 - TIN1) * 1.5))])
    if T["built"][0] <= t < T["discs"][0]:
        k = (t - TL.wt("built", "each") - 0.2) / 0.35
        st["hl"] = 4 - int(k) if 0 <= k < 5 else -1
        st["all_glow"] = 0.5 * p(t, TL.wt("built", "together"), TL.wt("built", "together") + 0.3)
    if T["discs"][0] <= t < T["review"][0]:
        st["disc_glow"] = p(t, T["discs"][0], T["discs"][0] + 0.3)
        st["green"] = p(t, TL.wt("discs", "adapt"), TL.wt("discs", "adapt") + 0.4)
    if T["risk"][0] <= t < TVER:
        st["spasm"] = 0.0
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
        mv = [(TIN1, (0, 0), 1.0), (T["built"][0] + 0.3, (-60, 60), 0.95), (T["discs"][0] + 0.3, (-20, 100), 1.15),
              (T["review"][0], (-60, 60), 0.95), (TOUT0, (0, 0), 1.0)]
        off = kf(t, [(a, b) for a, b, _ in mv]); zm = kf(t, [(a, c) for a, _, c in mv])
        tau = PL["tau"]
        wo = (M0 * (off[0] * math.cos(tau) - off[1] * math.sin(tau)), M0 * (off[0] * math.sin(tau) + off[1] * math.cos(tau)))
        return z_in * zm, rot_l, (PL["lum"][0] + wo[0], PL["lum"][1] + wo[1])
    if t < TOUT1:
        k = eio(p(t, TOUT0, TOUT1)); return z_in + (1 - z_in) * k, rot_l * (1 - k), mix(PL["lum"], fig_c, k)
    return 1.0, 0.0, fig_c


def window(t):
    if t < TIN0 - 0.4: return 0
    if t < TIN1: return 110 * back(p(t, TIN0 - 0.4, TIN0)) + 1100 * ss(p(t, TIN0 + 0.4, TIN1))
    if t < TOUT0: return 4000
    if t < TOUT1: return 1210 - 1100 * ss(p(t, TOUT0, TOUT1 - 0.2))
    return 110 * (1 - ss(p(t, TOUT1, TOUT1 + 0.4)))


def claim_card(ctx, t, a, strike=0.0):
    if a <= 0: return
    y = 520
    lines = ["NEVER LIFT WITH", "A BENT BACK"]
    rrect(ctx, 80, y - 150, W - 160, 300, 34); A.rgba(ctx, (0.05, 0.07, 0.12), 0.82 * a); ctx.fill_preserve()
    A.rgba(ctx, WHITE, 0.25 * a); ctx.set_line_width(3); ctx.stroke()
    A.txt(ctx, "“", 140, y - 40, 150, CYAN, 0.8 * a, shadow=False)
    for i, s in enumerate(lines):
        k = p(t, 0.35 + i * 0.7, 0.6 + i * 0.7)
        A.txt(ctx, s, W / 2, y - 10 + i * 100, 80, WHITE, a * k)
    if strike > 0:
        for i in range(2):
            yy = y - 36 + i * 100
            ctx.move_to(150, yy); ctx.line_to(150 + (W - 300) * eo(clamp(strike * 2 - i * 0.5)), yy + 6)
            A.rgba(ctx, RED, a); ctx.set_line_width(12); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()


def series_tag(ctx, t):
    a = 1 - p(t, TOTAL - 0.4, TOTAL)
    rrect(ctx, W / 2 - 190, 250, 380, 64, 32); A.rgba(ctx, CYAN, 0.16 * a); ctx.fill_preserve()
    A.rgba(ctx, CYAN, 0.8 * a); ctx.set_line_width(3); ctx.stroke()
    A.txt(ctx, "MYTH  or  FACT?", W / 2, 296, 38, WHITE, a, shadow=False)


def review_card(ctx, t):
    a = p(t, TREV0, TREV0 + 0.4) * (1 - p(t, TREV1, TREV1 + 0.4))
    if a <= 0: return
    ctx.rectangle(0, 0, W, H); A.rgba(ctx, (0.03, 0.04, 0.07), 0.65 * a); ctx.fill()
    s = 0.9 + 0.1 * eo(p(t, TREV0, TREV0 + 0.5))
    ctx.save(); ctx.translate(W / 2, 760); ctx.scale(s, s); ctx.translate(-W / 2, -760)
    rrect(ctx, 190, 440, 700, 620, 26); A.rgba(ctx, (0.94, 0.96, 1.0), 0.95 * a); ctx.fill()
    A.txt(ctx, "REVIEW OF STUDIES", W / 2, 530, 44, (0.1, 0.12, 0.18), a, shadow=False)
    for i in range(5):
        rrect(ctx, 250, 580 + i * 50, 580 - (i % 2) * 140, 18, 9); A.rgba(ctx, (0.65, 0.7, 0.8), 0.8 * a); ctx.fill()
    A.txt(ctx, "Saraceni et al., 2020", W / 2, 1010, 34, (0.3, 0.34, 0.42), a, bold=False, shadow=False)
    ctx.restore()
    C.stamp(ctx, t, TL.wt("review", "no"), "NO LINK WITH BACK PAIN", T["review"][1] + 0.3, y=880, col=GREEN)
    if t >= T["stiff"][0]:   # stiff vs relaxed lifters
        k = p(t, T["stiff"][0], T["stiff"][0] + 0.4) * a
        ctx.save(); ctx.translate(W / 2, 760); ctx.scale(s, s); ctx.translate(-W / 2, -760)
        rrect(ctx, 220, 600, 640, 330, 20); A.rgba(ctx, (0.94, 0.96, 1.0), k); ctx.fill()
        A.txt(ctx, "BACK PAIN?", W / 2, 720, 70, (0.85, 0.45, 0.05), k, shadow=False)
        A.txt(ctx, "often lifts STIFFER", W / 2, 820, 54, (0.1, 0.12, 0.18), k, shadow=False)
        ctx.restore()


def degree_tags(ctx, st, fr_world):
    """small '+7°' tags next to each level while bending"""
    a = st.get("deg", 0.0)
    if a <= 0: return
    for (x, y) in fr_world:
        A.txt(ctx, f"+{7 * st['flex']:.0f}°", x + 120, y + 10, 38, YEL, a)


EV = [(THIT, 0.7, True), (TVER, 0.9, True)]


def render(t):
    st = state(t)
    z, rot, foc = camera(t)
    sx, sy, zb, flash = C.shake(t, EV)
    fig_a = (1 - ss(p(t, TIN0 + 0.9, TIN1 - 0.1))) if t < TOUT0 else ss(p(t, TOUT0 + 0.5, TOUT1))
    green = max(st.get("green", 0), p(t, T["end"][0] + 0.2, T["end"][0] + 0.9) * (1 - p(t, TOTAL - 1, TOTAL)))
    redk = 0.35 * p(t, T["risk"][0], T["risk"][0] + 0.5) * (1 - p(t, TVER, TVER + 0.3))
    tint = mix(mix((0.09, 0.12, 0.20), (0.04, 0.19, 0.15), green), (0.20, 0.05, 0.06), clamp(redk))
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf); ctx.set_antialias(cairo.ANTIALIAS_GOOD)
    C.background(ctx, t, z, foc, tint, REF)
    outside = t < TIN0 or t > TOUT1 - 0.2
    b, held = lift(t) if outside else (0.85, False)
    P = BF.pose(b) if outside else PL
    ctx.save(); ctx.translate(W / 2 + sx, 950 + sy); ctx.scale(z * (1 + zb), z * (1 + zb)); ctx.rotate(rot); ctx.translate(-foc[0], -foc[1])
    world = ctx.get_matrix()
    if fig_a > 0:
        bx, by, bw, bh = box_rect(P, held and outside)
        ctx.rectangle(bx, by, bw, bh); A.rgba(ctx, (0.25, 0.75, 0.95), 0.12 * fig_a); ctx.fill_preserve()
        A.rgba(ctx, CYAN, 0.6 * fig_a); ctx.set_line_width(3); ctx.stroke()
        ctx.move_to(bx, by + bh * 0.35); ctx.line_to(bx + bw, by + bh * 0.35); A.rgba(ctx, CYAN, 0.35 * fig_a); ctx.stroke()
        g = cairo.RadialGradient(520, 1440, 10, 520, 1440, 400)
        g.add_color_stop_rgba(0, CYAN[0], CYAN[1], CYAN[2], 0.22 * fig_a); g.add_color_stop_rgba(1, CYAN[0], CYAN[1], CYAN[2], 0)
        ctx.save(); ctx.translate(0, 1440); ctx.scale(1, 0.1); ctx.translate(0, -1440); ctx.set_source(g)
        ctx.arc(520, 1440, 400, 0, 2 * math.pi); ctx.fill(); ctx.restore()
    ctx.restore()
    sil = C.silhouette_layer(world, lambda c: BF.figure(c, P), fig_a, lambda c: BF.figure(c, P, True))
    if sil:
        ctx.set_source_surface(sil[0], 0, 0); ctx.paint()
    rw = window(t); anchors = {}
    fr_world = []
    if rw > 0:
        ctx.save(); ctx.set_matrix(world)
        ctx.arc(P["lum"][0], P["lum"][1], rw, 0, 2 * math.pi)
        if rw < 2000:
            ctx.save(); ctx.clip_preserve(); ctx.set_source_rgb(0.03, 0.04, 0.07); ctx.paint(); ctx.restore()
        ctx.clip()
        ctx.push_group()
        ctx.translate(*P["lum"]); ctx.rotate(P["tau"]); ctx.scale(M0, M0)
        fr = SP.spine(ctx, t, st, anchors)
        fr_world = [ctx.user_to_device(f[0], f[1]) for f in fr]
        model = ctx.pop_group()
        ctx.set_source(model); ctx.paint()
        C.light_sweep(ctx, t, model)
        ctx.restore()
        if rw < 2000:
            C.window_rim(ctx, world, P["lum"], rw, z)
    C.bokeh_front(ctx, t, z, foc, REF)
    A.vignette(ctx, red=clamp(redk) * 0.6 + (0.4 * math.exp(-(t - THIT) * 3) if THIT < t < TIN0 else 0))
    C.fades(ctx)
    st["deg"] = p(t, TL.wt("built", "tilts"), TL.wt("built", "tilts") + 0.4) * (1 - p(t, T["discs"][0], T["discs"][0] + 0.3))
    degree_tags(ctx, st, fr_world)
    review_card(ctx, t)
    series_tag(ctx, t)
    ca = (1 - p(t, TIN0 - 0.2, TIN0 + 0.2)) + p(t, TVER - 0.2, TVER + 0.1) * (1 - p(t, TOUT0 + 0.2, TOUT0 + 0.5))
    claim_card(ctx, t if t < TIN0 else 3.0, clamp(ca), strike=p(t, TL.wt("verdict", "myth."), TL.wt("verdict", "myth.") + 0.4))
    if THIT <= t < TIN0 + 0.2:
        C.slam_word(ctx, "?", t, THIT, YEL, 260, 900, hold=TIN0 - THIT - 0.2, rot=0.08)
    lk = lambda a_, b_: p(t, a_, a_ + 0.4) * (1 - p(t, b_, b_ + 0.3))
    C.label(ctx, "disc", anchors.get("disc"), 860, 1060, lk(T["discs"][0], T["review"][0]), CYAN)
    C.label(ctx, "vertebra", anchors.get("vert"), 830, 700, lk(TL.wt("built", "vertebra"), T["discs"][0]), WHITE)
    C.slam_word(ctx, "BUILT TO BEND", t, TL.wt("built", "built"), GREEN, 116, 440, hold=TL.wt("built", "each") - TL.wt("built", "built") - 0.1, rot=0)
    C.slam_word(ctx, "A LITTLE PER LEVEL", t, TL.wt("built", "each"), YEL, 90, 440, hold=T["built"][1] - TL.wt("built", "each") + 0.2, rot=0)
    C.slam_word(ctx, "THEY ADAPT TO LOAD", t, TL.wt("discs", "adapt"), GREEN, 90, 440, hold=T["discs"][1] - TL.wt("discs", "adapt") + 0.2, rot=0)
    C.item_list(ctx, t, [("TOO HEAVY", TL.wt("risk", "heavy,")), ("TOO OFTEN", TL.wt("risk", "often,")),
                         ("TIRED", TL.wt("risk", "tired,")), ("NOT USED TO IT", TL.wt("risk", "load"))], TVER - 0.2, size=66)
    C.stamp(ctx, t, TL.wt("verdict", "myth."), "MOSTLY MYTH", TOUT0 + 0.4, y=830, col=RED)
    C.slam_word(ctx, "LIFT STRONG", t, T["end"][0], GREEN, 130, 440, hold=TL.wt("end", "train") - T["end"][0] - 0.2, rot=0)
    C.slam_word(ctx, "TRAIN YOUR BACK", t, TL.wt("end", "train"), GREEN, 104, 440, hold=TOTAL - TL.wt("end", "train") - 0.6, rot=0)
    C.captions(ctx, t, TL)
    if t > T["end"][0]:
        A.txt(ctx, "General information, not personal medical advice", W / 2, 1440, 26, GREY,
              0.8 * p(t, T["end"][0], T["end"][0] + 0.4) * (1 - p(t, TOTAL - 0.4, TOTAL)), bold=False, shadow=False)
    if flash > 0:
        A.rgba(ctx, WHITE, flash * 0.5); ctx.paint()
    return surf


BLUR = [(THIT - 0.05, THIT + 0.3), (TIN0, TIN1), (TOUT0, TOUT1)]
if __name__ == "__main__":
    C.run(render, TOTAL, BLUR, sys.argv)
