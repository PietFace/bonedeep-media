import sys; sys.path.insert(0, "/home/claude/v2")
import common as C

SEGS = [
    ('lift', 'You lift your arm out to the side...', 0.15, 1.0),
    ('sting', None, 0, 1.0),
    ('why', "Halfway up, it stings. Why? Let's look inside.", 0.35, 1.0),
    ('ball', 'Your shoulder: a ball, in a shallow socket.', 0.15, 1.0),
    ('cuff', 'Four rotator cuff muscles keep that ball centred.', 0.25, 1.0),
    ('roof', 'One tendon runs through a narrow gap, under a bony roof.', 0.25, 1.0),
    ('arc', 'Between sixty and a hundred and twenty degrees, that gap is tightest.', 0.25, 1.0),
    ('irr', 'Overload that tendon, it gets irritated, and that tight spot hurts.', 0.35, 1.0),
    ('signs', 'Pain lifting your arm. Pain at night. Weakness reaching up.', 0.4, 1.0),
    ('good', 'Good news: for most people, the right exercises are the first step.', 0.3, 1.0),
    ('check', 'Not improving? Get it checked.', 0.55, 1.0),
]
if __name__ == "__main__":
    C.make_voice(SEGS, "/home/claude/v2/shoulder", sfx_gap={"sting": 0.9})
