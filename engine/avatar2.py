import cairo, math, random
import anim2 as A
import knee_still as K
from avatar import S, base, ring, vign, save

d2r = math.pi / 180
C = (S / 2, S / 2)


def circ(c, r, cx=S / 2, cy=S / 2):
    c.new_path(); c.arc(cx, cy, r, 0, 2 * math.pi)


# ---------- A: cross-section of a limb: skin, fat, muscle, BONE in the middle ("bone deep") ----------
def opt_cross():
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, S, S); c = cairo.Context(s); c.set_antialias(cairo.ANTIALIAS_BEST)
    base(c)
    R = 380
    K.soft_shadow(c, lambda cc: circ(cc, R), 8, 14, 0.5, 50)
    # skin
    circ(c, R); g = cairo.RadialGradient(S / 2 - 80, S / 2 - 80, 50, S / 2, S / 2, R)
    g.add_color_stop_rgb(0, 0.96, 0.78, 0.66); g.add_color_stop_rgb(1, 0.78, 0.55, 0.45); c.set_source(g); c.fill()
    # fat
    circ(c, R - 22); g = cairo.RadialGradient(S / 2, S / 2, 100, S / 2, S / 2, R - 22)
    g.add_color_stop_rgb(0, 1.0, 0.90, 0.55); g.add_color_stop_rgb(1, 0.93, 0.80, 0.42); c.set_source(g); c.fill()
    c.save(); circ(c, R - 22); c.clip()
    r = random.Random(4)
    for _ in range(260):
        a = r.uniform(0, 2 * math.pi); rr = r.uniform(R - 70, R - 24)
        circ(c, r.uniform(4, 9), S / 2 + rr * math.cos(a), S / 2 + rr * math.sin(a))
        A.rgba(c, (0.85, 0.68, 0.30), 0.35); c.set_line_width(1.5); c.stroke()
    c.restore()
    # muscle compartments
    Rm = R - 62
    circ(c, Rm)
    g = cairo.RadialGradient(S / 2 - 60, S / 2 - 60, 40, S / 2, S / 2, Rm)
    g.add_color_stop_rgb(0, *K.MUS_L); g.add_color_stop_rgb(1, *K.MUS_D); c.set_source(g); c.fill()
    c.save(); circ(c, Rm); c.clip()
    for _ in range(1400):
        a = r.uniform(0, 2 * math.pi); rr = math.sqrt(r.uniform(0.04, 1)) * Rm
        circ(c, r.uniform(2, 5), S / 2 + rr * math.cos(a), S / 2 + rr * math.sin(a))
        A.rgba(c, (1, 0.6, 0.5) if r.random() < 0.5 else (0.3, 0.03, 0.02), 0.28); c.fill()
    # fascia between muscle groups
    for ang in (20, 105, 170, 250, 315):
        c.move_to(S / 2 + 120 * math.cos(ang * d2r), S / 2 + 120 * math.sin(ang * d2r))
        c.curve_to(S / 2 + 200 * math.cos((ang + 8) * d2r), S / 2 + 200 * math.sin((ang + 8) * d2r),
                   S / 2 + 260 * math.cos((ang - 6) * d2r), S / 2 + 260 * math.sin((ang - 6) * d2r),
                   S / 2 + Rm * math.cos(ang * d2r), S / 2 + Rm * math.sin(ang * d2r))
        A.rgba(c, (1, 0.95, 0.9), 0.75); c.set_line_width(5); c.stroke()
    c.restore()
    circ(c, Rm); A.rgba(c, (1, 0.95, 0.9), 0.8); c.set_line_width(5); c.stroke()
    # bone: glow, cortex, marrow
    Rb = 120
    for w, a in ((90, 0.10), (50, 0.18), (24, 0.30)):
        circ(c, Rb + 10); A.rgba(c, A.CYAN, a); c.set_line_width(w); c.stroke()
    K.textured(c, lambda cc: circ(cc, Rb), K.BONE_L, K.BONE_D, S / 2 - Rb, S / 2 - Rb, S / 2 + Rb, S / 2 + Rb,
               pores=80, pore_area=(S / 2 - Rb, S / 2 - Rb, S / 2 + Rb, S / 2 + Rb), inner=0.3, grain=0.15,
               spec=(S / 2 - 40, S / 2 - 40, 90, 0.5))
    K.textured(c, lambda cc: circ(cc, 62), (0.95, 0.75, 0.45), (0.78, 0.50, 0.28), S / 2 - 62, S / 2 - 62,
               S / 2 + 62, S / 2 + 62, pores=160, pore_area=(S / 2 - 62, S / 2 - 62, S / 2 + 62, S / 2 + 62),
               inner=0.4, grain=0.25)
    vign(c); ring(c)
    return s


