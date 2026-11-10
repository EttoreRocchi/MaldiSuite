"""Generate the MaldiSuite logo family: SVG masters and PNG exports.

Usage:
    python tools/build_logos.py FONT

FONT is the variable TTF of Instrument Sans (SIL Open Font License), the typeface
of the website: https://github.com/google/fonts/tree/main/ofl/instrumentsans
Needs fonttools, uharfbuzz and cairosvg. Text is converted to outlines, so neither
the SVG nor the PNG files need the font.

Every package is a hexagon in its own colour, with the same spectrum below a
motif of its own; MaldiSuite is the three hexagons joined. In the wordmarks "Maldi"
is teal, the package word takes the colour of the package and "Kit" is neutral.
Each package logo has a light and a dark version, whose wordmarks use the light
and dark colours of the website, a horizontal lockup for navigation bars and an
SVG favicon.

Writes assets/logos/*.svg, assets/*_logo*.png and assets/web/*.png. The package
repositories and the profile README keep their own copies (see NOTE.md).
"""

import math
import random
import sys
from io import BytesIO
from itertools import pairwise
from pathlib import Path

import cairosvg
import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parent.parent

TEAL = "#12829a"
GREEN = "#4f9a2c"
TEAL_DARK = "#4fc9d6"  # brand colours of the website's dark theme
GREEN_DARK = "#8fcf62"

# hexagon gradient of each package, light and deep end
PALETTE = {
    "amr": ("#2fb56a", "#0c7a55"),
    "batch": ("#a874f2", "#6330cf"),
    "deep": ("#f39a1c", "#c9500a"),
}
# wordmark colours, from the light and dark themes of the website
INK = {
    "light": {"maldi": "#0b6f82", "kit": "#3a555a", "amr": "#16884f", "batch": "#7a2fc4", "deep": "#c45f00"},
    "dark": {"maldi": "#4fc9d6", "kit": "#a9c3c7", "amr": "#2e9e60", "batch": "#9874df", "deep": "#c97a2c"},
}
KITS = {
    "maldiamrkit": ("amr", "AMR"),
    "maldibatchkit": ("batch", "Batch"),
    "maldideepkit": ("deep", "Deep"),
}
STICKS = (62, 128, 84, 208, 104, 276, 132, 186, 76, 112)

# PNG file: (SVG master, width in px, or None for the size of the master)
EXPORTS = {
    "assets/maldi_suite_logo.png": ("maldisuite", None),
    "assets/web/maldi_suite_logo.png": ("maldisuite", 300),
    "assets/web/maldi_suite_logo_dark.png": ("maldisuite_dark", 300),
    "assets/web/favicon-32.png": ("favicon", 32),
}
for _name in KITS:
    EXPORTS[f"assets/{_name}_logo.png"] = (_name, None)
    EXPORTS[f"assets/{_name}_logo_dark.png"] = (f"{_name}_dark", None)
    EXPORTS[f"assets/web/{_name}_logo.png"] = (_name, 304)
    EXPORTS[f"assets/web/{_name}_logo_dark.png"] = (f"{_name}_dark", 304)


def ntos(v):
    """Format a coordinate with at most one decimal."""
    return f"{v:.1f}".rstrip("0").rstrip(".")


class Outliner:
    """Shape text with kerning and convert it to SVG path data."""

    def __init__(self, font_path, weight):
        instance = instantiateVariableFont(
            TTFont(font_path), {"wght": weight, "wdth": 100}
        )
        buffer = BytesIO()
        instance.save(buffer)
        data = buffer.getvalue()
        self.ttf = TTFont(BytesIO(data))
        self.glyphs = self.ttf.getGlyphSet()
        self.order = self.ttf.getGlyphOrder()
        self.upm = self.ttf["head"].unitsPerEm
        self.hb_font = hb.Font(hb.Face(data))

    def shape(self, text, tracking=0):
        """Return (glyph name, x offset) pairs and the advance, in font units."""
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.hb_font, buf, {"kern": True, "liga": False})
        x, out = 0, []
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions, strict=True):
            out.append((self.order[info.codepoint], x + pos.x_offset))
            x += pos.x_advance + tracking
        return out, x - tracking

    def width(self, runs, size, tracking=0):
        """Return the width in px of the runs, shaped as one word."""
        return self.shape("".join(t for t, _ in runs), tracking)[1] * size / self.upm

    def paths(self, runs, x, y, size, tracking=0):
        """Return one <path> per coloured run, shaped as a single word."""
        shaped, _ = self.shape("".join(t for t, _ in runs), tracking)
        k = size / self.upm
        out, i = [], 0
        for run_text, colour in runs:
            pen = SVGPathPen(self.glyphs, ntos=ntos)
            for name, gx in shaped[i : i + len(run_text)]:
                self.glyphs[name].draw(TransformPen(pen, (k, 0, 0, -k, x + gx * k, y)))
            i += len(run_text)
            out.append(f'<path fill="{colour}" d="{pen.getCommands()}"/>')
        return "".join(out)


