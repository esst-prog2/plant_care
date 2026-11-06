import pytest

from app.care import (
    DROOPING,
    MAX_INTERVAL_DAYS,
    MIN_INTERVAL_DAYS,
    ON_TIME,
    WET,
    adjust_for_feedback,
    starting_interval,
)

# --- starting interval, from the bundled default and the condition answers -------------


def test_no_conditions_answered_keeps_the_bundled_default():
    assert starting_interval(7, 0, 0, 0) == 7


@pytest.mark.parametrize(
    "light, warmth, pot, expected",
    [
        (2, 0, 0, 9),  # low light: +2
        (-2, 0, 0, 5),  # bright light: -2
        (0, 1, 0, 8),  # cooler spot: +1
        (0, -1, 0, 6),  # warmer spot: -1
        (0, 0, -1, 6),  # clay pot: -1
        (0, 0, 1, 8),  # plastic/glazed pot: +1
    ],
)
def test_one_condition_answered(light, warmth, pot, expected):
    assert starting_interval(7, light, warmth, pot) == expected


def test_combined_conditions_add_up():
    assert starting_interval(7, 2, 1, -1) == 9  # 7 + 2 + 1 - 1


def test_starting_interval_is_clamped_to_the_minimum():
    assert starting_interval(4, -2, -1, -1) == MIN_INTERVAL_DAYS


def test_starting_interval_is_clamped_to_the_maximum():
    assert starting_interval(28, 2, 1, 1) == MAX_INTERVAL_DAYS


# --- watering feedback ------------------------------------------------------------------


def test_soil_still_wet_lengthens_the_interval():
    assert adjust_for_feedback(7, WET) == 8


def test_leaf_drooping_shortens_the_interval():
    assert adjust_for_feedback(7, DROOPING) == 6


def test_right_on_time_leaves_it_unchanged():
    assert adjust_for_feedback(7, ON_TIME) == 7


def test_no_choice_leaves_it_unchanged():
    assert adjust_for_feedback(7, None) == 7


def test_feedback_does_not_go_below_the_minimum():
    assert adjust_for_feedback(MIN_INTERVAL_DAYS, DROOPING) == MIN_INTERVAL_DAYS


def test_feedback_does_not_go_above_the_maximum():
    assert adjust_for_feedback(MAX_INTERVAL_DAYS, WET) == MAX_INTERVAL_DAYS
