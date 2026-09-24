"""Tests for Vida_Data/spatial_grid.py and its use in finding overlaps."""

import math
import random

import pytest

import geometry_utils
import list_utils
import spatial_grid
import vworldr


class Thing:
    def __init__(self, x, y, radius=0.1, isSeed=False):
        self.x = x
        self.y = y
        self.isSeed = isSeed
        self.radiusSeed = radius
        self.radiusStem = radius
        self.overlapList = []


def test_near_finds_things_within_the_distance_in_list_order():
    things = [Thing(5.0, 5.0), Thing(0.5, 0.0), Thing(-0.5, 0.2), Thing(0.0, 1.9)]
    grid = spatial_grid.SpatialGrid(things, 1.0)

    near = grid.near(0.0, 0.0, 2.0)

    assert near[0] is things[1]  # same order as the list,
    assert near[1] is things[2]  # not the order of the cells
    assert near[2] is things[3]
    assert things[0] not in near


def test_near_includes_things_exactly_at_the_distance():
    things = [Thing(3.0, 0.0), Thing(0.0, -3.0)]
    grid = spatial_grid.SpatialGrid(things, 1.0)
    assert grid.near(0.0, 0.0, 3.0) == things


def test_things_without_a_real_position_are_always_near():
    lost = Thing(math.nan, 0.0)
    grid = spatial_grid.SpatialGrid([Thing(50.0, 50.0), lost], 1.0)
    assert grid.near(0.0, 0.0, 1.0) == [lost]


def random_world(seed, count):
    rng = random.Random(seed)
    things = []
    for i in range(count):
        # mostly small seeds, some stems, a few big ones, packed closely
        radius = rng.choice([0.01, 0.02, 0.05, 0.2, 0.8])
        things.append(Thing(rng.uniform(-10, 10), rng.uniform(-10, 10), radius, isSeed=radius < 0.1))
    # a few exactly touching and exactly on top of each other
    things.append(Thing(0.0, 0.0, 0.5))
    things.append(Thing(1.0, 0.0, 0.5))
    things.append(Thing(1.0, 0.0, 0.2))
    return things


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_the_grid_finds_exactly_the_same_overlaps(in_repo_root, seed):
    world = vworldr.garden()
    world.soil = random_world(seed, 2000)
    grid, largestRadius = world.makeOverlapGrid()

    for thing in world.soil:
        without_grid = world.checkForOverlap(thing)
        with_grid = world.checkForOverlap(thing, grid, largestRadius)
        assert with_grid == without_grid


class ShadeThing:
    """Just enough of a plant or seed for determineShade."""

    def __init__(self, rng, isSeed):
        self.x = rng.uniform(-10, 10)
        self.y = rng.uniform(-10, 10)
        self.isSeed = isSeed
        self.r = rng.uniform(0.01, 0.05) if isSeed else rng.uniform(0.1, 2.0)
        self.absHeightStem = 0.0 if isSeed else rng.uniform(0.5, 20.0)
        self.canopyTransmittance = rng.choice([0.0, 0.02, 0.3, 0.6])
        self.minimumLightForGermination = 0.0
        self.colourLeaf = [100.0, 1.0, 1.0]
        self.subregion = []
        self.overlapList = []
        self.areaCovered = 0.0
        self.name = "thing"


class ShadeWorld:
    def __init__(self, soil):
        self.soil = soil
        self.showProgressBar = False
        self.lightIntensity = 1.0


def expected_overlaps(soil):
    """determineShade's first step done the slow way: each plant against the
    first theIndex objects in the soil, where theIndex is plants done so far."""
    expected = {}
    theIndex = 0
    last_looked_at = None
    for plant in soil:
        if not plant.isSeed:
            found = []
            for j in range(theIndex):
                other = soil[j]
                last_looked_at = other
                if geometry_utils.checkOverlap(plant.x, plant.y, plant.r, other.x, other.y, other.r) > 0:
                    found.append(other)
            found = list_utils.sort_by_attr(found, "absHeightStem")
            found.reverse()
            expected[id(plant)] = found
            theIndex = theIndex + 1
    return expected, last_looked_at


