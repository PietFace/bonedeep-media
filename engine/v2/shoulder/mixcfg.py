import sys; sys.path.insert(0, "/home/claude/v2")
import common as C
TL = C.Timeline("/home/claude/v2/shoulder/timeline.json"); T = TL.T
TS = T["sting"][0]
Am = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]      # A minor
Cm = [[60, 64, 67], [55, 59, 62], [57, 60, 64], [53, 57, 60]]      # C major
cfg = dict(bpm=96, seed=21, arp_step=2,
           sections=[(0, Am, "intro"), (TS + 0.3, Am, "explain"), (T["irr"][0], [[57, 60, 63], [57, 60, 64]], "warn"),
                     (T["signs"][0], Am, "explain"), (T["good"][0], Cm, "good")],
           drops=[(TS - 0.35, TS + 0.25)],
           sfx=[(TS - 0.35, "riser", 0.8, 1.8), (TS, "sting", 1.0), (TL.wt("why", "let's") - 0.1, "whoosh", 1.0, 1.7),
                (T["cuff"][0] - 0.1, "whoosh", 0.6, 0.6), (T["roof"][0] - 0.2, "whoosh", 0.6, 0.6),
                (T["irr"][0] + 0.4, "thud", 0.5), (T["irr"][0] + 1.97, "thud", 0.5), (T["irr"][0] + 3.54, "thud", 0.5),
                (TL.wt("check", "get"), "thud", 0.8), (T["check"][0] + 0.9, "whoosh", 0.8, 1.8)])
C.make_mix(TL, "/home/claude/v2/shoulder", cfg)
print("mix ok")
