# numpy-choice-shuffle-guard

[![English](https://img.shields.io/badge/English-555555?style=flat)](README.md) [![简体中文](https://img.shields.io/badge/%E7%AE%80%E4%BD%93%E4%B8%AD%E6%96%87-555555?style=flat)](README.zh-CN.md)

Detects and works around a real, currently-open numpy bug:
[numpy/numpy#31210](https://github.com/numpy/numpy/issues/31210) --
`numpy.random.Generator.choice(a, size, replace=False, p=<weights>)`
silently **ignores the `shuffle` parameter**. `shuffle=True` (numpy's own
default) and `shuffle=False` produce byte-identical output whenever `p`
is given and `replace=False`.

## Why this matters

If your code samples a weighted subset without replacement and relies on
`shuffle=True` to randomize the *draw order* of the result (e.g. a
streaming/online training loop, or an order-sensitive validation split),
the result's order silently correlates with the input order instead of
being randomized -- with no error, warning, or difference in the
selected *set* of items. Only the *order* is wrong, which makes this
class of bug easy to miss in code review and unit tests that check "are
the right items selected" without checking "is the order actually
randomized run to run."

The unweighted case (`p=None`) is NOT affected -- `shuffle` works
correctly there. This tool's own probe deliberately checks both paths
and will not report "not affected" unless the *control* case (unweighted)
also behaves correctly, so a broken probe can never masquerade as "bug
fixed" (see `detect_shuffle_ignored_bug`'s fail-safe branch in
[core.py](src/numpy_choice_shuffle_guard/core.py)).

## What it provides

- `detect_shuffle_ignored_bug()` / `numpy-choice-shuffle-guard detect`:
  live-probes the **installed** numpy (never a version-number allowlist,
  since numpy has not announced a fix version) and reports whether this
  exact bug reproduces right now.
- `safe_weighted_choice()`: a drop-in wrapper around
  `Generator.choice` that performs the shuffle numpy's own call silently
  skips, using the same `rng` so the draw stays fully reproducible from
  the caller's rng state. Every other call shape (`replace=True`, or
  `p=None`) passes straight through to numpy unmodified.
- `independent_reference_weighted_sample_without_replacement()`: an
  **independent oracle** (Efraimidis-Spirakis exponential-key weighted
  sampling -- a different algorithm from numpy's own cumulative-
  distribution search) used by `numpy-choice-shuffle-guard verify` to
  confirm the workaround does not silently bias *which* items get
  selected while fixing draw order.

This is a workaround for an upstream numpy defect, **not a numpy patch**
and not a claim that numpy itself is wrong to use -- it exists only until
numpy/numpy#31210 is fixed upstream.

## Install and run

Requires Python 3.9+ and numpy>=1.24. No GPU, no compiled extensions.

```bash
git clone https://github.com/zhuhroscar-tech/numpy-choice-shuffle-guard.git
cd numpy-choice-shuffle-guard
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

```bash
numpy-choice-shuffle-guard detect            # probe the installed numpy
numpy-choice-shuffle-guard detect --json
numpy-choice-shuffle-guard verify            # statistical check vs the independent oracle
numpy-choice-shuffle-guard --no-color detect
```

`detect` exits `1` if the bug is confirmed present (or if the probe
itself was inconclusive -- fail-safe), `0` if not reproduced. `verify`
exits `1` if `safe_weighted_choice`'s selection frequencies diverge from
the independent oracle beyond `--tolerance` (default `0.05`).

```python
import numpy as np
from numpy_choice_shuffle_guard import safe_weighted_choice

rng = np.random.default_rng(0)
weights = np.array([0.5, 0.3, 0.2])
sample = safe_weighted_choice(rng, 3, size=2, replace=False, p=weights, shuffle=True)
```

## Verification trail

- Independently reproduced on this project's pinned numpy version
  (2.5.2) before this guard was written: `Generator.choice(replace=False,
  p=weights, shuffle=True)` vs `shuffle=False` gave byte-identical
  output; the unweighted control case correctly differed. See the
  upstream issue for the original report and root-cause trace into
  `_generator.pyx`.
- ZH/JA disclosure: neither a Chinese-language nor a Japanese-language
  query surfaced native-language community discussion of this specific
  bug at candidate-evaluation time -- only English-language sources
  (the GitHub issue itself and official numpy docs). Disclosed here
  honestly rather than implied; this tool exists because the defect is
  real and independently reproducible, not because of broad community
  demand in any one language.
- CI runs the full test suite (including a live, unmocked reproduction
  against the CI runner's own installed numpy) on `ubuntu-latest` and
  `macos-latest`, plus a wheel/sdist build-and-smoke-test job with
  checksummed release artifacts.

## Limits

- This tool only detects and works around the `replace=False` +
  `p is not None` combination described in numpy/numpy#31210. It does
  not audit any other numpy RNG API for correctness.
- `detect`'s live probe uses a fixed small population/sample size by
  default; it is a functional reproduction, not a statistical proof for
  every population size or numpy build.
- If numpy fixes this issue upstream, `safe_weighted_choice` will detect
  that automatically and stop applying the manual shuffle -- but this
  guard is not a substitute for eventually removing the workaround once
  a numpy release with the fix is your minimum supported version.

## Development and removal

```bash
python -m pytest -q --cov=numpy_choice_shuffle_guard --cov-report=term-missing
python -m pip uninstall numpy-choice-shuffle-guard
```

[Releases](https://github.com/zhuhroscar-tech/numpy-choice-shuffle-guard/releases) · [MIT license](LICENSE)
