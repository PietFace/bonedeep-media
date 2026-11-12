import sys; sys.path.insert(0, "/home/claude/v2")
import common as C
TL = C.Timeline("/home/claude/v2/taller/timeline.json"); T = TL.T
F = [[53, 57, 60], [48, 52, 55], [50, 53, 57], [46, 50, 53]]
Ab = [[56, 60, 63], [51, 55, 58], [53, 56, 60], [49, 53, 56]]
cfg = dict(bpm=100, seed=131, arp_step=1,
           sections=[(0, F, "intro"), (T["discs"][0], F, "explain"), (T["night"][0], Ab, "intro"), (T["space"][0], Ab, "explain"),
                     (T["end"][0], F, "good")],
           drops=[],
           sfx=[(TL.wt("q", "night."), "whoosh", 0.5, 0.8), (TL.wt("how", "let's") - 0.1, "whoosh", 1.0, 1.6),
                (TL.wt("discs", "water"), "tick", 0.8), (TL.wt("day", "squeeze"), "tick", 0.7), (TL.wt("night", "soak"), "tick", 0.7),
                (T["space"][0] - 0.1, "whoosh", 0.8, 1.6), (TL.wt("space", "grow"), "riser", 0.4, 1.2), (TL.wt("end", "do"), "thud", 0.8)])
C.make_mix(TL, "/home/claude/v2/taller", cfg)
print("mix ok")
