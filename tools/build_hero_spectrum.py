"""Rebuild the hero spectrum of index.html from a MaldiAMRKit example spectrum.

Usage:
    python tools/build_hero_spectrum.py [PATH_TO_SPECTRUM]

The path defaults to tools/hero_spectrum.txt, a copy of MaldiAMRKit's data/1s.txt.
Requires maldiamrkit. The raw trace (2,000-20,000 m/z) points up, the same
spectrum after the default preprocessing and 3 Da binning points down; both
are downsampled and written into the two <path> elements of the hero SVG.
"""

import re
import sys
from pathlib import Path

import numpy as np
from maldiamrkit import MaldiSpectrum

ROOT = Path(__file__).resolve().parent.parent
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "tools" / "hero_spectrum.txt"
HTML = ROOT / "index.html"

WIDTH, AXIS, RAW_HEIGHT, BIN_HEIGHT = 1000, 200, 184, 176
MZ_MIN, MZ_MAX = 2000, 20000
RAW_COLUMNS, N_BARS = 1200, 400


def x_of(mz):
    return (np.asarray(mz, dtype=float) - MZ_MIN) / (MZ_MAX - MZ_MIN) * WIDTH


def raw_path(spec):
    raw = spec.raw[(spec.raw.mass >= MZ_MIN) & (spec.raw.mass <= MZ_MAX)]
    cols = np.clip((x_of(raw.mass) / WIDTH * RAW_COLUMNS).astype(int), 0, RAW_COLUMNS - 1)
    env = np.zeros(RAW_COLUMNS)
    np.maximum.at(env, cols, raw.intensity.to_numpy(dtype=float))
    env = np.clip(env / np.percentile(env, 99.8), 0, 1)
    step = WIDTH / RAW_COLUMNS
    return "M" + " L".join(f"{i * step:.1f},{AXIS - v * RAW_HEIGHT:.1f}" for i, v in enumerate(env))


def binned_path(spec):
    binned = spec.binned
    x = x_of(binned.mass.astype(float) + 1.5)
    groups = np.clip((x / WIDTH * N_BARS).astype(int), 0, N_BARS - 1)
    bars = np.zeros(N_BARS)
    np.maximum.at(bars, groups, binned.intensity.to_numpy(dtype=float))
    bars = bars - np.percentile(bars, 25)
    bars = np.clip(bars / np.percentile(bars, 99.5), 0, 1)
    step = WIDTH / N_BARS
    return "".join(f"M{(i + 0.5) * step:.1f} {AXIS + 6} v{max(v * BIN_HEIGHT, 0.6):.1f}" for i, v in enumerate(bars))


def main():
    spec = MaldiSpectrum(str(SRC))
    raw = raw_path(spec)
    spec.preprocess()
    spec.bin(bin_width=3)
    bins = binned_path(spec)

    html = HTML.read_text()
    for cls, d in (("sp-raw", raw), ("sp-bins", bins)):
        html, n = re.subn(rf'(<path class="{cls}"[^>]*?\sd=")[^"]*(")', lambda m: m.group(1) + d + m.group(2), html)
        if n != 1:
            sys.exit(f"Expected one <path class=\"{cls}\"> in index.html, found {n}")
    HTML.write_text(html)
    print(f"Updated the hero spectrum in {HTML.name} from {SRC}")


if __name__ == "__main__":
    main()
