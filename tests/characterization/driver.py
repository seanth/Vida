"""Run the unmodified Vida.py deterministically and record its state.

This script is not imported by the tests. The harness (``harness.py``) copies
the code into a temporary sandbox directory and runs this file there in a
separate Python process::

    python driver.py <scenario.json> <recording.json.xz>

Nothing in Vida itself is changed. Instead, before Vida.py starts, this driver
removes the sources of run-to-run variation from the outside:

* ``random`` is seeded with the scenario seed.
* ``time.time`` returns an increasing counter. Vida stores the time a seed
  was planted and uses it to break ties between overlapping objects of equal
  mass, so wall-clock time would make runs unrepeatable.
* ``uuid.uuid4`` returns an increasing counter, so object names repeat.
* ``os.listdir`` and ``glob.glob`` return sorted results. Directory order is
  filesystem dependent, and Vida picks "random" species by list position.
* ``os.system`` calls to the external ``cfdg``/``ffmpeg`` programs are skipped
  (they are not installed on test machines), and the call to ``vextract.py``
  is re-run through this driver so it gets the same sorted directory
  listings.

Vida saves the whole world with ``pickle.dump`` at the end of every cycle
when run with ``-a a``. The driver wraps ``pickle.dump`` so that, as well as
writing the normal pickle, it records a JSON-friendly copy of the state.
"""

from __future__ import annotations

import glob
import hashlib
import json
import lzma
import os
import pickle
import random
import re
import runpy
import shlex
import subprocess
import sys
import time
import traceback
import uuid
from pathlib import Path
from typing import Any

import yaml

# Per-object attributes that are bookkeeping, not simulation state. The
# values come from the patched clock, so they only reflect how many times
# time.time() was called.
IGNORED_OBJECT_ATTRS = {"timeCreation", "timeGermination", "timePlanted"}

# Seeds still attached to a plant (in its seedList) only ever have these
# attributes changed: makeSeed() sets the position and parentage, and
# growSeedOnPlant() adds mass. Everything else keeps the value set by
# zeroSeedValues(), so recording it for every attached seed every cycle would
# only make the recordings bigger.
ATTACHED_SEED_ATTRS = {"name", "motherPlant", "motherPlantName", "x", "y", "z", "r",
                       "massSeed", "radiusSeed", "elevation"}

# Garden attributes that hold other objects (recorded separately), and the
# planting counter, which only numbers seeds in order (like timePlanted).
GARDEN_CONTAINER_ATTRS = {"soil", "deathNote", "platonicSeeds", "theRegions", "terrainImage",
                          "plantingCount"}

UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


# ---------------------------------------------------------------------------
# Determinism patches
# ---------------------------------------------------------------------------


# The real functions, kept so that patching again for a later stage wraps
# these rather than the previous patch.
_REAL_LISTDIR = os.listdir
_REAL_GLOB = glob.glob
_REAL_SYSTEM = os.system


class Counter:
    """Counts 1, 2, 3, ... each time next_value() is called."""

    def __init__(self) -> None:
        self.value = 0

    def next_value(self) -> int:
        self.value = self.value + 1
        return self.value


_clock = Counter()
_uuid_counter = Counter()


def _fake_time() -> float:
    return float(_clock.next_value())


def _fake_uuid4() -> uuid.UUID:
    return uuid.UUID(int=_uuid_counter.next_value())


def _sorted_listdir(path: str = ".") -> list[str]:
    return sorted(_REAL_LISTDIR(path))


def _sorted_glob(*args: Any, **kwargs: Any) -> list[str]:
    return sorted(_REAL_GLOB(*args, **kwargs))


def install_patches(seed: int) -> None:
    """Make the next run of Vida repeatable. Called before each stage."""
    global _clock, _uuid_counter
    random.seed(seed)
    _clock = Counter()
    _uuid_counter = Counter()
    time.time = _fake_time
    uuid.uuid4 = _fake_uuid4
    os.listdir = _sorted_listdir
    glob.glob = _sorted_glob
    os.system = _system


