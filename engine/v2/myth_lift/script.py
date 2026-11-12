import sys; sys.path.insert(0, "/home/claude/v2")
import common as C

SEGS = [
    ('claim', 'Never lift with a bent back.', 0.2, 0.95),
    ('hit', None, 0, 1.0),
    ('check', "We've all been told. Let's check.", 0.35, 1.0),
    ('built', 'Your spine is built to bend. Each vertebra tilts a little, and together they flex smoothly.', 0.3, 1.0),
    ('discs', 'Discs and ligaments are made for that movement, and they adapt to load.', 0.3, 1.0),
    ('review', 'A large review found no link between a rounded back when lifting, and getting back pain.', 0.35, 1.0),
    ('stiff', 'In fact, people with back pain often lift stiffer, and more carefully.', 0.35, 1.0),
    ('risk', "What matters more? Too heavy, too often, when you're tired, or a load your body isn't used to.", 0.4, 1.0),
    ('verdict', 'So: mostly a myth.', 0.5, 0.95),
    ('end', 'Lift in a way that feels strong. And train your back to handle load.', 0.6, 1.0),
]
if __name__ == "__main__":
    C.make_voice(SEGS, "/home/claude/v2/myth_lift", sfx_gap={"hit": 0.8})
