# Changelog

All notable changes to this meta-package will be documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
