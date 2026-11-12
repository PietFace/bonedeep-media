import sys; sys.path.insert(0, "/home/claude/v2")
import common as C
TL = C.Timeline("/home/claude/v2/kneecap/timeline.json"); T = TL.T
TREM = TL.wt("without", "without")
F = [[53, 57, 60], [48, 52, 55], [50, 53, 57], [46, 50, 53]]
Dm = [[50, 53, 57], [46, 50, 53], [48, 52, 55], [45, 48, 52]]
cfg = dict(bpm=112, seed=88, arp_step=1,
           sections=[(0, F, "intro"), (T["sesamoid"][0], F, "explain"), (TREM, Dm, "warn"), (T["baby"][0], F, "explain"),
                     (T["end"][0], F, "good")],
           drops=[(TREM - 0.3, TREM + 0.1)],
           sfx=[(TL.wt("shield", "let's") - 0.1, "whoosh", 1.0, 1.6), (TL.wt("sesamoid", "bone"), "tick", 0.7),
                (TL.wt("lever", "leverage."), "tick", 0.8), (TREM, "pop", 0.9), (TREM + 0.4, "thud", 0.7),
                (TL.wt("baby", "turns"), "riser", 0.4, 1.4), (TL.wt("thick", "thickest"), "tick", 0.8),
                (TL.wt("end", "big"), "thud", 0.9), (T["end"][0] - 0.1, "whoosh", 0.7, 1.5)])
C.make_mix(TL, "/home/claude/v2/kneecap", cfg)
print("mix ok")