def _system(command: str) -> int:
    words = shlex.split(command)
    if words and Path(words[0]).name in {"cfdg", "ffmpeg", "ContextFreeCLI.exe"}:
        with open("external_commands.log", "a") as log:
            log.write(command + "\n")
        return 0
    for i, word in enumerate(words):
        if word.endswith("vextract.py"):
            result = subprocess.run(
                [sys.executable, __file__, "--run-script", *words[i:]],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
            )
            return result.returncode
    return _REAL_SYSTEM(command)


# ---------------------------------------------------------------------------
# State serialisation
# ---------------------------------------------------------------------------


class Recorder:
    """Turns Vida's object graph into plain JSON data."""

    def __init__(self, species_keys: set[str]) -> None:
        # Species parameters are recorded once per species rather than on
        # every object. colourLeaf is a species parameter, but Vida changes
        # colourLeaf[2] on each plant to show how shaded it is, so keep it.
        self.species_keys = species_keys - {"colourLeaf"}
        self.names: dict[str, str] = {}
        self.cycles: list[dict[str, Any]] = []
        self.platonic: dict[str, dict[str, Any]] = {}
        self.species_by_name: dict[str, Any] = {}

    def name(self, raw: Any) -> Any:
        """Replace generated names with ids in order of first appearance.

        Vida names objects with uuid4(). Mapping them to "#0", "#1", ... in
        the order they are first recorded means a change that calls uuid4()
        a different number of times does not break the comparison, as long
        as the objects themselves are the same.
        """
        if not isinstance(raw, str) or raw == "":
            return raw
        if raw not in self.names:
            self.names[raw] = f"#{len(self.names)}"
        return self.names[raw]

    def name_for_match(self, match: re.Match[str]) -> str:
        """Same as name(), for use with re.sub() on a uuid match."""
        return self.name(match.group(0))

    def value(self, v: Any) -> Any:
        if v is None or isinstance(v, (bool, int, float, str)):
            return v
        if isinstance(v, (list, tuple)):
            return [self.value(x) for x in v]
        if isinstance(v, dict):
            return {str(k): self.value(x) for k, x in v.items()}
        return f"<{type(v).__name__}>"

    def obj(self, o: Any, attached: bool = False) -> dict[str, Any]:
        out: dict[str, Any] = {}
        changes = self.species_changes(o)
        if changes and not attached:
            out["speciesChanges"] = changes
        for key, v in sorted(vars(o).items()):
            if key in self.species_keys or key in IGNORED_OBJECT_ATTRS:
                continue
            if attached and key not in ATTACHED_SEED_ATTRS:
                continue
            if key in ("name", "motherPlantName"):
                out[key] = self.name(v)
            elif key == "motherPlant":
                out[key] = 0 if v == 0 else self.name(v.name)
            elif key == "seedList":
                out[key] = [self.obj(s, attached=True) for s in v]
            elif key == "overlapList":
                out[key] = [self.name(p.name) for p in v]
            elif key == "subregion":
                out[key] = [r.name for r in v]
            else:
                out[key] = self.value(v)
        return out

    def species_changes(self, o: Any) -> dict[str, Any]:
        """Species parameters on this object that differ from its species file.

        These are normally the same for every object of a species, so they
        are recorded once per species. A "Species" event changes them on the
        objects already in the world, and this shows those changes.
        """
        original = self.species_by_name.get(getattr(o, "nameSpecies", None))
        changes: dict[str, Any] = {}
        if original is None:
            return changes
        for key in sorted(self.species_keys):
            if hasattr(o, key) and getattr(o, key) != getattr(original, key, None):
                changes[key] = self.value(getattr(o, key))
        return changes

    def garden(self, g: Any) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, v in sorted(vars(g).items()):
            if key in GARDEN_CONTAINER_ATTRS:
                continue
            out[key] = self.value(v)
        return out

    def snapshot(self, g: Any) -> None:
        for seed in getattr(g, "platonicSeeds", {}).values():
            self.species_by_name.setdefault(seed.nameSpecies, seed)
        for key, seed in getattr(g, "platonicSeeds", {}).items():
            if key not in self.platonic:
                # getattr, not vars(): a species' settings may be kept on its
                # class rather than on each seed (see shareSpeciesSettings)
                self.platonic[key] = {k: self.value(getattr(seed, k)) for k in sorted(self.species_keys)
                                      if hasattr(seed, k)}
        terrain = getattr(g, "terrainImage", [])
        self.cycles.append(
            {
                "cycle": g.cycleNumber,
                "numbPlants": g.numbPlants,
                "numbSeeds": g.numbSeeds,
                "garden": self.garden(g),
                "terrain_sha256": hashlib.sha256(terrain[2]).hexdigest() if len(terrain) == 3 else None,
                "regions": [self.garden(r) for r in getattr(g, "theRegions", [])],
                "soil": [self.obj(o) for o in g.soil],
                "dead": [self.obj(o) for o in g.deathNote],
            }
        )


