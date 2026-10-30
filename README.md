# MaldiSuite

[![Website](https://img.shields.io/badge/website-online-0b6f82)](https://ettorerocchi.github.io/MaldiSuite/)
[![PyPI meta-package](https://img.shields.io/pypi/v/maldisuite.svg?color=4f9a2c)](https://pypi.org/project/maldisuite/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

<p align="center">
  <img src="assets/maldi_suite_logo.png" alt="MaldiSuite" width="320"/>
</p>

<p align="center">
  <strong>A Python ecosystem for MALDI-TOF spectral processing and analysis in antimicrobial resistance research</strong>
</p>

**MaldiSuite** combines preprocessing, batch effect correction, and deep learning classifiers in a single sklearn-compatible workflow for clinical microbiology and computational biology research.

> **Landing page:** [MaldiSuite](<https://ettorerocchi.github.io/MaldiSuite/>)

---

## What this repository contains

This repository serves two purposes:

1. **Landing page** for the website.
2. **Meta-package**: a minimal PyPI package (`maldisuite`) that installs the three
   packages of the suite with pinned compatible versions.

This repository **does not** contain the source code of the three packages.
Each package lives in its own repository, with its own issues, documentation,
and release cycle.

## The three packages

MaldiAMRKit owns the data model, preprocessing, evaluation, and biomarker / drift modules; MaldiBatchKit re-exports every corrector (ComBat variants, Limma, Harmony, MALDI-specific harmonisers) at the top level; MaldiDeepKit ships scikit-learn-compatible deep classifiers (`MaldiMLPClassifier`, `MaldiCNNClassifier`, `MaldiResNetClassifier`, `MaldiTransformerClassifier`).

| Logo | Package | Purpose | Repository |
|:---:|---|---|---|
| <img src="assets/maldiamrkit_logo.png" alt="MaldiAMRKit" width="80"> | **MaldiAMRKit** | Preprocessing, evaluation, biomarkers, drift monitoring | [MaldiAMRKit](https://github.com/EttoreRocchi/MaldiAMRKit) |
| <img src="assets/maldibatchkit_logo.png" alt="MaldiBatchKit" width="80"> | **MaldiBatchKit** | Batch effect correction for mass spectra | [MaldiBatchKit](https://github.com/EttoreRocchi/MaldiBatchKit) |
| <img src="assets/maldideepkit_logo.png" alt="MaldiDeepKit" width="80"> | **MaldiDeepKit** | Deep learning classifiers for MALDI-TOF spectra | [MaldiDeepKit](https://github.com/EttoreRocchi/MaldiDeepKit) |

## Installation

Install the full suite with a single command:

```bash
pip install maldisuite
```

This installs `maldiamrkit`, `maldibatchkit`, and `maldideepkit` at compatible versions. `maldisuite` 0.3.0 pins:

| Package | Pinned range |
|---|---|
| MaldiAMRKit | `maldiamrkit[batch,formats]>=0.22.1,<0.23` |
| MaldiBatchKit | `maldibatchkit[viz]>=0.2.0,<0.3` |
| MaldiDeepKit | `maldideepkit>=0.3.0,<0.4` |

Alternatively, install individual packages separately:

```bash
pip install maldiamrkit     # preprocessing, biomarkers, drift
pip install maldibatchkit   # batch effect correction
pip install maldideepkit    # deep learning classifiers
```

## Quick start

```python
from maldiamrkit import MaldiSet
from maldiamrkit.evaluation import CaseGroupedKFold, vme_scorer
from maldiamrkit.susceptibility import LabelEncoder
from maldibatchkit import BatchAwareWarping, SpeciesAwareComBat
from maldideepkit import MaldiMLPClassifier
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import Pipeline

# metadata.csv: ID, Drug (R/S), Species, batch, patient_id
data = MaldiSet.from_directory("spectra/", "metadata.csv", bin_width=3)
meta = data.meta.loc[data.X.index]
y = LabelEncoder().fit_transform(data.get_y_single("Drug"))  # R=1, S=0

pipe = Pipeline([
    ("warp",   BatchAwareWarping(batch=meta["batch"])),
    ("combat", SpeciesAwareComBat(batch=meta["batch"],
                                  species=meta["Species"])),
    ("clf",    MaldiMLPClassifier(input_dim=data.X.shape[1],
                                  random_state=0)),
])

scores = cross_val_score(
    pipe, data.X, y,
    scoring=vme_scorer,
    cv=CaseGroupedKFold(n_splits=5, random_state=0),
    groups=meta["patient_id"],
)
print(f"VME: {-scores.mean():.3f}")
```

Every step is refitted inside each training fold, and `CaseGroupedKFold` keeps all spectra of a patient in the same fold. Tested with maldiamrkit 0.22.1, maldibatchkit 0.2.0 and maldideepkit 0.3.0.

## Citation

MaldiSuite is described in an Application Note currently under review at *Bioinformatics*. The full citation will be added here once the article is published.

## License

MIT License - see [`LICENSE`](LICENSE) for the full text.

## Acknowledgments

MaldiSuite builds on the work of the mass spectrometry and clinical microbiology communities. In particular, we acknowledge:

- MALDIquant (Gibb & Strimmer, 2012, *Bioinformatics*)
- The Borgwardt Lab and the DRIAMS benchmark (Weis et al., 2022, *Nature Medicine*), which established Python-based MALDI-TOF AMR prediction as a research area