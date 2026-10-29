"""Index + score every real media file on the client drive (read-only).

Writes index.json and 400px thumbnails into the work dir. Skips macOS `._*`
AppleDouble stubs. Stills: sharpness (Laplacian variance on a 512px copy),
mean luminance, clipped highs/lows, perceptual hash for burst de-dupe.
Videos: ffprobe facts, a frame at 40% duration, gamma from the Sony XML sidecar.

Usage: index_media.py <source_root> <work_dir>
"""
import json, os, re, subprocess, sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

SRC, WORK = Path(sys.argv[1]), Path(sys.argv[2])
STILL = {".jpg", ".jpeg", ".heic", ".png", ".tif", ".tiff", ".dng"}
VIDEO = {".mp4", ".mov"}
(WORK / "thumbs").mkdir(parents=True, exist_ok=True)


def sid(p: Path) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", str(p.relative_to(SRC)))[-120:]


def still(p: Path):
    import numpy as np, cv2, imagehash
    from PIL import Image, ImageOps
    import pillow_heif
    pillow_heif.register_heif_opener()
    im = Image.open(p)
    if im.format == "JPEG":
        im.draft("RGB", (1024, 1024))
    exif = im.getexif()
    im = ImageOps.exif_transpose(im).convert("RGB")
    w0, h0 = Image.open(p).size
    im.thumbnail((512, 512))
    g = np.asarray(im.convert("L"), dtype=np.float32)
    sharp = float(cv2.Laplacian(g, cv2.CV_32F).var())
    rec = {
        "kind": "still", "path": str(p), "id": sid(p), "w": w0, "h": h0,
        "sharp": round(sharp, 1), "lum": round(float(g.mean()), 1),
        "clipHi": round(float((g > 250).mean()), 4), "clipLo": round(float((g < 5).mean()), 4),
        "phash": str(imagehash.phash(im)), "model": str(exif.get(272, "")), "time": str(exif.get(306, "")),
        "raw": any((p.with_suffix(s)).exists() for s in (".ARW", ".arw")),
    }
    t = im.copy(); t.thumbnail((400, 400)); t.save(WORK / "thumbs" / f"{rec['id']}.jpg", quality=78)
    return rec


def video(p: Path):
    pr = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                         "stream=width,height,r_frame_rate:format=duration", "-of", "json", str(p)],
                        capture_output=True, text=True, timeout=60)
    j = json.loads(pr.stdout or "{}")
    st = (j.get("streams") or [{}])[0]
    dur = float(j.get("format", {}).get("duration", 0) or 0)
    num, _, den = st.get("r_frame_rate", "0/1").partition("/")
    fps = round(float(num) / float(den or 1), 2) if num else 0
    gamma = ""
    for x in (p.with_name(p.stem + "M01.XML"), p.with_name(p.stem + "M01.xml")):
        if x.exists():
            m = re.search(r'CaptureGammaEquation" value="([^"]+)"', x.read_text(errors="ignore"))
            cf = re.search(r'captureFps="([^"]+)"', x.read_text(errors="ignore"))
            gamma = m.group(1) if m else ""
            if cf: fps = cf.group(1)
            break
    rec = {"kind": "video", "path": str(p), "id": sid(p), "w": st.get("width"), "h": st.get("height"),
           "fps": fps, "dur": round(dur, 2), "gamma": gamma}
    subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-ss", str(max(0.0, dur * 0.4)), "-i", str(p),
                    "-frames:v", "1", "-vf", "scale=400:-2", str(WORK / "thumbs" / f"{rec['id']}.jpg")], timeout=120)
    return rec


def work(p):
    try:
        return still(p) if p.suffix.lower() in STILL else video(p)
    except Exception as e:  # unreadable file: record and move on
        return {"kind": "error", "path": str(p), "err": str(e)[:200]}


if __name__ == "__main__":
    files = [p for p in SRC.rglob("*") if p.is_file() and not p.name.startswith("._")
             and p.suffix.lower() in STILL | VIDEO and "Packaging identity" not in str(p)]
    print(f"{len(files)} files", flush=True)
    out, done = [], 0
    with ProcessPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(work, p) for p in files]
        for f in as_completed(futs):
            out.append(f.result()); done += 1
            if done % 200 == 0:
                print(f"{done}/{len(files)}", flush=True)
                json.dump(out, open(WORK / "index.json", "w"))
    json.dump(out, open(WORK / "index.json", "w"))
    print("done", sum(r["kind"] == "error" for r in out), "errors", flush=True)
