# numpy-choice-shuffle-guard

This repository has moved.

`numpy-choice-shuffle-guard` has been consolidated into the umbrella package:

https://github.com/zhuhroscar-tech/numpy-correctness-guards

Use the shared CLI/API there instead:

```bash
git clone https://github.com/zhuhroscar-tech/numpy-correctness-guards.git
cd numpy-correctness-guards
python -m pip install -e '.[dev]'
numpy-guard run choice-shuffle detect --json
numpy-guard run choice-shuffle verify
```

Python API:

```python
from numpy_correctness_guards.guards.choice_shuffle import safe_weighted_choice
```

The migrated guard still detects and works around `numpy.random.Generator.choice(..., replace=False, p=weights, shuffle=True)` ignoring `shuffle` in the weighted-without-replacement path (`numpy/numpy#31210`).

This repository is kept read-only for historical links and releases. New fixes should go to `numpy-correctness-guards`.

[Umbrella package](https://github.com/zhuhroscar-tech/numpy-correctness-guards) · [MIT license](LICENSE)
