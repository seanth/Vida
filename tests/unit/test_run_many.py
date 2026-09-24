"""Tests for tools/run_many.py: working out which runs to start."""

import importlib.util
from pathlib import Path

import pytest

TOOL = Path(__file__).resolve().parents[2] / "tools" / "run_many.py"
spec = importlib.util.spec_from_file_location("run_many", TOOL)
run_many = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_many)


def test_reading_seeds():
    assert run_many.readSeeds("1-4") == [1, 2, 3, 4]
    assert run_many.readSeeds("1,3,5") == [1, 3, 5]
    assert run_many.readSeeds("1-3,10") == [1, 2, 3, 10]


def test_one_run_per_seed_each_with_its_own_name():
    runs = run_many.runsForSeeds([1, 2], ["-n", "forest", "-w", "100", "-t", "50"])
    assert runs == [
        ["-n", "forest-seed1", "-seed", "1", "-w", "100", "-t", "50"],
        ["-n", "forest-seed2", "-seed", "2", "-w", "100", "-t", "50"],
    ]


def test_runs_without_a_name_are_called_run():
    assert run_many.runsForSeeds([7], ["-w", "50"]) == [["-n", "run-seed7", "-seed", "7", "-w", "50"]]


def test_seed_in_the_options_is_refused():
    with pytest.raises(SystemExit):
        run_many.runsForSeeds([1], ["-n", "forest", "-seed", "3"])


def test_runs_from_a_file(tmp_path):
    runs = tmp_path / "runs.txt"
    runs.write_text("# dry and wet\n-n dry -w 100 -seed 1\n\n-n wet -w 100 -seed 1\n")
    assert run_many.runsFromFile(str(runs)) == [["-n", "dry", "-w", "100", "-seed", "1"], ["-n", "wet", "-w", "100", "-seed", "1"]]
    assert run_many.nameOf(["-n", "dry", "-w", "100"]) == "dry"
