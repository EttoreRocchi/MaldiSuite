# Changelog

All notable changes to this meta-package will be documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Landing page: the roadmap shows one timeline per package, with the latest release, the work in development and the planned releases.

## [0.4.0] - 2026-11-10

### Added
- Animated overview of the three packages in the README (`tools/build_suite_svg.py`).
- Shared theme of the package documentations: `assets/docs/maldisuite.css` and `assets/docs/maldisuite-footer.html`.

### Changed
- Bumped the pins to `maldiamrkit[batch,formats]>=0.22.2,<0.23` and `maldideepkit>=0.4.0,<0.5` (self-supervised pre-training); the quick start is tested with maldibatchkit 0.2.2.
- Redrew the suite and package logos as one family, with a new favicon (`tools/build_logos.py`).
- Package logos with versions for light and dark backgrounds.
- Landing page: package logos without the white box, switching with the theme.

## [0.3.0] - 2026-10-30

### Changed
- Bumped the MaldiAMRKit pin to `maldiamrkit[batch,formats]>=0.22.1,<0.23` (reworked warping, leakage-safe splits); the other pins are unchanged.
- Redesigned the landing page, with dark mode, DRIAMS benchmark charts, research and roadmap sections.

### Fixed
- Quick start in the README and on the landing page: R/S labels are now encoded before VME scoring.

## [0.2.0] - 2026-09-21

### Changed
- Bumped pins to `maldiamrkit[batch,formats]>=0.20.0,<0.21`, `maldibatchkit[viz]>=0.2.0,<0.3`, `maldideepkit>=0.3.0,<0.4`, so that `pip install maldisuite` brings in mzML/mzXML I/O (the `formats` extra of MaldiAMRKit 0.20.0) and the classifiers used in the Application Note benchmarks (MaldiDeepKit 0.3.0).

### Added
- Landing page: social preview cards, favicon, mobile nav, copy buttons on install blocks, and funding note.

## [0.1.0] - 2026-04-28

### Added
- Initial release of the `maldisuite` meta-package.
- Pins compatible versions of `maldiamrkit[batch]>=0.14.0`, `maldibatchkit[viz]>=0.1.0`, and `maldideepkit>=0.1.0`.
- Landing page deployed at https://ettorerocchi.github.io/MaldiSuite/, with the suite logo and the three package logos.