@pytest.mark.parametrize("seed", [4, 5, 6])
def test_shading_finds_exactly_the_same_overlaps(seed):
    rng = random.Random(seed)
    soil = []
    for i in range(1500):
        soil.append(ShadeThing(rng, isSeed=rng.random() < 0.3))
    expected, last_looked_at = expected_overlaps(soil)

    random.seed(seed)
    vworldr.determineShade(ShadeWorld(soil))

    for plant in soil:
        if not plant.isSeed:
            assert plant.overlapList == expected[id(plant)]
            if len(plant.overlapList) == 1:
                # shaded by one other plant: uses the transmittance of the last
                # object the first step looked at (see determineShade)
                over = plant.overlapList[0]
                total = geometry_utils.areaCircle(plant.r)
                covered = geometry_utils.areaOverlappingCircles(plant.x, plant.y, plant.r, over.x, over.y, over.r)
                covered = covered - covered * last_looked_at.canopyTransmittance
                exposed = (total - covered) / total
                assert plant.areaCovered == total - total * exposed


def test_grid_add_and_remove_keep_list_order():
    things = [Thing(0.0, 0.0), Thing(0.1, 0.0), Thing(0.2, 0.0)]
    grid = spatial_grid.SpatialGrid(things, 1.0)
    added = Thing(0.3, 0.0)

    grid.remove(things[1])
    grid.add(added)

    assert grid.near(0.0, 0.0, 1.0) == [things[0], things[2], added]


class Crowd:
    """A plant or seed with what removeOverlaps and kill() use."""

    def __init__(self, name, x, y, isSeed, radius, massTotal, timePlanted):
        self.name = name
        self.x = x
        self.y = y
        self.isSeed = isSeed
        self.radiusSeed = radius
        self.radiusStem = radius
        self.massTotal = massTotal
        self.massSeed = 0.01
        self.timePlanted = timePlanted
        self.overlapList = []
        self.subregion = []
        self.seedList = []
        self.delayInGermination = 0
        self.causeOfDeath = ""
        self.motherPlant = 0
        self.motherPlantName = ""


def random_crowd(rng, number):
    isSeed = rng.random() < 0.5
    thing = Crowd("crowd " + str(number), rng.uniform(-4, 4), rng.uniform(-4, 4), isSeed,
                  rng.choice([0.02, 0.05, 0.1, 0.3]), rng.choice([0.0, 1.0, 2.0]), number)
    if not isSeed and rng.random() < 0.3:
        # a plant carrying seeds, which drop to the ground if it dies
        for i in range(rng.randint(1, 3)):
            seed = Crowd(thing.name + " seed " + str(i), thing.x + rng.uniform(-0.5, 0.5),
                         thing.y + rng.uniform(-0.5, 0.5), True, 0.02, 0.0, 0)
            thing.seedList.append(seed)
    return thing


def remove_overlaps_the_slow_way(world):
    """removeOverlaps as it was before the grid: check against everything."""
    for obj in world.soil[:]:
        for other in world.checkForOverlap(obj):
            if obj.massTotal > other.massTotal:
                other.causeOfDeath = "crushed"
                world.kill(other)
                break
            elif obj.massTotal < other.massTotal:
                obj.causeOfDeath = "crushed"
                world.kill(obj)
                break
            elif obj.massTotal == other.massTotal:
                obj.causeOfDeath = "overlap violation"
                if obj.timePlanted > other.timePlanted:
                    world.kill(obj)
                else:
                    world.kill(other)
                break


def crowded_world(seed):
    world = vworldr.garden()
    world.theRegions = []
    world.showProgressBar = False
    world.allowOverlaps = False
    rng = random.Random(seed)
    for i in range(600):
        world.soil.append(random_crowd(rng, i))
    return world


def describe(thing):
    # Dropped seeds are given a new random name (uuid4) when they are planted,
    # so they are described by where they are instead.
    if thing.name.startswith("crowd"):
        name = thing.name
    else:
        name = "seed dropped at %r, %r" % (thing.x, thing.y)
    return (name, thing.causeOfDeath)


def outcome(world):
    alive = [describe(thing) for thing in world.soil]
    dead = [describe(thing) for thing in world.deathNote]
    return alive, dead


@pytest.mark.parametrize("seed", [7, 8, 9])
def test_remove_overlaps_gives_the_same_result_as_checking_everything(in_repo_root, seed):
    world = crowded_world(seed)
    remove_overlaps_the_slow_way(world)

    world_with_grid = crowded_world(seed)
    world_with_grid.removeOverlaps()

    alive, dead = outcome(world_with_grid)
    assert (alive, dead) == outcome(world)
    assert len(dead) > 100  # plenty of overlaps were resolved
    assert any("dropped" in name for name, cause in alive)  # and seeds were dropped
