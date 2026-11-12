import sys; sys.path.insert(0, "/home/claude/v2")
import common as C

SEGS = [
    ('worn', 'When the cartilage in your knee is worn away, bone grinds on bone.', 0.15, 1.0),
    ('hit', None, 0, 1.0),
    ('title', "Then, this is what a new knee looks like.", 0.35, 1.0),
    ('cut', 'First, the surgeon cuts a few millimetres off the worn ends of the thigh bone and shin bone.', 0.3, 1.0),
    ('metal', 'Metal parts go on both ends, fixed with bone cement, or with bone growing into them.', 0.3, 1.0),
    ('plastic', 'A smooth plastic insert goes in between. Now it glides, instead of grinding.', 0.35, 1.0),
    ('walk', 'Most people are up and walking, with support, within a day or so.', 0.3, 1.0),
    ('rehab', 'Then the real work: months of bending and strengthening.', 0.35, 1.0),
    ('last', 'Most new knees still work more than twenty years later.', 0.4, 1.0),
    ('end', 'Not magic. Metal, plastic, and a lot of rehab.', 0.6, 1.0),
]
if __name__ == "__main__":
    C.make_voice(SEGS, "/home/claude/v2/tka", sfx_gap={"hit": 0.8})
