import numpy as np, wave

SR = 44100
SCENES = [4.5, 7.5, 7.0, 8.5, 8.0, 7.5]
TOTAL = sum(SCENES)
N = int(SR * TOTAL)
t = np.arange(N) / SR
out = np.zeros(N)

def note(f):
    return 440.0 * 2 ** ((f - 69) / 12)

bpm = 96
beat = 60 / bpm
bar = 4 * beat
# Am  F  C  G  (midi chords)
chords = [[57, 60, 64], [53, 57, 60], [48, 55, 60], [55, 59, 62]]
bass = [45, 41, 48, 43]

def env(n, a, r):
    e = np.ones(n)
    na, nr = min(int(a * SR), n // 2), min(int(r * SR), n // 2)
    e[:na] = np.linspace(0, 1, na)
    e[-nr:] *= np.linspace(1, 0, nr)
    return e

i = 0
pos = 0.0
while pos < TOTAL:
    ch = chords[i % 4]
    s0 = int(pos * SR); n = min(int(bar * SR), N - s0)
    tt = np.arange(n) / SR
    e = env(n, 0.4, 0.6)
    pad = sum(np.sin(2 * np.pi * note(m) * tt) + 0.25 * np.sin(4 * np.pi * note(m) * tt + 0.3) for m in ch)
    out[s0:s0 + n] += 0.06 * pad * e
    bb = np.sin(2 * np.pi * note(bass[i % 4]) * tt)
    out[s0:s0 + n] += 0.10 * bb * e
    # arpeggio plucks (eighth notes)
    arp = ch + [ch[0] + 12]
    for k in range(8):
        st = pos + k * beat / 2
        if st >= TOTAL:
            break
        a0 = int(st * SR); m = min(int(0.6 * SR), N - a0)
        tp = np.arange(m) / SR
        f = note(arp[k % 4] + 12)
        pl = (np.sin(2 * np.pi * f * tp) + 0.3 * np.sin(4 * np.pi * f * tp)) * np.exp(-tp * 7)
        out[a0:a0 + m] += 0.05 * pl
    # soft kick on beats 1 and 3
    for k in (0, 2):
        st = pos + k * beat
        a0 = int(st * SR); m = min(int(0.25 * SR), N - a0)
        if m <= 0:
            continue
        tp = np.arange(m) / SR
        f = 110 * np.exp(-tp * 25) + 45
        out[a0:a0 + m] += 0.22 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tp * 14)
    pos += bar; i += 1

rng = np.random.default_rng(1)
# whooshes at scene changes
acc = 0
for d in SCENES[:-1]:
    acc += d
    a0 = int((acc - 0.35) * SR); m = int(0.6 * SR)
    nz = rng.standard_normal(m)
    nz = np.convolve(nz, np.ones(30) / 30, mode="same")
    e = np.sin(np.linspace(0, np.pi, m)) ** 2
    out[a0:a0 + m] += 0.5 * nz * e
# crack at the tear (scene 4 starts at 19.0, tear at +5.3)
a0 = int((4.5 + 7.5 + 7.0 + 5.3) * SR); m = int(0.35 * SR)
tp = np.arange(m) / SR
out[a0:a0 + m] += 0.6 * rng.standard_normal(m) * np.exp(-tp * 30)
out[a0:a0 + m] += 0.4 * np.sin(2 * np.pi * 70 * tp) * np.exp(-tp * 10)

# fade out
fo = int(1.5 * SR)
out[-fo:] *= np.linspace(1, 0, fo)
out = out / np.max(np.abs(out)) * 0.7
pcm = (out * 32767).astype(np.int16)
with wave.open("music.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print("ok", TOTAL)
