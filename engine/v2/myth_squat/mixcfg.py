import sys; sys.path.insert(0, "/home/claude/v2")
import common as C
TL = C.Timeline("/home/claude/v2/myth_squat/timeline.json"); T = TL.T
THIT = T["hit"][0]; TV = TL.wt("verdict", "myth.")
Am = [[57, 60, 64], [53, 57, 60], [55, 59, 62], [52, 55, 59]]
Cm = [[60, 64, 67], [55, 59, 62], [57, 60, 64], [53, 57, 60]]
cfg = dict(bpm=106, seed=99, arp_step=1,
           sections=[(0, Am, "intro"), (THIT + 0.3, Am, "explain"), (T["wrap"][0], Cm, "good"), (T["risk"][0], [[57, 60, 63], [57, 60, 64]], "warn"),
                     (T["verdict"][0], Cm, "good")],
           drops=[(THIT - 0.3, THIT + 0.2), (TV - 0.3, TV + 0.1)],
           sfx=[(THIT - 0.3, "riser", 0.6, 1.3), (THIT, "sting", 0.9), (TL.wt("check", "let's") - 0.1, "whoosh", 1.0, 1.5),
                (TL.wt("area", "bigger"), "tick", 0.8), (TL.wt("wrap", "wraps"), "tick", 0.8), (TL.wt("calf", "taking"), "tick", 0.8),
                (TL.wt("review", "no"), "thud", 0.8), (TL.wt("risk", "too"), "thud", 0.5), (TV, "thud", 1.0), (TV, "sting", 0.7),
                (T["end"][0] - 0.1, "whoosh", 0.8, 1.7)])
C.make_mix(TL, "/home/claude/v2/myth_squat", cfg)
print("mix ok")
