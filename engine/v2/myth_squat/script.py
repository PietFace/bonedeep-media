import sys; sys.path.insert(0, "/home/claude/v2")
import common as C

SEGS = [
    ('claim', 'Deep squats are bad for your knees.', 0.2, 0.95),
    ('hit', None, 0, 1.0),
    ('check', "You've heard it. Let's check.", 0.35, 1.0),
    ('area', 'As you bend deeper, your kneecap touches a bigger area, so the pressure is spread out.', 0.3, 1.0),
    ('wrap', 'The tendon above it wraps around the thigh bone, and takes part of the load.', 0.3, 1.0),
    ('calf', 'And at the bottom, your thigh rests on your calf, taking even more load off the joint.', 0.3, 1.0),
    ('review', 'A large review found no evidence that deep squats harm healthy knees.', 0.35, 1.0),
    ('risk', 'The real risk? Too much weight, too soon, or poor technique.', 0.4, 1.0),
    ('verdict', 'So: myth.', 0.5, 0.95),
    ('end', 'Squat deep, build up gradually. And if it hurts, adjust the depth.', 0.6, 1.0),
]
if __name__ == "__main__":
    C.make_voice(SEGS, "/home/claude/v2/myth_squat", sfx_gap={"hit": 0.8})