def load_species_keys() -> set[str]:
    keys: set[str] = set()
    paths = [Path("Vida_Data/Default_species.yml"), *Path("Species").glob("*.yml")]
    for path in paths:
        with open(path) as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
        keys.update(data)
    return keys


def update_world_preferences(changes: dict[str, Any]) -> None:
    """Edit the sandbox's world preferences file (for -rl, which re-reads it)."""
    path = Path("Vida World Preferences.yml")
    with open(path) as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
    data.update(changes)
    with open(path, "w") as f:
        yaml.safe_dump(data, f, sort_keys=False)


def normalised_file_hashes(names: Recorder) -> dict[str, str]:
    """Hash every output file, with uuid names replaced by stable ids."""
    hashes: dict[str, str] = {}
    for path in sorted(Path(".").glob("Output-*/**/*")):
        if not path.is_file() or path.suffix == ".pickle":
            continue
        data = path.read_bytes()
        if path.suffix in {".csv", ".cfdg", ".dxf", ".txt"}:
            text = data.decode("utf-8", errors="replace")
            text = UUID_RE.sub(names.name_for_match, text)
            data = text.encode()
        hashes[path.as_posix()] = hashlib.sha256(data).hexdigest()
    return hashes


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------


def run_script(args: list[str]) -> None:
    """Run another Vida script (vextract.py) with the same sorted listings."""
    install_patches(seed=0)
    sys.argv = args
    runpy.run_path(args[0], run_name="__main__")


def main(scenario_path: str, recording_path: str) -> None:
    scenario = json.loads(Path(scenario_path).read_text())
    recorder = Recorder(load_species_keys())

    real_dump = pickle.dump

    def recording_dump(obj: Any, file: Any, *args: Any, **kwargs: Any) -> None:
        if hasattr(obj, "soil"):
            recorder.snapshot(obj)
        real_dump(obj, file, *args, **kwargs)

    pickle.dump = recording_dump

    stages = []
    for stage in scenario["stages"]:
        if stage.get("world_preferences"):
            update_world_preferences(stage["world_preferences"])
        install_patches(stage["seed"])
        sys.argv = ["Vida.py", *stage["args"]]
        first_cycle = len(recorder.cycles)
        error = None
        try:
            runpy.run_path("Vida.py", run_name="__main__")
        except BaseException as exc:  # noqa: BLE001 - crashes are recorded, not raised
            if isinstance(exc, SystemExit) and exc.code in (None, 0):
                pass
            else:
                error = {"type": type(exc).__name__, "message": str(exc)}
                traceback.print_exc()
        stages.append({"args": stage["args"], "first_cycle": first_cycle, "error": error})

    recording = {
        "stages": stages,
        "species": recorder.platonic,
        "cycles": recorder.cycles,
        "files": normalised_file_hashes(recorder),
    }
    payload = json.dumps(recording, indent=0, sort_keys=True, allow_nan=True).encode()
    with lzma.open(recording_path, "wb", preset=9 | lzma.PRESET_EXTREME) as f:
        f.write(payload)


if __name__ == "__main__":
    if sys.argv[1] == "--run-script":
        run_script(sys.argv[2:])
    else:
        main(sys.argv[1], sys.argv[2])
