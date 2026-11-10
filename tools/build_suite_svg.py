"""Generate assets/suite_packages.svg, the animated figure of the README.

Usage:
    python tools/build_suite_svg.py [OUTPUT]

Needs only the standard library. Three cards, one per package and in no particular
order: a spotlight moves from card to card, and each card shows in turn three things
its package offers. Spectra, samples, scores and probabilities are synthetic (fixed
seed, so the output is reproducible): they illustrate the packages, they are not
results.

The animation is pure SMIL: GitHub shows README images through <img>, where
JavaScript and external files do not run. For the same reason text colours are
mid-tones readable on both themes: inside <img>, prefers-color-scheme follows the
operating system, not the GitHub theme.
"""

import math
import random
import sys
from itertools import pairwise
from pathlib import Path

DEFAULT_OUT = Path(__file__).resolve().parent.parent / "assets" / "suite_packages.svg"

TXT = "#6e7781"  # text, about 4.5:1 on white and 4.2:1 on #0d1117
GREY = "#7d8590"  # strokes and shapes
R_C = "#D55E00"  # Resistant, as in the MaldiAMRKit and MaldiDeepKit figures
S_C = "#009E73"  # Susceptible, as in the MaldiAMRKit and MaldiDeepKit figures
SITE_FILL = ["#E69F00", "#56B4E9", "#009E73"]  # as in the MaldiBatchKit figure
SITE_EDGE = ["#B07A00", "#2F8BC0", "#00775A"]
# package: (text colour, gradient light end, gradient deep end), as in the logos
AMR = ("#16884f", "#2fb56a", "#0c7a55")
BATCH = ("#8f55dc", "#a874f2", "#6330cf")
DEEP = ("#c45f00", "#f39a1c", "#c9500a")

TEMPO = 1.5  # real seconds per second of the timeline below: raise it to slow down
LEAD = 0.2  # start of the first scene (s)
SCENE = 2.0  # duration of a scene (s)
TURN = 3 * SCENE  # time a card keeps the spotlight (s)
FADE = 0.2
DUR = LEAD + 3 * TURN + 0.4  # loop duration (s)
RESET = SCENE + 0.3  # a scene rewinds this long after its start, once hidden

CARD_X = (16, 277, 538)
CARD_Y, CARD_W, CARD_H = 8, 246, 336
PAD = 12
STAGE_Y = CARD_Y + 58
STAGE_W = CARD_W - 2 * PAD
ROW_Y = (CARD_Y + 252, CARD_Y + 273, CARD_Y + 294)
PIP_Y = CARD_Y + 325
INSTALL_Y = 366

EASE = "0.42 0 0.58 1"
LINEAR = "0 0 1 1"

rng = random.Random(20261109)


def num(v):
    """Format a number with at most two decimals."""
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def key_time(t):
    """Convert a time in seconds to a SMIL keyTimes value."""
    if t <= 0:
        return "0"
    if t >= DUR:
        return "1"
    return f"{t / DUR:.4f}".rstrip("0").rstrip(".")


def anim(attr, keyframes, tag="animate", extra=""):
    """Return a SMIL animation from absolute (time, value) keyframes."""
    kfs = list(keyframes)
    if kfs[0][0] > 0:
        kfs.insert(0, (0.0, kfs[0][1]))
    if kfs[-1][0] < DUR:
        kfs.append((DUR, kfs[-1][1]))
    # two keyframes at the same time (a scene starting with the loop) count as one
    kfs = [
        kf
        for kf, nxt in zip(kfs, [*kfs[1:], None], strict=True)
        if not nxt or nxt[0] - kf[0] > 1e-9
    ]
    for (ta, _), (tb, _) in pairwise(kfs):
        if tb <= ta:
            raise ValueError(f"keyframes of {attr} are not increasing: {kfs}")
    vals = []
    for _, v in kfs:
        if isinstance(v, tuple):
            vals.append(" ".join(num(x) for x in v))
        else:
            vals.append(v if isinstance(v, str) else num(v))
    splines = [LINEAR if a == b else EASE for a, b in pairwise(vals)]
    extra = f" {extra}" if extra else ""
    return (
        f'<{tag} attributeName="{attr}"{extra} dur="{num(DUR * TEMPO)}s" '
        'repeatCount="indefinite" calcMode="spline" '
        f'keyTimes="{";".join(key_time(t) for t, _ in kfs)}" '
        f'keySplines="{";".join(splines)}" values="{";".join(vals)}"/>'
    )


def rel(t0, pairs):
    """Shift (time, value) keyframes by t0."""
    return [(t0 + dt, v) for dt, v in pairs]


def opacity(keyframes):
    """Return an opacity animation."""
    return anim("opacity", keyframes)


def translate(keyframes):
    """Return a translate animation."""
    return anim("transform", keyframes, "animateTransform", 'type="translate"')


def scale(keyframes):
    """Return a scale animation."""
    return anim("transform", keyframes, "animateTransform", 'type="scale"')


def motion(path, t0, t1):
    """Return an animateMotion along path during [t0, t1], parked otherwise."""
    times = ";".join(key_time(t) for t in (0, t0, t1, DUR))
    return (
        f'<animateMotion dur="{num(DUR * TEMPO)}s" repeatCount="indefinite" calcMode="linear" '
        f'path="{path}" keyTimes="{times}" keyPoints="0;0;1;1"/>'
    )


def appear(t0, pairs):
    """Return an opacity that rises at the given offsets and rewinds once hidden."""
    return opacity(
        rel(t0, [*pairs, (RESET, pairs[-1][1]), (RESET + 0.05, pairs[0][1])])
    )


