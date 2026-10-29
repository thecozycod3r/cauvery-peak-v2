"""Export graded replacements for the site's existing photos (assets/media/r-*.webp).

replace.json: "frames" pull one graded frame from a shoot clip (S-Log3 LUT,
exposure picked per clip from the ladder, optional 90° CCW turn); "stills"
develop a camera still (RAW when present) with the soft estate look. Each
output keeps the aspect of the photo it replaces ("map": old -> new) at 1.5x
its old pixel size, capped at 1600 wide; "heroes" (ph-*) are 2000x1125
for the interior-page headers. Old files are left untouched.
Usage: export_replace.py <work_dir> <site_dir> [--only a,b]
"""
import json, subprocess, sys, tempfile
from pathlib import Path
import numpy as np
from PIL import Image, ImageOps, ImageFilter
import pillow_heif
pillow_heif.register_heif_opener()

WORK, SITE = Path(sys.argv[1]), Path(sys.argv[2])
OUT = SITE / "assets" / "media"
R = json.load(open(WORK / "replace.json"))
src = lambda sheet, n: json.load(open(WORK / "sheets" / f"{sheet}.json"))[str(n)]
index = {r["path"]: r for r in json.load(open(WORK / "index.json")) if "path" in r}
ONLY = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None
old_of = {v: k for k, v in R["map"].items()}


def lut_from_cube(path):
    table = [float(x) for l in open(path) if l[:1].isdigit() or l[:1] == "-" for x in l.split()]
    return ImageFilter.Color3DLUT(33, table)


def target(name):
    if name.startswith("ph-"): return (2000, 1125)  # interior-page heroes
    w, h = Image.open(SITE / "assets" / f"{old_of[name]}.webp").size
    k = min(1.5, 1600 / w)
    return round(w * k), round(h * k)


def frame(p, rot):
    t = max(0.0, index[p]["dur"] * 0.4); best = None
    with tempfile.TemporaryDirectory() as d:
        for e in ("0.3", "0.42", "0.55", "0.75", "1.0"):
            out = f"{d}/{e}.png"
            subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-ss", f"{t:.2f}", "-i", p, "-frames:v", "1",
                            "-vf", f"format=rgb48le,lut3d={WORK}/luts/slog3_e{e}.cube", out], check=True)
            im = Image.open(out).convert("RGB")
            L = np.asarray(im.convert("L").resize((240, 135)), dtype=float) / 255
            # aim mid-grey on average without letting more than 2% clip
            score = abs(L.mean() - 0.45) + 4 * max(0.0, (L > 0.98).mean() - 0.02)
            if best is None or score < best[0]: best = (score, e, im)
    im = best[2].rotate(90, expand=True) if rot else best[2]
    return im, best[1]


soft = lut_from_cube(WORK / "luts" / "rec709_soft.cube")


def still(p):
    raw = next((Path(p).with_suffix(x) for x in (".ARW", ".arw") if Path(p).with_suffix(x).exists()), None)
    if raw:
        import rawpy
        with rawpy.imread(str(raw)) as r:  # LibRaw applies orientation itself
            rgb = r.postprocess(use_camera_wb=True, no_auto_bright=False, bright=1.05, output_bps=8, output_color=rawpy.ColorSpace.sRGB)
        # Dusk frames develop dark next to a bright sky: lift the mids with a
        # gamma curve (highlights stay put) until mean luminance reaches ~0.40.
        a = rgb.astype(np.float32) / 255
        m = float((a @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)).mean())
        if m < 0.36:
            a = a ** (np.log(0.40) / np.log(max(m, 0.05)))
            rgb = (a * 255 + 0.5).astype(np.uint8)
        return Image.fromarray(rgb).filter(soft), raw.name
    return ImageOps.exif_transpose(Image.open(p)).convert("RGB").filter(soft), Path(p).name


jobs = [(n, "f", v) for n, v in R["frames"].items()] + [(n, "s", v) for n, v in R["stills"].items()]
jobs += [(n, v[0], v[1:]) for n, v in R.get("heroes", {}).items()]
for name, kind, v in jobs:
    if ONLY and name not in ONLY: continue
    if kind == "f":
        im, how = frame(src(v[0], v[1]), v[2]); how = f"e{how}{' rot' if v[2] else ''}"
    else:
        im, how = still(src(v[0], v[1]))
    im = ImageOps.fit(im, target(name), method=Image.LANCZOS, centering=(0.5, 0.45))
    out = OUT / f"{name}.webp"; im.save(out, quality=76, method=6)
    print(f"{name:14} {im.size[0]}x{im.size[1]} {out.stat().st_size//1024:4d}KB  {how}  (replaces {old_of.get(name, 'hero')})")
