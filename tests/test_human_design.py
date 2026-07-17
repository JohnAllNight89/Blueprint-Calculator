"""Verification tests for the Human Design and Gene Keys engines.

Reference profile: Johnathon Anthony Long — 1989-06-24 01:55 UT
(June 23 1989, 21:55 EDT, Atlanta). Expected mechanics were derived by
hand from the computed activations: four defined channels forming two
separate areas of definition, no Sacral and no motor-to-Throat
connection → Projector, Splenic authority, Split Definition, 5/1
profile.
"""

import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engines import gene_keys, geolocation, human_design

BIRTH_UTC = datetime(1989, 6, 24, 1, 55, tzinfo=timezone.utc)


def _chart():
    return human_design.calculate_chart(BIRTH_UTC)


def test_wheel_anchors():
    # Gate 41 opens the wheel at 02°00' Aquarius (302°).
    assert human_design.gate_and_line(302.0) == {
        "gate": 41, "line": 1, "gate_name": "Decrease", "notation": "41.1",
    }
    # Just before the wheel start we are in the last line of Gate 60.
    assert human_design.gate_and_line(301.999)["gate"] == 60
    assert human_design.gate_and_line(301.999)["line"] == 6
    # The spring equinox point (0° Aries) falls inside Gate 25.
    assert human_design.gate_and_line(0.0)["gate"] == 25


def test_wheel_covers_all_64_gates():
    seen = {
        human_design.gate_and_line(index * 5.625 + 0.1)["gate"]
        for index in range(64)
    }
    assert seen == set(range(1, 65))


def test_design_sun_is_exactly_88_degrees_before_natal_sun():
    chart = _chart()
    personality_sun = next(
        e for e in chart["personality"]["activations"] if e["body"] == "Sun"
    )
    design_sun = next(
        e for e in chart["design"]["activations"] if e["body"] == "Sun"
    )
    arc = (personality_sun["longitude"] - design_sun["longitude"]) % 360
    assert abs(arc - 88.0) < 1e-5
    # ~88° of solar longitude corresponds to roughly 88-92 days prenatal.
    assert chart["design"]["moment_utc"].startswith("1989-03-25")


def test_design_solver_crosses_aries_boundary_without_looping():
    # Natal Sun at ~4.5° Aries places the design Sun at ~276.5° — the
    # solver has to walk backwards across 0° Aries and must still converge.
    natal = datetime(1989, 3, 25, 12, 0, tzinfo=timezone.utc)
    chart = human_design.calculate_chart(natal)
    personality_sun = next(
        e for e in chart["personality"]["activations"] if e["body"] == "Sun"
    )
    design_sun = next(
        e for e in chart["design"]["activations"] if e["body"] == "Sun"
    )
    arc = (personality_sun["longitude"] - design_sun["longitude"]) % 360
    assert abs(arc - 88.0) < 1e-5


def test_reference_type_authority_profile():
    chart = _chart()
    assert chart["type"] == "Projector"
    assert chart["authority"].startswith("Splenic")
    assert chart["profile"] == "5/1"
    assert chart["profile_label"] == "Heretic / Investigator"
    assert chart["definition"] == "Split Definition"
    assert chart["strategy"] == "Wait for the Invitation"


def test_reference_channels_and_centers():
    chart = _chart()
    labels = sorted(channel["label"] for channel in chart["channels"])
    assert labels == ["10–20", "17–62", "18–58", "28–38"]
    assert chart["defined_centers"] == ["Ajna", "G", "Root", "Spleen", "Throat"]
    assert "Sacral" in chart["open_centers"]


def test_reference_sun_gates():
    chart = _chart()
    personality_sun = next(
        e for e in chart["personality"]["activations"] if e["body"] == "Sun"
    )
    design_sun = next(
        e for e in chart["design"]["activations"] if e["body"] == "Sun"
    )
    assert personality_sun["notation"] == "15.5"
    assert design_sun["notation"] == "17.1"


def test_channels_reference_valid_gates_and_centers():
    for gate_a, gate_b in human_design.CHANNELS:
        assert gate_a in human_design.GATE_TO_CENTER
        assert gate_b in human_design.GATE_TO_CENTER
        assert (
            human_design.GATE_TO_CENTER[gate_a]
            != human_design.GATE_TO_CENTER[gate_b]
        )
    assert len(human_design.CHANNELS) == 36
    assert len(human_design.GATE_TO_CENTER) == 64


def test_gene_keys_activation_sequence():
    profile = gene_keys.calculate_profile(_chart())
    sequence = {
        sphere["sphere"]: sphere for sphere in profile["activation_sequence"]
    }
    assert list(sequence) == ["Life's Work", "Evolution", "Radiance", "Purpose"]
    assert sequence["Life's Work"]["notation"] == "15.5"
    assert sequence["Evolution"]["notation"] == "10.5"
    assert sequence["Radiance"]["notation"] == "17.1"
    assert sequence["Purpose"]["notation"] == "18.1"
    # Sun/Earth pairs sit in opposite gates, so keys must differ.
    assert sequence["Life's Work"]["gene_key"] != sequence["Evolution"]["gene_key"]


def test_gene_keys_dataset_complete():
    assert set(gene_keys.GENE_KEYS) == set(range(1, 65))
    for key, (name, shadow, gift, siddhi) in gene_keys.GENE_KEYS.items():
        assert all(isinstance(field, str) and field for field in (name, shadow, gift, siddhi)), key


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
    print("All Human Design / Gene Keys verification tests passed.")
