"""Tests for the allometry and growth equations in Vida_Data/vplantr.py.

Each test sets the species constants it uses explicitly, so it reads as a
worked example of one equation and does not depend on any species file.
Symbols follow the comments in the species files:

    Ms  stem (woody) mass, kg          Ds  stem diameter, m
    Ml  canopy (leaf) mass, kg         Hs  stem height, m
"""

import math
import random

import pytest

import vplantr


@pytest.fixture
def plant(in_repo_root):
    """A plant (still a seed) with the default species' values loaded."""
    return vplantr.genericPlant()


# ---------------------------------------------------------------------------
# Stem diameter and height
# ---------------------------------------------------------------------------


def test_stem_diameter_from_stem_mass(plant):
    # Ds = speciesConstant20 * Ms ^ speciesExponent20; the radius is half of that.
    plant.speciesConstant20 = 0.03
    plant.speciesExponent20 = 0.4
    plant.massStem = 2.0
    plant.radiusStem = 0.01

    plant.calcRadiusStemFromMassStem()

    diameter = 0.03 * 2.0**0.4
    assert plant.radiusStem == diameter / 2.0
    assert plant.GRs == diameter / 2.0 - 0.01  # growth in radius this cycle


def set_height_constants(plant):
    # Young:  Hs = speciesConstant7 * Ds ^ speciesExponent7 - speciesConstant6
    # Mature: Hs = speciesConstant8 * ln(Ds) + heightStemMax
    plant.speciesConstant7 = 100.0
    plant.speciesExponent7 = 1.0
    plant.speciesConstant6 = 0.0
    plant.speciesConstant8 = 10.0
    plant.heightStemMax = 40.0


def test_young_plant_height_follows_the_power_law(plant, garden):
    set_height_constants(plant)
    plant.radiusStem = 0.005  # Ds = 0.01 m
    plant.age = 3

    plant.calcHeightStemFromRadiusStem(garden)

    # Young height is 100 * 0.01 = 1.0 m; the mature formula gives
    # 10 * ln(0.01) + 40 = -6.05 m, which is lower, so the plant is young.
    assert plant.heightStem == 100.0 * 0.01
    assert plant.isMature is False


def test_young_plant_uses_the_taller_of_the_two_heights(plant, garden):
    set_height_constants(plant)
    plant.radiusStem = 0.25  # Ds = 0.5 m
    plant.age = 30

    plant.calcHeightStemFromRadiusStem(garden)

    # Young formula: 100 * 0.5 = 50 m. Mature formula: 10 * ln(0.5) + 40 = 33.1 m.
    # The young height is still the taller, so the plant stays young.
    assert plant.heightStem == 100.0 * 0.5
    assert plant.isMature is False


def test_plant_becomes_mature_and_records_its_age(plant, garden):
    set_height_constants(plant)
    plant.speciesExponent7 = 2.0  # young: Hs = 100 * Ds^2
    plant.radiusStem = 0.1  # Ds = 0.2: young 4.0 m, mature 10 * ln(0.2) + 40 = 23.9 m
    plant.age = 12

    plant.calcHeightStemFromRadiusStem(garden)

    assert plant.isMature is True
    assert plant.matureAge == 12
    assert plant.heightStem == 10.0 * math.log(0.2) + 40.0


def test_a_negative_height_kills_the_plant(plant, garden):
    # A young plant keeps the taller of the two heights, so only a mature
    # plant can get a negative height: here 10 * ln(0.01) + 40 = -6.05 m.
    set_height_constants(plant)
    plant.isMature = True
    plant.radiusStem = 0.005  # Ds = 0.01 m

    plant.calcHeightStemFromRadiusStem(garden)

    assert plant.heightStem == 10.0 * math.log(0.01) + 40.0
    assert garden.killed == [plant]
    assert plant.causeOfDeath == "impossible height calculation"


