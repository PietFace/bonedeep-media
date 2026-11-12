import cairo, math, random
import anim2 as A
import anim3 as F
import anim4 as V
import knee_still as K

S = 1024


def base(ctx, tint=(0.09, 0.12, 0.20)):
    g = cairo.RadialGradient(S / 2, S / 2, 40, S / 2, S / 2, S * 0.75)
    g.add_color_stop_rgb(0, *tint); g.add_color_stop_rgb(1, 0.02, 0.025, 0.045)
    ctx.set_source(g); ctx.paint()
    r = random.Random(3)
    for _ in range(40):
        x, y, rad = r.uniform(0, S), r.uniform(0, S), r.uniform(2, 7)
        A.rgba(ctx, A.CYAN, r.uniform(0.06, 0.18)); ctx.arc(x, y, rad, 0, 2 * math.pi); ctx.fill()


def ring(ctx, col=A.CYAN):
    for w, a in ((28, 0.06), (14, 0.12), (6, 0.5)):
        ctx.arc(S / 2, S / 2, S / 2 - 40, 0, 2 * math.pi); A.rgba(ctx, col, a); ctx.set_line_width(w); ctx.stroke()


def vign(ctx):
    g = cairo.RadialGradient(S / 2, S / 2, S * 0.30, S / 2, S / 2, S * 0.52)
    g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0, 0, 0, 0.85)
    ctx.set_source(g); ctx.paint()


def save(surf, name):
    surf.write_to_png(name)
    # circle preview
    p = cairo.ImageSurface(cairo.FORMAT_ARGB32, S, S); c = cairo.Context(p)
    c.set_source_rgb(1, 1, 1); c.paint()
    c.arc(S / 2, S / 2, S / 2, 0, 2 * math.pi); c.clip(); c.set_source_surface(surf, 0, 0); c.paint()
    return p


# A: glowing menisci from above (signature of the first video)
def opt_a():
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, S, S); c = cairo.Context(s); c.set_antialias(cairo.ANTIALIAS_BEST)
    base(c)
    c.save(); c.translate(S / 2, S / 2 + 10); c.scale(1.18, 1.18)
    V.draw_top(c, ghost=0.0, glow=1.0)
    c.restore()
    vign(c); ring(c)
    return s


# B: front-view knee, menisci glowing
def opt_b():
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, S, S); c = cairo.Context(s); c.set_antialias(cairo.ANTIALIAS_BEST)
    base(c)
    c.save(); c.translate(S / 2, S / 2 + 20); c.scale(0.78, 0.78); c.translate(-540, -1010)
    F.paint_layer(c, "back"); F.paint_layer(c, "men")
    F.men_glow(c, F.LAT, 1.0); F.men_glow(c, F.MED, 1.0)
    F.paint_layer(c, "fem")
    c.restore()
    vign(c); ring(c)
    return s


# C: Blender render of the real 3D knee, cropped to the joint
def opt_c():
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, S, S); c = cairo.Context(s); c.set_antialias(cairo.ANTIALIAS_BEST)
    base(c, (0.03, 0.035, 0.06))
    img = cairo.ImageSurface.create_from_png("/home/claude/three/blender_knee2.png")
    sc = 1.25
    c.save(); c.translate(S / 2, S / 2); c.scale(sc, sc); c.translate(-450, -760)
    c.set_source_surface(img, 0, 0); c.get_source().set_filter(cairo.FILTER_BEST); c.paint()
    c.restore()
    vign(c); ring(c)
    return s


if __name__ == "__main__":
    prev = []
    for n, f in (("A", opt_a), ("B", opt_b), ("C", opt_c)):
        prev.append(save(f(), f"bonedeep_avatar_{n}.png"))
    m = cairo.ImageSurface(cairo.FORMAT_ARGB32, S * 3 + 80, S + 40); c = cairo.Context(m)
    c.set_source_rgb(1, 1, 1); c.paint()
    for i, p in enumerate(prev):
        c.set_source_surface(p, 20 + i * (S + 20), 20); c.paint()
    m.write_to_png("bonedeep_avatar_opties.png")
