"""Tests for Vida_Data/list_utils.py and Vida_Data/colour_utils.py."""

import colour_utils
import list_utils


class Thing:
    def __init__(self, name, height):
        self.name = name
        self.height = height


def names(things):
    return [thing.name for thing in things]


def test_sort_by_attribute_is_shortest_first_and_keeps_ties_in_order():
    things = [Thing("a", 3.0), Thing("b", 1.0), Thing("c", 3.0), Thing("d", 2.0)]
    assert names(list_utils.sort_by_attr(things, "height")) == ["b", "d", "a", "c"]


def test_sort_by_attribute_in_place_changes_the_list_itself():
    things = [Thing("a", 2.0), Thing("b", 1.0)]
    same_list = things
    list_utils.sort_by_attr_inplace(things, "height")
    assert names(same_list) == ["b", "a"]


def test_remove_duplicates_keeps_one_of_each():
    # The order of the result is not guaranteed.
    assert sorted(list_utils.remove_duplicates([3, 1, 3, 2, 1])) == [1, 2, 3]


def test_sum_in_order_adds_first_to_last():
    # Adding 0.1 + 0.2 first gives 0.30000000000000004, and adding 0.3 to
    # that gives 0.6000000000000001. Python 3.12's sum() gives 0.6 instead,
    # which is why Vida uses sum_in_order: the same answer on every version.
    assert list_utils.sum_in_order([0.1, 0.2, 0.3]) == 0.6000000000000001
    assert list_utils.sum_in_order([]) == 0


def test_hsv_colours_map_to_autocad_colour_numbers():
    # HSV here is [hue in degrees, saturation 0-1, brightness 0-1].
    assert colour_utils.HSV_to_ACI([0.0, 0.0, 0.0]) == 0  # black
    # Pure red, green and blue appear twice in the colour table, and the
    # later entry wins, so they map to 10, 90 and 170 rather than 1, 3 and 5.
    assert colour_utils.HSV_to_ACI([0.0, 1.0, 1.0]) == 10
    assert colour_utils.HSV_to_ACI([120.0, 1.0, 1.0]) == 90
    assert colour_utils.HSV_to_ACI([240.0, 1.0, 1.0]) == 170
    assert colour_utils.HSV_to_ACI([0.0, 0.0, 1.0]) == 255  # white


def test_colours_not_in_the_table_use_the_closest_entry():
    # The default leaf colour at half brightness is RGB (7, 128, 0), which
    # is not in the table; the closest entry is (0, 129, 0), colour 94.
    assert colour_utils.HSV_to_ACI([116.6, 1.0, 0.5]) == 94