def test_a_shrinking_stem_is_not_caught(plant, garden):
    # The check for a stem getting shorter compares the new height with
    # heightStem *after* heightStem has been set to the new height, so it
    # never fires; only a negative height kills the plant.
    set_height_constants(plant)
    plant.heightStem = 5.0
    plant.radiusStem = 0.01  # Ds = 0.02 m, so the young height is 2 m

    plant.calcHeightStemFromRadiusStem(garden)

    assert plant.heightStem == 2.0
    assert plant.GHs == 2.0 - 5.0
    assert garden.killed == []


# ---------------------------------------------------------------------------
# Canopy
# ---------------------------------------------------------------------------


def test_canopy_mass_uses_the_young_equation_before_maturity(plant):
    # Young:  Ml = speciesConstant2 * Ms ^ speciesExponent2
    plant.speciesConstant2 = 0.1
    plant.speciesExponent2 = 0.9
    plant.speciesConstant3 = 0.2
    plant.speciesExponent3 = 0.7
    plant.startMakingSeedsAge = 100
    plant.massStem = 4.0
    plant.massLeaf = 0.25
    plant.age = 5

    plant.calcMassLeafFromMassStem()

    assert plant.massLeaf == 0.1 * 4.0**0.9
    assert plant.GMl == 0.1 * 4.0**0.9 - 0.25


def test_canopy_mass_uses_the_mature_equation_after_maturity(plant):
    # Mature: Ml = speciesConstant3 * Ms ^ speciesExponent3
    plant.speciesConstant2 = 0.1
    plant.speciesExponent2 = 0.9
    plant.speciesConstant3 = 0.2
    plant.speciesExponent3 = 0.7
    plant.startMakingSeedsAge = 100
    plant.massStem = 4.0
    plant.isMature = True

    plant.calcMassLeafFromMassStem()

    assert plant.massLeaf == 0.2 * 4.0**0.7


def test_canopy_mass_also_counts_as_mature_after_startMakingSeedsAge(plant):
    plant.speciesConstant3 = 0.2
    plant.speciesExponent3 = 0.7
    plant.startMakingSeedsAge = 10
    plant.massStem = 4.0
    plant.age = 10
    plant.isMature = False

    plant.calcMassLeafFromMassStem()

    assert plant.massLeaf == 0.2 * 4.0**0.7


def test_canopy_radius_of_a_flat_disc(plant):
    # The canopy is a disc of thickness heightLeafMax:
    # area = Ml / densityLeaf / heightLeafMax, and radius = sqrt(area / 3.14).
    plant.massLeaf = 0.5
    plant.densityLeaf = 500.0
    plant.heightLeafMax = 0.001
    plant.leafIsHemisphere = False

    plant.calcRadiusLeafFromMassLeaf()

    disc_area = 0.5 / 500.0 / 0.001
    radius = math.sqrt(disc_area / 3.14)
    assert plant.radiusLeaf == radius
    assert plant.areaPhotosynthesis == 3.14 * radius * radius


def test_canopy_radius_of_a_hemisphere(plant):
    # A hemisphere has twice the surface of a disc of the same radius, so the
    # same leaf area spread over a hemisphere gives a radius 1/sqrt(2) as big.
    plant.massLeaf = 0.5
    plant.densityLeaf = 500.0
    plant.heightLeafMax = 0.001
    plant.leafIsHemisphere = True

    plant.calcRadiusLeafFromMassLeaf()

    disc_radius = math.sqrt(0.5 / 500.0 / 0.001 / 3.14)
    assert plant.radiusLeaf == disc_radius * 0.7071067812


# ---------------------------------------------------------------------------
# Photosynthesis
# ---------------------------------------------------------------------------


