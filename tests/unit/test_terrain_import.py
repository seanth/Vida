"""Tests for Vida_Data/vterrainImport.py: reading heights from an image."""

from PIL import Image

import vterrainImport


def make_image(width, height, values, mode="L"):
    """Build a small image in the [mode, size, bytes] form Vida stores."""
    image = Image.new(mode, (width, height))
    image.putdata(values)
    return [image.mode, image.size, image.tobytes()]


# A 4 x 3 greyscale image whose pixel values count up 0, 1, 2, ... row by row:
#    0  1  2  3
#    4  5  6  7
#    8  9 10 11
IMAGE = make_image(4, 3, list(range(12)))


def test_pixel_lookup_rounds_to_the_nearest_pixel():
    assert vterrainImport.getPixelValue(0, 0, IMAGE) == 0
    assert vterrainImport.getPixelValue(1.4, 0, IMAGE) == 1
    assert vterrainImport.getPixelValue(1.6, 0, IMAGE) == 2
    assert vterrainImport.getPixelValue(2, 1, IMAGE) == 6


def test_pixel_lookup_rounds_halves_to_even():
    # Python's round() sends x.5 to the nearest even number.
    assert vterrainImport.getPixelValue(2.5, 0, IMAGE) == 2
    assert vterrainImport.getPixelValue(1.5, 0, IMAGE) == 2


def test_pixel_lookup_beyond_the_far_edge_uses_the_last_pixel():
    assert vterrainImport.getPixelValue(9, 0, IMAGE) == 3
    assert vterrainImport.getPixelValue(9, 9, IMAGE) == 11


def test_pixel_lookup_with_negative_coordinates_wraps_around():
    # Negative coordinates count back from the far edge, like negative list
    # indexes in Python (this is Pillow's behaviour), so -1 is the last column.
    assert vterrainImport.getPixelValue(-1, 0, IMAGE) == 3
    assert vterrainImport.getPixelValue(-4, 0, IMAGE) == 0


def test_elevation_is_proportional_to_the_pixel_value():
    # Pixel value 255 is the maximum elevation, 0 is zero.
    assert vterrainImport.elevationFromPixel(255, 10.0) == 10.0
    assert vterrainImport.elevationFromPixel(51, 10.0) == 2.0
    assert vterrainImport.elevationFromPixel(0, 10.0) == 0.0


def test_elevation_defaults_to_a_50_metre_range():
    assert vterrainImport.elevationFromPixel(255) == 50.0


def test_colour_pixels_use_the_red_value():
    assert vterrainImport.elevationFromPixel((51, 200, 0), 10.0) == 2.0
