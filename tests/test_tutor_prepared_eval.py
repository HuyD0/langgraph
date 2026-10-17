"""The prepared answers' eval follows the course's own Evals module (drill.tutor_prepared_eval)."""

import pytest

from drill import tutor_prepared_eval as tpe
from drill.content.build import build_data


@pytest.fixture(scope="module")
def data():
    return build_data()


def test_every_phase_reaches_every_split_and_whole_lessons_stay_together(data):
    splits = tpe.assign(data)
    assert set(splits) == set(data["lessons"]) and set(splits.values()) == set(tpe.SPLITS)
    phase = tpe.phases(data)
    for ph in set(phase.values()):
        assert {splits[l] for l in phase if phase[l] == ph} == set(tpe.SPLITS), f"{ph} is missing a split"


def test_placed_lessons_never_move_and_a_new_one_fills_its_phases_gap(data):
    splits = tpe.assign(data)
    assert tpe.assign(data, splits) == splits
    phase = tpe.phases(data)
    ship = [l for l in phase if phase[l] == "Ship"]
    without = {l: s for l, s in splits.items() if l != ship[0]}
    without_ship = [without[l] for l in ship[1:]]
    again = tpe.assign(data, without)
    assert {l: again[l] for l in without} == without  # nobody moved
    short = max(tpe.SPLITS, key=lambda sp: (tpe.SHARES[sp] * len(ship) - without_ship.count(sp), -tpe.SPLITS.index(sp)))
    assert again[ship[0]] == short


def test_the_committed_splits_cover_every_lesson(data):
    assert set(tpe.load_splits()) == set(data["lessons"]), "run `drill tutor prepared-eval` to place new lessons"


def test_wilson_and_kappa_match_the_course():
    rate, low, high = tpe.wilson(90, 100)
    assert rate == 0.9 and round(low, 3) == 0.826 and round(high, 3) == 0.945
    assert tpe.wilson(0, 0) == (0.0, 0.0, 0.0)
    # nearly everything passes: 96% raw agreement, but kappa shows the judge barely beats chance
    a = [True] * 96 + [False] * 4
    b = [True] * 98 + [False] * 2
    assert round(tpe.kappa(a, b), 2) == 0.66  # the same as sklearn.metrics.cohen_kappa_score
    assert tpe.kappa([True] * 5, [True] * 5) is None  # no variation: kappa is undefined, not perfect
