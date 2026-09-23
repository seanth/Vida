"""Check that Vida still does exactly what it did when the recordings were made.

Each scenario in ``scenarios/`` is run through the unmodified Vida.py (see
``driver.py``) and compared, number for number, with its recording in
``golden/``. See README.md in this folder for what to do when one fails.
"""

from __future__ import annotations

import os

import pytest

from . import harness

# Recordings are made on Linux. Other platforms can differ
# in the last digit of some maths functions; set this (e.g. to 1e-9) to
# compare floating point numbers with a tolerance instead of exactly.
RTOL = float(os.environ.get("VIDA_CHARACTERIZATION_RTOL", "0"))


@pytest.mark.parametrize("name", harness.scenario_names())
def test_scenario_matches_recording(name: str) -> None:
    expected = harness.read_recording(harness.golden_path(name))
    actual = harness.run_scenario(name)
    differences = harness.compare(expected, actual, rtol=RTOL)
    assert not differences, (
        f"Scenario {name!r} no longer matches its recording. First differences:\n  "
        + "\n  ".join(differences)
        + "\nIf this change is intended, re-record with:\n"
        + f"  python -m tests.characterization.harness record {name}"
    )


def test_every_scenario_has_a_recording() -> None:
    scenarios = set(harness.scenario_names())
    recordings = {p.name.removesuffix(".json.xz") for p in harness.GOLDEN.glob("*.json.xz")}
    assert scenarios - recordings == set(), "scenarios without a recording (run: harness record <name>)"
    assert recordings - scenarios == set(), "recordings without a scenario file (delete them)"


def snapshots_for_each_stage(recording):
    """Split a recording's snapshots into one list per stage (run of Vida)."""
    starts = []
    for stage in recording["stages"]:
        starts.append(stage["first_cycle"])
    starts.append(len(recording["cycles"]))
    runs = []
    for i in range(len(recording["stages"])):
        runs.append(recording["cycles"][starts[i]:starts[i + 1]])
    return runs


def where_everything_is(snapshot):
    """Position, size and state of every object, without its generated name."""
    things = []
    for thing in snapshot["soil"] + snapshot["dead"]:
        things.append((thing["x"], thing["y"], thing["z"], thing["isSeed"], thing["age"],
                       thing["massTotal"], thing["causeOfDeath"]))
    return things


def test_seed_option_repeats_a_run_exactly():
    recording = harness.read_recording(harness.golden_path("seed_option"))
    first_run, second_run = snapshots_for_each_stage(recording)
    assert len(first_run) == len(second_run) > 1
    for first, second in zip(first_run, second_run, strict=True):
        assert where_everything_is(first) == where_everything_is(second)
