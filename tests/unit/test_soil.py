"""Tests for Vida_Data/vsoil.py: the soil must behave exactly like a list."""

import copy
import pickle
import random

import pytest

import vsoil


class Thing:
    """A stand-in for a plant or seed (compared by identity, like a plant)."""

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "Thing(%s)" % self.name


def nameOf(thing):
    return thing.name


def check_same(soil, plain):
    assert list(soil) == plain
    assert len(soil) == len(plain)
    for place, thing in enumerate(plain):
        assert soil.index(thing) == place
        assert thing in soil


def test_finding_and_removing_like_a_list():
    things = [Thing(i) for i in range(10)]
    soil = vsoil.Soil(things[:6])
    plain = things[:6]
    soil.append(things[6])
    plain.append(things[6])
    soil.remove(things[2])
    plain.remove(things[2])
    del soil[0]
    del plain[0]
    assert soil.pop() is plain.pop()
    check_same(soil, plain)
    assert things[2] not in soil
    assert things[9] not in soil
    assert [1, 2] not in soil  # something that can't be a key is never in it
    with pytest.raises(ValueError):
        soil.index(things[9])
    with pytest.raises(ValueError):
        soil.remove(things[2])


def test_many_random_changes_match_a_list():
    random.seed(4)
    soil = vsoil.Soil()
    plain = []
    made = 0
    for step in range(20000):
        choice = random.random()
        if choice < 0.5 or not plain:
            thing = Thing(made)
            made += 1
            soil.append(thing)
            plain.append(thing)
        elif choice < 0.8:
            thing = random.choice(plain)
            assert soil.index(thing) == plain.index(thing)
            soil.remove(thing)
            plain.remove(thing)
        elif choice < 0.9:
            place = random.randrange(len(plain))
            del soil[place]
            del plain[place]
        elif choice < 0.95:
            thing = random.choice(plain)
            assert thing in soil
        else:
            place = random.randrange(len(plain))
            assert soil[place] is plain[place]
        if step % 997 == 0:
            check_same(soil, plain)
    check_same(soil, plain)


def test_going_through_it_while_removing_is_exactly_like_a_list():
    # Removing the thing you're on skips the next one, and things added while
    # going through are reached too: Vida's drought and waterlogging checks
    # depend on this, so it must stay the same.
    def walk(soil, things):
        seen = []
        for thing in soil:
            seen.append(thing.name)
            if thing.name % 3 == 0:
                soil.remove(thing)
            if thing.name == 4:
                soil.append(things[20])
        return seen, [thing.name for thing in soil]

    things = [Thing(i) for i in range(21)]
    assert walk(vsoil.Soil(things[:12]), things) == walk(things[:12], things)


def test_rearranging_still_works():
    things = [Thing(i) for i in range(8)]
    soil = vsoil.Soil(things[:5])
    plain = things[:5]
    for method, arguments in [("insert", (1, things[5])), ("reverse", ()), ("extend", ([things[6]],))]:
        getattr(soil, method)(*arguments)
        getattr(plain, method)(*arguments)
        check_same(soil, plain)
    soil.sort(key=nameOf)
    plain.sort(key=nameOf)
    check_same(soil, plain)
    soil[0] = things[7]
    plain[0] = things[7]
    check_same(soil, plain)
    del soil[1:3]
    del plain[1:3]
    check_same(soil, plain)
    soil += [things[2]]
    plain += [things[2]]
    check_same(soil, plain)
    assert type(soil[:]) is list  # a copy is a plain list, as before


def test_the_same_thing_twice_behaves_like_a_list():
    things = [Thing(i) for i in range(3)]
    soil = vsoil.Soil(things)
    plain = list(things)
    soil.append(things[1])
    plain.append(things[1])
    assert soil.index(things[1]) == plain.index(things[1]) == 1
    soil.remove(things[1])
    plain.remove(things[1])
    assert list(soil) == plain
    assert soil.index(things[1]) == plain.index(things[1]) == 2


def test_growing_past_its_room_keeps_working():
    things = [Thing(i) for i in range(1000)]
    soil = vsoil.Soil()
    plain = []
    for thing in things:
        soil.append(thing)
        plain.append(thing)
        if thing.name % 7 == 0:
            soil.remove(thing)
            plain.remove(thing)
    check_same(soil, plain)


def test_saving_and_copying():
    things = [Thing(i) for i in range(5)]
    soil = vsoil.Soil(things)
    soil.remove(things[1])
    loaded = pickle.loads(pickle.dumps(soil))
    assert type(loaded) is vsoil.Soil
    assert [thing.name for thing in loaded] == [0, 2, 3, 4]
    assert loaded.index(loaded[2]) == 2
    copied = copy.deepcopy(soil)
    assert [thing.name for thing in copied] == [0, 2, 3, 4]
    assert copied.index(copied[3]) == 3