# ---------- B: vertebra seen from above ----------
def vert(c):
    cx, cy = S / 2, S / 2
    c.new_path()
    # body (front = up)
    c.move_to(cx - 190, cy - 120)
    c.curve_to(cx - 200, cy - 300, cx + 200, cy - 300, cx + 190, cy - 120)
    c.curve_to(cx + 185, cy - 50, cx + 140, cy - 40, cx + 110, cy - 40)
    # right pedicle + transverse process
    c.line_to(cx + 120, cy - 10)
    c.curve_to(cx + 220, cy - 30, cx + 330, cy - 20, cx + 370, cy + 10)
    c.curve_to(cx + 385, cy + 40, cx + 350, cy + 60, cx + 320, cy + 50)
    c.curve_to(cx + 250, cy + 40, cx + 180, cy + 60, cx + 130, cy + 90)
    # lamina to spinous process
    c.curve_to(cx + 90, cy + 140, cx + 40, cy + 180, cx + 30, cy + 260)
    c.curve_to(cx + 30, cy + 320, cx + 10, cy + 350, cx, cy + 350)
    c.curve_to(cx - 10, cy + 350, cx - 30, cy + 320, cx - 30, cy + 260)
    c.curve_to(cx - 40, cy + 180, cx - 90, cy + 140, cx - 130, cy + 90)
    c.curve_to(cx - 180, cy + 60, cx - 250, cy + 40, cx - 320, cy + 50)
    c.curve_to(cx - 350, cy + 60, cx - 385, cy + 40, cx - 370, cy + 10)
    c.curve_to(cx - 330, cy - 20, cx - 220, cy - 30, cx - 120, cy - 10)
    c.line_to(cx - 110, cy - 40)
    c.curve_to(cx - 140, cy - 40, cx - 185, cy - 50, cx - 190, cy - 120)
    c.close_path()
    # spinal canal (hole)
    c.new_sub_path()
    c.move_to(cx, cy - 10)
    c.curve_to(cx + 62, cy - 10, cx + 70, cy + 50, cx + 45, cy + 85)
    c.curve_to(cx + 22, cy + 110, cx - 22, cy + 110, cx - 45, cy + 85)
    c.curve_to(cx - 70, cy + 50, cx - 62, cy - 10, cx, cy - 10)
    c.close_path()


def opt_vert():
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, S, S); c = cairo.Context(s); c.set_antialias(cairo.ANTIALIAS_BEST)
    base(c)
    c.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    c.save(); c.translate(0, -20)
    for w, a in ((60, 0.07), (34, 0.12), (16, 0.22)):
        vert(c); A.rgba(c, A.CYAN, a); c.set_line_width(w); c.set_line_join(cairo.LINE_JOIN_ROUND); c.stroke()
    K.soft_shadow(c, vert, 8, 14, 0.5, 50)
    K.textured(c, vert, K.BONE_L, K.BONE_D, S / 2 - 300, S / 2 - 300, S / 2 + 300, S / 2 + 300, pores=500,
               pore_area=(S / 2 - 380, S / 2 - 300, S / 2 + 380, S / 2 + 360), spec=(S / 2 - 60, S / 2 - 200, 220, 0.4))
    # spinal cord glowing inside the canal
    cx, cy = S / 2, S / 2
    for rr, a in ((48, 0.25), (36, 0.5)):
        c.new_path(); c.save(); c.translate(cx, cy + 40); c.scale(1, 0.85); c.arc(0, 0, rr, 0, 2 * math.pi); c.restore()
        A.rgba(c, A.CYAN, a); c.fill()
    c.new_path(); c.save(); c.translate(cx, cy + 40); c.scale(1, 0.85); c.arc(0, 0, 26, 0, 2 * math.pi); c.restore()
    A.rgba(c, (0.85, 0.97, 1.0), 1); c.fill()
    c.restore()
    c.set_fill_rule(cairo.FILL_RULE_WINDING)
    vign(c); ring(c)
    return s


if __name__ == "__main__":
    prev = []
    for n, f in (("cross", opt_cross), ("vertebra", opt_vert)):
        prev.append(save(f(), f"bonedeep_avatar_{n}.png"))
    m = cairo.ImageSurface(cairo.FORMAT_ARGB32, S * 2 + 60, S + 40); c = cairo.Context(m)
    c.set_source_rgb(1, 1, 1); c.paint()
    for i, p in enumerate(prev):
        c.set_source_surface(p, 20 + i * (S + 20), 20); c.paint()
    m.write_to_png("bonedeep_avatar_opties2.png")
