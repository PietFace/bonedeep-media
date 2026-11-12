"""Bone Deep v2 engine: voice, timeline, music+SFX, silhouette, camera FX, captions, render loop."""
import sys, os, json, math, random, re, subprocess
sys.path.insert(0, "/home/claude/short")
import cairo, numpy as np, cv2
import anim2 as A
import knee_still as K
from anim import p, eo, eio, back, clamp, rrect

W, H, FPS = 1080, 1920, 30
d2r = math.pi / 180
YEL, RED, WHITE, GREY, CYAN = A.YEL, A.RED, A.WHITE, A.GREY, A.CYAN
GREEN = (0.25, 0.95, 0.60)
SFX_DIR = "/home/claude/bonedeep-media/engine/sfx"


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


# ---------------- voice + timeline ----------------
def make_voice(segs, outdir, lead=0.35, sfx_gap=None, voice="bm_george"):
    """segs: list of (id, text or None, pause_after, speed). None = silent gap for a sound effect."""
    import soundfile as sf
    from kokoro_onnx import Kokoro
    sfx_gap = sfx_gap or {}
    k = Kokoro("/home/claude/tts/kokoro-v1.0.int8.onnx", "/home/claude/tts/voices-v1.0.bin")
    sr = 24000
    parts = [np.zeros(int(lead * sr), np.float32)]
    t = lead; tl = []
    for sid, text, pause, speed in segs:
        if text is None:
            g = sfx_gap.get(sid, 0.9)
            tl.append({"id": sid, "text": "", "t0": round(t, 3), "t1": round(t + 0.25, 3), "words": []})
            parts.append(np.zeros(int(g * sr), np.float32)); t += g
            continue
        a, sr = k.create(text, voice=voice, speed=speed, lang="en-gb")
        a = a.astype(np.float32)
        env = np.abs(a) > 0.01
        if env.any():
            i0, i1 = np.argmax(env), len(a) - np.argmax(env[::-1])
            a = a[max(0, i0 - 240): min(len(a), i1 + 480)]
        dur = len(a) / sr
        words = text.split()
        wts = [len(re.sub(r"[^A-Za-z0-9']", "", w)) + 2 + (4 if w[-1] in ",.?!:" else 0) for w in words]
        tot = sum(wts); acc = 0; wl = []
        for w, wt in zip(words, wts):
            wl.append({"w": w, "t0": round(t + dur * acc / tot, 3), "t1": round(t + dur * (acc + wt) / tot, 3)})
            acc += wt
        tl.append({"id": sid, "text": text, "t0": round(t, 3), "t1": round(t + dur, 3), "words": wl})
        parts += [a, np.zeros(int(pause * sr), np.float32)]
        t += dur + pause
    sf.write(os.path.join(outdir, "vo_raw.wav"), np.concatenate(parts), sr)
    total = round(t + 0.2, 3)
    json.dump({"total": total, "segs": tl}, open(os.path.join(outdir, "timeline.json"), "w"), indent=1)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(outdir, "vo_raw.wav"), "-af",
                    "highpass=f=70,acompressor=threshold=-20dB:ratio=3:attack=5:release=90,equalizer=f=3000:t=q:w=1:g=2",
                    "-ar", "48000", os.path.join(outdir, "vo.wav")], check=True)
    for s in tl:
        print(f'{s["id"]:10s} {s["t0"]:6.2f}-{s["t1"]:6.2f} {s["text"]}')
    print("total", total)


class Timeline:
    def __init__(self, path):
        d = json.load(open(path))
        self.total = d["total"]; self.segs = d["segs"]
        self.T = {s["id"]: (s["t0"], s["t1"]) for s in self.segs}
        self.W = {s["id"]: s["words"] for s in self.segs}

    def __getitem__(self, k):
        return self.T[k]

    def wt(self, seg, word):
        for w in self.W[seg]:
            if w["w"].lower().strip(",.?!:") == word.lower().strip(",.?!:"):
                return w["t0"]
        return self.T[seg][0]


