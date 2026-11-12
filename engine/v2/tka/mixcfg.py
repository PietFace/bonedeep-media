import sys; sys.path.insert(0, "/home/claude/v2"); sys.path.insert(0, "/home/claude/v2/tka")
import common as C
TL = C.Timeline("/home/claude/v2/tka/timeline.json"); T = TL.T
THIT = T["hit"][0]
TF0, TF1 = TL.wt("cut", "cuts"), TL.wt("cut", "shin") - 0.5
TT0, TT1 = TL.wt("cut", "shin"), T["cut"][1] - 0.2
Bm = [[47, 50, 54], [43, 47, 50], [45, 49, 52], [42, 45, 49]]
Dm = [[50, 54, 57], [45, 49, 52], [47, 50, 54], [43, 47, 50]]
saws = [(TF0 + i * 0.22, "tick", 0.5) for i in range(int((TF1 - TF0) / 0.22))] + [(TT0 + i * 0.22, "tick", 0.5) for i in range(int((TT1 - TT0) / 0.22))]
cfg = dict(bpm=92, seed=77, arp_step=2,
           sections=[(0, Bm, "warn"), (THIT + 0.3, Bm, "intro"), (T["cut"][0], Bm, "explain"), (T["plastic"][0], Dm, "good"),
                     (T["walk"][0], Dm, "good")],
           drops=[(THIT - 0.3, THIT + 0.2)],
           sfx=[(TL.wt("worn", "grinds"), "crack", 0.6), (THIT - 0.3, "riser", 0.6, 1.3), (THIT, "sting", 0.9), (THIT, "thud", 0.8),
                (T["title"][0] - 0.1, "whoosh", 1.0, 1.6), (TF1, "thud", 0.6), (TT1, "thud", 0.6),
                (TL.wt("metal", "metal") + 0.7, "thud", 0.8), (TL.wt("metal", "both") + 0.7, "thud", 0.8),
                (TL.wt("plastic", "insert") + 0.6, "pop", 0.8), (T["walk"][0] - 0.1, "whoosh", 0.8, 1.6)] + saws)
C.make_mix(TL, "/home/claude/v2/tka", cfg)
print("mix ok")
