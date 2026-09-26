# Characterization tests

These tests record exactly what Vida does today and fail if that changes.
They are the safety net for tidying up and restructuring the code: a change
that is meant to leave the results alone (a refactor, a speed-up, a clean-up)
should pass them without touching any recording. A change that is meant to
alter results (a new feature, a bug fix) will fail them, and the recordings
are then updated on purpose, so the change is visible in review.

They do not check that Vida is *right*, only that it is *unchanged*.

## Running them

From the repository root:

```sh
pip install -r requirements.txt -r requirements-dev.txt
pytest -n auto          # about 15 seconds on 4 cores; plain `pytest` also works
```

The same checks without pytest, with a short report per scenario:

```sh
python -m tests.characterization.harness check
```

## When a test fails

The failure message lists the first differences, earliest cycle first, for
example:

```
snapshot[0](cycle 0).soil[0].areaPhotosynthesis: 9.126e-07 != expected 9.121e-07
snapshot[0](cycle 0).soil[0].massFixed: 0.00121055 != expected 0.00120994
```

That reads as: after cycle 0, the first object in `theGarden.soil` has a
different photosynthetic area, and therefore fixed a different amount of
carbon. The first difference is usually the cause; later ones follow from it.

* If you did not mean to change the results, the difference points at what
  changed.
* If you did (a bug fix, a new feature), re-record the affected scenarios and
  commit the new recordings together with the change:

  ```sh
  python -m tests.characterization.harness record                # all scenarios
  python -m tests.characterization.harness record terrain_water  # just one
  ```

To look at a run's output files and log, keep its sandbox:

```sh
python -m tests.characterization.harness check hex_single_species --keep /tmp/runs
```

## How it works

Each scenario in `scenarios/` describes a Vida run: which species to use, any
changes to the world preferences, event and placement files, and the
command-line arguments. `harness.py` builds a throwaway copy of the program
(`Vida.py` and `Vida_Data/` from the repository) with those inputs, and runs
it through `driver.py` in a separate Python process.

**Vida's code is not modified.** To make runs repeatable, `driver.py` patches
a few things from the outside before starting `Vida.py`:

| Patched | Why |
|---|---|
| `random` starts from each stage's `runid` | Vida is stochastic. |
| `time.time()` returns 1, 2, 3, ... | Vida records when each seed was planted and uses it to break ties between overlapping objects of equal mass. |
| `uuid.uuid4()` returns a counter | Object names are uuids. |
| `os.listdir()` and `glob.glob()` are sorted | Directory order depends on the file system, and Vida picks "random" species by their position in the list of files in `Species/`. |
| `os.system()` skips `cfdg` and `ffmpeg` | They are not installed on test machines. |

Run with `-a a`, Vida pickles the whole world at the end of every cycle. The
driver wraps `pickle.dump` to also record a copy of that state: every object
in `theGarden.soil` (plants and seeds on the ground, with the seeds still
attached to each plant), everything that died that cycle (`deathNote`), the
regions, and the world settings. Numbers are stored at full precision and
compared exactly.

Each recording in `golden/` (an xz-compressed JSON file) also holds:

* each species' parameters, once;
* a hash of every file Vida wrote: the per-cycle CSV data, the `vextract.py`
  statistics, and any `.cfdg`/`.dxf` graphics;
* for each stage, whether Vida crashed, and with what error.

Object names are replaced by `#0`, `#1`, ... in the order they first appear,
so a change in how many uuids are generated does not matter as long as the
same objects exist.

Species files, placement files, terrain images and the default `Vida.ini`
and `Vida World Preferences.yml` used by the tests are frozen copies in
`inputs/`. Editing the copies in the repository therefore does not affect
these tests; they only notice changes to the code.

## The scenarios

