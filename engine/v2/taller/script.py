import sys; sys.path.insert(0, "/home/claude/v2")
import common as C

SEGS = [
    ('q', "You're taller in the morning than at night.", 0.3, 0.95),
    ('how', "About one to two centimetres. Let's look inside.", 0.35, 1.0),
    ('discs', 'Between your vertebrae sit discs, like little water cushions.', 0.3, 1.0),
    ('day', 'All day, gravity and movement squeeze a bit of fluid out of them, so they get slightly thinner.', 0.35, 1.0),
    ('night', 'When you lie down at night, they soak it back up.', 0.35, 1.0),
    ('space', 'Without gravity, astronauts even grow a few centimetres in space.', 0.4, 1.0),
    ('end', 'Want to measure tall? Do it in the morning.', 0.6, 1.0),
]
if __name__ == "__main__":
    C.make_voice(SEGS, "/home/claude/v2/taller")
