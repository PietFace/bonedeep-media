import sys; sys.path.insert(0, "/home/claude/v2")
import common as C

SEGS = [
    ('q', 'Why do you even have a kneecap?', 0.3, 0.95),
    ('shield', "It's not just a shield. Let's look inside.", 0.35, 1.0),
    ('sesamoid', 'Your kneecap is a bone that grows inside a tendon.', 0.25, 1.0),
    ('lever', 'It pushes that tendon forward, away from the joint. That gives your thigh muscle more leverage.', 0.3, 1.0),
    ('without', 'Without it, straightening your knee takes much more force. Stairs, squats, standing up: all harder.', 0.35, 1.0),
    ('baby', "And babies don't have a bony one yet. It starts out as cartilage, and turns to bone around age three to six.", 0.35, 1.0),
    ('thick', 'Behind it sits the thickest cartilage in your body.', 0.4, 1.0),
    ('end', 'Small bone. Big job.', 0.6, 1.0),
]
if __name__ == "__main__":
    C.make_voice(SEGS, "/home/claude/v2/kneecap")