# ---------------- music + SFX ----------------
def make_mix(tl, outdir, cfg):
    """cfg: bpm, sections [(t_start, chords(list of midi triads), mood)], drops [(t0,t1)],
    sfx [(t, kind, amp)], seed."""
    import soundfile as sf
    SR = 48000; N = int(tl.total * SR)
    mus = np.zeros(N); sfx = np.zeros(N)
    rng = np.random.default_rng(cfg.get("seed", 3))

    def nt(m): return 440.0 * 2 ** ((m - 69) / 12)

    def add(buf, t, sig):
        i = int(t * SR)
        if i >= N: return
        if i < 0: sig = sig[-i:]; i = 0
        m = min(len(sig), N - i); buf[i:i + m] += sig[:m]

    def env_ar(n, a, r):
        e = np.ones(n); na, nr = min(int(a * SR), n // 2), min(int(r * SR), n // 2)
        e[:na] = np.linspace(0, 1, na); e[-nr:] *= np.linspace(1, 0, nr); return e

    def nlp(n, k): return np.convolve(rng.standard_normal(n), np.ones(k) / k, mode="same")

    def in_drop(t): return any(a <= t <= b for a, b in cfg.get("drops", []))

    bpm = cfg["bpm"]; beat = 60 / bpm; bar = 4 * beat
    secs = cfg["sections"]
    t = 0.0; i = 0
    while t < tl.total:
        cur = [s for s in secs if s[0] <= t][-1]
        chords, mood = cur[1], cur[2]
        ch = chords[i % len(chords)]
        n = int(bar * SR); tt = np.arange(n) / SR
        pad = sum(np.sin(2 * np.pi * nt(m) * tt) + 0.3 * np.sin(2 * np.pi * nt(m) * 1.003 * tt + 1) for m in ch)
        add(mus, t, (0.035 if mood == "intro" else 0.05) * pad * env_ar(n, 0.5, 0.6))
        if mood != "intro":
            add(mus, t, 0.12 * np.sin(2 * np.pi * nt(ch[0] - 24) * tt) * env_ar(n, 0.05, 0.4))
        arp = ch + [ch[1] + 12]
        steps = {"intro": 4, "warn": 4}.get(mood, 8)
        for k in range(steps):
            st = t + k * bar / steps
            if in_drop(st): continue
            m = arp[(k * cfg.get("arp_step", 3)) % len(arp)] + 12
            nn = int(0.5 * SR); tp = np.arange(nn) / SR
            f = nt(m)
            pl = (np.sin(2 * np.pi * f * tp) + 0.35 * np.sin(2 * np.pi * 4 * f * tp) * np.exp(-tp * 18)) * np.exp(-tp * 6)
            add(mus, st, 0.07 * pl)
        if mood != "intro":
            for b in range(4):
                st = t + b * beat
                if in_drop(st): continue
                if b % 2 == 0 or mood == "warn":
                    m = int(0.28 * SR); tp = np.arange(m) / SR
                    f = 110 * np.exp(-tp * 28) + 42
                    add(mus, st, 0.32 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tp * 10))
                m = int(0.05 * SR); tp = np.arange(m) / SR
                add(mus, st + beat / 2, 0.05 * (rng.standard_normal(m) - nlp(m, 4)) * np.exp(-tp * 70))
        t += bar; i += 1
    for a, b in cfg.get("drops", []):
        ia, ib = int(a * SR), int(b * SR)
        mus[max(0, ia - int(0.15 * SR)):ia] *= np.linspace(1, 0, min(ia, int(0.15 * SR)))
        mus[ia:ib] = 0

    def thud(amp):
        m = int(0.6 * SR); tp = np.arange(m) / SR
        return amp * 0.6 * np.sin(2 * np.pi * np.cumsum(80 * np.exp(-tp * 8) + 38) / SR) * np.exp(-tp * 6)

    def whoosh(dur, amp=1.0, k=8):
        m = int(dur * SR); kk = np.arange(m) / m
        return amp * 0.3 * nlp(m, k) * np.sin(np.pi * kk) ** 2

    def riser(dur, amp=1.0):
        m = int(dur * SR); tp = np.arange(m) / SR; k = tp / tp[-1]
        return amp * (0.35 * nlp(m, 8) * k ** 2 + 0.08 * np.sin(2 * np.pi * np.cumsum(180 + 700 * k ** 2) / SR) * k)

    def sting(amp):   # sharp 'pain' zap: bright noise burst + dissonant high tones
        m = int(0.7 * SR); tp = np.arange(m) / SR
        s = rng.standard_normal(m) * np.exp(-tp * 30) * 0.6
        for f in (1975, 2093, 2960):
            s += 0.25 * np.sin(2 * np.pi * f * tp) * np.exp(-tp * 7)
        s += 0.6 * np.sin(2 * np.pi * np.cumsum(70 * np.exp(-tp * 6) + 35) / SR) * np.exp(-tp * 5)
        return amp * 0.5 * s

    def heartbeat(t0, t1, amp):
        tb = t0
        while tb < t1:
            add(sfx, tb, thud(0.45 * amp)); add(sfx, tb + 0.28, thud(0.3 * amp)); tb += 0.85

    def tick(amp):
        m = int(0.06 * SR); tp = np.arange(m) / SR
        return amp * (0.5 * np.sin(2 * np.pi * 2400 * tp) * np.exp(-tp * 120) + 0.3 * rng.standard_normal(m) * np.exp(-tp * 90))

    rec = {}
    for name in ("crack", "pop"):
        pth = os.path.join(SFX_DIR, f"sfx_{name}_rec.wav")
        if os.path.exists(pth):
            rec[name], _ = sf.read(pth)
    for ev in cfg.get("sfx", []):
        t, kind, amp = ev[0], ev[1], ev[2]
        if kind == "thud": add(sfx, t, thud(amp))
        elif kind == "whoosh": add(sfx, t, whoosh(ev[3] if len(ev) > 3 else 1.6, amp))
        elif kind == "riser": add(sfx, t - ev[3], riser(ev[3], amp))
        elif kind == "sting": add(sfx, t, sting(amp))
        elif kind == "tick": add(sfx, t, tick(amp))
        elif kind == "heartbeat": heartbeat(t, ev[3], amp)
        elif kind in rec: add(sfx, t - 0.06, amp * rec[kind])
    fi, fo = int(0.4 * SR), int(0.9 * SR)
    mus[:fi] *= np.linspace(0, 1, fi); mus[-fo:] *= np.linspace(1, 0, fo)
    vo, vsr = sf.read(os.path.join(outdir, "vo.wav"))
    if vo.ndim > 1: vo = vo.mean(1)
    voice = np.zeros(N); voice[:min(N, len(vo))] = vo[:N]
    w = int(0.12 * SR)
    envv = np.convolve(np.abs(voice), np.ones(w) / w, mode="same")
    duck = 1 - 0.62 * np.clip(envv / (envv.max() * 0.25), 0, 1)
    duck = np.convolve(duck, np.ones(int(0.08 * SR)) / int(0.08 * SR), mode="same")
    out = 0.30 * mus / (np.abs(mus).max() + 1e-9) * duck + 0.75 * sfx + 0.85 * voice / (np.abs(voice).max() + 1e-9)
    out = np.tanh(out * 1.2) / np.tanh(1.2)
    sf.write(os.path.join(outdir, "mix.wav"), out.astype(np.float32), SR)


