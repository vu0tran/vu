"""Draws demo.gif from the recorded run (record.sh writes out_*.txt in the current folder: the real
output of each command shown). python3 make_gif.py demo.gif"""
import sys
from PIL import Image, ImageDraw, ImageFont

COLS, ROWS, FS = 90, 26, 15
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", FS)
bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", FS)
CW = font.getlength("M"); LH = int(FS * 1.45); PAD = 18; BAR = 30
W = int(PAD * 2 + CW * COLS); H = BAR + PAD * 2 + LH * ROWS
BG, FG, DIM, GREEN, RED, YEL = (13, 17, 23), (220, 225, 232), (125, 133, 144), (87, 210, 120), (255, 110, 100), (240, 200, 90)

def style(line):
    if line.startswith("$ #"): return YEL, True
    if line.startswith("$ "): return FG, True
    if line.startswith("attacker's server got"): return RED, True
    if line.startswith("  ") and "error" not in line and line.lstrip()[:2].isdigit(): return DIM, False
    if "error:" in line or line.startswith("    "): return RED, False
    if line.startswith("#") or line.lstrip().startswith("//"): return DIM, False
    if line.startswith("need "): return GREEN, False
    return FG, False

frames, durs, screen = [], [], []

def render(cursor=False):
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, BAR], fill=(30, 35, 44))
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([14 + i * 20, 10, 26 + i * 20, 22], fill=c)
    d.text((W / 2, BAR / 2), "the same compromised package, in Node and in Vu", fill=DIM, font=font, anchor="mm")
    rows = screen[-ROWS:]
    for r, (line, st) in enumerate(rows):
        y = BAR + PAD + r * LH
        col, b = st
        if line.startswith("$ "):
            d.text((PAD, y), "$", fill=GREEN, font=bold)
            d.text((PAD + CW * 2, y), line[2:], fill=col, font=bold if b else font)
        else:
            d.text((PAD, y), line, fill=col, font=bold if b else font)
    if cursor and rows:
        last = rows[-1][0]
        x = PAD + CW * len(last); y = BAR + PAD + (len(rows) - 1) * LH
        d.rectangle([x, y + 2, x + CW - 1, y + LH - 3], fill=FG)
    return im

def frame(ms, cursor=False):
    frames.append(render(cursor)); durs.append(ms)

def add(line):
    """A line, wrapped at the terminal's width (continuations keep its colour)."""
    st = style(line)
    while len(line) > COLS:
        cut = line.rfind(" ", 0, COLS)
        if cut < COLS // 2: cut = COLS
        screen.append((line[:cut], st)); line = "    " + line[cut:].lstrip()
    screen.append((line, st))

def typed(cmd, pause=350):
    st = style("$ " + cmd)
    screen.append(("$ ", st)); frame(400, True)
    for i in range(3, len(cmd) + 3, 3):
        screen[-1] = ("$ " + cmd[:i], st); frame(30, True)
    frame(pause, True)

def out(path, each=0, end=1200):
    for l in open(path).read().rstrip("\n").split("\n"):
        add(l)
        if each: frame(each)
    frame(end)

typed("# slugify 1.1.0 was pushed from a stolen maintainer account. In Node:", 600)
typed("tail -2 node_modules/slugify/index.js")
out("out_node_cat.txt", end=2200)
typed("node main.js")
frame(500)
out("out_node.txt", each=900, end=3000)
screen.append(("", (FG, False)))
typed("# The same compromised version, in Vu:", 600)
typed("tail -4 ~/.cache/vu/pkg/slugify@v1.1.0/slugify.vu")
out("out_vu_cat.txt", end=2200)
typed("cat vu.pkg")
out("out_vu_pkg.txt", end=1200)
typed("vu run main.vu")
frame(700)
out("out_vu.txt", end=3500)
typed("# A package gets only what its vu.pkg line grants: fs, net, os, ffi. This one got none.", 6000)

pal = frames[-1].quantize(colors=64)
q = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
q[0].save(sys.argv[1], save_all=True, append_images=q[1:], duration=durs, loop=0, optimize=True)
print(len(frames), "frames", round(sum(durs) / 1000, 1), "s", W, "x", H)
