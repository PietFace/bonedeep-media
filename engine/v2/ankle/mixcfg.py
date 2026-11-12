import sys; sys.path.insert(0, "/home/claude/v2")
import common as C
TL = C.Timeline("/home/claude/v2/ankle/timeline.json"); T = TL.T
TR = TL.wt("roll", "rolls.") + 0.1
TTEAR = TL.wt("grades", "tears")
Dm = [[50, 53, 57], [46, 50, 53], [53, 57, 60], [48, 52, 55]]      # D minor
Fm = [[53, 57, 60], [48, 52, 55], [50, 53, 57], [46, 50, 53]]      # F major
cfg = dict(bpm=100, seed=33, arp_step=3,
           sections=[(0, Dm, "intro"), (TR + 0.3, Dm, "explain"), (T["swell"][0], [[50, 53, 56], [50, 53, 57]], "warn"),
                     (T["rest"][0], Fm, "good"), (T["flags"][0], Dm, "warn"), (T["end"][0], Fm, "good")],
           drops=[(TR - 0.4, TR + 0.2), (TTEAR - 0.3, TTEAR + 0.1)],
           sfx=[(1.1, "whoosh", 0.5, 0.9), (TR, "crack", 0.8), (TR, "thud", 1.0), (TL.wt("what", "let's") - 0.1, "whoosh", 1.0, 1.7),
                (TTEAR, "crack", 1.0), (TTEAR, "thud", 0.8), (T["swell"][0] + 0.3, "heartbeat", 0.8, T["swell"][1]),
                (TL.wt("flags", "get"), "thud", 0.8), (T["end"][0] - 0.1, "whoosh", 0.8, 1.8)])
C.make_mix(TL, "/home/claude/v2/ankle", cfg)
print("mix ok")