def set_light_constants(plant):
    # New mass = (light-use part) * areaAvailable * Ml ^ photoExponent, where
    # the light-use part is photoConstant for the lit fraction of the canopy
    # (scaled by the water and drought factors) and photoConstantShade for
    # the shaded fraction.
    plant.photoConstant = 1.5
    plant.photoConstantShade = 1.0
    plant.photoExponent = -0.5
    plant.fractionMinimumSurvival = 0.2
    plant.massLeaf = 4.0
    plant.areaPhotosynthesis = 10.0
    plant.waterGrowthFraction = 1.0
    plant.droughtGrowthFraction = 1.0


def test_new_mass_of_an_unshaded_plant(plant, garden):
    set_light_constants(plant)
    plant.areaCovered = 0.0

    new_mass = plant.calcNewMassFromLeaf(garden)

    assert new_mass == pytest.approx(1.5 * 10.0 * 4.0**-0.5)


def test_new_mass_of_a_partly_shaded_plant(plant, garden):
    set_light_constants(plant)
    plant.areaCovered = 4.0  # 60% of the canopy is lit

    new_mass = plant.calcNewMassFromLeaf(garden)

    light_use = 1.5 * 0.6 + 1.0 * 0.4
    assert new_mass == pytest.approx(light_use * 6.0 * 4.0**-0.5)


def test_water_and_drought_only_scale_the_lit_part(plant, garden):
    set_light_constants(plant)
    plant.areaCovered = 4.0
    plant.waterGrowthFraction = 0.5
    plant.droughtGrowthFraction = 0.8

    new_mass = plant.calcNewMassFromLeaf(garden)

    light_use = 1.5 * 0.6 * 0.5 * 0.8 + 1.0 * 0.4
    assert new_mass == pytest.approx(light_use * 6.0 * 4.0**-0.5)


def test_too_little_light_returns_minus_one(plant, garden):
    # -1.0 is the signal for "not enough light to survive". The fraction lit
    # must be strictly more than fractionMinimumSurvival.
    set_light_constants(plant)
    plant.areaCovered = 8.0  # exactly 20% lit
    assert plant.calcNewMassFromLeaf(garden) == -1.0


# ---------------------------------------------------------------------------
# Germination
# ---------------------------------------------------------------------------


def set_seed_constants(plant):
    plant.massSeedMax = 0.01
    plant.massSeed = 0.01
    plant.fractionSeedMassToPlant = 0.5
    plant.fractMassSeedMaxToGerm = 0.8
    plant.fractionCarbonToStem = 0.9
    plant.fractionFailGerminate = 0.0
    plant.countToGerm = 0


def test_a_seed_waits_while_it_is_delayed(plant, garden):
    set_seed_constants(plant)
    plant.countToGerm = 3

    plant.germinate(garden)

    assert plant.isSeed is True
    assert plant.countToGerm == 2


def test_a_healthy_seed_germinates(plant, garden):
    set_seed_constants(plant)

    plant.germinate(garden)

    # Half the seed's mass becomes plant; 90% of that goes to the stem.
    assert plant.isSeed is False
    assert plant.age == 1
    assert plant.massStem == 0.01 * 0.5 * 0.9
    assert plant.massLeaf == 0.01 * 0.5 - 0.01 * 0.5 * 0.9
    assert garden.numbSeeds == 0
    assert garden.numbPlants == 1
    assert garden.killed == []


def test_a_seed_below_80_percent_of_full_mass_fails(plant, garden):
    set_seed_constants(plant)
    plant.massSeed = 0.008  # exactly 80% is not enough

    plant.germinate(garden)

    assert garden.killed == [plant]
    assert plant.causeOfDeath == "failed to germinate(immaturity)"


def test_germination_can_fail_at_random(plant, garden):
    set_seed_constants(plant)
    plant.fractionFailGerminate = 1.0  # every seed fails

    plant.germinate(garden)

    assert garden.killed == [plant]
    assert plant.causeOfDeath == "failed to germinate(random death)"


