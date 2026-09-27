"""Tests for Vida_Data/vevents.py: kill zones, safe zones and regions."""

import vevents


class Thing:
    """A stand-in for a plant or seed, with just what the zone code looks at."""

    def __init__(self, x, y, isSeed=False, species="Oak", radius=0.1, height=1.0):
        self.x = x
        self.y = y
        self.isSeed = isSeed
        self.nameSpecies = species
        self.radiusStem = radius
        self.radiusSeed = radius
        self.heightStem = height
        self.subregion = []
        self.causeOfDeath = ""


class Region:
    def __init__(self, name, shape, x, y, size):
        self.name = name
        self.shape = shape
        self.x = x
        self.y = y
        self.size = size


def test_selection_tests():
    assert vevents.selectionMatches(5.0, ">", 2.0) is True
    assert vevents.selectionMatches(1.0, ">", 2.0) is False
    assert vevents.selectionMatches(1.0, "<", 2.0) is True
    assert vevents.selectionMatches(2.0, "=", 2.0) is True
    assert vevents.selectionMatches(2.0, "==", 3.0) is False


def test_reading_a_selection():
    zone = {"selection": [{"attribute": "heightStem", "logic": ">", "value": 2.0}]}
    assert vevents.readZoneSelection(zone) == ("heightStem", ">", 2.0)


def test_a_zone_without_a_selection_selects_everything():
    assert vevents.readZoneSelection({})[0] == "none"


def test_a_selection_missing_a_part_is_ignored():
    # Each of attribute, logic and value is needed. Only value used to be
    # checked, so a selection without attribute or logic crashed.
    for missing in ["attribute", "logic", "value"]:
        selection = {"attribute": "heightStem", "logic": ">", "value": 2.0}
        del selection[missing]
        assert vevents.readZoneSelection({"selection": [selection]})[0] == "none"


def test_a_selection_with_bad_logic_is_ignored():
    zone = {"selection": [{"attribute": "heightStem", "logic": "!=", "value": 2.0}]}
    assert vevents.readZoneSelection(zone)[0] == "none"


def test_greater_or_less_than_a_word_is_ignored():
    zone = {"selection": [{"attribute": "nameSpecies", "logic": "<", "value": "Oak"}]}
    assert vevents.readZoneSelection(zone)[0] == "none"


def test_circle_zones_count_things_touching_the_edge():
    # A circle zone of size (radius) 5 centred on 0,0. A stem of radius 0.1
    # centred 5.05 away still touches it.
    assert vevents.whereInZone(Thing(0.0, 0.0), "circle", 0.0, 0.0, 5.0) > 0
    assert vevents.whereInZone(Thing(5.05, 0.0), "circle", 0.0, 0.0, 5.0) > 0
    assert vevents.whereInZone(Thing(6.0, 0.0), "circle", 0.0, 0.0, 5.0) == 0


def test_square_zones_only_look_at_the_centre():
    # A square zone of size (side) 10 centred on 0,0 reaches from -5 to 5.
    assert vevents.whereInZone(Thing(5.0, 5.0), "square", 0.0, 0.0, 10.0) > 0
    assert vevents.whereInZone(Thing(5.05, 0.0), "square", 0.0, 0.0, 10.0) == 0


def test_killzone_kills_only_its_targets(garden):
    oak_inside = Thing(1.0, 1.0)
    pine_inside = Thing(-1.0, 1.0, species="Pine")
    seed_inside = Thing(0.0, 0.0, isSeed=True)
    oak_outside = Thing(20.0, 20.0)
    garden.soil = [oak_inside, pine_inside, seed_inside, oak_outside]

    zone = {"x": 0.0, "y": 0.0, "size": 10.0, "shape": "square", "target": "plants", "species_name": "Oak"}
    vevents.zoneEvent(garden, "Killzone", zone, 0)

    assert garden.killed == [oak_inside]
    assert oak_inside.causeOfDeath == "killzone"


def test_killzone_with_a_selection(garden):
    short = Thing(1.0, 1.0, height=1.0)
    tall = Thing(-1.0, 1.0, height=5.0)
    garden.soil = [short, tall]

    zone = {"x": 0.0, "y": 0.0, "size": 10.0, "shape": "square", "target": "all",
            "selection": [{"attribute": "heightStem", "logic": ">", "value": 2.0}]}
    vevents.zoneEvent(garden, "Killzone", zone, 0)

    assert garden.killed == [tall]


def test_killzone_selection_on_a_missing_attribute_is_dropped(garden):
    # When the attribute is missing, that object is spared and a warning is
    # printed, and the selection is ignored for the rest of the zone.
    first = Thing(1.0, 1.0)
    second = Thing(-1.0, 1.0)
    garden.soil = [first, second]

    zone = {"x": 0.0, "y": 0.0, "size": 10.0, "shape": "square", "target": "all",
            "selection": [{"attribute": "noSuchThing", "logic": ">", "value": 2.0}]}
    vevents.zoneEvent(garden, "Killzone", zone, 0)

    assert garden.killed == [second]


def test_safezone_kills_everything_outside_and_the_non_target_inside(garden):
    plant_inside = Thing(1.0, 1.0)
    seed_inside = Thing(0.0, 0.0, isSeed=True)
    plant_outside = Thing(20.0, 20.0)
    garden.soil = [plant_inside, seed_inside, plant_outside]

    zone = {"x": 0.0, "y": 0.0, "size": 10.0, "shape": "square", "target": "plants"}
    vevents.zoneEvent(garden, "Safezone", zone, 0)

    assert garden.killed == [seed_inside, plant_outside]


def test_new_region_is_added_to_things_inside_it(garden, in_repo_root):
    inside = Thing(1.0, 1.0)
    outside = Thing(20.0, 20.0)
    garden.soil = [inside, outside]
    garden.theRegions = []

    region_settings = {"name": "shady", "shape": "circle", "x": 0.0, "y": 0.0, "size": 10.0,
                       "lightIntensity": 0.5}
    updatePlants = vevents.regionEvent(garden, region_settings, False, 0)

    region = garden.theRegions[0]
    assert region.lightIntensity == 0.5
    assert inside.subregion == [region]
    assert outside.subregion == []
    assert updatePlants is False


def test_changed_region_is_added_to_things_now_inside_it(garden, in_repo_root):
    garden.soil = []
    garden.theRegions = []
    vevents.regionEvent(garden, {"name": "shady", "shape": "square", "x": 0.0, "y": 0.0, "size": 2.0}, False, 0)
    region = garden.theRegions[0]

    now_inside = Thing(4.0, 0.0)
    garden.soil = [now_inside]
    updatePlants = vevents.regionEvent(garden, {"name": "shady", "size": 10.0}, False, 0)

    assert updatePlants is True
    assert now_inside.subregion == [region]


def test_species_event_changes_only_that_species(garden):
    oak = Thing(0.0, 0.0)
    pine = Thing(1.0, 0.0, species="Pine")
    oak.makeSeeds = True
    pine.makeSeeds = True
    garden.soil = [oak, pine]

    vevents.speciesEvent(garden, {"name": "Oak", "makeSeeds": False}, 0)

    assert oak.makeSeeds is False
    assert pine.makeSeeds is True
