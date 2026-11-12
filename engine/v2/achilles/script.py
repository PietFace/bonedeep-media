import sys; sys.path.insert(0, "/home/claude/v2")
import common as C

SEGS = [
    ('run', "You've been running more lately...", 0.15, 1.0),
    ('morning', 'and now, every morning, your heel is stiff and sore.', 0.1, 1.0),
    ('hit', None, 0, 1.0),
    ('why', "Why? Let's look inside.", 0.35, 1.0),
    ('anat', 'Your calf muscles end in the Achilles tendon: the strongest tendon in your body.', 0.25, 1.0),
    ('load', 'Every running step, it carries several times your body weight.', 0.25, 1.0),
    ('over', 'Overload it too fast, and it gets irritated, and thickens.', 0.3, 1.0),
    ('pattern', 'Stiff in the morning. Better once warm. Worse the next day.', 0.35, 1.0),
    ('rest', "Just rest? It calms down, then comes back. Tendons need load.", 0.3, 1.0),
    ('fix', 'Slow, heavy calf raises, and build your running back up gradually.', 0.35, 1.0),
    ('flags', 'A sudden pop, like a kick to your calf? Get it checked, same day.', 0.4, 1.0),
    ('end', "Otherwise: load it smart. It's built for this.", 0.6, 1.0),
]
if __name__ == "__main__":
    C.make_voice(SEGS, "/home/claude/v2/achilles", sfx_gap={"hit": 0.8})
