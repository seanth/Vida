"""Shared setup for the unit tests.

Vida's modules live in Vida_Data/ and import each other by name, so that
folder is put on the import path here. Some of them also read files such as
Vida_Data/Default_species.yml relative to the current folder, so the
``in_repo_root`` fixture runs a test from the repository root.
"""

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "Vida_Data"))


@pytest.fixture
def in_repo_root(monkeypatch):
    monkeypatch.chdir(REPO)


class FakeGarden:
    """Just enough of a garden (the world) for the plant methods under test.

    It remembers what it was asked to kill instead of removing anything.
    """

    def __init__(self):
        self.killed = []
        self.planted = []
        self.cycleNumber = 5
        self.ignoreGermDeathAtStart = True
        self.numbSeeds = 1
        self.numbPlants = 0
        self.terrainImage = []

    def kill(self, thing):
        self.killed.append(thing)

    def plantSeed(self, seed):
        self.planted.append(seed)
        return seed


@pytest.fixture
def garden():
    return FakeGarden()