def pop(x, y, t, inner):
    """Return content that pops up at time t and disappears once its scene is hidden."""
    t0 = t[0] + t[1]
    return (
        f'<g transform="translate({num(x)} {num(y)})"><g transform="scale(.001)">'
        + scale(
            [
                (0, 0.001),
                (t0, 0.001),
                (t0 + 0.16, 1.2),
                (t0 + 0.3, 1),
                (t[0] + RESET, 1),
                (t[0] + RESET + 0.05, 0.001),
            ]
        )
        + inner
        + "</g></g>"
    )


def grow(t0, start, end, width):
    """Return a width animation from 0 between two offsets, rewinding once hidden."""
    return anim(
        "width",
        rel(
            t0,
            [(start, 0), (end, width), (RESET, width), (RESET + 0.05, 0)],
        ),
    )


def polyline(xs, ys):
    """Return a relative polyline, so that morph keyframes share one structure."""
    ax = [round(x * 10) for x in xs]
    ay = [round(y * 10) for y in ys]
    moves = " ".join(
        f"{num((ax[i] - ax[i - 1]) / 10)},{num((ay[i] - ay[i - 1]) / 10)}"
        for i in range(1, len(ax))
    )
    return f"M{num(ax[0] / 10)},{num(ay[0] / 10)}l{moves}"


def signal(u):
    """Return a clean synthetic spectrum at the relative position u in [0, 1]."""
    peaks = (
        (0.031, 0.26, 0.005),
        (0.063, 0.42, 0.005),
        (0.131, 0.64, 0.006),
        (0.172, 0.48, 0.006),
        (0.236, 0.95, 0.007),
        (0.287, 0.36, 0.007),
        (0.317, 0.28, 0.007),
        (0.392, 0.56, 0.008),
        (0.419, 0.24, 0.008),
        (0.461, 0.42, 0.009),
        (0.543, 0.22, 0.01),
        (0.617, 0.15, 0.011),
        (0.72, 0.1, 0.013),
        (0.87, 0.05, 0.014),
    )
    return sum(h * math.exp(-0.5 * ((u - c) / s) ** 2) for c, h, s in peaks)


def drift(u):
    """Return the drifting baseline at the relative position u in [0, 1]."""
    return 0.05 + 0.3 * math.exp(-u * 4.2)


def scene_preprocess(x0, y0, t0):
    """Return a raw spectrum that becomes clean, then binned."""
    base, height = y0 + 150, 116.0
    n = 91
    us = [i / (n - 1) for i in range(n)]
    xs = [x0 + u * STAGE_W for u in us]
    raw = polyline(
        xs,
        [
            base
            - height
            * (signal(u) + drift(u) + rng.gauss(0, 0.02 + 0.05 * math.sqrt(signal(u))))
            for u in us
        ],
    )
    clean = polyline(xs, [base - height * signal(u) for u in us])
    n_bars = 36
    bar_w = STAGE_W / n_bars
    values = [
        max(max(signal((b + k / 6) / n_bars) for k in range(7)), 0.012)
        for b in range(n_bars)
    ]
    top = max(values)
    bars = "".join(
        f'<rect x="{num(x0 + b * bar_w + 0.7)}" y="{num(base - v * height)}" '
        f'width="{num(bar_w - 1.4)}" height="{num(v * height)}" rx=".8"/>'
        for b, v in enumerate(values)
    )
    strip = "".join(
        f'<rect x="{num(x0 + b * bar_w + 0.4)}" y="{base + 6}" '
        f'width="{num(bar_w - 0.8)}" height="10" '
        f'fill-opacity="{num(0.08 + 0.92 * (v / top) ** 0.6)}"/>'
        for b, v in enumerate(values)
    )
    x1 = x0 + STAGE_W
    return (
        f'<clipPath id="wipe"><rect x="{x0}" y="{y0 - 4}" width="0" '
        f'height="{base - y0 + 6}">'
        + grow(t0, 0.95, 1.55, STAGE_W)
        + "</rect></clipPath>"
        f'<path d="M{x0} {base}H{x1}" stroke="{GREY}" stroke-opacity=".7"/>'
        f'<g clip-path="url(#wipe)" fill="url(#v-amr)">{bars}</g>'
        f'<path d="{raw}" stroke="{AMR[0]}" stroke-width="1.3" stroke-linejoin="round">'
        + anim(
            "d",
            rel(t0, [(0.25, raw), (0.85, clean), (RESET, clean), (RESET + 0.05, raw)]),
        )
        + opacity(rel(t0, [(1.1, 1), (1.5, 0.15), (RESET, 0.15), (RESET + 0.05, 1)]))
        + "</path>"
        f'<g fill="{AMR[0]}" opacity="0">'
        + appear(t0, [(1.4, 0), (1.7, 1)])
        + strip
        + "</g>"
        f'<rect x="{x0}" y="{base - 124}" width="2" height="124" fill="{AMR[1]}" '
        'opacity="0">'
        + anim(
            "x",
            rel(
                t0,
                [(0.25, x0), (0.85, x1), (0.9, x0), (0.95, x0), (1.55, x1), (1.6, x0)],
            ),
        )
        + opacity(
            rel(
                t0,
                [
                    (0.23, 0),
                    (0.27, 0.9),
                    (0.83, 0.9),
                    (0.87, 0),
                    (0.93, 0),
                    (0.97, 0.9),
                    (1.53, 0.9),
                    (1.57, 0),
                ],
            )
        )
        + "</rect>"
    )


