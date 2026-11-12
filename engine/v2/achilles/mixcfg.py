import sys; sys.path.insert(0, "/home/claude/v2")
import common as C
TL = C.Timeline("/home/claude/v2/achilles/timeline.json"); T = TL.T
THIT = T["hit"][0]; TPOP = TL.wt("flags", "pop,")
Em = [[52, 55, 59], [48, 52, 55], [50, 54, 57], [47, 50, 54]]      # E minor
Gm = [[55, 59, 62], [50, 54, 57], [52, 55, 59], [48, 52, 55]]      # G major
cfg = dict(bpm=104, seed=55, arp_step=2,
           sections=[(0, Em, "intro"), (THIT + 0.3, Em, "explain"), (T["over"][0], [[52, 55, 58], [52, 55, 59]], "warn"),
                     (T["fix"][0], Gm, "good"), (T["flags"][0], Em, "warn"), (T["end"][0], Gm, "good")],
           drops=[(THIT - 0.35, THIT + 0.2), (TPOP - 0.3, TPOP + 0.1)],
           sfx=[(THIT - 0.35, "riser", 0.6, 1.4), (THIT, "sting", 1.0), (TL.wt("why", "let's") - 0.1, "whoosh", 1.0, 1.7),
                (TL.wt("over", "irritated,"), "thud", 0.6), (TL.wt("over", "irritated,") + 0.2, "heartbeat", 0.6, T["pattern"][1]),
                (TPOP, "pop", 1.0), (TPOP, "thud", 0.9), (TL.wt("flags", "get"), "thud", 0.8), (T["end"][0] - 0.1, "whoosh", 0.8, 1.8)])
C.make_mix(TL, "/home/claude/v2/achilles", cfg)
print("mix ok")