# ---------------- drawing helpers ----------------
def limb(ctx, a, b, w0, w1):
    ang = math.atan2(b[1] - a[1], b[0] - a[0]); nx, ny = -math.sin(ang), math.cos(ang)
    ctx.move_to(a[0] + nx * w0 / 2, a[1] + ny * w0 / 2)
    ctx.line_to(b[0] + nx * w1 / 2, b[1] + ny * w1 / 2)
    ctx.arc_negative(b[0], b[1], w1 / 2, ang + math.pi / 2, ang - math.pi / 2)
    ctx.line_to(a[0] - nx * w0 / 2, a[1] - ny * w0 / 2)
    ctx.arc_negative(a[0], a[1], w0 / 2, ang - math.pi / 2, ang + math.pi / 2)
    ctx.close_path()


def silhouette_layer(matrix, draw_front, alpha, draw_back=None):
    if alpha <= 0:
        return None
    def mask_of(fn):
        m = cairo.ImageSurface(cairo.FORMAT_A8, W, H)
        c = cairo.Context(m); c.set_matrix(matrix); c.set_antialias(cairo.ANTIALIAS_GOOD)
        if fn: fn(c); c.set_source_rgba(0, 0, 0, 1); c.fill()
        st = m.get_stride()
        return np.ndarray((H, st), np.uint8, m.get_data())[:, :W].astype(np.float32) / 255
    mask = mask_of(draw_front)
    maskb = mask_of(draw_back) if draw_back else np.zeros_like(mask)
    allm = np.maximum(mask, maskb)
    glow = cv2.GaussianBlur(allm, (0, 0), 14) * 0.9 + cv2.GaussianBlur(allm, (0, 0), 4) * 0.6
    glow = np.clip(glow - allm, 0, 1)
    inner = np.clip(allm - cv2.GaussianBlur(allm, (0, 0), 6), 0, 1)
    gy = np.linspace(1.0, 0.6, H, dtype=np.float32)[:, None]
    body = np.stack([0.30 * gy, 0.20 * gy, 0.12 * gy], -1) * mask[..., None] + \
        np.stack([0.17 * gy, 0.11 * gy, 0.07 * gy], -1) * (maskb * (1 - mask))[..., None]
    cy = np.array([1.0, 0.85, 0.25], np.float32)
    rgb = body + glow[..., None] * cy * 0.85 + inner[..., None] * cy * 0.55
    a = np.clip(allm + glow * 0.85, 0, 1)
    out = np.zeros((H, W, 4), np.float32)
    out[..., :3] = np.clip(rgb, 0, 1) * alpha; out[..., 3] = a * alpha
    out[..., :3] = np.minimum(out[..., :3], out[..., 3:4])
    buf = np.ascontiguousarray((out * 255).astype(np.uint8))
    return cairo.ImageSurface.create_for_data(memoryview(buf), cairo.FORMAT_ARGB32, W, H), buf


