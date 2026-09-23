"""Tests for Vida_Data/vjson.py: the file the web viewer reads."""

import json

import vjson


class Thing:
    def __init__(self, species, x, y, isSeed):
        self.nameSpecies = species
        self.x = x
        self.y = y
        self.elevation = 0.5
        self.isSeed = isSeed
        self.isMature = True
        self.age = 7
        self.radiusSeed = 0.01
        self.radiusStem = 0.05
        self.heightStem = 3.0
        self.radiusLeaf = 1.25
        self.colourSpecies = [285.0, 1.0, 1.0]
        self.colourLeaf = [116.6, 1.0, 0.75]
        self.colourStem = [20.0, 0.9, 0.5]
        self.canopyTransmittance = 0.02
        self.causeOfDeath = "lack of light"


class Region:
    name = "shade"
    shape = "circle"
    x = 1.0
    y = 2.0
    size = 10.0
    lightIntensity = 0.5


class World:
    name = "test"
    theWorldSize = 20
    terrainImage = []
    cycleNumber = 3
    waterLevel = 0.0
    lightIntensity = 1.0

    def __init__(self):
        self.soil = [Thing("Oak", 1.0, 2.0, False), Thing("Oak", 3.0, 4.0, True), Thing("Pine", 5.0, 6.0, False)]
        self.deathNote = [Thing("Oak", 0.0, 0.0, False)]
        self.theRegions = [Region()]


def test_viewer_file(tmp_path):
    world = World()
    viewer = vjson.ViewerFile(tmp_path / "viewer.jsonl", world, "test")
    viewer.writeCycle(world)
    world.cycleNumber = 4
    viewer.writeCycle(world)
    viewer.close()

    lines = (tmp_path / "viewer.jsonl").read_text().splitlines()
    header = json.loads(lines[0])
    first = json.loads(lines[1])
    second = json.loads(lines[2])

    assert header["worldSize"] == 20
    assert header["terrain"] is None
    assert header["plantFields"] == vjson.PLANT_FIELDS

    # species are numbered as they first appear, and only described once
    assert [species["name"] for species in first["newSpecies"]] == ["Oak", "Pine"]
    assert second["newSpecies"] == []

    oak = dict(zip(header["plantFields"], first["plants"][0]))
    assert oak == {"x": 1.0, "y": 2.0, "elevation": 0.5, "stemRadius": 0.05, "stemHeight": 3.0,
                   "canopyRadius": 1.25, "species": 0, "light": 0.75, "mature": 1, "age": 7}
    assert first["seeds"] == [[3.0, 4.0, 0.5, 0.01, 0]]
    assert first["deaths"] == {"lack of light": 1}
    assert first["regions"][0]["lightIntensity"] == 0.5
    assert second["cycle"] == 4


def test_numbers_that_json_cannot_hold_become_null():
    assert vjson.number(float("nan")) is None
    assert vjson.number(float("inf")) is None
    assert vjson.number(1.234567) == 1.2346


def test_the_viewer_sample_matches_the_file_format():
    # viewer/sample is made by vjson; remake it (see viewer/README.md) if this fails
    import gzip
    from pathlib import Path

    sample = Path(__file__).resolve().parents[2] / "viewer" / "sample" / "viewer.jsonl.gz"
    with gzip.open(sample, "rt") as theFile:
        header = json.loads(theFile.readline())
        first = json.loads(theFile.readline())
    assert header["format"] == "vida-viewer"
    assert header["version"] == vjson.FORMAT_VERSION
    assert header["plantFields"] == vjson.PLANT_FIELDS
    assert header["seedFields"] == vjson.SEED_FIELDS
    assert len(first["plants"][0]) == len(vjson.PLANT_FIELDS)
