"""Verification tests for the Pythagorean numerology engine.

Hardcoded reference profile: Johnathon Anthony Long, June 23, 1989.
Run with `pytest` or directly with `python tests/test_numerology.py`.
"""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engines import numerology


REFERENCE_NAME = "Johnathon Anthony Long"
REFERENCE_DATE = date(1989, 6, 23)


def test_life_path_is_2():
    # Month 6, Day 23 → 5, Year 1989 → 27 → 9; 6 + 5 + 9 = 20 → 2
    result = numerology.calculate_life_path(REFERENCE_DATE)
    assert result["number"] == 2
    assert result["total"] == 20
    assert not result["is_master"]


def test_expression_is_7():
    # Full name letter values total 97 → 16 → 7
    result = numerology.calculate_expression(REFERENCE_NAME)
    assert result["number"] == 7
    assert result["total"] == 97


def test_soul_urge_is_master_33():
    # Vowels total exactly 33 — the master number must NOT reduce to 6.
    result = numerology.calculate_soul_urge(REFERENCE_NAME)
    assert result["number"] == 33
    assert result["total"] == 33
    assert result["is_master"]


def test_personality_is_1():
    # Consonants total 64 → 10 → 1
    result = numerology.calculate_personality(REFERENCE_NAME)
    assert result["number"] == 1
    assert result["total"] == 64


def test_master_numbers_survive_reduction():
    for master in (11, 22, 33):
        value, steps = numerology.reduce_number(master)
        assert value == master
        assert steps == [master]
    # 29 reduces to 11 and stops there.
    assert numerology.reduce_number(29)[0] == 11
    # Non-master multi-digit numbers reduce fully.
    assert numerology.reduce_number(20)[0] == 2
    assert numerology.reduce_number(97)[0] == 7


def test_pythagorean_map_is_complete_and_correct():
    assert len(numerology.PYTHAGOREAN_MAP) == 26
    for index, letter in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
        assert numerology.PYTHAGOREAN_MAP[letter] == (index % 9) + 1


def test_reference_verification_report_passes():
    report = numerology.verify_reference_profile()
    assert report["all_passed"], report


if __name__ == "__main__":
    failures = 0
    for name, func in sorted(globals().items()):
        if name.startswith("test_") and callable(func):
            try:
                func()
                print(f"  ✓ {name}")
            except AssertionError as error:
                failures += 1
                print(f"  ✗ {name}: {error}")
    if failures:
        sys.exit(f"{failures} test(s) failed")
    print("All numerology verification tests passed.")
