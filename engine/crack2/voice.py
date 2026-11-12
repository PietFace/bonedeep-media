"""George voice-over for the knee-cracking Short. Writes vo.wav + timeline.json (segment and word times)."""
import json, re, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

SEGS = [  # (id, text, pause_after_s, speed)
    ("squat", "You squat down,", 0.10, 1.0),
    ("goes", "and your knee goes...", 0.30, 0.95),
    ("crack", None, 0.0, 1.0),
    ("bad", "Is that bad? Let's look inside.", 0.35, 1.0),
    ("capsule", "Your knee is wrapped in a capsule, filled with fluid.", 0.15, 1.0),
    ("gas", "That fluid holds dissolved gas.", 0.15, 1.0),
    ("bend", "When you bend, the pressure drops, and a bubble forms...", 0.15, 1.0),
    ("pop", None, 0.0, 1.0),
    ("tendon", "Sometimes, it's a tendon, flicking over a bump of bone.", 0.35, 1.0),
    ("harmless", "Painless cracking is very common, and usually harmless.", 0.40, 1.0),
    ("pain", "But if it comes with pain,", 0.05, 1.0),
    ("swell", "swelling,", 0.10, 1.0),
    ("lock", "or your knee locks, or gives way,", 0.10, 1.0),
    ("check", "get it checked.", 0.50, 1.0),
    ("move", "Otherwise? Keep moving. Your knees love it.", 0.60, 1.0),
]
LEAD = 0.35   # silence before the first word

k = Kokoro("/home/claude/tts/kokoro-v1.0.int8.onnx", "/home/claude/tts/voices-v1.0.bin")
sr = 24000
parts = [np.zeros(int(LEAD * sr), np.float32)]
t = LEAD
timeline = []
SFX_GAP = {"crack": 1.05, "pop": 0.85}   # silence where the real sound effect plays
for sid, text, pause, speed in SEGS:
    if text is None:
        g = SFX_GAP[sid]
        timeline.append({"id": sid, "text": "", "t0": round(t, 3), "t1": round(t + 0.25, 3), "words": []})
        parts.append(np.zeros(int(g * sr), np.float32)); t += g
        continue
    a, sr = k.create(text, voice="bm_george", speed=speed, lang="en-gb")
    a = a.astype(np.float32)
    # trim leading/trailing silence
    env = np.abs(a) > 0.01
    if env.any():
        i0, i1 = np.argmax(env), len(a) - np.argmax(env[::-1])
        a = a[max(0, i0 - 240): min(len(a), i1 + 480)]
    dur = len(a) / sr
    # estimate word times by syllable-ish weight (letters + punctuation pauses)
    words = text.split()
    wts = [len(re.sub(r"[^A-Za-z']", "", w)) + 2 + (4 if w[-1] in ",.?!" else 0) for w in words]
    tot = sum(wts); acc = 0; wl = []
    for w, wt in zip(words, wts):
        wl.append({"w": w, "t0": round(t + dur * acc / tot, 3), "t1": round(t + dur * (acc + wt) / tot, 3)})
        acc += wt
    timeline.append({"id": sid, "text": text, "t0": round(t, 3), "t1": round(t + dur, 3), "words": wl})
    parts += [a, np.zeros(int(pause * sr), np.float32)]
    t += dur + pause
vo = np.concatenate(parts)
sf.write("vo_raw.wav", vo, sr)
total = round(t + 0.2, 3)
json.dump({"total": total, "segs": timeline}, open("timeline.json", "w"), indent=1)
for s in timeline:
    print(f'{s["id"]:9s} {s["t0"]:6.2f} - {s["t1"]:6.2f}  {s["text"]}')
print("total", total)