rnd = random.Random(7)
FAR = [(rnd.uniform(-300, W + 300), rnd.uniform(-300, H + 300), rnd.uniform(2, 5), rnd.uniform(0, 6.28)) for _ in range(90)]
NEAR = [(rnd.uniform(-200, W + 200), rnd.uniform(-200, H + 200), rnd.uniform(40, 110), rnd.uniform(0, 6.28)) for _ in range(9)]


def background(ctx, t, z, foc, tint, ref=(520, 900)):
    g = cairo.RadialGradient(W / 2, 950, 60, W / 2, 950, 1250)
    g.add_color_stop_rgb(0, *tint); g.add_color_stop_rgb(1, 0.02, 0.025, 0.045)
    ctx.set_source(g); ctx.paint()
    px, py = -(foc[0] - ref[0]) * z * 0.08, -(foc[1] - ref[1]) * z * 0.08
    for x, y, r, ph in FAR:
        xx = (x + px - 6 * t) % (W + 600) - 300; yy = (y + py - 10 * t) % (H + 600) - 300
        A.rgba(ctx, CYAN, 0.10 + 0.08 * math.sin(t * 2 + ph)); ctx.arc(xx, yy, r, 0, 2 * math.pi); ctx.fill()


def bokeh_front(ctx, t, z, foc, ref=(520, 900)):
    px, py = -(foc[0] - ref[0]) * z * 0.5, -(foc[1] - ref[1]) * z * 0.5
    for x, y, r, ph in NEAR:
        xx = (x + px + 14 * math.sin(t * 0.4 + ph)) % (W + 400) - 200
        yy = (y + py - 22 * t) % (H + 400) - 200
        g = cairo.RadialGradient(xx, yy, r * 0.2, xx, yy, r)
        g.add_color_stop_rgba(0, CYAN[0], CYAN[1], CYAN[2], 0.10)
        g.add_color_stop_rgba(0.75, CYAN[0], CYAN[1], CYAN[2], 0.07)
        g.add_color_stop_rgba(1, CYAN[0], CYAN[1], CYAN[2], 0)
        ctx.set_source(g); ctx.arc(xx, yy, r, 0, 2 * math.pi); ctx.fill()


