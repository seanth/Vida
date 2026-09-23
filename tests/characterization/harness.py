"""Build sandboxes, run scenarios through the driver, and compare recordings.

Usage from the repository root::

    python -m tests.characterization.harness record            # re-record every scenario
    python -m tests.characterization.harness record terrain_water  # re-record one scenario
    python -m tests.characterization.harness check             # compare against the recordings

The pytest tests in ``test_characterization.py`` call the same functions.
"""

from __future__ import annotations

import argparse
import json
import lzma
import math
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SCENARIOS = HERE / "scenarios"
GOLDEN = HERE / "golden"
INPUTS = HERE / "inputs"
DRIVER = HERE / "driver.py"

# The code under test comes from the repository...
CODE_FILES = ["Vida.py"]
CODE_DIRS = ["Vida_Data"]
# ...but configuration and data come from frozen copies in inputs/, so that
# editing a species file or a default in the repository does not change what
# these tests expect. They are meant to catch changes to the code.
CONFIG_FILES = ["Vida.ini", "Vida World Preferences.yml"]


def scenario_names() -> list[str]:
    return sorted(p.stem for p in SCENARIOS.glob("*.yml"))


def load_scenario(name: str) -> dict[str, Any]:
    with open(SCENARIOS / f"{name}.yml") as f:
        return yaml.safe_load(f)


def golden_path(name: str) -> Path:
    return GOLDEN / f"{name}.json.xz"


# ---------------------------------------------------------------------------
# Running
# ---------------------------------------------------------------------------


def build_sandbox(scenario: dict[str, Any], sandbox: Path) -> None:
    """Copy the code under test and the scenario's inputs into ``sandbox``.

    Paths in a scenario file are relative to ``inputs/``.
    """
    for name in CODE_FILES:
        shutil.copy2(REPO / name, sandbox / name)
    for name in CODE_DIRS:
        shutil.copytree(REPO / name, sandbox / name, ignore=shutil.ignore_patterns("__pycache__"))
    for name in CONFIG_FILES:
        shutil.copy2(INPUTS / name, sandbox / name)

    # Vida uses the .yml files directly inside Species/ (not subfolders).
    species_dir = sandbox / "Species"
    species_dir.mkdir()
    for rel in scenario.get("species", []):
        source = INPUTS / rel
        for path in sorted(source.glob("*.yml")) if source.is_dir() else [source]:
            shutil.copy2(path, species_dir / path.name)

    for filename, spec in (scenario.get("species_variants") or {}).items():
        with open(INPUTS / spec["base"]) as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
        data.update(spec.get("set", {}))
        with open(species_dir / filename, "w") as f:
            yaml.safe_dump(data, f, sort_keys=False)

    prefs = scenario.get("world_preferences")
    if prefs:
        prefs_path = sandbox / "Vida World Preferences.yml"
        with open(prefs_path) as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
        data.update(prefs)
        with open(prefs_path, "w") as f:
            yaml.safe_dump(data, f, sort_keys=False)

    for dest, src in (scenario.get("files") or {}).items():
        target = sandbox / dest
        target.parent.mkdir(parents=True, exist_ok=True)
        source = INPUTS / src
        if source.is_dir():
            shutil.copytree(source, target)
        else:
            shutil.copy2(source, target)

    if scenario.get("events") is not None:
        with open(sandbox / "events.yml", "w") as f:
            yaml.safe_dump(scenario["events"], f, sort_keys=False)


def run_scenario(name: str, keep_sandbox: Path | None = None) -> dict[str, Any]:
    """Run one scenario and return its recording."""
    scenario = load_scenario(name)
    with tempfile.TemporaryDirectory(prefix=f"vida-{name}-") as tmp:
        sandbox = Path(tmp)
        build_sandbox(scenario, sandbox)
        (sandbox / "scenario.json").write_text(json.dumps(scenario))
        env = {**os.environ, "PYTHONHASHSEED": "0"}
        with open(sandbox / "run.log", "w") as log:
            subprocess.run(
                [sys.executable, str(DRIVER), "scenario.json", "recording.json.xz"],
                cwd=sandbox,
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
                check=True,
                timeout=scenario.get("timeout", 600),
            )
        recording = read_recording(sandbox / "recording.json.xz")
        if keep_sandbox is not None:
            shutil.copytree(sandbox, keep_sandbox, dirs_exist_ok=True)
        return recording


