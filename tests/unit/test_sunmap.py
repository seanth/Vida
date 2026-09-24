"""Tests for Vida_Data/vsunmap.py: shade worked out with a map of the sunlight."""

import math
import random

import pytest

import vsunmap


class Plant:
    def __init__(self, x, y, r, height, transmittance=0.0, elevation=0.0, isSeed=0,
                 minimumLightForGermination=0.0):
        self.x = x
        self.y = y
        self.r = r
        self.heightStem = height
        self.elevation = elevation
        self.canopyTransmittance = transmittance
        self.isSeed = isSeed
        self.minimumLightForGermination = minimumLightForGermination
        self.subregion = []
        self.colourLeaf = [116.6, 1.0, 1.0]
        self.overlapList = ["left over from last cycle"]
        self.areaCovered = 0.0


class Garden:
    def __init__(self, soil):
        self.soil = soil
        self.lightIntensity = 1.0


class Region:
    def __init__(self, lightIntensity):
        self.lightIntensity = lightIntensity


def light(plant):
    return plant.colourLeaf[2]


def shade(soil, cellSize=0.01):
    vsunmap.determineShade(Garden(soil), cellSize)


def test_a_plant_on_its_own_gets_full_sun():
    plant = Plant(0.0, 0.0, 1.0, 5.0)
    shade([plant])
    assert light(plant) == 1.0
    assert plant.areaCovered == 0.0
    assert plant.overlapList == []


def test_a_plant_under_a_bigger_taller_canopy_gets_what_that_canopy_lets_through():
    tall = Plant(0.0, 0.0, 5.0, 10.0, transmittance=0.1)
    small = Plant(1.0, 1.0, 0.5, 2.0)
    shade([small, tall])
    assert light(tall) == 1.0
    assert light(small) == pytest.approx(0.1)
    area = 3.14 * 0.5 * 0.5
    assert small.areaCovered == pytest.approx(area * 0.9)


def test_light_through_two_canopies_is_dimmed_by_both():
    top = Plant(0.0, 0.0, 5.0, 10.0, transmittance=0.5)
    middle = Plant(0.0, 0.0, 3.0, 6.0, transmittance=0.2)
    bottom = Plant(0.2, 0.0, 0.5, 1.0)
    shade([bottom, middle, top])
    assert light(middle) == pytest.approx(0.5)
    assert light(bottom) == pytest.approx(0.5 * 0.2)


def test_a_shorter_plant_never_shades_a_taller_one():
    short_and_wide = Plant(0.0, 0.0, 5.0, 2.0, transmittance=0.0)
    tall_and_narrow = Plant(0.5, 0.0, 0.5, 8.0, transmittance=0.0)
    shade([short_and_wide, tall_and_narrow])
    assert light(tall_and_narrow) == 1.0
    # the narrow canopy covers 1% of the wide one's area
    assert light(short_and_wide) == pytest.approx(1.0 - 0.01, abs=0.002)


def test_plants_of_the_same_height_do_not_shade_each_other():
    one = Plant(0.0, 0.0, 1.0, 3.0)
    two = Plant(0.5, 0.0, 1.0, 3.0)
    shade([one, two])
    assert light(one) == 1.0
    assert light(two) == 1.0


def test_height_includes_the_ground_so_a_short_tree_on_a_hill_shades_the_valley():
    on_the_hill = Plant(0.0, 0.0, 3.0, 2.0, transmittance=0.0, elevation=10.0)
    in_the_valley = Plant(0.0, 0.0, 1.0, 8.0, elevation=0.0)
    shade([in_the_valley, on_the_hill])
    assert light(on_the_hill) == 1.0
    assert light(in_the_valley) == 0.0


def test_a_seed_that_needs_light_is_shaded_but_never_shades():
    plant = Plant(0.0, 0.0, 2.0, 3.0, transmittance=0.25)
    seed = Plant(0.1, 0.1, 0.004, 99.0, isSeed=1, minimumLightForGermination=0.2)
    # a seed on a hill, higher than the plant, overlapping it
    high_seed = Plant(0.0, 0.0, 5.0, 0.0, isSeed=1, minimumLightForGermination=0.2,
                      elevation=50.0)
    shade([seed, high_seed, plant])
    # heightStem of a seed is ignored: a seed lies on the ground
    assert light(seed) == pytest.approx(0.25)
    assert light(high_seed) == 1.0
    assert light(plant) == 1.0


