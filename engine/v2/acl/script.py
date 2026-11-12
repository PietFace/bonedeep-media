import sys; sys.path.insert(0, "/home/claude/v2")
import common as C

SEGS = [
    ('tear', 'Your ACL is torn. And it rarely heals by itself.', 0.15, 1.0),
    ('hit', None, 0, 1.0),
    ('title', 'This is what an ACL reconstruction looks like.', 0.35, 1.0),
    ('harvest', 'Often, the surgeon takes a strip of hamstring tendon from your own leg.', 0.3, 1.0),
    ('tunnels', 'Then drills a tunnel through the shin bone, and one into the thigh bone.', 0.3, 1.0),
    ('pull', 'The tendon is pulled through, and fixed in place. Your new ACL.', 0.35, 1.0),
    ('weak', 'But in the first months, it gets weaker before it gets stronger, as it slowly turns into ligament.', 0.35, 1.0),
    ('rehab', 'Most people return to sport after nine months or more. Going back too early raises the risk of tearing it again.', 0.4, 1.0),
    ('end', 'New ligament. Long rehab. Worth it.', 0.6, 1.0),
]
if __name__ == "__main__":
    C.make_voice(SEGS, "/home/claude/v2/acl", sfx_gap={"hit": 0.6})
