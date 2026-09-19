"""numpy-choice-shuffle-guard: version and package marker."""
__version__ = "0.1.0"

from .core import (  # noqa: F401
    BugDetectionResult,
    detect_shuffle_ignored_bug,
    independent_reference_weighted_sample_without_replacement,
    safe_weighted_choice,
)
