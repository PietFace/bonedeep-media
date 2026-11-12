import sys; sys.path.insert(0, "/home/claude/v2")
import common as C
TL = C.Timeline("/home/claude/v2/back/timeline.json"); T = TL.T
THIT = T["hit"][0]
Gm = [[55, 58, 62], [51, 55, 58], [53, 57, 60], [50, 54, 57]]      # G minor
Bb = [[58, 62, 65], [53, 57, 60], [55, 58, 62], [51, 55, 58]]      # Bb major
cfg = dict(bpm=88, seed=44, arp_step=1,
           sections=[(0, Gm, "intro"), (THIT + 0.3, Gm, "explain"), (T["strain"][0], [[55, 58, 61], [55, 58, 62]], "warn"),
                     (T["better"][0], Bb, "good"), (T["flags"][0], Gm, "warn"), (T["end"][0], Bb, "good")],
           drops=[(THIT - 0.35, THIT + 0.2)],
           sfx=[(THIT - 0.35, "riser", 0.7, 1.6), (THIT, "sting", 1.0), (THIT, "thud", 0.9),
                (TL.wt("feel", "let's") - 0.1, "whoosh", 1.0, 1.7), (TL.wt("strain", "lock"), "thud", 0.6),
                (TL.wt("strain", "lock") + 0.2, "heartbeat", 0.7, T["hurt"][1]),
                (TL.wt("flags", "get"), "thud", 0.9), (T["end"][0] - 0.1, "whoosh", 0.8, 1.8)])
C.make_mix(TL, "/home/claude/v2/back", cfg)
print("mix ok")