def test_seeds_that_need_no_light_are_left_alone():
    plant = Plant(0.0, 0.0, 2.0, 3.0, transmittance=0.0)
    seed = Plant(0.1, 0.1, 0.004, 0.0, isSeed=1, minimumLightForGermination=0.0)
    seed.colourLeaf[2] = 0.123
    shade([plant, seed])
    assert light(seed) == 0.123
    assert seed.overlapList == ["left over from last cycle"]


def test_the_light_of_a_region_is_applied_to_the_plants_in_it():
    plant = Plant(0.0, 0.0, 1.0, 3.0)
    plant.subregion = [Region(0.3), Region(0.6)]
    shade([plant])
    # the last region a plant is in counts, as in the classic shading
    assert light(plant) == pytest.approx(0.6)


def lens_area(r, d):
    # area where two circles of radius r, d apart, overlap
    return 2 * r * r * math.acos(d / (2 * r)) - (d / 2) * math.sqrt(4 * r * r - d * d)


def test_a_half_covered_plant_matches_the_geometry():
    top = Plant(0.0, 0.0, 1.0, 5.0, transmittance=0.0)
    below = Plant(1.0, 0.0, 1.0, 2.0)
    shade([top, below], cellSize=0.002)
    expected = 1.0 - lens_area(1.0, 1.0) / math.pi
    assert light(below) == pytest.approx(expected, abs=0.002)


def test_the_order_of_the_soil_does_not_matter():
    rng = random.Random(3)
    soil = []
    for i in range(40):
        soil.append(Plant(rng.uniform(-5, 5), rng.uniform(-5, 5), rng.uniform(0.2, 2.0),
                          rng.uniform(1, 10), transmittance=rng.uniform(0.0, 0.5)))
    shade(soil, cellSize=0.02)
    before = [light(plant) for plant in soil]
    shuffled = soil[:]
    rng.shuffle(shuffled)
    shade(shuffled, cellSize=0.02)
    assert [light(plant) for plant in soil] == before


def reference_light(plant, soil, points_across=80):
    # The fraction of full sun reaching plant, worked out a different way:
    # at a grid of points over its canopy, multiply together the
    # transmittance of every taller canopy above that point, and average.
    total = 0.0
    count = 0
    step = 2 * plant.r / points_across
    for i in range(points_across):
        for j in range(points_across):
            px = plant.x - plant.r + (i + 0.5) * step
            py = plant.y - plant.r + (j + 0.5) * step
            if (px - plant.x) ** 2 + (py - plant.y) ** 2 > plant.r ** 2:
                continue
            reaching = 1.0
            for other in soil:
                if other is plant or other.isSeed:
                    continue
                if other.heightStem + other.elevation <= plant.heightStem + plant.elevation:
                    continue
                if (px - other.x) ** 2 + (py - other.y) ** 2 <= other.r ** 2:
                    reaching = reaching * other.canopyTransmittance
            total = total + reaching
            count = count + 1
    return total / count


def test_matches_a_brute_force_reference_in_crowded_random_worlds():
    rng = random.Random(11)
    errors = []
    for world in range(4):
        soil = []
        for i in range(25):
            soil.append(Plant(rng.uniform(-4, 4), rng.uniform(-4, 4), rng.uniform(0.3, 2.5),
                              rng.uniform(1, 12), transmittance=rng.uniform(0.0, 0.6),
                              elevation=rng.uniform(0.0, 2.0)))
        shade(soil, cellSize=0.01)
        for plant in soil:
            errors.append(abs(light(plant) - reference_light(plant, soil)))
    assert max(errors) < 0.02
    assert sum(errors) / len(errors) < 0.005


def test_a_huge_world_uses_bigger_cells_rather_than_huge_memory():
    far_apart = [Plant(-5000.0, -5000.0, 1.0, 3.0), Plant(5000.0, 5000.0, 1.0, 3.0)]
    theMap = vsunmap.SunlightMap(far_apart, 0.05)
    assert theMap.rows <= vsunmap.MAX_CELLS + 1
    assert theMap.columns <= vsunmap.MAX_CELLS + 1
    assert theMap.cellSize > 0.05
