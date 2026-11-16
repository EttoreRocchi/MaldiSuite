"""Run the quick start of the README and of each tab of the site on a synthetic cohort.

Writes 90 synthetic spectra (45 patients, two spectra each, three batches, two
species) and their metadata CSV to a temporary folder, plus the same cohort as
a binned matrix (X.csv, X.npy, y.npy, groups.npy) for the single-package tabs.
Runs the README quick start and every tab of index.html whose code differs from
it, with the current Python. Fails if a script fails, or if it prints a VME or
an AUROC outside 0-1.

Run it after installing maldisuite: python tools/smoke_test.py
"""

import html
import re
import subprocess
import sys
import tempfile
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PEAKS = np.linspace(2500, 19000, 40)
BATCHES = {"site_a": (0.0, 1.0), "site_b": (1.5, 1.3), "site_c": (-1.5, 0.8)}


def make_cohort(folder: Path, seed: int = 0) -> None:
    """Write spectra/<ID>.txt files and metadata.csv in folder."""
    rng = np.random.default_rng(seed)
    spectra = folder / "spectra"
    spectra.mkdir()
    mz = np.linspace(2000, 20000, 18000)
    heights = rng.uniform(50, 1000, PEAKS.size)
    rows = []
    for patient in range(45):
        batch = list(BATCHES)[patient % 3]
        shift, scale = BATCHES[batch]
        label = "R" if rng.random() < 0.4 else "S"
        for rep in range(2):
            peaks = heights * rng.lognormal(0, 0.2, PEAKS.size)
            intensity = 300 * np.exp(-(mz - 2000) / 4000) + rng.normal(0, 5, mz.size)
            for centre, height in zip(PEAKS + shift, peaks):
                intensity += height * np.exp(-0.5 * ((mz - centre) / 4) ** 2)
            if label == "R":
                intensity += 600 * np.exp(-0.5 * ((mz - 7150 - shift) / 4) ** 2)
            sample_id = f"p{patient:02d}r{rep}"
            np.savetxt(spectra / f"{sample_id}.txt",
                       np.column_stack([mz, np.clip(intensity * scale, 0, None)]), fmt="%.3f")
            rows.append({"ID": sample_id, "Drug": label,
                         "Species": "Escherichia coli" if patient % 2 else "Klebsiella pneumoniae",
                         "batch": batch, "patient_id": f"p{patient:02d}"})
    pd.DataFrame(rows).to_csv(folder / "metadata.csv", index=False)


def write_matrices(folder: Path) -> None:
    """Write the binned cohort as X.csv, X.npy, y.npy and groups.npy in folder."""
    from maldiamrkit import MaldiSet
    from maldiamrkit.susceptibility import LabelEncoder

    data = MaldiSet.from_directory(folder / "spectra", folder / "metadata.csv", bin_width=3)
    meta = data.meta.loc[data.X.index]
    data.X.rename_axis("ID").to_csv(folder / "X.csv")
    np.save(folder / "X.npy", data.X.to_numpy())
    np.save(folder / "y.npy", LabelEncoder().fit_transform(data.get_y_single("Drug")))
    np.save(folder / "groups.npy", meta["patient_id"].to_numpy())


def readme_quickstart() -> str:
    """Return the Python block of the README quick start."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    match = re.search(r"## Quick start\n\n```python\n(.*?)```", readme, re.DOTALL)
    if match is None:
        sys.exit("No Python block under '## Quick start' in README.md")
    return match.group(1)


def site_quickstarts() -> dict[str, str]:
    """Return the code of each quick start tab of index.html, by tab key."""
    page = (ROOT / "index.html").read_text(encoding="utf-8")
    blocks = re.findall(r'<code id="quickstart-code-([a-z]+)">(.*?)</code>', page, re.DOTALL)
    if not blocks:
        sys.exit("No quick start tabs in index.html")
    return {key: html.unescape(re.sub(r"<[^>]+>", "", code)) for key, code in blocks}


def run(name: str, code: str, folder: Path) -> None:
    """Run code in folder; exit on failure or on a VME or AUROC outside 0-1."""
    print(f"== {name}", flush=True)
    result = subprocess.run([sys.executable, "-c", code], check=False,
                            cwd=folder, capture_output=True, text=True)
    print(result.stdout, end="", flush=True)
    print(result.stderr, end="", file=sys.stderr, flush=True)
    if result.returncode:
        sys.exit(f"{name} failed with exit code {result.returncode}")
    for metric, value in re.findall(r"(VME|AUROC): (-?\d+\.\d+)", result.stdout):
        if not 0 <= abs(float(value)) <= 1:
            sys.exit(f"{name} printed {metric} {value}, outside 0-1")


def main() -> None:
    packages = ("maldisuite", "maldiamrkit", "maldibatchkit", "maldideepkit")
    print("Python", sys.version.split()[0], "|",
          ", ".join(f"{name} {version(name)}" for name in packages))
    readme = readme_quickstart()
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        make_cohort(folder)
        write_matrices(folder)
        run("README quick start", readme, folder)
        for key, code in site_quickstarts().items():
            if code.strip() != readme.strip():
                run(f"site tab '{key}'", code, folder)


if __name__ == "__main__":
    main()
