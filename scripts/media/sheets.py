"""Numbered contact sheets from index.json, per folder, for picking by eye.

Stills: drop the softest 30% per folder and badly clipped frames, collapse
bursts (perceptual hash within distance 8) to the sharpest frame.
Videos: every clip, frame at 40%, labelled with fps/gamma/duration.
Writes sheets/<folder>.jpg and sheets/<folder>.json (number -> source path).

Usage: sheets.py <work_dir> [folder-substring ...]
"""
import json, sys
from collections import defaultdict
from pathlib import Path
import imagehash
from PIL import Image, ImageDraw, ImageFont

WORK = Path(sys.argv[1]); FILTERS = sys.argv[2:]
idx = [r for r in json.load(open(WORK / "index.json")) if r["kind"] in ("still", "video")]
(WORK / "sheets").mkdir(exist_ok=True)
font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 22)


def folder(r):
    p = Path(r["path"]).parts
    i = p.index("Cauvery peak")
    return "-".join(x for x in p[i + 1:-1] if x not in ("PRIVATE", "M4ROOT", "CLIP", "DCIM")).replace(" ", "")


groups = defaultdict(list)
for r in idx:
    groups[(folder(r), r["kind"])].append(r)

for (fold, kind), rs in sorted(groups.items()):
    if FILTERS and not any(f.lower() in fold.lower() for f in FILTERS):
        continue
    if kind == "still":
        rs = [r for r in rs if r["clipHi"] < 0.08 and r["clipLo"] < 0.25]
        if len(rs) > 8:
            cut = sorted(r["sharp"] for r in rs)[int(len(rs) * 0.3)]
            rs = [r for r in rs if r["sharp"] >= cut]
        keep = []
        for r in sorted(rs, key=lambda r: -r["sharp"]):
            h = imagehash.hex_to_hash(r["phash"])
            if all(h - imagehash.hex_to_hash(k["phash"]) > 8 for k in keep):
                keep.append(r)
        rs = sorted(keep, key=lambda r: r["path"])
    else:
        rs = sorted(rs, key=lambda r: r["path"])
    if not rs:
        continue
    cols, tw, th = 8, 300, 200
    for part in range(0, len(rs), 96):
        chunk = rs[part:part + 96]
        rows = (len(chunk) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * tw, rows * (th + 28)), "white")
        d = ImageDraw.Draw(sheet)
        mapping = {}
        for i, r in enumerate(chunk):
            n = part + i + 1
            mapping[n] = r["path"]
            x, y = (i % cols) * tw, (i // cols) * (th + 28)
            try:
                t = Image.open(WORK / "thumbs" / f"{r['id']}.jpg").convert("RGB")
                t.thumbnail((tw - 6, th - 6)); sheet.paste(t, (x + 3, y + 3))
            except Exception:
                pass
            label = f"{n}" + (f"  {r.get('fps')} {('LOG' if 'log' in str(r.get('gamma')) else '')} {r.get('dur', 0):.0f}s" if kind == "video" else "")
            d.text((x + 4, y + th + 2), label, fill="black", font=font)
        name = f"{fold}-{kind}" + (f"-{part // 96 + 1}" if len(rs) > 96 else "")
        sheet.save(WORK / "sheets" / f"{name}.jpg", quality=72)
        json.dump(mapping, open(WORK / "sheets" / f"{name}.json", "w"), indent=0)
        print(f"{name}: {len(chunk)}")
