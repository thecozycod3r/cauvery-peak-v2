"""Grade + export the picked media into the site (assets/media/).

Videos: LUT (S-Log3 -> estate, per-clip exposure), optional 90° CCW turn for
vertically-shot clips, cover-crop to the target frame, 100p conformed to 25p
slow motion, H.264 no audio + faststart, plus a WebP poster from frame 0.
Stills: estate look at soft strength (phone/camera JPEGs are pre-processed),
cover-crop, WebP q80. Usage: export.py <work_dir> <site_dir>
"""
import json, subprocess, sys
from pathlib import Path
from PIL import Image, ImageOps, ImageFilter
import pillow_heif
pillow_heif.register_heif_opener()

WORK, SITE = Path(sys.argv[1]), Path(sys.argv[2])
OUT = SITE / "assets" / "media"; OUT.mkdir(parents=True, exist_ok=True)
picks = json.load(open(WORK / "picks.json"))
src = lambda sheet, n: json.load(open(WORK / "sheets" / f"{sheet}.json"))[str(n)]
index = {r["path"]: r for r in json.load(open(WORK / "index.json")) if "path" in r}


def lut_from_cube(path):
    lines = [l for l in open(path) if l[:1].isdigit() or l[:1] == "-" or (l[:1] == "0")]
    size = 33
    table = [float(x) for l in lines for x in l.split()]
    return ImageFilter.Color3DLUT(size, table)


ONLY = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None
for name, (sheet, n) in ([] if "--stills" in sys.argv else [kv for kv in picks["videos"].items() if not ONLY or kv[0] in ONLY]):
    p, s = src(sheet, n), picks["spec"][name]
    fps = str(index.get(p, {}).get("fps", "25"))
    slow = 4 if fps.startswith("100") else 1
    vf = [f"format=rgb48le,lut3d={WORK}/luts/{s['lut']}.cube"]
    if s["rot"]: vf.append("transpose=2")
    vf += [f"scale={s['w']}:{s['h']}:force_original_aspect_ratio=increase:flags=lanczos", f"crop={s['w']}:{s['h']}"]
    if slow > 1: vf.append(f"setpts={slow}*PTS")
    vf += ["fps=25", "format=yuv420p"]
    seconds = s["len"] / slow + 0.2
    mp4 = OUT / f"{name}.mp4"
    subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-ss", "0.5", "-t", f"{seconds:.2f}", "-i", p, "-an",
                    "-vf", ",".join(vf), "-c:v", "libx264", "-profile:v", "high", "-crf", "24" if s["w"] > 1000 else "25",
                    "-preset", "slow", "-g", "50", "-movflags", "+faststart", str(mp4)], check=True)
    poster = OUT / f"{name}{'-poster' if name.startswith('hero') else ''}.png"
    subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-i", str(mp4), "-frames:v", "1", str(poster)], check=True)
    im = Image.open(poster).convert("RGB"); webp = poster.with_suffix(".webp")
    im.save(webp, quality=80, method=6); poster.unlink()
    print(f"{name:14} {fps:>5}fps slow×{slow} {mp4.stat().st_size//1024:6d}KB  poster {webp.stat().st_size//1024}KB")

SIZES = {"est-shevaroys": (1200, 1600), "est-glenfell": (1200, 1600), "est-cauverypeak": (1200, 1600),
         "heritage": (1200, 1500), "shop-life": (1200, 1500), "cafe-lv": (1600, 1200), "closer": (2400, 1350)}
soft = lut_from_cube(WORK / "luts" / "rec709_soft.cube")
for name, (sheet, n) in ([] if ONLY else picks["stills"].items()):
    p = src(sheet, n)
    raw = next((Path(p).with_suffix(x) for x in (".ARW", ".arw") if Path(p).with_suffix(x).exists()), None)
    if raw:
        # The a7 III had its S-Log3 picture profile on for stills too, so the
        # camera JPEG is flat. Develop the RAW instead (camera white balance,
        # sRGB, gentle auto-brightness). LibRaw applies the orientation itself.
        import rawpy
        with rawpy.imread(str(raw)) as r:
            rgb = r.postprocess(use_camera_wb=True, no_auto_bright=False, bright=1.05, output_bps=8, output_color=rawpy.ColorSpace.sRGB)
        im = Image.fromarray(rgb)  # LibRaw already applies the camera orientation
    else:
        im = ImageOps.exif_transpose(Image.open(p)).convert("RGB")
    im = ImageOps.fit(im, SIZES[name], method=Image.LANCZOS, centering=(0.5, 0.45))
    im = im.filter(soft)
    out = OUT / f"{name}.webp"; im.save(out, quality=76, method=6)
    print(f"{name:16} {out.stat().st_size//1024:5d}KB  <- {Path(raw or p).name}")
