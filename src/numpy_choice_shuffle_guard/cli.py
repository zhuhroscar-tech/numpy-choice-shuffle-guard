"""numpy-choice-shuffle-guard CLI: probe the installed numpy for the
Generator.choice(replace=False, p=...) shuffle-ignored bug (numpy/numpy#31210)
and report distribution-correctness checks against an independent oracle.
"""
from __future__ import annotations

import argparse
import json
import sys

import numpy as np

from . import __version__
from .core import (
    detect_shuffle_ignored_bug,
    independent_reference_weighted_sample_without_replacement,
    safe_weighted_choice,
)
from .style import print_fields, resolve_style, status_headline


def cmd_detect(args: argparse.Namespace) -> int:
    result = detect_shuffle_ignored_bug(
        population_size=args.population_size,
        sample_size=args.sample_size,
        seed=args.seed,
    )
    if args.json:
        print(json.dumps(result.__dict__, indent=2, sort_keys=True))
        return 1 if result.affected else 0

    style = resolve_style(args.no_color)
    level = "fail" if result.affected else "ok"
    print(status_headline(style, level, "numpy Generator.choice shuffle probe"))
    print_fields(
        [
            ("numpy version", result.numpy_version),
            ("affected", "yes" if result.affected else "no"),
            ("detail", result.detail),
        ]
    )
    return 1 if result.affected else 0


def cmd_verify(args: argparse.Namespace) -> int:
    """Statistically verify safe_weighted_choice()'s selection frequencies
    against the independent Efraimidis-Spirakis oracle over many trials.
    This checks the WORKAROUND does not silently bias which items get
    selected while fixing draw order -- a real correctness property, not
    just "it runs without crashing".
    """
    rng = np.random.default_rng(args.seed)
    n = args.population_size
    k = args.sample_size
    weights = np.linspace(1.0, 2.0, n)
    weights = weights / weights.sum()

    selection_counts_guard = np.zeros(n, dtype=np.int64)
    selection_counts_oracle = np.zeros(n, dtype=np.int64)

    for trial in range(args.trials):
        guard_sample = safe_weighted_choice(
            rng, n, size=k, replace=False, p=weights, shuffle=True,
            force_workaround=True,
        )
        selection_counts_guard[guard_sample] += 1

        oracle_sample = independent_reference_weighted_sample_without_replacement(
            n, k, weights, seed=args.seed + trial + 1,
        )
        selection_counts_oracle[oracle_sample] += 1

    guard_freq = selection_counts_guard / args.trials
    oracle_freq = selection_counts_oracle / args.trials
    max_abs_diff = float(np.max(np.abs(guard_freq - oracle_freq)))
    mean_abs_diff = float(np.mean(np.abs(guard_freq - oracle_freq)))
    passed = max_abs_diff <= args.tolerance

    payload = {
        "trials": args.trials,
        "population_size": n,
        "sample_size": k,
        "max_abs_freq_diff": max_abs_diff,
        "mean_abs_freq_diff": mean_abs_diff,
        "tolerance": args.tolerance,
        "passed": passed,
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if passed else 1

    style = resolve_style(args.no_color)
    level = "ok" if passed else "fail"
    print(status_headline(style, level, "selection-frequency check vs independent oracle"))
    print_fields(
        [
            ("trials", str(args.trials)),
            ("max abs frequency diff", f"{max_abs_diff:.4f}"),
            ("mean abs frequency diff", f"{mean_abs_diff:.4f}"),
            ("tolerance", f"{args.tolerance:.4f}"),
            ("passed", "yes" if passed else "no"),
        ]
    )
    return 0 if passed else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="numpy-choice-shuffle-guard",
        description=(
            "Detect and work around numpy/numpy#31210: "
            "Generator.choice(replace=False, p=weights) silently ignores "
            "the shuffle parameter."
        ),
    )
    parser.add_argument("--version", action="version", version=f"numpy-choice-shuffle-guard {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    detect = sub.add_parser("detect", help="probe the installed numpy for the bug")
    detect.add_argument("--population-size", type=int, default=500)
    detect.add_argument("--sample-size", type=int, default=100)
    detect.add_argument("--seed", type=int, default=0)
    detect.add_argument("--json", action="store_true")
    detect.add_argument("--no-color", action="store_true")
    detect.set_defaults(func=cmd_detect)

    verify = sub.add_parser(
        "verify", help="statistically verify safe_weighted_choice against an independent oracle"
    )
    verify.add_argument("--population-size", type=int, default=200)
    verify.add_argument("--sample-size", type=int, default=40)
    verify.add_argument("--trials", type=int, default=2000)
    verify.add_argument("--tolerance", type=float, default=0.05)
    verify.add_argument("--seed", type=int, default=0)
    verify.add_argument("--json", action="store_true")
    verify.add_argument("--no-color", action="store_true")
    verify.set_defaults(func=cmd_verify)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
