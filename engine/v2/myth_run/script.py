import sys; sys.path.insert(0, "/home/claude/v2")
import common as C

SEGS = [
    ('claim', 'Running ruins your knees.', 0.2, 0.95),
    ('hit', None, 0, 1.0),
    ('check', "Everyone says it. Let's check.", 0.35, 1.0),
    ('load', 'Every running step pushes several times your body weight through your knee.', 0.25, 1.0),
    ('cart', 'But cartilage has no blood supply. It feeds by being squeezed and released, like a sponge.', 0.3, 1.0),
    ('data', 'And in a large review of studies, recreational runners had less knee and hip arthritis than people who did not run.', 0.3, 1.0),
    ('elite', 'Only years of high-level competition raised the risk.', 0.35, 1.0),
    ('risk', 'The bigger risks? An old knee injury, extra body weight, and ramping up too fast.', 0.4, 1.0),
    ('verdict', 'So: myth.', 0.5, 0.95),
    ('end', 'Build up gradually. Your knees can take it.', 0.6, 1.0),
]
if __name__ == "__main__":
    C.make_voice(SEGS, "/home/claude/v2/myth_run", sfx_gap={"hit": 0.8})
