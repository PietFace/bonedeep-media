"""Unique score + SFX for the knee-cracking Short, ducked under the voice. Writes mix.wav."""
import json, numpy as np, soundfile as sf, sys
sys.path.insert(0, "/home/claude/crack2")

SR = 48000
TL = json.load(open("/home/claude/crack2/timeline.json"))
TOTAL = TL["total"]
T = {s["id"]: (s["t0"], s["t1"]) for s in TL["segs"]}
WORDS = {s["id"]: s["words"] for s in TL["segs"]}


def wt(seg, word):
    for w in WORDS[seg]:
        if w["w"].lower().strip(",.?!") == word:
            return w["t0"]
    return T[seg][0]


N = int(TOTAL * SR)
mus = np.zeros(N); sfx = np.zeros(N)
rng = np.random.default_rng(11)


def nt(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def add(buf, t, sig):
    i = int(t * SR)
    if i >= N or i + len(sig) <= 0:
        return
    if i < 0:
        sig = sig[-i:]; i = 0
    m = min(len(sig), N - i); buf[i:i + m] += sig[:m]


def env_ar(n, a, r):
    e = np.ones(n); na, nr = min(int(a * SR), n // 2), min(int(r * SR), n // 2)
    e[:na] = np.linspace(0, 1, na); e[-nr:] *= np.linspace(1, 0, nr); return e


def noise_lp(n, k):
    return np.convolve(rng.standard_normal(n), np.ones(k) / k, mode="same")


TC, TPOP = T["crack"][0], T["pop"][0]
TFLICK = wt("tendon", "flicking") + 0.15
TGIVE, TLOCK, TCHECK = wt("lock", "gives"), wt("lock", "locks"), T["check"][0]
THARM, TPAIN, TMOVE = T["harmless"][0], T["pain"][0], T["move"][0]

bpm = 92; beat = 60 / bpm; bar = 4 * beat
# E minor world: Em  C  G  D ; harmless/outro in G major: G  D  Em  C
minor = [[52, 55, 59], [48, 52, 55], [55, 59, 62], [50, 54, 57]]
major = [[55, 59, 62], [50, 54, 57], [52, 55, 59], [48, 52, 55]]
tension = [[52, 55, 58], [52, 55, 59]]      # dim colour for red flags


def section(t):
    if t < TC:
        return "intro"
    if t < THARM:
        return "explain"
    if t < TPAIN:
        return "good"
    if t < TMOVE:
        return "warn"
    return "outro"


def pluck(f, n, decay=6.0, bright=0.35):
    tt = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * tt) + bright * np.sin(2 * np.pi * 4 * f * tt) * np.exp(-tt * 18)) * np.exp(-tt * decay)


# --- score ---
t = 0.0; i = 0
while t < TOTAL:
    sec = section(t)
    ch = (major if sec in ("good", "outro") else tension if sec == "warn" else minor)[i % (2 if sec == "warn" else 4)]
    n = int(bar * SR); tt = np.arange(n) / SR
    pad = sum(np.sin(2 * np.pi * nt(m) * tt) + 0.3 * np.sin(2 * np.pi * nt(m) * 1.003 * tt + 1) for m in ch)
    pv = 0.05 if sec != "intro" else 0.035
    add(mus, t, pv * pad * env_ar(n, 0.5, 0.6))
    # sub bass
    if sec != "intro":
        add(mus, t, 0.12 * np.sin(2 * np.pi * nt(ch[0] - 24) * tt) * env_ar(n, 0.05, 0.4))
    # marimba-ish arpeggio in 8ths (busier when explaining)
    arp = ch + [ch[1] + 12]
    steps = 8 if sec in ("explain", "good", "outro") else 4
    for k in range(steps):
        st = t + k * bar / steps
        if TC - 0.45 < st < TC + 0.2:     # silence before the crack
            continue
        m = arp[(k * 3) % len(arp)] + 12
        add(mus, st, 0.07 * pluck(nt(m), int(0.5 * SR)))
    # soft kick + hat, only once the story is going
    if sec in ("explain", "good", "warn", "outro"):
        for b in range(4):
            st = t + b * beat
            if TC - 0.45 < st < TC + 0.2:
                continue
            if b % 2 == 0 or sec == "warn":
                m = int(0.28 * SR); tp = np.arange(m) / SR
                f = 110 * np.exp(-tp * 28) + 42
                add(mus, st, 0.32 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tp * 10))
            m = int(0.05 * SR); tp = np.arange(m) / SR
            add(mus, st + beat / 2, 0.05 * (rng.standard_normal(m) - noise_lp(m, 4)) * np.exp(-tp * 70))
    t += bar; i += 1

# riser into the crack
r0 = T["goes"][0]; m = int((TC - 0.45 - r0) * SR); tp = np.arange(m) / SR; k = tp / tp[-1]
add(mus, r0, (0.35 * noise_lp(m, 8) * k ** 2 + 0.08 * np.sin(2 * np.pi * np.cumsum(180 + 700 * k ** 2) / SR) * k))
a, b = int((TC - 0.45) * SR), int(TC * SR)
mus[a:b] *= np.linspace(1, 0.0, b - a)