def scene_align(x0, y0, t0):
    """Return three shifted spectra whose peaks align onto common positions."""
    n = 76
    us = [i / (n - 1) for i in range(n)]
    xs = [x0 + u * STAGE_W for u in us]
    main = (0.131, 0.236, 0.392, 0.461)
    guides = "".join(f"M{num(x0 + c * STAGE_W)} {y0 + 2}V{y0 + 168}" for c in main)
    out = [
        f'<path d="{guides}" stroke="{GREY}" stroke-dasharray="2 3" opacity="0">'
        + appear(t0, [(1.05, 0), (1.3, 1)])
        + "</path>"
    ]
    rows = ((y0 + 52, 0.022, 0.55), (y0 + 110, -0.018, 0.8), (y0 + 168, 0.012, 1))
    for base, shift, alpha in rows:
        wobble = [signal(u + shift + 0.008 * math.sin(2 * math.pi * u)) for u in us]
        shifted = polyline(xs, [base - v * 46 for v in wobble])
        aligned = polyline(xs, [base - signal(u) * 46 for u in us])
        out.append(
            f'<path d="{shifted}" stroke="{AMR[0]}" stroke-opacity="{alpha}" '
            'stroke-width="1.3" stroke-linejoin="round">'
            + anim(
                "d",
                rel(
                    t0,
                    [
                        (0.3, shifted),
                        (1.1, aligned),
                        (RESET, aligned),
                        (RESET + 0.05, shifted),
                    ],
                ),
            )
            + "</path>"
        )
    return "".join(out)


def scene_mic(x0, y0, t0):
    """Return MIC values read against breakpoints as R / S categories."""
    rows = (
        ("Ciprofloxacin", "4", "R", R_C),
        ("Ceftriaxone", "8", "R", R_C),
        ("Meropenem", "≤0.25", "S", S_C),
    )
    out = [
        (
            f'<g class="tx lb"><text x="{x0}" y="{y0 + 14}">drug</text>'
            f'<text x="{x0 + 138}" y="{y0 + 14}" text-anchor="end">MIC (mg/L)</text>'
            f'<text x="{x0 + 200}" y="{y0 + 14}" text-anchor="middle">EUCAST</text></g>'
        )
    ]
    for k, (drug, mic, cat, colour) in enumerate(rows):
        y = y0 + 58 + 46 * k
        out.append(
            f'<text class="tx bd" x="{x0}" y="{y}">{drug}</text>'
            f'<text class="tx cm" x="{x0 + 138}" y="{y}" text-anchor="end">{mic}</text>'
            f'<path d="M{x0 + 150} {y - 4.5}H{x0 + 172}m-5 -3.5l5 3.5l-5 3.5" '
            f'stroke="{GREY}" stroke-width="1.4" stroke-linecap="round" '
            'stroke-linejoin="round"/>'
            + pop(
                x0 + 200,
                y - 4.5,
                (t0, 0.35 + 0.35 * k),
                f'<rect x="-19" y="-13" width="38" height="26" rx="13" fill="{colour}"/>'
                f'<text class="pl2" y="4.6" text-anchor="middle" fill="#fff">{cat}</text>',
            )
        )
    return "".join(out)


def relax(points, key, min_d=16.0, iters=300):
    """Push overlapping markers apart, keeping them inside the plot."""
    for _ in range(iters):
        moved = False
        for i, p in enumerate(points):
            for q in points[i + 1 :]:
                dx, dy = q[key][0] - p[key][0], q[key][1] - p[key][1]
                d = math.hypot(dx, dy) or 1.0
                if d < min_d:
                    push = (min_d - d) / 2 * 0.6
                    p[key][0] -= dx / d * push
                    p[key][1] -= dy / d * push
                    q[key][0] += dx / d * push
                    q[key][1] += dy / d * push
                    moved = True
        for pt in points:
            pt[key][0] = min(max(pt[key][0], 12), STAGE_W - 10)
            pt[key][1] = min(max(pt[key][1], 10), 154)
        if not moved:
            break


def make_samples():
    """Return 18 samples clustered by site (a) and by species (b)."""
    site_centres = [(50, 42), (112, 122), (178, 40)]
    species_centres = [(46, 118), (112, 40), (180, 118)]
    species_offset = [(-11, -8), (11, -8), (0, 11)]
    samples = []
    for site in range(3):
        for species in range(3):
            for _ in range(2):
                ox, oy = species_offset[species]
                sx, sy = site_centres[site]
                bx, by = species_centres[species]
                samples.append(
                    {
                        "site": site,
                        "species": species,
                        "a": [sx + ox + rng.gauss(0, 7), sy + oy + rng.gauss(0, 7)],
                        "b": [bx + rng.gauss(0, 15), by + rng.gauss(0, 14)],
                    }
                )
    rng.shuffle(samples)  # interleave the draw order, so no colour sits on top
    relax(samples, "a")
    relax(samples, "b")
    for s in samples:
        s["delay"] = rng.uniform(0, 0.25)
    return samples


def ellipse(points, pad):
    """Return centre and radii of an ellipse around the points."""
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    return (
        (max(xs) + min(xs)) / 2,
        (max(ys) + min(ys)) / 2,
        (max(xs) - min(xs)) / 2 + pad,
        (max(ys) - min(ys)) / 2 + pad,
    )


def marker(species, fill, edge):
    """Return the shape of a species, centred on the origin."""
    style = f'fill="{fill}" stroke="{edge}"'
    if species == 0:
        return f'<circle r="5" {style}/>'
    if species == 1:
        return f'<polygon points="0,-6.6 5.8,3.4 -5.8,3.4" {style}/>'
    return f'<rect x="-4.4" y="-4.4" width="8.8" height="8.8" rx="1.4" {style}/>'


