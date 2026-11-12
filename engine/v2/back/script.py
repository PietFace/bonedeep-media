import sys; sys.path.insert(0, "/home/claude/v2")
import common as C

SEGS = [
    ('bend', 'You bend down to pick something up...', 0.15, 1.0),
    ('hit', None, 0, 1.0),
    ('lock', 'and your back locks up.', 0.25, 1.0),
    ('feel', "Feels like something slipped out of place? Let's look inside.", 0.35, 1.0),
    ('anat', 'Five strong vertebrae, with tough discs in between.', 0.25, 1.0),
    ('nothing', 'In most cases, nothing has slipped, or moved out of place.', 0.3, 1.0),
    ('strain', 'A muscle or ligament gets strained, and the muscles around it lock up, to protect it.', 0.3, 1.0),
    ('hurt', "It can hurt a lot, but pain doesn't always mean damage.", 0.3, 1.0),
    ('better', 'Most people feel clearly better within a few weeks.', 0.25, 1.0),
    ('move', 'Bed rest? Usually not. Gentle movement helps.', 0.35, 1.0),
    ('flags', 'Numbness around your groin, trouble peeing, or weak legs? Get help, right away.', 0.4, 1.0),
    ('end', 'Otherwise: keep moving. Your back is stronger than you think.', 0.6, 1.0),
]
if __name__ == "__main__":
    C.make_voice(SEGS, "/home/claude/v2/back", sfx_gap={"hit": 0.8})
