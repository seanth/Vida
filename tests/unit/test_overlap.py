"""Tests for Vida_Data/voverlap.py: the same overlaps as the old grid loop."""

import math
import random

import geometry_utils
import spatial_grid
import voverlap


class Thing:
    def __init__(self, x, y, r):
        self.x = x
        self.y = y
        self.r = r


def the_old_way(soil, plantPlaces, reaches, cellSize):
    # determineShade's loop before voverlap: the k-th plant against the
    # first k objects of the soil, found with a spatial grid
    grid = spatial_grid.SpatialGrid(soil, cellSize)
    answers = []
    for k in range(len(plantPlaces)):
        plant = soil[plantPlaces[k]]
        found = []
        for other in grid.near(plant.x, plant.y, reaches[k], k):
            if geometry_utils.checkOverlap(plant.x, plant.y, plant.r, other.x, other.y, other.r) > 0:
                if other not in found and other is not plant:
                    found.append(other)
        answers.append([soil.index(other) for other in found])
    return answers


def ask_both(soil, plantPlaces):
    largest = max([thing.r for thing in soil] + [0.0])
    cellSize = max(2.0 * largest, 1.0)
    reaches = [(soil[place].r + largest) * 1.000001 + 0.000001 for place in plantPlaces]
    return (voverlap.findEarlierOverlaps(soil, plantPlaces, reaches, cellSize),
            the_old_way(soil, plantPlaces, reaches, cellSize))


def test_random_worlds_give_the_same_overlaps():
    random.seed(11)
    for world in range(30):
        size = random.choice([5.0, 30.0, 100.0])
        soil = []
        for i in range(random.randint(1, 400)):
            r = random.choice([0.0, 0.05, random.uniform(0.01, 4.0)])
            soil.append(Thing(random.uniform(-size, size), random.uniform(-size, size), r))
        plantPlaces = sorted(random.sample(range(len(soil)), random.randint(1, len(soil))))
        new, old = ask_both(soil, plantPlaces)
        assert new == old


def test_circles_that_just_touch():
    # 3-4-5 triangles: centres exactly 5 apart, radii adding up to exactly 5
    soil = [Thing(0.0, 0.0, 2.0), Thing(3.0, 4.0, 3.0), Thing(-3.0, -4.0, 3.0000000001),
            Thing(6.0, 8.0, 2.0), Thing(0.0, 0.0, 0.0), Thing(0.0, 0.0, 0.0)]
    new, old = ask_both(soil, list(range(len(soil))))
    assert new == old
    assert 0 in new[1]  # touching counts as overlapping


def test_nothing_asked():
    assert voverlap.findEarlierOverlaps([Thing(0.0, 0.0, 1.0)], [], [], 1.0) == []


def test_positions_that_are_not_numbers_are_left_to_the_old_way():
    soil = [Thing(0.0, 0.0, 1.0), Thing(math.nan, 0.0, 1.0)]
    assert voverlap.findEarlierOverlaps(soil, [0, 1], [2.0, 2.0], 2.0) is None
    soil = [Thing(0.0, 0.0, 1.0), Thing(0.0, 0.0, math.inf)]
    assert voverlap.findEarlierOverlaps(soil, [0, 1], [2.0, 2.0], 2.0) is None
