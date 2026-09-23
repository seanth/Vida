"""Tests for Vida_Data/vplacement.py: reading seed placement files."""

import vplacement


def test_each_line_becomes_species_x_y_and_delay(tmp_path):
    placement = tmp_path / "placement.csv"
    placement.write_text("Generic Gymnosperm.yml, 0.0, 1.5, 0\n\nrandom, -2.0, 3.0, 5\n")

    lines = vplacement.readPlacementFile(placement)

    assert lines == [["Generic Gymnosperm.yml", 0.0, 1.5, 0], ["random", -2.0, 3.0, 5]]


def test_short_lines_are_filled_in_and_long_lines_cut_short():
    lines = vplacement.checkSeedPlacementList(["random, 1.0, 2.0", "random, 1.0, 2.0, 3, 9.9"])
    assert lines == [["random", 1.0, 2.0, 0], ["random", 1.0, 2.0, 3]]


def test_whole_number_coordinates_are_rejected():
    # "4" is read as a whole number (int), and x and y must be decimals (float).
    lines = vplacement.checkSeedPlacementList(["random, 4, 2.0, 0", "random, 1.0, 2.0, 0"])
    assert lines == [["random", 1.0, 2.0, 0]]


def test_after_a_bad_line_the_next_line_is_not_checked():
    # The check deletes bad lines from the list while looping over it, so the
    # line after a deleted one is skipped: here the second bad line is kept.
    lines = vplacement.checkSeedPlacementList(["a.yml, 1, 2.0, 0", "b.yml, 3, 4.0, 0", "c.yml, 5.0, 6.0, 0"])
    assert lines == [["b.yml", 3, 4.0, 0], ["c.yml", 5.0, 6.0, 0]]
