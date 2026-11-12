import sys; sys.path.insert(0, "/home/claude/v2")
import common as C
TL = C.Timeline("/home/claude/v2/acl/timeline.json"); T = TL.T
TPOP = TL.wt("tear", "torn.")
TTD0, TTD1 = TL.wt("tunnels", "drills"), TL.wt("tunnels", "one") - 0.2
TFD0, TFD1 = TL.wt("tunnels", "one"), T["tunnels"][1] + 0.1
TFIX = TL.wt("pull", "fixed")
Em = [[52, 55, 59], [48, 52, 55], [50, 54, 57], [47, 50, 54]]
Gm = [[55, 59, 62], [50, 54, 57], [52, 55, 59], [48, 52, 55]]
drills = [(TTD0 + i * 0.12, "tick", 0.45) for i in range(int((TTD1 - TTD0) / 0.12))] + [(TFD0 + i * 0.12, "tick", 0.45) for i in range(int((TFD1 - TFD0) / 0.12))]
cfg = dict(bpm=108, seed=121, arp_step=2,
           sections=[(0, Em, "intro"), (TPOP + 0.3, Em, "warn"), (T["title"][0], Em, "explain"), (T["weak"][0], [[52, 55, 58], [52, 55, 59]], "warn"),
                     (TL.wt("weak", "stronger,"), Gm, "good"), (T["rehab"][0], Gm, "good")],
           drops=[(TPOP - 0.3, TPOP + 0.2)],
           sfx=[(TPOP, "pop", 1.0), (TPOP, "thud", 0.9), (T["title"][0] - 0.1, "whoosh", 1.0, 1.6),
                (TL.wt("harvest", "tendon"), "whoosh", 0.5, 0.8), (TFIX + 0.3, "thud", 0.8), (TFIX + 0.45, "thud", 0.6),
                (TL.wt("pull", "new"), "sting", 0.5), (T["rehab"][0] - 0.1, "whoosh", 0.8, 1.6), (TL.wt("end", "worth"), "thud", 0.8)] + drills)
C.make_mix(TL, "/home/claude/v2/acl", cfg)
print("mix ok")