def fades(ctx):
    tg = cairo.LinearGradient(0, 0, 0, 900)
    tg.add_color_stop_rgba(0, 0.02, 0.02, 0.04, 0.55); tg.add_color_stop_rgba(1, 0.02, 0.02, 0.04, 0)
    ctx.set_source(tg); ctx.rectangle(0, 0, W, 900); ctx.fill()
    bg = cairo.LinearGradient(0, 1150, 0, 1500)
    bg.add_color_stop_rgba(0, 0.02, 0.02, 0.04, 0); bg.add_color_stop_rgba(1, 0.02, 0.02, 0.04, 0.6)
    ctx.set_source(bg); ctx.rectangle(0, 1150, W, H - 1150); ctx.fill()


def captions(ctx, t, tl, skip=()):
    seg = None
    for s in tl.segs:
        if s["t0"] - 0.05 <= t <= s["t1"] + 0.25:
            seg = s
    if seg is None or seg["id"] in skip or not seg["words"]:
        return
    size = 58; A.font(ctx, size); sp = size * 0.36
    lines, cur, wsum = [], [], 0
    for w in seg["words"]:
        ww = ctx.text_extents(w["w"]).x_advance
        if cur and wsum + sp + ww > 880:
            lines.append(cur); cur, wsum = [], 0
        cur.append((w, ww)); wsum += (sp if len(cur) > 1 else 0) + ww
    lines.append(cur)
    a_in = clamp((t - seg["t0"] + 0.05) / 0.12) * (1 - clamp((t - seg["t1"] - 0.1) / 0.15))
    y0 = 1300 - (len(lines) - 1) * size * 0.6
    for li, line in enumerate(lines):
        tw = sum(ww for _, ww in line) + sp * (len(line) - 1)
        x = W / 2 - tw / 2; y = y0 + li * size * 1.2
        for w, ww in line:
            active = w["t0"] <= t < w["t1"]; said = t >= w["t0"]
            col = YEL if active else (WHITE if said else (0.62, 0.66, 0.72))
            s_ = 1.06 if active else 1.0
            ctx.save(); ctx.translate(x + ww / 2, y - size * 0.35); ctx.scale(s_, s_); ctx.translate(-(x + ww / 2), -(y - size * 0.35))
            A.font(ctx, size); ctx.move_to(x, y); ctx.text_path(w["w"])
            A.rgba(ctx, (0, 0, 0), 0.85 * a_in); ctx.set_line_width(10); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke()
            A.txt(ctx, w["w"], x, y, size, col, a_in, align="l", shadow=False)
            ctx.restore()
            x += ww + sp