def read_recording(path: Path) -> dict[str, Any]:
    with lzma.open(path, "rt") as f:
        return json.load(f)


def write_recording(recording: dict[str, Any], path: Path) -> None:
    payload = json.dumps(recording, indent=0, sort_keys=True, allow_nan=True).encode()
    with lzma.open(path, "wb", preset=9 | lzma.PRESET_EXTREME) as f:
        f.write(payload)


# ---------------------------------------------------------------------------
# Comparing
# ---------------------------------------------------------------------------


def _differences(expected: Any, actual: Any, path: str, rtol: float) -> Iterator[str]:
    if isinstance(expected, dict) and isinstance(actual, dict):
        for key in sorted(set(expected) | set(actual)):
            if key not in actual:
                yield f"{path}.{key}: missing (expected {expected[key]!r})"
            elif key not in expected:
                yield f"{path}.{key}: unexpected (got {actual[key]!r})"
            else:
                yield from _differences(expected[key], actual[key], f"{path}.{key}", rtol)
    elif isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            yield f"{path}: length {len(actual)} != expected {len(expected)}"
        for i, (e, a) in enumerate(zip(expected, actual, strict=False)):  # length reported above
            yield from _differences(e, a, f"{path}[{i}]", rtol)
    elif (
        isinstance(expected, float)
        and isinstance(actual, float)
        and rtol > 0
        and math.isclose(expected, actual, rel_tol=rtol, abs_tol=rtol)
    ):
        return
    elif type(expected) is not type(actual) or expected != actual:
        # NaN never equals itself, but two NaNs are the same recorded value.
        if not (isinstance(expected, float) and isinstance(actual, float)
                and math.isnan(expected) and math.isnan(actual)):
            yield f"{path}: {actual!r} != expected {expected!r}"


def compare(expected: dict[str, Any], actual: dict[str, Any], rtol: float = 0.0,
            limit: int = 25) -> list[str]:
    """Return human-readable differences, earliest cycle first.

    Floats must match exactly unless ``rtol`` is given. Exact matching is
    the point of these tests: a change that is meant to be a pure refactor
    should not move any number at all.
    """
    diffs: list[str] = []

    def add(items: Iterator[str]) -> bool:
        for item in items:
            diffs.append(item)
            if len(diffs) >= limit:
                return False
        return True

    ok = add(_differences(expected["stages"], actual["stages"], "stages", rtol))
    exp_cycles, act_cycles = expected["cycles"], actual["cycles"]
    if ok and len(exp_cycles) != len(act_cycles):
        ok = add(iter([f"cycles: recorded {len(act_cycles)} snapshots, expected {len(exp_cycles)}"]))
    for i, (e, a) in enumerate(zip(exp_cycles, act_cycles, strict=False)):
        if not ok:
            break
        ok = add(_differences(e, a, f"snapshot[{i}](cycle {e.get('cycle')})", rtol))
    if ok:
        ok = add(_differences(expected["species"], actual["species"], "species", rtol))
    if ok:
        add(_differences(expected["files"], actual["files"], "files", rtol))
    return diffs


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["record", "check"])
    parser.add_argument("names", nargs="*", help="scenario names (default: all)")
    parser.add_argument("--keep", type=Path, help="copy each finished sandbox into this folder")
    parser.add_argument("--rtol", type=float, default=0.0, help="relative tolerance for floats when checking")
    parser.add_argument("-j", "--jobs", type=int, default=os.cpu_count(), help="scenarios to run at once")
    args = parser.parse_args(argv)

    names = args.names or scenario_names()

    def run(name: str) -> dict[str, Any]:
        return run_scenario(name, keep_sandbox=args.keep / name if args.keep else None)

    # Each scenario runs in its own process, so they can run side by side.
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        recordings = pool.map(run, names)

    failed = 0
    for name, recording in zip(names, recordings, strict=True):
        if args.command == "record":
            write_recording(recording, golden_path(name))
            print(f"recorded {name}: {len(recording['cycles'])} snapshots")
            continue
        if not golden_path(name).exists():
            failed += 1
            print(f"FAIL {name}: no recording yet (run: harness record {name})")
            continue
        diffs = compare(read_recording(golden_path(name)), recording, rtol=args.rtol)
        if diffs:
            failed += 1
            print(f"FAIL {name}")
            for d in diffs:
                print(f"    {d}")
        else:
            print(f"ok   {name}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
