"""Tests for tools/run_many.py: working out which runs to start."""

import importlib.util
from pathlib import Path

import pytest

TOOL = Path(__file__).resolve().parents[2] / "tools" / "run_many.py"
spec = importlib.util.spec_from_file_location("run_many", TOOL)
run_many = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_many)


def test_reading_rng_starts():
    assert run_many.readRngStarts("1-4") == [1, 2, 3, 4]
    assert run_many.readRngStarts("1,3,5") == [1, 3, 5]
    assert run_many.readRngStarts("1-3,10") == [1, 2, 3, 10]


def test_one_run_per_rng_start_each_with_its_own_name():
    runs = run_many.runsForRngStarts([1, 2], ["-n", "forest", "-w", "100", "-t", "50"])
    assert runs == [
        ["-n", "forest-rng1", "-rngstart", "1", "-w", "100", "-t", "50"],
        ["-n", "forest-rng2", "-rngstart", "2", "-w", "100", "-t", "50"],
    ]


def test_runs_without_a_name_use_vidas_default_name():
    assert run_many.runsForRngStarts([7], ["-w", "50"]) == [["-n", "default-rng7", "-rngstart", "7", "-w", "50"]]


def test_rngstart_in_the_options_is_refused():
    with pytest.raises(SystemExit):
        run_many.runsForRngStarts([1], ["-n", "forest", "-rngstart", "3"])


def test_runs_from_a_file(tmp_path):
    runs = tmp_path / "runs.txt"
    runs.write_text("# dry and wet\n-n dry -w 100 -rngstart 1\n\n-n wet -w 100 -rngstart 1\n")
    assert run_many.runsFromFile(str(runs)) == [["-n", "dry", "-w", "100", "-rngstart", "1"], ["-n", "wet", "-w", "100", "-rngstart", "1"]]
    assert run_many.nameOf(["-n", "dry", "-w", "100"]) == "dry"