def slam_word(ctx, word, t, t0, col, size, y, hold=1.0, rot=-0.05):
    k = p(t, t0, t0 + 0.2)
    if k <= 0: return
    a = clamp(k * 3) * (1 - p(t, t0 + hold, t0 + hold + 0.2))
    if a <= 0: return
    s = 1.7 - 0.7 * eo(k)
    ctx.save(); ctx.translate(W / 2, y - size * 0.35); ctx.scale(s, s); ctx.rotate(rot); ctx.translate(-W / 2, -(y - size * 0.35))
    A.font(ctx, size); e = ctx.text_extents(word)
    if e.x_advance > 960:
        sc = 960 / e.x_advance; ctx.translate(W / 2, y); ctx.scale(sc, sc); ctx.translate(-W / 2, -y)
    for gw, ga in ((34, 0.10), (16, 0.22)):
        ctx.move_to(W / 2 - e.x_advance / 2, y); ctx.text_path(word)
        A.rgba(ctx, col, ga * a); ctx.set_line_width(gw); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke()
    A.txt(ctx, word, W / 2, y, size, col, a)
    ctx.restore()


def label(ctx, s, anchor, lx, ly, k, col=CYAN):
    if k <= 0 or anchor is None: return
    tx, ty = anchor
    A.rgba(ctx, col, k); ctx.arc(tx, ty, 8, 0, 2 * math.pi); ctx.fill()
    ctx.set_line_width(3.5); ctx.move_to(tx, ty)
    ctx.line_to(tx + (lx - tx) * eo(k), ty + (ly - ty) * eo(k)); ctx.stroke()
    A.txt(ctx, s, lx, ly - 14, 44, col, p(k, 0.5, 1))


def item_list(ctx, t, items, end, col=RED, mark="!", y0=400, step=96, size=74):
    a_all = 1 - p(t, end, end + 0.25)
    if not items or t < items[0][1] or a_all <= 0: return
    for i, (w, t0) in enumerate(items):
        k = p(t, t0, t0 + 0.18)
        if k <= 0: continue
        y = y0 + i * step; x = 150 + (1 - eo(k)) * -120; a = clamp(k * 2) * a_all
        A.rgba(ctx, col, a); ctx.arc(x, y - 20, 22, 0, 2 * math.pi); ctx.fill()
        A.txt(ctx, mark, x, y - 4, 34 if mark == "!" else 30, WHITE, a, shadow=False)
        A.txt(ctx, w, x + 48, y, size, col, a, align="l")


def stamp(ctx, t, t0, text, end, y=830, col=WHITE):
    k = p(t, t0, t0 + 0.18)
    if k <= 0: return
    a = clamp(k * 3) * (1 - p(t, end, end + 0.25))
    if a <= 0: return
    s = 1.8 - 0.8 * eo(k)
    ctx.save(); ctx.translate(W / 2, y); ctx.rotate(-0.07); ctx.scale(s, s)
    A.font(ctx, 72); e = ctx.text_extents(text)
    if e.x_advance > 860: ctx.scale(860 / e.x_advance, 860 / e.x_advance)
    rrect(ctx, -e.x_advance / 2 - 34, -70, e.x_advance + 68, 104, 18)
    A.rgba(ctx, col, a); ctx.set_line_width(8); ctx.stroke()
    A.txt(ctx, text, 0, 4, 72, col, a)
    ctx.restore()


def shake(t, events):
    sx = sy = zb = fl = 0
    for te, amp, big in events:
        dt = t - te
        if dt < 0: continue
        e = math.exp(-dt * 7)
        sx += 30 * amp * e * math.sin(dt * 71 + te); sy += 30 * amp * e * math.cos(dt * 53 + te)
        zb += 0.06 * amp * math.exp(-dt * 9)
        if big: fl = max(fl, 0.6 * math.exp(-dt * 7))
    return sx, sy, zb, fl


def window_rim(ctx, world, c, rw, z):
    ctx.save(); ctx.set_matrix(world)
    for w_, a_ in ((26, 0.10), (12, 0.25), (4, 0.9)):
        ctx.arc(c[0], c[1], rw, 0, 2 * math.pi); A.rgba(ctx, CYAN, a_); ctx.set_line_width(w_ / z); ctx.stroke()
    ctx.restore()


