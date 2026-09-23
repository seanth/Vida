"""Tests for Vida_Data/geometry_utils.py: circles, squares and overlaps."""

import math

import geometry_utils


def test_distance_between_points():
    # A 3-4-5 right-angled triangle.
    assert geometry_utils.distBetweenPoints(0.0, 0.0, 3.0, 4.0) == 5.0
    assert geometry_utils.distBetweenPoints(1.0, 1.0, 1.0, 1.0) == 0.0


def test_area_of_a_circle_uses_pi_as_3_14():
    # Vida uses 3.14 rather than math.pi here. Changing it would change
    # every canopy area, so the tests pin the value that is used.
    assert geometry_utils.areaCircle(2.0) == 3.14 * 2.0 * 2.0


def test_radius_of_a_circle_undoes_area_of_a_circle():
    area = geometry_utils.areaCircle(1.5)
    assert math.isclose(geometry_utils.radiusCircle(area), 1.5)


def test_check_overlap_reports_none_complete_or_partial():
    # checkOverlap(x, y, r, xx, yy, rr) returns
    #   0 when the circles do not touch,
    #   1 when one is completely inside the other,
    #   2 when they partly overlap (touching edges count as partial).
    assert geometry_utils.checkOverlap(0.0, 0.0, 1.0, 5.0, 0.0, 1.0) == 0
    assert geometry_utils.checkOverlap(0.0, 0.0, 3.0, 0.5, 0.0, 1.0) == 1
    assert geometry_utils.checkOverlap(0.0, 0.0, 1.0, 1.5, 0.0, 1.0) == 2
    assert geometry_utils.checkOverlap(0.0, 0.0, 1.0, 2.0, 0.0, 1.0) == 2


def test_overlap_area_of_separate_circles_is_zero():
    assert geometry_utils.areaOverlappingCircles(0.0, 0.0, 1.0, 5.0, 0.0, 1.0) == 0.0


def test_overlap_area_of_partly_overlapping_circles_is_the_lens_area():
    # Compare with the textbook formula for the area where two circles
    # (radii r1, r2, centres d apart) overlap.
    r1, r2, d = 2.0, 1.5, 2.5
    part1 = r1 * r1 * math.acos((d * d + r1 * r1 - r2 * r2) / (2 * d * r1))
    part2 = r2 * r2 * math.acos((d * d + r2 * r2 - r1 * r1) / (2 * d * r2))
    part3 = 0.5 * math.sqrt((-d + r1 + r2) * (d + r1 - r2) * (d - r1 + r2) * (d + r1 + r2))
    lens = part1 + part2 - part3

    area = geometry_utils.areaOverlappingCircles(0.0, 0.0, r1, d, 0.0, r2)
    assert math.isclose(area, lens)


def test_overlap_area_when_one_circle_is_inside_the_other():
    # When one circle is completely inside the other, the overlap is taken
    # to be the whole of the FIRST circle (3.14 * r * r), whichever circle
    # is the smaller. Vida calls this with the shaded plant first.
    first_is_small = geometry_utils.areaOverlappingCircles(0.0, 0.0, 1.0, 0.2, 0.0, 3.0)
    first_is_big = geometry_utils.areaOverlappingCircles(0.0, 0.0, 3.0, 0.2, 0.0, 1.0)
    assert first_is_small == 3.14 * 1.0 * 1.0
    assert first_is_big == 3.14 * 3.0 * 3.0


def test_point_inside_circle_includes_the_edge():
    assert geometry_utils.pointInsideCircle(0.0, 0.0, 1.0, 0.5, 0.5) == 1
    assert geometry_utils.pointInsideCircle(0.0, 0.0, 1.0, 1.0, 0.0) == 1
    assert geometry_utils.pointInsideCircle(0.0, 0.0, 1.0, 1.0, 0.1) == 0


def test_point_inside_square_includes_the_edge():
    # The square is centred on (squareX, squareY); size is the side length.
    assert geometry_utils.pointInsideSquare(0.0, 0.0, 10.0, 4.0, -4.0) == 1
    assert geometry_utils.pointInsideSquare(0.0, 0.0, 10.0, 5.0, 5.0) == 1
    assert geometry_utils.pointInsideSquare(0.0, 0.0, 10.0, 5.1, 0.0) == 0


def test_grid_spacing_for_seeds_on_a_square_world():
    # N points on a square grid in a world of side L are placed
    # L / (1 + sqrt(N)) apart, which leaves a margin at the edges.
    assert geometry_utils.placePointsInGrid(16, 100.0) == 100.0 / 5.0


def test_bounding_box_of_a_circle():
    assert geometry_utils.boundCircle(1.0, 2.0, 0.5) == [0.5, 1.5, 1.5, 2.5]
