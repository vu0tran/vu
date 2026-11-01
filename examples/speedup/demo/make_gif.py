"""Renders demo.gif from a recorded run: record.sh writes out_*.txt (the real output of each command
shown), and this draws them as a terminal. python3 make_gif.py demo.gif"""
import sys
from PIL import Image, ImageDraw, ImageFont

COLS, ROWS, FS = 86, 22, 16
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", FS)
bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", FS)
CW = font.getlength("M"); LH = int(FS * 1.45); PAD = 18; BAR = 30
W = int(PAD * 2 + CW * COLS); H = BAR + PAD * 2 + LH * ROWS
BG, FG, DIM, GREEN, YEL, BLUE = (13, 17, 23), (220, 225, 232), (125, 133, 144), (87, 210, 120), (240, 200, 90), (110, 170, 255)

def color_of(line):
    if line.startswith("$ #"): return DIM, False
    if line.startswith("$ "): return FG, True
    if line.startswith("did_you_mean, "): return YEL, True
    if line.startswith("same answers") or "now runs the Vu version" in line: return GREEN, False
    if line.startswith("speed on"): return YEL, False
    if line.startswith("#") or line.startswith("    #"): return DIM, False
    return FG, False

frames, durs = [], []
screen = []
def render(cursor=False):
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, BAR], fill=(30, 35, 44))
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([14 + i * 20, 10, 26 + i * 20, 22], fill=c)
    d.text((W / 2, BAR / 2), "vu speedup", fill=DIM, font=font, anchor="mm")
    rows = screen[-ROWS:]
    for r, line in enumerate(rows):
        y = BAR + PAD + r * LH
        if line.startswith("$ "):
            d.text((PAD, y), "$", fill=GREEN, font=bold)
            col, b = color_of(line)
            d.text((PAD + CW * 2, y), line[2:], fill=col, font=bold if b else font)
        else:
            col, b = color_of(line)
            d.text((PAD, y), line, fill=col, font=bold if b else font)
    if cursor:
        last = rows[-1] if rows else ""
        x = PAD + CW * len(last); y = BAR + PAD + (len(rows) - 1) * LH
        d.rectangle([x, y + 2, x + CW - 1, y + LH - 3], fill=FG)
    return im

def frame(ms, cursor=False):
    frames.append(render(cursor)); durs.append(ms)

def fit(line):
    return line if len(line) <= COLS else line[:COLS - 1] + "…"

def typed(cmd):
    screen.append("$ ")
    frame(500, True)
    step = 3
    for i in range(step, len(cmd) + step, step):
        screen[-1] = "$ " + cmd[:i]
        frame(35, True)
    frame(350, True)

def out(lines, each=0, end=1200):
    for l in lines:
        screen.append(fit(l))
        if each: frame(each)
    frame(end)

def lines_of(path):
    return open(path).read().rstrip("\n").split("\n")

typed("cat typos.py")
out(lines_of("out_cat.txt"), end=1800)
typed("python3 time_it.py")
frame(900)
out(lines_of("out_before.txt"), end=1800)
typed("# did_you_mean.vu: the Vu version, written by Claude from vu speedup's prompt")
typed("vu speedup typos.py:did_you_mean --port did_you_mean.vu")
sp = lines_of("out_speedup.txt")
frame(1200)
out(sp[:2], each=700, end=600)
out(sp[2:], each=1000, end=2200)
typed("python3 time_it.py")
frame(500)
out(lines_of("out_after.txt"), end=3500)
screen.append(""); screen.append("")
typed("tail -6 typos.py")
out(lines_of("out_tail.txt"), end=5000)

pal = frames[-1].quantize(colors=64)
q = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
q[0].save(sys.argv[1], save_all=True, append_images=q[1:], duration=durs, loop=0, optimize=True)
print(len(frames), "frames", sum(durs) / 1000, "s", W, "x", H)