def scene_correct(x0, y0, t0):
    """Return the samples moving from site clusters to species clusters."""
    samples = make_samples()
    out = [
        (
            f'<path d="M{x0} {y0}V{y0 + 168}H{x0 + STAGE_W}" stroke="{GREY}" '
            'stroke-opacity=".7"/>'
        )
    ]
    halos = []
    for site in range(3):
        cx, cy, rx, ry = ellipse([s["a"] for s in samples if s["site"] == site], 10)
        halos.append(
            f'<ellipse cx="{num(x0 + cx)}" cy="{num(y0 + cy)}" rx="{num(rx)}" '
            f'ry="{num(ry)}" fill="{SITE_FILL[site]}"/>'
        )
    out.append(
        '<g fill-opacity=".16">'
        + "".join(halos)
        + opacity(rel(t0, [(0.3, 1), (0.8, 0), (RESET, 0), (RESET + 0.05, 1)]))
        + "</g>"
    )
    outlines = []
    for species in range(3):
        cx, cy, rx, ry = ellipse(
            [s["b"] for s in samples if s["species"] == species], 10
        )
        outlines.append(
            f'<ellipse cx="{num(x0 + cx)}" cy="{num(y0 + cy)}" rx="{num(rx)}" '
            f'ry="{num(ry)}"/>'
        )
    out.append(
        f'<g fill="{GREY}" fill-opacity=".08" stroke="{GREY}" stroke-opacity=".7" '
        'stroke-dasharray="3 3" opacity="0">'
        + "".join(outlines)
        + appear(t0, [(1.2, 0), (1.6, 1)])
        + "</g>"
    )
    for s in samples:
        a = (x0 + s["a"][0], y0 + s["a"][1])
        b = (x0 + s["b"][0], y0 + s["b"][1])
        out.append(
            f'<g transform="translate({num(a[0])} {num(a[1])})">'
            + marker(s["species"], SITE_FILL[s["site"]], SITE_EDGE[s["site"]])
            + translate(
                rel(
                    t0,
                    [
                        (0.3 + s["delay"], a),
                        (1.35 + s["delay"], b),
                        (RESET, b),
                        (RESET + 0.05, a),
                    ],
                )
            )
            + "</g>"
        )
    return "".join(out)


def scene_diagnose(x0, y0, t0):
    """Return kBET and LISI bars before and after a correction."""
    bw = STAGE_W
    out = [
        (
            f'<text class="tx lb" x="{x0}" y="{y0 + 14}">mixing of sites</text>'
            f'<rect x="{x0 + 122}" y="{y0 + 5}" width="10" height="10" rx="2" fill="{GREY}" '
            'fill-opacity=".55"/>'
            f'<text class="tx lb" x="{x0 + 136}" y="{y0 + 14}">before</text>'
            f'<rect x="{x0 + 178}" y="{y0 + 5}" width="10" height="10" rx="2" '
            'fill="url(#v-batch)"/>'
            f'<text class="tx lb" x="{x0 + 192}" y="{y0 + 14}">after</text>'
        )
    ]
    groups = (("kBET", y0 + 46, 0.24, 0.82), ("LISI", y0 + 112, 0.31, 0.76))
    for name, y, before, after in groups:
        out.append(
            f'<text class="tx bd" x="{x0}" y="{y}" font-weight="600">{name}</text>'
            f'<rect x="{x0}" y="{y + 8}" width="{bw}" height="15" rx="4" fill="{GREY}" '
            'fill-opacity=".14"/>'
            f'<rect x="{x0}" y="{y + 27}" width="{bw}" height="15" rx="4" fill="{GREY}" '
            'fill-opacity=".14"/>'
            f'<rect x="{x0}" y="{y + 8}" width="0" height="15" rx="4" fill="{GREY}" '
            'fill-opacity=".55">' + grow(t0, 0.2, 0.7, before * bw) + "</rect>"
            f'<rect x="{x0}" y="{y + 27}" width="0" height="15" rx="4" '
            'fill="url(#h-batch)">' + grow(t0, 0.8, 1.45, after * bw) + "</rect>"
        )
    return "".join(out)


def scene_tune(x0, y0, t0):
    """Return correctors compared as a hyperparameter, the best one marked."""
    rows = (
        ("combat", 0.62),
        ("limma", 0.48),
        ("harmony", 0.71),
        ("species-combat", 0.84),
    )
    bx, bw = x0 + 114, 78
    ys = [y0 + 30 + 35 * k for k in range(4)]
    out = [
        f'<text class="tx lb" x="{x0}" y="{y0 + 14}">GridSearchCV over method</text>',
        f'<rect x="{x0 - 5}" y="{ys[0]}" width="{STAGE_W + 10}" height="30" rx="7" '
        f'fill="{BATCH[0]}" fill-opacity=".14" stroke="{BATCH[0]}" stroke-opacity=".6">'
        + anim(
            "y",
            rel(
                t0,
                [
                    (0.15, ys[0]),
                    (0.4, ys[1]),
                    (0.65, ys[2]),
                    (0.9, ys[3]),
                    (RESET, ys[3]),
                    (RESET + 0.05, ys[0]),
                ],
            ),
        )
        + "</rect>",
    ]
    for k, (name, score) in enumerate(rows):
        y = ys[k]
        fill = f'fill="{BATCH[0]}"' if k == 3 else f'fill="{GREY}" fill-opacity=".6"'
        out.append(
            f'<text class="tx cm" x="{x0 + 3}" y="{y + 19.5}">{name}</text>'
            f'<rect x="{bx}" y="{y + 8}" width="{bw}" height="14" rx="4" fill="{GREY}" '
            'fill-opacity=".14"/>'
            f'<rect x="{bx}" y="{y + 8}" width="0" height="14" rx="4" {fill}>'
            + grow(t0, 0.15 + 0.25 * k, 0.45 + 0.25 * k, score * bw)
            + "</rect>"
        )
    out.append(
        pop(
            x0 + STAGE_W - 11,
            ys[3] + 15,
            (t0, 1.15),
            f'<circle r="10" fill="{BATCH[0]}"/><path d="M-4.4 .3L-1.3 3.4L4.5 -3.3" '
            'stroke="#fff" stroke-width="2.1" stroke-linecap="round" '
            'stroke-linejoin="round"/>',
        )
    )
    return "".join(out)