def light_sweep(ctx, t, model):
    sw = ((t * 0.45) % 1.6) - 0.3
    dev = ctx.device_to_user
    x0, y0 = dev(-200 + sw * W * 1.6, 0); x1, y1 = dev(200 + sw * W * 1.6, 400)
    lg = cairo.LinearGradient(x0, y0, x1, y1)
    lg.add_color_stop_rgba(0, 1, 1, 1, 0); lg.add_color_stop_rgba(0.5, 1, 0.98, 0.92, 0.22); lg.add_color_stop_rgba(1, 1, 1, 1, 0)
    ctx.set_source(lg); ctx.mask(model)


def pulse_path(ctx, pts, t, a, col=(1, 0.3, 0.25), speed=1.6):
    """glowing nerve with travelling pain pulses; pts = 4 bezier points"""
    if a <= 0: return
    ctx.move_to(*pts[0]); ctx.curve_to(*pts[1], *pts[2], *pts[3])
    A.rgba(ctx, (1.0, 0.85, 0.35), 0.75 * a); ctx.set_line_width(9); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
    for j in range(3):
        k = ((t * speed + j / 3) % 1.0); u = 1 - k
        q = tuple(u**3 * pts[0][i] + 3 * u * u * k * pts[1][i] + 3 * u * k * k * pts[2][i] + k**3 * pts[3][i] for i in (0, 1))
        g = cairo.RadialGradient(q[0], q[1], 2, q[0], q[1], 70)
        g.add_color_stop_rgba(0, 1, 1, 1, a); g.add_color_stop_rgba(0.3, col[0], col[1], col[2], 0.8 * a)
        g.add_color_stop_rgba(1, col[0], col[1], col[2], 0)
        ctx.set_source(g); ctx.arc(q[0], q[1], 70, 0, 2 * math.pi); ctx.fill()


def glow_blob(ctx, x, y, r, col, a):
    if a <= 0: return
    g = cairo.RadialGradient(x, y, r * 0.1, x, y, r)
    g.add_color_stop_rgba(0, col[0], col[1], col[2], 0.55 * a); g.add_color_stop_rgba(1, col[0], col[1], col[2], 0)
    ctx.set_source(g); ctx.arc(x, y, r, 0, 2 * math.pi); ctx.fill()


# ---------------- render loop ----------------
def run(render, total, blur_windows, argv):
    def frame_bytes(i):
        t = i / FPS
        if any(a <= t <= b for a, b in blur_windows):
            acc = None
            for j in range(4):
                sf_ = render(t + (j - 1.5) / (4 * FPS) * 0.6)
                arr = np.ndarray((H, W, 4), np.uint8, sf_.get_data()).astype(np.uint16)
                acc = arr if acc is None else acc + arr
            return (acc // 4).astype(np.uint8).tobytes()
        return bytes(render(t).get_data())
    if argv[1] == "still":
        render(float(argv[2])).write_to_png(argv[3]); return
    i0, i1, out = int(argv[2]), int(argv[3]), argv[4]
    tmp = out.replace(".mp4", ".tmp.mp4")
    pr = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                           "-pix_fmt", "yuv420p", "-r", str(FPS), tmp], stdin=subprocess.PIPE)
    for i in range(i0, i1):
        pr.stdin.write(frame_bytes(i))
    pr.stdin.close()
    if pr.wait() == 0:
        os.replace(tmp, out)
    print("done", out, flush=True)


def contact(film_py, times, out, cols=7):
    from PIL import Image
    d = os.path.dirname(out)
    for t in times:
        subprocess.run([sys.executable, film_py, "still", str(t), os.path.join(d, f"st_{t}.png")], check=True)
    rows = (len(times) + cols - 1) // cols
    m = Image.new("RGB", (216 * cols, 384 * rows))
    for i, t in enumerate(times):
        m.paste(Image.open(os.path.join(d, f"st_{t}.png")).resize((216, 384)), ((i % cols) * 216, (i // cols) * 384))
    m.save(out)
