"""CLI tests for numpy-choice-shuffle-guard."""
from __future__ import annotations

import json

import pytest

from numpy_choice_shuffle_guard.cli import main


def test_detect_json_exits_0_or_1_and_has_required_fields(capsys):
    rc = main(["detect", "--json", "--population-size", "300", "--sample-size", "50"])
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert "numpy_version" in payload
    assert "affected" in payload
    assert "detail" in payload
    assert rc in (0, 1)
    assert rc == (1 if payload["affected"] else 0)


def test_detect_text_mode_prints_status_headline(capsys):
    rc = main(["detect", "--no-color", "--population-size", "300", "--sample-size", "50"])
    out = capsys.readouterr().out
    assert "numpy Generator.choice shuffle probe" in out
    assert "numpy version" in out
    assert rc in (0, 1)


def test_verify_json_reports_passed_field(capsys):
    rc = main([
        "verify", "--json",
        "--population-size", "50", "--sample-size", "10",
        "--trials", "50", "--tolerance", "0.15",
    ])
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert "passed" in payload
    assert "max_abs_freq_diff" in payload
    assert rc == (0 if payload["passed"] else 1)


def test_verify_text_mode_prints_status_headline(capsys):
    rc = main([
        "verify", "--no-color",
        "--population-size", "50", "--sample-size", "10",
        "--trials", "50", "--tolerance", "0.15",
    ])
    out = capsys.readouterr().out
    assert "selection-frequency check vs independent oracle" in out
    assert rc in (0, 1)


def test_version_flag(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])
    assert exc_info.value.code == 0
    out = capsys.readouterr().out
    assert "numpy-choice-shuffle-guard" in out


def test_no_subcommand_requires_a_command():
    with pytest.raises(SystemExit):
        main([])