def schematic_mlp(c):
    """Return a small fully connected network."""
    layers = ((10, (6, 24, 42)), (46, (0, 16, 32, 48)), (82, (13, 35)))
    edges = "".join(
        f"M{x0} {y0}L{x1} {y1}"
        for (x0, ys0), (x1, ys1) in pairwise(layers)
        for y0 in ys0
        for y1 in ys1
    )
    nodes = "".join(
        f'<circle cx="{x}" cy="{y}" r="3.4"/>' for x, ys in layers for y in ys
    )
    return (
        f'<path d="{edges}" stroke="{c}" stroke-width=".8" stroke-opacity=".6"/>'
        f'<g fill="{c}">{nodes}</g>'
    )


def schematic_cnn(c):
    """Return a kernel over a spectrum and the feature maps it produces."""
    xs = [i * 1.1 for i in range(46)]
    ys = [47 - 42 * signal(0.1 + i / 100) for i in range(46)]
    cells = "".join(
        f'<rect x="{66 + 6.2 * i}" y="{2 + 16 * r}" width="5.2" height="13" rx="1" '
        f'fill="{c}" fill-opacity="{num(0.3 + 0.7 * ((i * 3 + r * 5) % 7) / 6)}"/>'
        for i in range(4)
        for r in range(3)
    )
    return (
        f'<path d="{polyline(xs, ys)}" stroke="{c}" stroke-linejoin="round"/>'
        f'<rect x="14" y="1" width="13" height="47" rx="2.5" stroke="{c}" '
        'stroke-dasharray="2.5 2.5"/>'
        f'<path d="M53 25h8m-3 -3l3 3l-3 3" stroke="{c}" stroke-linecap="round"/>{cells}'
    )


def schematic_resnet(c):
    """Return convolution blocks bridged by skip connections."""
    blocks = "".join(
        f'<rect x="{x}" y="29" width="13" height="14" rx="2" fill="{c}" '
        'fill-opacity=".3"/>'
        for x in (7, 23, 50, 66)
    )
    adds = "".join(
        f'<circle cx="{x}" cy="36" r="4.4" stroke="{c}"/>'
        f'<path d="M{x - 2.4} 36H{x + 2.4}M{x} 33.6V38.4" stroke="{c}"/>'
        for x in (43, 86)
    )
    return (
        f'<path d="M0 36H90" stroke="{c}"/>'
        f'<path d="M3 35C3 4 43 4 43 31M46 35C46 4 86 4 86 31" stroke="{c}"/>'
        + blocks
        + adds
    )


def schematic_vit(c):
    """Return spectrum tokens linked by self-attention."""
    tokens = "".join(
        f'<rect x="{x}" y="36" width="12" height="12" rx="2.4" fill="{c}" '
        'fill-opacity=".45"/>'
        for x in (6, 28, 50, 72)
    )
    arcs = "".join(
        f"M{a} 34Q{(a + b) / 2} {34 - 2 * h} {b} 34"
        for a, b, h in (
            (12, 34, 12),
            (34, 56, 12),
            (56, 78, 12),
            (12, 56, 24),
            (34, 78, 24),
        )
    )
    return f'<path d="{arcs}" stroke="{c}" stroke-width=".95"/>{tokens}'


def scene_backbones(x0, y0, t0):
    """Return the four backbones, lighting up in turn."""
    w, h = 107, 80
    tiles = (
        ("MLP", schematic_mlp, x0, y0 + 2),
        ("1-D CNN", schematic_cnn, x0 + 115, y0 + 2),
        ("1-D ResNet", schematic_resnet, x0, y0 + 90),
        ("1-D ViT", schematic_vit, x0 + 115, y0 + 90),
    )
    out = []
    for k, (name, draw, x, y) in enumerate(tiles):
        t = 0.1 + 0.45 * k
        out.append(
            f'<g transform="translate({x} {y})">'
            f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="7" fill="{GREY}" '
            f'fill-opacity=".07" stroke="{GREY}" stroke-opacity=".45"/>'
            f'<text class="tx lb2" x="9" y="15">{name}</text>'
            f'<g transform="translate(8 24)">{draw(GREY)}</g>'
            '<g opacity="0">'
            + opacity(
                rel(
                    t0,
                    [
                        (t, 0),
                        (t + 0.12, 1),
                        (t + 0.45, 1),
                        (t + 0.6, 0.45),
                        (RESET, 0.45),
                        (RESET + 0.05, 0),
                    ],
                )
            )
            + f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="7" '
            f'fill="{DEEP[0]}" fill-opacity=".1" stroke="{DEEP[0]}" stroke-width="1.4"/>'
            f'<text class="lb2" x="9" y="15" fill="{DEEP[0]}">{name}</text>'
            f'<g transform="translate(8 24)">{draw(DEEP[0])}</g></g></g>'
        )
    return "".join(out)