def hexagon(cx, cy, r, round_r):
    """Return a pointy-top hexagon path with rounded corners."""
    pts = [
        (cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
        for a in (-90, -30, 30, 90, 150, 210)
    ]

    def toward(p, q):
        dx, dy = q[0] - p[0], q[1] - p[1]
        n = math.hypot(dx, dy)
        return p[0] + dx / n * round_r, p[1] + dy / n * round_r

    d = []
    for i, p in enumerate(pts):
        a, b = toward(p, pts[i - 1]), toward(p, pts[(i + 1) % 6])
        d.append(
            f"{'M' if i == 0 else 'L'}{ntos(a[0])} {ntos(a[1])}"
            f"Q{ntos(p[0])} {ntos(p[1])} {ntos(b[0])} {ntos(b[1])}"
        )
    return "".join(d) + "Z"


def motif_amr():
    """Return a rod-shaped bacterium with pili, a flagellum and its DNA."""
    half, r = 44, 33
    ink = PALETTE["amr"][1]
    pili = []
    for i in range(6):
        x = -half + i * 2 * half / 5
        pili.append(f"M{ntos(x)} {-r - 3}V{-r - 15}M{ntos(x)} {r + 3}V{r + 15}")
    for deg in (150, 180, 210):
        c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
        pili.append(
            f"M{ntos(-half + (r + 3) * c)} {ntos((r + 3) * s)}"
            f"L{ntos(-half + (r + 15) * c)} {ntos((r + 15) * s)}"
        )
    return (
        '<g transform="translate(-14 0) rotate(-16)" stroke-linecap="round" '
        'fill="none">'
        f'<path d="{"".join(pili)}" stroke="#fff" stroke-width="6"/>'
        f'<path d="M{half + r - 2} 0c8 -15 17 -15 25 0s17 15 25 0" stroke="#fff" '
        'stroke-width="7"/>'
        f'<rect x="{-half - r}" y="{-r}" width="{2 * (half + r)}" height="{2 * r}" '
        f'rx="{r}" fill="#fff"/>'
        f'<path d="M-44 0c11 -22 22 -22 33 0s22 22 33 0s22 -22 22 -8" stroke="{ink}" '
        'stroke-width="7"/>'
        f'<path d="M-44 0c11 22 22 22 33 0s22 -22 33 0s22 22 22 8" stroke="{ink}" '
        'stroke-width="7" stroke-opacity=".55"/>'
        "</g>"
    )


def motif_batch():
    """Return two batch clusters merging into a single harmonised one."""
    rng = random.Random(11)

    def cluster(cx, cy, n, spread, r, opacity):
        pts, tries = [], 0
        while len(pts) < n and tries < 5000:
            tries += 1
            x, y = rng.gauss(cx, spread), rng.gauss(cy, spread)
            if all((x - a) ** 2 + (y - b) ** 2 > (2.35 * r) ** 2 for a, b in pts):
                pts.append((x, y))
        return "".join(
            f'<circle cx="{ntos(x)}" cy="{ntos(y)}" r="{r}" fill-opacity="{opacity}"/>'
            for x, y in pts
        )

    return (
        '<g fill="#fff">'
        + cluster(-76, -38, 6, 11, 6.5, 0.62)
        + cluster(-76, 38, 6, 11, 6.5, 0.62)
        + cluster(64, 0, 13, 19, 7, 1)
        + "</g>"
        '<g stroke="#fff" stroke-width="7" stroke-linecap="round" '
        'stroke-linejoin="round" fill="none">'
        '<path d="M-44 -40C-22 -38 -8 -26 8 -12"/><path d="M-44 40C-22 38 -8 26 8 12"/>'
        '<path d="M-7 -12L9 -11L8 -28"/><path d="M-7 12L9 11L8 28"/>'
        "</g>"
    )


def motif_deep():
    """Return a small three-layer network."""
    layers = ((-82, (-40, 0, 40)), (0, (-54, -18, 18, 54)), (82, (-22, 22)))
    edges = "".join(
        f"M{x0} {y0}L{x1} {y1}"
        for (x0, ys0), (x1, ys1) in pairwise(layers)
        for y0 in ys0
        for y1 in ys1
    )
    nodes = "".join(
        f'<circle cx="{x}" cy="{y}" r="{11 if j == 2 else 9.5}"/>'
        for j, (x, ys) in enumerate(layers)
        for y in ys
    )
    return (
        f'<path d="{edges}" stroke="#fff" stroke-width="3.6" stroke-opacity=".6" '
        'stroke-linecap="round"/>'
        f'<g fill="#fff">{nodes}</g>'
    )


MOTIF = {"amr": motif_amr, "batch": motif_batch, "deep": motif_deep}


def badge(key, cx, cy, r, content):
    """Return a hexagon and its gradient; content is spectrum, motif or None."""
    k = r / 200
    light, deep = PALETTE[key]
    gid = f"g-{key}"
    defs = (
        f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" '
        f'x1="{ntos(cx - 0.5 * r)}" y1="{ntos(cy - r)}" '
        f'x2="{ntos(cx + 0.5 * r)}" y2="{ntos(cy + r)}">'
        f'<stop offset="0" stop-color="{light}"/>'
        f'<stop offset="1" stop-color="{deep}"/></linearGradient>'
    )
    body = [f'<path d="{hexagon(cx, cy, r, 26 * k)}" fill="url(#{gid})"/>']
    if content is None:
        return "".join(body), defs
    body.append(
        f'<path d="{hexagon(cx, cy, r - 13 * k, 20 * k)}" fill="none" stroke="#fff" '
        f'stroke-opacity=".3" stroke-width="{ntos(4.5 * k)}"/>'
    )
    if content == "spectrum":
        base, step = cy + 90 * k, 25 * k
        x0 = cx - 4.5 * step
        d = "".join(
            f"M{ntos(x0 + i * step)} {ntos(base)}V{ntos(base - h * 0.31 * k)}"
            for i, h in enumerate(STICKS)
        )
        body.append(
            f'<path d="{d}" stroke="#fff" stroke-opacity=".95" '
            f'stroke-width="{ntos(13 * k)}" stroke-linecap="round"/>'
            f'<path d="M{ntos(cx - 122 * k)} {ntos(base + 17 * k)}'
            f'H{ntos(cx + 122 * k)}" stroke="#fff" stroke-width="{ntos(5.5 * k)}" '
            'stroke-linecap="round"/>'
        )
        my, scale = cy - 72 * k, 1.0 * k
    else:
        my, scale = cy, 1.28 * k
    body.append(
        f'<g transform="translate({ntos(cx)} {ntos(my)}) scale({scale:.3f})">'
        f"{MOTIF[key]()}</g>"
    )
    return "".join(body), defs


def emblem(cx, top, r, gap, content):
    """Return the three hexagons joined: AMR above, Batch and Deep below."""
    half_w = math.sqrt(3) / 2 * r
    row = 1.5 * r + gap * math.sqrt(3) / 2
    places = (
        ("amr", cx, top),
        ("batch", cx - half_w - gap / 2, top + row),
        ("deep", cx + half_w + gap / 2, top + row),
    )
    parts = [badge(key, x, y, r, content) for key, x, y in places]
    return "".join(p[0] for p in parts), "".join(p[1] for p in parts)


def svg_doc(width, height, title, body, defs=""):
    """Return a complete SVG document."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{title}">'
        f"<title>{title}</title><defs>{defs}</defs>{body}</svg>\n"
    )


def wordmark(key, word, mode):
    """Return the coloured runs of a package wordmark."""
    ink = INK[mode]
    return [("Maldi", ink["maldi"]), (word, ink[key]), ("Kit", ink["kit"])]


def kit_logo(bold, key, word, mode):
    """Return a package logo: hexagon above the wordmark."""
    hexagon_svg, defs = badge(key, 500, 216, 208, "spectrum")
    runs = wordmark(key, word, mode)
    size, tracking = 128, -9
    x = 500 - bold.width(runs, size, tracking) / 2
    text = bold.paths(runs, x, 556, size, tracking)
    return svg_doc(1000, 590, f"Maldi{word}Kit logo", hexagon_svg + text, defs)


def kit_lockup(bold, key, word, mode):
    """Return a horizontal package logo for navigation bars: hexagon, then wordmark."""
    hexagon_svg, defs = badge(key, 52, 54, 46, "motif")
    runs = wordmark(key, word, mode)
    size, tracking = 58, -3
    width = round(112 + bold.width(runs, size, tracking) + 6)
    text = bold.paths(runs, 112, 75, size, tracking)
    return svg_doc(width, 108, f"Maldi{word}Kit", hexagon_svg + text, defs)


def kit_favicon(key, word):
    """Return the package hexagon with its motif, for SVG favicons."""
    body, defs = badge(key, 100, 100, 96, "motif")
    return svg_doc(200, 200, f"Maldi{word}Kit", body, defs)


def suite_logo(bold, maldi=TEAL, suite=GREEN):
    """Return the MaldiSuite logo: the emblem next to the wordmark."""
    body, defs = emblem(196, 112, 100, 9, "motif")
    runs = [("Maldi", maldi), ("Suite", suite)]
    size, tracking, x0 = 172, -11, 396
    width = round(x0 + bold.width(runs, size, tracking) + 14)
    text = bold.paths(runs, x0, 256, size, tracking)
    return svg_doc(width, 392, "MaldiSuite logo", body + text, defs)


def favicon():
    """Return the emblem without motifs, which would blur at 32 px."""
    body, defs = emblem(186, 106, 100, 12, None)
    return svg_doc(372, 372, "MaldiSuite", body, defs)


def touch_icon():
    """Return the emblem on a white square, as iOS rounds and needs no alpha."""
    body, defs = emblem(300, 196, 104, 10, "motif")
    backdrop = '<rect width="600" height="600" fill="#fff"/>'
    return svg_doc(600, 600, "MaldiSuite", backdrop + body, defs)


def main() -> None:
    """Write the SVG masters and export the PNG files."""
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    bold = Outliner(sys.argv[1], 700)
    masters = {
        "maldisuite": suite_logo(bold),
        "maldisuite_dark": suite_logo(bold, TEAL_DARK, GREEN_DARK),
        "favicon": favicon(),
    }
    for name, (key, word) in KITS.items():
        masters[name] = kit_logo(bold, key, word, "light")
        masters[f"{name}_dark"] = kit_logo(bold, key, word, "dark")
        masters[f"{name}_lockup"] = kit_lockup(bold, key, word, "light")
        masters[f"{name}_lockup_dark"] = kit_lockup(bold, key, word, "dark")
        masters[f"{name}_favicon"] = kit_favicon(key, word)

    logo_dir = ROOT / "assets" / "logos"
    logo_dir.mkdir(exist_ok=True)
    for name, svg in masters.items():
        (logo_dir / f"{name}.svg").write_text(svg, encoding="utf-8", newline="\n")
    for png, (name, width) in EXPORTS.items():
        size = {"output_width": width} if width else {}
        cairosvg.svg2png(
            bytestring=masters[name].encode(), write_to=str(ROOT / png), **size
        )
    cairosvg.svg2png(
        bytestring=touch_icon().encode(),
        write_to=str(ROOT / "assets" / "web" / "apple-touch-icon.png"),
        output_width=180,
    )
    print(f"Wrote {len(masters)} masters and {len(EXPORTS) + 1} PNG files")


if __name__ == "__main__":
    main()
