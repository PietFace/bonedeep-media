import sys; sys.path.insert(0, "/home/claude/v2")
import common as C

SEGS = [
    ('step', 'You step off a curb...', 0.15, 1.0),
    ('roll', 'and your ankle rolls.', 0.1, 1.0),
    ('hit', None, 0, 1.0),
    ('what', "What just happened? Let's look inside.", 0.35, 1.0),
    ('ligs', 'On the outside of your ankle, three small ligaments hold your foot to your leg.', 0.25, 1.0),
    ('inward', 'When your foot rolls inward, they stretch, and the front one usually takes the hit.', 0.25, 1.0),
    ('grades', 'A mild sprain overstretches it. A bad one tears it.', 0.3, 1.0),
    ('swell', 'Blood and fluid rush in, so it swells, and bruises.', 0.35, 1.0),
    ('rest', 'Rest it for weeks? No. Most sprains heal better if you move early, and train your balance.', 0.35, 1.0),
    ('flags', "Can't walk on it, or pain right on the bone? Get it checked.", 0.4, 1.0),
    ('end', "Otherwise: train that ankle. It'll thank you.", 0.6, 1.0),
]
if __name__ == "__main__":
    C.make_voice(SEGS, "/home/claude/v2/ankle", sfx_gap={"hit": 0.8})