def scene_uncertainty(x0, y0, t0):
    """Return predictions with their uncertainty and conformal prediction sets."""
    ax0, ax_w = x0 + 58, 100
    axis_y = y0 + 150
    rows = (
        ("isolate 1", 0.88, 0.07, ("R",)),
        ("isolate 2", 0.55, 0.2, ("R", "S")),
        ("isolate 3", 0.12, 0.08, ("S",)),
    )
    mid = ax0 + ax_w / 2
    out = [
        (
            f'<text class="tx lb" x="{ax0}" y="{y0 + 14}">P(Resistant)</text>'
            f'<text class="tx lb" x="{x0 + STAGE_W}" y="{y0 + 14}" text-anchor="end">'
            "prediction set</text>"
            f'<path d="M{ax0} {axis_y}H{ax0 + ax_w}" stroke="{GREY}" stroke-opacity=".7"/>'
            f'<path d="M{mid} {y0 + 24}V{axis_y}" stroke="{GREY}" stroke-dasharray="2 3"/>'
            f'<g class="tx lb" text-anchor="middle"><text x="{ax0}" y="{axis_y + 15}">0</text>'
            f'<text x="{mid}" y="{axis_y + 15}">0.5</text>'
            f'<text x="{ax0 + ax_w}" y="{axis_y + 15}">1</text></g>'
        )
    ]
    for k, (name, p, err, cats) in enumerate(rows):
        y = y0 + 48 + 38 * k
        x = ax0 + p * ax_w
        half = err * ax_w
        out.append(
            f'<text class="tx lb" x="{x0}" y="{y + 3.5}">{name}</text>'
            f'<rect x="{num(x)}" y="{y - 2.5}" width="0" height="5" rx="2.5" '
            f'fill="{DEEP[0]}" fill-opacity=".6">'
            + anim(
                "width",
                rel(
                    t0,
                    [(0.35, 0), (0.9, 2 * half), (RESET, 2 * half), (RESET + 0.05, 0)],
                ),
            )
            + anim(
                "x",
                rel(
                    t0,
                    [(0.35, x), (0.9, x - half), (RESET, x - half), (RESET + 0.05, x)],
                ),
            )
            + "</rect>"
            f'<circle cx="{num(x)}" cy="{y}" r="6" fill="url(#v-deep)"/>'
        )
        for i, cat in enumerate(reversed(cats)):
            colour = R_C if cat == "R" else S_C
            out.append(
                pop(
                    x0 + STAGE_W - 11 - 25 * i,
                    y,
                    (t0, 1.0 + 0.15 * k),
                    f'<circle r="10.5" fill="{colour}"/>'
                    f'<text class="pl2" y="4.6" text-anchor="middle" fill="#fff">{cat}'
                    "</text>",
                )
            )
    return "".join(out)


def scene_dual(x0, y0, t0):
    """Return a spectrum and side features merging into one classifier."""
    n = 44
    us = [i / (n - 1) for i in range(n)]
    xs = [x0 + u * 82 for u in us]
    trace = polyline(xs, [y0 + 76 - 50 * signal(u * 0.55) for u in us])
    bits = "".join(
        f'<rect x="{x0 + 7 * i}" y="{y0 + 122}" width="5.8" height="32" rx="1.2" '
        f'fill-opacity="{0.85 if (i * 7 + 3) % 5 < 2 else 0.2}"/>'
        for i in range(12)
    )
    fx, fy = x0 + 132, y0 + 96
    top = f"M{x0 + 88} {y0 + 56}C{x0 + 108} {y0 + 56} {x0 + 100} {fy} {fx - 15} {fy}"
    low = f"M{x0 + 88} {y0 + 138}C{x0 + 108} {y0 + 138} {x0 + 100} {fy} {fx - 15} {fy}"
    out_path = f"M{fx + 15} {fy}H{fx + 34}"
    out = [
        f'<text class="tx lb" x="{x0}" y="{y0 + 14}">spectrum</text>',
        f'<path d="{trace}" stroke="{DEEP[0]}" stroke-width="1.3" stroke-linejoin="round"/>',
        f'<text class="tx lb" x="{x0}" y="{y0 + 112}">side features</text>',
        f'<g fill="{DEEP[0]}">{bits}</g>',
        (
            f'<path d="{top}{low}{out_path}" stroke="{GREY}" stroke-width="1.4" '
            'stroke-opacity=".7"/>'
        ),
        (
            f'<circle cx="{fx}" cy="{fy}" r="15" fill="url(#v-deep)"/>'
            f'<path d="M{fx - 6} {fy}H{fx + 6}M{fx} {fy - 6}V{fy + 6}" stroke="#fff" '
            'stroke-width="2.4" stroke-linecap="round"/>'
        ),
    ]
    for path, start, end in ((top, 0.25, 0.8), (low, 0.25, 0.8), (out_path, 0.9, 1.15)):
        out.append(
            f'<circle r="4" fill="{DEEP[1]}" opacity="0">'
            + motion(path, t0 + start, t0 + end)
            + opacity(
                rel(t0, [(start, 0), (start + 0.03, 1), (end - 0.03, 1), (end, 0)])
            )
            + "</circle>"
        )
    bx, bw = x0 + 184, 38
    for letter, colour, y, p in (("R", R_C, fy - 25, 0.84), ("S", S_C, fy + 11, 0.16)):
        out.append(
            f'<text class="lt" x="{x0 + 171}" y="{y + 11.5}" fill="{colour}">{letter}</text>'
            f'<rect x="{bx}" y="{y}" width="{bw}" height="14" rx="4" fill="{GREY}" '
            'fill-opacity=".16"/>'
            f'<rect x="{bx}" y="{y}" width="0" height="14" rx="4" fill="{colour}">'
            + grow(t0, 1.15, 1.6, p * bw)
            + "</rect>"
        )
    return "".join(out)


def hexagon_path(r):
    """Return a pointy-top hexagon with rounded corners, centred on the origin."""
    pts = [
        (r * math.cos(math.radians(a)), r * math.sin(math.radians(a)))
        for a in (-90, -30, 30, 90, 150, 210)
    ]
    round_r = 0.13 * r

    def toward(p, q):
        dx, dy = q[0] - p[0], q[1] - p[1]
        n = math.hypot(dx, dy)
        return p[0] + dx / n * round_r, p[1] + dy / n * round_r

    d = []
    for i, p in enumerate(pts):
        a, b = toward(p, pts[i - 1]), toward(p, pts[(i + 1) % 6])
        d.append(
            f"{'M' if i == 0 else 'L'}{num(a[0])} {num(a[1])}"
            f"Q{num(p[0])} {num(p[1])} {num(b[0])} {num(b[1])}"
        )
    return "".join(d) + "Z"