# --- SFX ---
def room(sig, length=0.18, mixv=0.25):
    m = int(length * SR); tp = np.arange(m) / SR
    ir = rng.standard_normal(m) * np.exp(-tp * 28); ir[0] = 1.0 / mixv
    out = np.convolve(sig, ir)[:len(sig) + m] * mixv
    return out


def crack_sfx(amp=1.0):
    """Realistic joint crack: a cluster of sharp micro-clicks, a short bony resonance and a gritty tail."""
    m = int(0.35 * SR); s = np.zeros(m); tp = np.arange(m) / SR
    t0 = 0.0
    for j in range(5):
        i = int(t0 * SR); n = int(0.02 * SR); tt = np.arange(n) / SR
        f = rng.uniform(1800, 4200)
        click = np.sin(2 * np.pi * f * tt) * np.exp(-tt * rng.uniform(250, 420))
        burst = rng.standard_normal(n) * np.exp(-tt * 900)
        a = (1.0 if j == 0 else rng.uniform(0.35, 0.8))
        s[i:i + n] += a * (0.8 * click + 0.6 * burst)
        t0 += rng.uniform(0.004, 0.011)
    s += 0.55 * np.sin(2 * np.pi * 210 * tp) * np.exp(-tp * 45)          # bony knock
    s += 0.25 * np.sin(2 * np.pi * 420 * tp) * np.exp(-tp * 70)
    for _ in range(18):                                                  # gritty tail
        i = int(rng.uniform(0.03, 0.14) * SR); n = int(0.004 * SR)
        s[i:i + n] += rng.uniform(0.08, 0.25) * rng.standard_normal(n) * np.exp(-np.arange(n) / SR * 1500)
    s = room(s)
    s = s / np.abs(s).max()
    # a soft cinematic low hit underneath, kept small so the crack stays the star
    n = int(0.8 * SR); tt = np.arange(n) / SR
    low = 0.35 * np.sin(2 * np.pi * np.cumsum(55 * np.exp(-tt * 5) + 32) / SR) * np.exp(-tt * 5)
    out = np.zeros(max(len(s), n)); out[:len(s)] += s * 0.9; out[:n] += low
    return amp * out


def pop_sfx(amp=1.0, f0=420):
    """Bubble 'plop': a fast upward pitch glide with a damped liquid resonance."""
    n = int(0.12 * SR); tt = np.arange(n) / SR
    f = f0 * (1 + 2.6 * (1 - np.exp(-tt * 55)))
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 38) * np.minimum(1, tt * 900)
    s[:40] += np.linspace(0.6, 0, 40) * np.sign(rng.standard_normal(40))
    s = room(s, 0.12, 0.2)
    return amp * 0.8 * s / np.abs(s).max()


def whoosh(dur, up=True):
    m = int(dur * SR); tp = np.arange(m) / SR; k = tp / dur
    e = np.sin(np.pi * k) ** 2
    return 0.3 * noise_lp(m, 6 if up else 14) * e


def thud(amp=1.0):
    m = int(0.6 * SR); tp = np.arange(m) / SR
    return amp * 0.6 * np.sin(2 * np.pi * np.cumsum(80 * np.exp(-tp * 8) + 38) / SR) * np.exp(-tp * 6)


add(sfx, TC, crack_sfx(1.0))
add(sfx, T["bad"][0] + 0.15, whoosh(1.8))
add(sfx, TPOP, pop_sfx(1.0, 380))
add(sfx, TPOP + 0.11, pop_sfx(0.35, 520))
m = int(0.06 * SR); tp = np.arange(m) / SR
add(sfx, TFLICK, 0.5 * np.sin(2 * np.pi * 2400 * tp) * np.exp(-tp * 120) + 0.3 * rng.standard_normal(m) * np.exp(-tp * 90))
add(sfx, TFLICK, thud(0.3))
# heartbeat under the red flags
hb = TPAIN + 0.2
while hb < TCHECK:
    add(sfx, hb, thud(0.45)); add(sfx, hb + 0.28, thud(0.3)); hb += 0.85
add(sfx, TGIVE, thud(0.9))
add(sfx, TCHECK, thud(0.8))
add(sfx, T["move"][0] - 0.1, whoosh(1.8, up=False))

# fade in/out so the loop is seamless
fi, fo = int(0.4 * SR), int(0.9 * SR)
mus[:fi] *= np.linspace(0, 1, fi); mus[-fo:] *= np.linspace(1, 0, fo)

# --- voice + ducking ---
vo, vsr = sf.read("/home/claude/crack2/vo.wav")
if vo.ndim > 1:
    vo = vo.mean(1)
assert vsr == SR
voice = np.zeros(N); voice[:min(N, len(vo))] = vo[:N]
envv = np.convolve(np.abs(voice), np.ones(int(0.12 * SR)) / int(0.12 * SR), mode="same")
duck = 1 - 0.62 * np.clip(envv / (envv.max() * 0.25), 0, 1)
duck = np.convolve(duck, np.ones(int(0.08 * SR)) / int(0.08 * SR), mode="same")
musn = mus / (np.abs(mus).max() + 1e-9)
mix = 0.30 * musn * duck + 0.75 * sfx + 1.0 * voice / (np.abs(voice).max() + 1e-9) * 0.85
mix = np.tanh(mix * 1.2) / np.tanh(1.2)
sf.write("/home/claude/crack2/mix.wav", mix.astype(np.float32), SR)
print("ok", TOTAL)
