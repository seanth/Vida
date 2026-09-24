"""Tests for species settings shared by the plants of a species (vplantr.py)."""

import copy
import pickle

import pytest

import vplantr


@pytest.fixture
def platonic(in_repo_root, tmp_path):
    """A species' template seed, made as Vida makes one, with shared settings."""
    speciesFile = tmp_path / "Testus_plantus.yml"
    speciesFile.write_text("nameSpecies: Testus_plantus\nphotoConstant: 2.5\ncolourStem: [20.0, 0.9, 0.5]\n")
    seed = vplantr.genericPlant()
    names = seed.importPrefs(str(speciesFile))
    return vplantr.shareSpeciesSettings(seed, "Testus_plantus.yml", vplantr.defaultSettingNames() + names)


def test_settings_are_kept_on_the_species_class(platonic):
    assert type(platonic).__name__ == "Testus_plantus"
    assert isinstance(platonic, vplantr.genericPlant)
    assert platonic.photoConstant == 2.5
    assert "photoConstant" not in vars(platonic)
    assert "massSeedMax" not in vars(platonic)  # from Default_species.yml
    assert platonic.massSeedMax == type(platonic).massSeedMax


def test_lists_changed_inside_a_plant_stay_on_the_plant(platonic):
    for name in vplantr.PER_PLANT_SETTINGS:
        assert name in vars(platonic)
    seed = platonic.copyForNewSeed()
    seed.colourLeaf[2] = 0.25
    assert platonic.colourLeaf[2] != 0.25


def test_changing_a_setting_on_one_plant_leaves_the_others_alone(platonic):
    # as a Species event does
    one = copy.copy(platonic)
    other = copy.copy(platonic)
    setattr(one, "photoConstant", 9.0)
    assert one.photoConstant == 9.0
    assert other.photoConstant == 2.5
    assert type(platonic).photoConstant == 2.5


def test_a_new_seed_copies_only_the_plants_own_values(platonic):
    seed = platonic.copyForNewSeed()
    assert type(seed) is type(platonic)
    assert set(vars(seed)) == set(vars(platonic))
    assert len(vars(seed)) < len(type(platonic).sharedSpeciesSettings) + 60


def test_the_same_settings_give_the_same_class(platonic):
    shared = type(platonic).sharedSpeciesSettings
    assert vplantr.speciesClass(vplantr.genericPlant, "Testus_plantus.yml", dict(shared)) is type(platonic)
    changed = dict(shared, photoConstant=3.0)
    assert vplantr.speciesClass(vplantr.genericPlant, "Testus_plantus.yml", changed) is not type(platonic)


def test_saving_and_loading_plants(platonic):
    plants = []
    for i in range(50):
        plant = platonic.copyForNewSeed()
        plant.x = float(i)
        plant.motherPlant = plant  # a plant can be its own mother, as the first seeds are
        plants.append(plant)
    loaded = pickle.loads(pickle.dumps(plants))
    assert [plant.x for plant in loaded] == [float(i) for i in range(50)]
    assert loaded[3].motherPlant is loaded[3]
    assert type(loaded[0]) is type(platonic)
    assert loaded[0].photoConstant == 2.5
    # the species' settings are saved once, not once for each plant
    one = len(pickle.dumps(plants[:1]))
    assert len(pickle.dumps(plants)) < one * 10


def test_deep_copies(platonic):
    copied = copy.deepcopy(platonic)
    assert type(copied) is type(platonic)
    assert copied.photoConstant == 2.5
    assert copied.colourLeaf == platonic.colourLeaf
    assert copied.colourLeaf is not platonic.colourLeaf