def motif_amr(ink):
    """Return the bacterium of the MaldiAMRKit logo, without its finest details."""
    return (
        '<g transform="translate(-12 0) rotate(-16)" stroke-linecap="round" '
        'fill="none" stroke="#fff">'
        '<path d="M75 0c8 -15 17 -15 25 0s17 15 25 0" stroke-width="9"/>'
        '<rect x="-77" y="-36" width="154" height="72" rx="36" fill="#fff" '
        'stroke="none"/>'
        f'<path d="M-44 0c11 -22 22 -22 33 0s22 22 33 0s22 -22 22 -8" stroke="{ink}" '
        'stroke-width="10"/></g>'
    )


def motif_batch(_ink):
    """Return the two clusters merging of the MaldiBatchKit logo, simplified."""
    left = ((-88, -44), (-66, -30), (-92, -20), (-88, 44), (-66, 30), (-92, 20))
    right = ((52, -24), (82, -22), (40, 8), (70, 6), (98, 8), (56, 32), (86, 30))
    return (
        '<g fill="#fff">'
        + "".join(
            f'<circle cx="{x}" cy="{y}" r="10" fill-opacity=".65"/>' for x, y in left
        )
        + "".join(f'<circle cx="{x}" cy="{y}" r="11"/>' for x, y in right)
        + '</g><path d="M-42 -32Q-14 -26 10 -8M-42 32Q-14 26 10 8" stroke="#fff" '
        'stroke-width="9" stroke-linecap="round" fill="none"/>'
    )


def motif_deep(_ink):
    """Return the network of the MaldiDeepKit logo, simplified."""
    layers = ((-84, (-44, 0, 44)), (0, (-54, -18, 18, 54)), (84, (-24, 24)))
    edges = "".join(
        f"M{x0} {y0}L{x1} {y1}"
        for (x0, ys0), (x1, ys1) in pairwise(layers)
        for y0 in ys0
        for y1 in ys1
    )
    nodes = "".join(
        f'<circle cx="{x}" cy="{y}" r="13"/>' for x, ys in layers for y in ys
    )
    return (
        f'<path d="{edges}" stroke="#fff" stroke-width="5" stroke-opacity=".6"/>'
        f'<g fill="#fff">{nodes}</g>'
    )


def card(k, name, palette, gid, install, motif, scenes):
    """Return one package card: its hexagon, three scenes and their labels."""
    x = CARD_X[k]
    x0 = x + PAD
    colour = palette[0]
    t_turn = LEAD + k * TURN
    t_end = t_turn + TURN
    rect = (
        f'x="{x + 0.5}" y="{CARD_Y + 0.5}" width="{CARD_W - 1}" height="{CARD_H - 1}"'
    )
    out = [
        "<g>"
        + opacity(
            [
                (0, 0.72),
                (t_turn - FADE, 0.72),
                (t_turn, 1),
                (t_end - FADE, 1),
                (t_end, 0.72),
            ]
        ),
        (
            f'<rect {rect} rx="12" fill="{GREY}" fill-opacity=".06" stroke="{GREY}" '
            'stroke-opacity=".5"/>'
        ),
        '<g opacity="0">'
        + opacity(
            [(0, 0), (t_turn - FADE, 0), (t_turn, 1), (t_end - FADE, 1), (t_end, 0)]
        )
        + f'<rect {rect} rx="12" stroke="{colour}" stroke-width="4" filter="url(#glow)"/>'
        f'<rect {rect} rx="12" fill="{colour}" fill-opacity=".07" stroke="{colour}" '
        'stroke-width="1.6"/></g>',
        f'<g transform="translate({x + PAD + 15} {CARD_Y + 30})"><g transform="scale(1)">'
        + scale(
            [
                (0, 1),
                (t_turn - 0.01, 1),
                (t_turn + 0.16, 1.22),
                (t_turn + 0.34, 1),
            ]
        )
        + f'<path d="{hexagon_path(19)}" fill="url(#{gid})"/>'
        f'<g transform="scale(.13)">{motif(palette[2])}</g></g></g>',
        f'<text class="nm" x="{x + 52}" y="{CARD_Y + 36}" fill="{colour}">{name}</text>',
    ]
    for i, (scene, label, api) in enumerate(scenes):
        t = t_turn + i * SCENE
        if i == 0:
            seen = [
                (0, 1),
                (t + SCENE - FADE, 1),
                (t + SCENE, 0),
                (t_end - FADE, 0),
                (t_end, 1),
            ]
        else:
            seen = [
                (0, 0),
                (t - FADE, 0),
                (t, 1),
                (t + SCENE - FADE, 1),
                (t + SCENE, 0),
            ]
        out.append(
            f'<g opacity="{1 if i == 0 else 0}">'
            + opacity(seen)
            + scene(x0, STAGE_Y, t)
            + "</g>"
        )
        lit = [(0, 0), (t - FADE, 0), (t, 1), (t + SCENE - FADE, 1), (t + SCENE, 0)]
        y = ROW_Y[i]
        out.append(
            f'<circle cx="{x0 + 3}" cy="{y - 4}" r="3" fill="{GREY}" fill-opacity=".45"/>'
            f'<circle cx="{x0 + 3}" cy="{y - 4}" r="3.6" fill="{colour}" opacity="0">'
            + opacity(lit)
            + "</circle>"
            f'<text class="tx rw" x="{x0 + 13}" y="{y}">{label}'
            + anim(
                "fill",
                [
                    (0, TXT),
                    (t - FADE, TXT),
                    (t, colour),
                    (t + SCENE - FADE, colour),
                    (t + SCENE, TXT),
                ],
            )
            + "</text>"
            f'<text class="tx c2" x="{x + CARD_W - PAD}" y="{y}" text-anchor="end">{api}'
            "</text>"
        )
    out.append(
        f'<path d="M{x0} {CARD_Y + 306}H{x + CARD_W - PAD}" stroke="{GREY}" '
        'stroke-opacity=".3"/>'
        f'<text class="c" x="{x0}" y="{PIP_Y}" fill="{colour}">$ pip install {install}'
        "</text>"
    )
    out.append("</g>")
    return "".join(out)