| Scenario | What it exercises |
|---|---|
| `southern_pine_random` | The 19 active southern pine species, random placement: the everyday run. |
| `hex_single_species` | Dense hexagonal planting: shading by one and by several neighbours (Monte Carlo), off-world deaths, ballistic dispersal. |
| `square_grid_allow_flags` | Square grid with overlaps, off-world stems and buckling all allowed, and random and slow-growth death off. Stops at the population cap. |
| `dispersal_and_germination` | Dispersal methods 3 and 4, delayed and failed germination, flat canopies, Euler-Greenhill buckling, the stressed-seeding ("selfishness") branch, Janzen-Connell mortality. |
| `dropped_seeds` | Plants killed while carrying partly grown seeds, which drop to the ground. |
| `events_regions_zones` | Regions (square and circle, created then changed), Garden changes, kill zones (by species, percent and attribute tests), a safe zone, seeding events. |
| `placement_file` | A placement CSV with odd lines, stems growing into each other (crushing), senescence. |
| `terrain_water` | Terrain from a folder with an `.xlsx` elevation table, rising water, water and drought tolerance, submerged seeds, seed dispersal over terrain; then a non-square RGB image with command-line elevation settings. |
| `graphics_outputs` | The `.cfdg` (bottom + side view) and 3D `.dxf` files. |
| `repeat_and_resume` | `-x 2` repeats, resuming with `-r`, and resuming with `-rl` (reloads world preferences). |
| `species_event` | "Species" events that change a species' parameters part way through a run. |
| `seed_event_from_file` | A "Seed" event that adds seeds from a placement file part way through a run. |
| `dispersal_methods_0_1_2` | Seed dispersal methods 0, 1 and 2, on flat ground and on terrain. |

The scenarios run about 80-93% of the lines in `vplantr.py`, `vworldr.py` and
`Vida.py`. The main simulation paths *not* reached are immature seeds failing
to germinate, deaths from waterlogging or drought, slow-growth death inside a
region, the unused `dieNow()`, and error branches that would crash anyway.
Only the bottom + side and 3D views are checked among the graphics.

### Adding a scenario

Copy an existing file in `scenarios/`, change it, and record it with
`harness record <name>`. The keys are:

```yaml
description: what the scenario is for
species: [species/generic, species/terrain/Acer_rubrum_species14.yml]  # folders or files in inputs/
species_variants:            # extra species made by changing an existing one
  Floppy.yml:
    base: species/generic/Generic Angiosperm.yml
    set: {nameSpecies: Floppy, youngsModulusStem: 0.05}
world_preferences: {allowOverlaps: true}   # changes to Vida World Preferences.yml
files: {placement.csv: placement/mixed.csv} # copied from inputs/ into the run folder
events: {10: [{Garden: [{lightIntensity: 0.5}]}]}   # written to events.yml
stages:                      # one or more runs of Vida.py, in the same folder
  - runid: 1
    args: [-n, name, -w, "20", -s, "10", -t, "10", -a, a, -f, a]
```

Always pass `-a a` so the state is recorded every cycle. Keep scenarios small
(tens to a few hundred objects): every object is recorded every cycle, and the
recordings are committed. `-m` (population cap) helps.

## Platforms and Python versions

The recordings were made on Linux, and CI checks them there with Python
3.11, 3.12 and 3.13, which all give exactly the same results.

(Python 3.12 changed the built-in `sum()` to add floats more accurately,
which changes the last digit of some totals. Vida adds numbers up with
`list_utils.sum_in_order()` instead, so results do not depend on the
Python version.)

**macOS and Windows** have their own maths libraries, which can round a few
functions differently in the last digit. If exact comparison fails there,
`VIDA_CHARACTERIZATION_RTOL=1e-9 pytest` compares floats with a tolerance
(though a difference that changes a random draw will still show up).

## Bugs found while writing these tests

When they were found, each crash was pinned in a `known_crashes` scenario,
so that fixing it was a deliberate change to the recordings. They have all
been fixed since, and each now has a scenario that uses the feature.

1. Fixed: a `Species` event crashed because `speciesAttrs.remove('name')` was
   called on `dict.keys()`, which has no `remove()` in Python 3.
2. Fixed: a `Seed` event with a placement file crashed, because
   `speciesIsMissing==True` was a comparison, not an assignment, and the
   name was never defined.
3. Fixed: seed dispersal methods 0, 1 and 2 crashed with `UnboundLocalError`
   when the first seed was dispersed, because the terrain search after the
   dispersal methods read `theDistance`, which only methods 3 and 4 set
   (`vplantr.py`, `disperseSeed`). Every species in the repository uses
   method 4.
4. Fixed: dispersal method 0 passed floats to `random.randrange()`. That is
   a `TypeError` on Python 3.12+, and on 3.11 it was already a `ValueError`
   for worlds of odd size.

Also noticed, but not crashes: in `disperseSeed`, the terrain binary search
calls `elevationFromPixel(thePixelValue)` without `theGarden.maxElevation`,
so it uses the default 50 m while the first lookup uses the real maximum.
