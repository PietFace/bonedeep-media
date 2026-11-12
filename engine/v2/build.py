"""Render a v2 video: python3 build.py <dir> <out.mp4>  (dir has film.py, timeline.json, mix.wav)"""
import sys, os, json, subprocess
d, out = sys.argv[1], sys.argv[2]
N = int(json.load(open(os.path.join(d, "timeline.json")))["total"] * 30)
parts = 3
cuts = [N * i // parts for i in range(parts + 1)]
os.makedirs(os.path.join(d, "out"), exist_ok=True)
procs = []
for i in range(parts):
    f = os.path.join(d, "out", f"p{i}.mp4")
    if os.path.exists(f): os.remove(f)
    procs.append(subprocess.Popen([sys.executable, os.path.join(d, "film.py"), "video", str(cuts[i]), str(cuts[i + 1]), f]))
for pr in procs:
    pr.wait()
lst = os.path.join(d, "out", "list.txt")
open(lst, "w").write("".join(f"file 'p{i}.mp4'\n" for i in range(parts)))
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
                os.path.join(d, "out", "video.mp4")], check=True)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(d, "out", "video.mp4"), "-i", os.path.join(d, "mix.wav"),
                "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-shortest", out], check=True)
print("built", out)
