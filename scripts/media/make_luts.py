"""Build the Cauvery Peak grading LUTs (33^3 .cube, full-range RGB in/out).

  slog3_to_estate.cube   S-Log3 / S-Gamut3.Cine footage  ->  Rec.709 + house look
  rec709_to_estate.cube  Rec.709 footage and camera JPEGs ->  house look only

House look, "Shevaroy morning": gentle filmic contrast; shadows lean cool
toward the brand petrol; deep natural greens (yellow-greens pulled toward
green and slightly desaturated so the canopy never goes neon); skin hues left
alone; low-sun warmth in the highlights. Kept deliberately mild so the same
look holds across very different sources (Sony a7 III / a6400, client phones).

Usage: make_luts.py <out_dir> [--strength 1.0]
"""
import colorsys, sys
from pathlib import Path
import numpy as np

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
STRENGTH = float(sys.argv[sys.argv.index("--strength") + 1]) if "--strength" in sys.argv else 1.0
N = 33

# Sony S-Gamut3.Cine -> Rec.709 primaries (linear light)
SG3C_TO_709 = np.array([
    [1.6269474, -0.5401385, -0.0868089],
    [-0.1785155, 1.4179409, -0.2394254],
    [-0.0444361, -0.1959199, 1.2403560],
])


def slog3_to_linear(v):
    """v: full-range 0..1 RGB as ffmpeg delivers it from limited-range YUV.
    Sony's S-Log3 formula is written in absolute 10-bit code values."""
    code = v * 876.0 + 64.0
    lin = np.where(
        code >= 171.2102946929,
        (10.0 ** ((code - 420.0) / 261.5)) * (0.18 + 0.01) - 0.01,
        (code - 95.0) * 0.01125 / (171.2102946929 - 95.0),
    )
    return lin


def filmic(x, exposure=1.0):
    """Narkowicz ACES-fit tone curve on scene-linear, then display gamma."""
    x = np.maximum(x * exposure, 0)
    a, b, c, d, e = 2.51, 0.03, 2.43, 0.59, 0.14
    y = np.clip((x * (a * x + b)) / (x * (c * x + d) + e), 0, 1)
    return np.where(y <= 0.0031308, 12.92 * y, 1.055 * np.power(y, 1 / 2.4) - 0.055)


def look(rgb, k=1.0):
    """House look on display-referred 0..1 RGB (array of shape (n, 3))."""
    r = rgb.copy()
    L = r @ np.array([0.2126, 0.7152, 0.0722])
    # gentle S-curve around mid grey
    s = 0.5 + (r - 0.5) * (1.0 + 0.16 * k) - 0.10 * k * (r - 0.5) ** 3
    r = s
    # split tone: cool petrol shadows, warm low-sun highlights
    sh = ((1 - L) ** 2)[:, None]
    hi = (L ** 2)[:, None]
    r += k * (sh * np.array([-0.018, 0.004, 0.022]) + hi * np.array([0.022, 0.010, -0.016]))
    # hue work in HSV
    out = np.empty_like(r)
    for i, (R, G, B) in enumerate(np.clip(r, 0, 1)):
        h, s_, v = colorsys.rgb_to_hsv(R, G, B)
        deg = h * 360
        if 60 <= deg <= 165:                       # yellow-green .. green
            w = 1 - abs(deg - 112) / 53            # strongest in mid-green
            yellowish = max(0.0, (100 - deg) / 40)  # 60..100 = yellow-greens
            deg += k * 8 * yellowish               # pull toward green
            s_ *= 1 - k * (0.10 * yellowish + 0.04 * w)
            v *= 1 - k * 0.03 * w                  # deepen the canopy a touch
        elif 10 <= deg <= 45:                      # skin / soil: protect
            pass
        else:
            s_ *= 1 - k * 0.04
        out[i] = colorsys.hsv_to_rgb((deg % 360) / 360, min(s_, 1), min(v, 1))
    return np.clip(out, 0, 1)


def write_cube(path, fn, title):
    g = np.linspace(0, 1, N)
    # .cube order: red fastest
    b, gg, r = np.meshgrid(g, g, g, indexing="ij")
    rgb = np.stack([r.ravel(), gg.ravel(), b.ravel()], axis=1)
    res = fn(rgb)
    with open(path, "w") as f:
        f.write(f'TITLE "{title}"\nLUT_3D_SIZE {N}\nDOMAIN_MIN 0 0 0\nDOMAIN_MAX 1 1 1\n')
        for row in res:
            f.write(f"{row[0]:.6f} {row[1]:.6f} {row[2]:.6f}\n")
    print("wrote", path)


def slog3_pipeline(rgb):
    lin = slog3_to_linear(rgb) @ SG3C_TO_709.T
    disp = filmic(lin, exposure=1.2)
    return look(disp, STRENGTH)


def rec709_pipeline(rgb):
    return look(rgb, STRENGTH)


write_cube(OUT / "slog3_to_estate.cube", slog3_pipeline, "Cauvery Peak - S-Log3 to estate")
write_cube(OUT / "rec709_to_estate.cube", rec709_pipeline, "Cauvery Peak - Rec709 to estate")