def test_random_failure_can_be_ignored_in_the_first_cycle(plant, garden):
    set_seed_constants(plant)
    plant.fractionFailGerminate = 1.0
    garden.cycleNumber = 0
    garden.ignoreGermDeathAtStart = True

    plant.germinate(garden)

    assert plant.isSeed is False


# ---------------------------------------------------------------------------
# Making seeds
# ---------------------------------------------------------------------------


def set_reproduction_constants(plant):
    # Carbon available for seeds = reproductionConstant * massFixed ^ reproductionExponent,
    # times fractionCarbonToSeeds. That is divided into seeds of massSeedMax.
    plant.reproductionConstant = 1.0
    plant.reproductionExponent = 1.0
    plant.fractionCarbonToSeeds = 1.0
    plant.fractionSelfishness = 0.5
    plant.massSeedMax = 0.1
    plant.massFixed = 0.35
    plant.massFixedRecord = [0.35]
    plant.radiusLeaf = 1.0


def test_number_of_seeds_started(plant, garden):
    set_reproduction_constants(plant)
    random.seed(1)

    plant.makeSomeSeeds(10, garden)

    assert len(plant.seedList) == 3  # int(0.35 / 0.1)


def test_seeds_already_on_the_plant_count_towards_the_total(plant, garden):
    set_reproduction_constants(plant)
    random.seed(1)
    plant.makeSomeSeeds(10, garden)

    plant.makeSomeSeeds(10, garden)

    assert len(plant.seedList) == 3


def test_seeds_started_per_cycle_are_capped(plant, garden):
    set_reproduction_constants(plant)
    random.seed(1)

    plant.makeSomeSeeds(2, garden)

    assert len(plant.seedList) == 2


def test_a_stressed_plant_puts_all_its_spare_carbon_into_seeds(plant, garden):
    # A plant that normally keeps back half its spare carbon
    # (fractionCarbonToSeeds 0.5) uses all of it for seeds when this cycle's
    # growth falls below fractionSelfishness of its recent average.
    set_reproduction_constants(plant)
    plant.fractionCarbonToSeeds = 0.5
    plant.massFixedRecord = [1.0, 1.0]  # recent average 1.0; now 0.35
    random.seed(1)

    plant.makeSomeSeeds(10, garden)

    assert len(plant.seedList) == 3  # int(0.35 / 0.1), not int(0.175 / 0.1)


def test_a_new_seed_copies_the_species_settings_but_not_the_family(plant, garden):
    mother = vplantr.genericPlant()
    plant.motherPlant = mother
    plant.seedList = [vplantr.genericPlant()]
    plant.photoConstant = 2.5
    plant.radiusLeaf = 1.0

    seed = plant.copyForNewSeed()

    assert seed.photoConstant == 2.5
    # Lists are the seed's own copies, so changing one does not change the other.
    assert seed.colourLeaf == plant.colourLeaf
    assert seed.colourLeaf is not plant.colourLeaf
    seed.colourLeaf[2] = 0.25
    assert plant.colourLeaf[2] != 0.25
    # The family is not copied; zeroSeedValues() resets it for the new seed.
    assert seed.motherPlant is mother
    seed.zeroSeedValues()
    assert seed.motherPlant == 0
    assert seed.seedList == []
    assert len(plant.seedList) == 1


def test_a_new_seed_gets_its_own_copy_of_anything_that_is_not_a_plain_list(plant):
    # Lists of numbers are copied with list(); anything else (a list of
    # lists, a dictionary) still goes through deepcopy, all the way down.
    plant.pairs = [[1, 2], [3, 4]]
    plant.table = {"a": [1, 2]}

    seed = plant.copyForNewSeed()

    assert seed.pairs == plant.pairs
    assert seed.pairs[0] is not plant.pairs[0]
    assert seed.table == plant.table
    assert seed.table["a"] is not plant.table["a"]
    # numbers and strings are shared, as deepcopy shared them too
    assert seed.nameSpecies is plant.nameSpecies