DESC = (
    '<desc id="d">Animated overview of the three MaldiSuite packages, side by side and '
    f"in no particular order. A spotlight moves from card to card every {num(TURN * TEMPO)} seconds. "
    "MaldiAMRKit shows preprocessing of a raw spectrum into bins, alignment of shifted "
    "spectra, and MIC values read as resistant or susceptible against EUCAST "
    "breakpoints. MaldiBatchKit shows samples moving from clusters by acquisition site "
    "to clusters by species, kBET and LISI scores before and after correction, and "
    "correctors compared in a grid search. MaldiDeepKit shows four backbones (MLP, 1-D "
    "CNN, 1-D ResNet, 1-D ViT), predictions with uncertainty and conformal prediction "
    "sets, and a dual-branch classifier joining a spectrum and side features. All data "
    "are illustrative. Below the cards: use one, or all three, pip install "
    "maldisuite.</desc>"
)
STYLE = (
    "<style>"
    'text{font-family:system-ui,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif}'
    f".tx{{fill:{TXT}}}"
    ".nm{font-size:16px;font-weight:600}.rw{font-size:11.5px;font-weight:600}"
    ".lb{font-size:10.5px}.lb2{font-size:11px;font-weight:600}.bd{font-size:13px}"
    ".lt{font-size:13px;font-weight:700}.pl2{font-size:13px;font-weight:700}"
    ".ib{font-size:13px;font-weight:600}"
    ".c,.c2,.ci,.cm{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,"
    '"DejaVu Sans Mono",monospace}'
    ".c{font-size:10.5px}.c2{font-size:9.5px}.cm{font-size:12px}.ci{font-size:13px;font-weight:600}"
    "</style>"
)


def gradient(gid, light, deep, x2=0, y2=1):
    """Return a linear gradient over the bounding box of the painted shape."""
    return (
        f'<linearGradient id="{gid}" x1="0" y1="0" x2="{x2}" y2="{y2}">'
        f'<stop offset="0" stop-color="{light}"/>'
        f'<stop offset="1" stop-color="{deep}"/></linearGradient>'
    )


def defs():
    """Return the shared gradients and the glow of the active card."""
    return (
        "<defs>"
        + gradient("g-amr", AMR[1], AMR[2], 0.4, 1)
        + gradient("g-batch", BATCH[1], BATCH[2], 0.4, 1)
        + gradient("g-deep", DEEP[1], DEEP[2], 0.4, 1)
        + gradient("v-amr", AMR[1], AMR[2])
        + gradient("v-batch", BATCH[1], BATCH[2])
        + gradient("v-deep", DEEP[1], DEEP[2])
        + gradient("h-batch", BATCH[2], BATCH[1], 1, 0)
        + '<filter id="glow" x="-12%" y="-12%" width="124%" height="124%">'
        '<feGaussianBlur stdDeviation="5"/></filter></defs>'
    )


def footer():
    """Return the install line under the cards, the same at every moment."""
    y = INSTALL_Y
    return (
        f'<text class="tx ib" x="392" y="{y + 4}" text-anchor="end">'
        "Use one, or all three</text>"
        f'<rect x="402" y="{y - 14}" width="204" height="27" rx="7" fill="#0b1c20" '
        'stroke="#2c5560"/>'
        f'<text class="ci" x="412" y="{y + 4}" fill="#4fc9d6">$</text>'
        f'<text class="ci" x="426" y="{y + 4}" fill="#d6e7e9" textLength="170" '
        'lengthAdjust="spacing">pip install maldisuite</text>'
        f'<text class="tx lb" x="784" y="{y + 4}" text-anchor="end">illustrative data'
        "</text>"
    )


def build() -> str:
    """Return the SVG document as a string."""
    parts = [
        (
            '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="386" '
            'viewBox="0 0 800 386" role="img" aria-labelledby="t d" fill="none">'
        ),
        '<title id="t">MaldiSuite: what each of the three packages offers</title>',
        DESC,
        STYLE,
        defs(),
        card(
            0,
            "MaldiAMRKit",
            AMR,
            "g-amr",
            "maldiamrkit",
            motif_amr,
            (
                (scene_preprocess, "Preprocess", "PreprocessingPipeline"),
                (scene_align, "Align", "Warping"),
                (scene_mic, "Read MICs", "MICEncoder"),
            ),
        ),
        card(
            1,
            "MaldiBatchKit",
            BATCH,
            "g-batch",
            "maldibatchkit",
            motif_batch,
            (
                (scene_correct, "Correct", "SpeciesAwareComBat"),
                (scene_diagnose, "Diagnose", "BatchCorrectionBenchmark"),
                (scene_tune, "Tune", "AutoCorrector"),
            ),
        ),
        card(
            2,
            "MaldiDeepKit",
            DEEP,
            "g-deep",
            "maldideepkit",
            motif_deep,
            (
                (scene_backbones, "Backbones", "MaldiMLPClassifier"),
                (scene_uncertainty, "Uncertainty", "ConformalPredictor"),
                (scene_dual, "Combine", "MaldiDualBranchClassifier"),
            ),
        ),
        footer(),
        "</svg>",
    ]
    return "\n".join(parts) + "\n"


def main() -> None:
    """Write the SVG to the path given on the command line, or to DEFAULT_OUT."""
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUT
    svg = build()
    with out.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(svg)
    print(f"Wrote {out} ({len(svg.encode('utf-8'))} bytes)")


if __name__ == "__main__":
    main()
