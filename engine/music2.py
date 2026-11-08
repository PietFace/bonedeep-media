import numpy as np, wave
from anim2 import TOTAL, START, global_events

SR = 44100
N = int(SR * TOTAL)
out = np.zeros(N)
rng = np.random.default_rng(4)


def nt(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def add(a0, sig):
    a0 = int(a0)
    if a0 >= N or a0 < 0:
        return
    m = min(len(sig), N - a0)
    out[a0:a0 + m] += sig[:m]


def lp_noise(n, k):
    x = rng.standard_normal(n)
    return np.convolve(x, np.ones(k) / k, mode="same")


bpm = 120
beat = 60 / bpm
groove_start = START["titel"]
tear_t = START["scheur"] + 4.75
drop0, drop1 = tear_t - 0.25, tear_t
slot_t = START["slot"]
minor = [33, 29, 36, 31]   # A F C G bass (midi)
pad_minor = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]
pad_major = [[53, 57, 60], [48, 52, 55], [55, 59, 62], [57, 61, 64]]
bass_major = [29, 36, 31, 33]

# drone + heartbeat in cold open
n0 = int(groove_start * SR)
tt = np.arange(n0) / SR
out[:n0] += 0.12 * np.sin(2 * np.pi * 55 * tt) * np.minimum(1, tt * 3)
out[:n0] += 0.05 * np.sin(2 * np.pi * 82.4 * tt + np.sin(tt * 3))
for hb in (0.0, 0.45, 2.2, 2.65):
    m = int(0.2 * SR); tp = np.arange(m) / SR
    add(hb * SR, 0.35 * np.sin(2 * np.pi * (60 * np.exp(-tp * 10) + 40) * tp) * np.exp(-tp * 18))

# groove
t0 = groove_start
i = 0
while t0 < TOTAL:
    major = t0 >= slot_t
    for b in range(4):
        tb = t0 + b * beat
        if tb >= TOTAL:
            break
        silent = drop0 <= tb < drop1 + 0.3
        if silent:
            continue
        # kick
        m = int(0.3 * SR); tp = np.arange(m) / SR
        f = 120 * np.exp(-tp * 30) + 45
        add(tb * SR, 0.45 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tp * 9))
        # offbeat hat
        m = int(0.06 * SR); tp = np.arange(m) / SR
        hat = rng.standard_normal(m) - lp_noise(m, 4)
        add((tb + beat / 2) * SR, 0.08 * hat * np.exp(-tp * 60))
        # 8th-note bass pulse
        bn = (bass_major if major else minor)[i % 4]
        for e in (0, 0.5):
            m = int(0.24 * SR); tp = np.arange(m) / SR
            fq = nt(bn + 12)
            sig = sum(np.sin(2 * np.pi * fq * h * tp) / h for h in (1, 2, 3, 4))
            env = np.exp(-tp * 9) * np.minimum(1, tp * 200)
            add((tb + e * beat) * SR, 0.13 * sig * env)
    # pad
    ch = (pad_major if major else pad_minor)[i % 4]
    m = int(4 * beat * SR); tp = np.arange(m) / SR
    env = np.minimum(1, tp * 3) * np.minimum(1, (4 * beat - tp) * 4)
    pad = sum(np.sin(2 * np.pi * nt(n) * tp) + 0.3 * np.sin(2 * np.pi * nt(n) * 2.003 * tp) for n in ch)
    seg = 0.035 * pad * env
    a0 = int(t0 * SR)
    # mute pad in drop
    add(a0, seg)
    t0 += 4 * beat; i += 1

# riser before tear
r0 = START["scheur"] + 3.0
m = int((drop0 - r0) * SR); tp = np.arange(m) / SR
k = tp / tp[-1]
riser = lp_noise(m, 6) * k ** 2 * 0.5 + 0.12 * np.sin(2 * np.pi * np.cumsum(200 + 900 * k ** 2) / SR) * k
add(r0 * SR, riser)
# silence the drop window (keep tails short)
a, b = int(drop0 * SR), int(drop1 * SR)
out[a:b] *= np.linspace(1, 0.05, b - a)

# event hits
for te, kind in global_events():
    if kind == "slam":
        m = int(0.25 * SR); tp = np.arange(m) / SR
        sig = 0.35 * np.sin(2 * np.pi * (90 * np.exp(-tp * 20) + 50) * tp) * np.exp(-tp * 14)
        sig += 0.15 * rng.standard_normal(m) * np.exp(-tp * 45)
    elif kind == "boom":
        m = int(1.0 * SR); tp = np.arange(m) / SR
        sig = 0.6 * np.sin(2 * np.pi * np.cumsum(70 * np.exp(-tp * 6) + 32) / SR) * np.exp(-tp * 4)
        sig += 0.18 * lp_noise(m, 3) * np.exp(-tp * 25)
    else:  # tear
        m = int(2.2 * SR); tp = np.arange(m) / SR
        crack = rng.standard_normal(m) * np.exp(-tp * 18)
        crack += 0.6 * rng.standard_normal(m) * (np.sin(tp * 260) > 0.6) * np.exp(-tp * 8)
        sig = 0.7 * crack + 0.9 * np.sin(2 * np.pi * np.cumsum(55 * np.exp(-tp * 2) + 28) / SR) * np.exp(-tp * 2.2)
    add(te * SR, sig)

# whoosh into each scene
for n, s in START.items():
    if s <= 0:
        continue
    m = int(0.45 * SR); tp = np.arange(m) / SR
    add((s - 0.35) * SR, 0.35 * lp_noise(m, 20) * np.sin(np.linspace(0, np.pi, m)) ** 2)

fo = int(1.2 * SR)
out[-fo:] *= np.linspace(1, 0, fo)
out = np.tanh(out * 1.6)
out = out / np.max(np.abs(out)) * 0.89
with wave.open("music2.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype(np.int16).tobytes())
print("ok", TOTAL)
