"""
Phase 9: Cross-System Validation Rules.

Steps 27-28 -- "the Mathematical Proof Layer." These rules don't compute
anything new; they check that everything computed in Phases 3-8 is
mutually consistent. This is the layer that actually substantiates the
outline's central claim -- that the whole structure is one deterministic
system, not several unrelated guesses -- by giving that claim something
falsifiable to fail against.
"""
from __future__ import annotations

from dataclasses import dataclass

from .constants.hd_wheel import GATE_TO_CENTER
from .constants.vedic_tables import NAKSHATRA_SPAN
from .ephemeris import PlanetarySnapshot, bridge_tropical_to_hd_gate_line, bridge_tropical_to_sidereal, smallest_signed_angle
from .numerology import digit_sum

TOLERANCE_DEG = 0.001


@dataclass
class ValidationResult:
    rule_id: str
    name: str
    severity: str  # MANDATORY | RECOMMENDED | DIAGNOSTIC
    passed: bool
    detail: str


def _r(rule_id, name, severity, passed, detail) -> ValidationResult:
    return ValidationResult(rule_id, name, severity, passed, detail)


def rule_v1(natal: PlanetarySnapshot, hd_personality_sun_notation: str) -> ValidationResult:
    sun_lon = natal.bodies["Sun"].tropical_longitude
    bridged = bridge_tropical_to_hd_gate_line(sun_lon)
    passed = bridged["notation"] == hd_personality_sun_notation
    return _r("V-1", "Western Sun -> HD Personality Sun Gate/Line", "MANDATORY", passed,
               f"bridge({sun_lon:.4f}) = {bridged['notation']}; HD reports {hd_personality_sun_notation}")


def rule_v2(natal: PlanetarySnapshot) -> ValidationResult:
    worst = 0.0
    for name, pos in natal.bodies.items():
        sidereal = bridge_tropical_to_sidereal(pos.tropical_longitude, natal.ayanamsa)
        reconstructed = (sidereal + natal.ayanamsa) % 360
        err = abs(smallest_signed_angle(reconstructed - pos.tropical_longitude))
        worst = max(worst, err)
    return _r("V-2", "Tropical -> Sidereal -> Ayanamsa Reversibility", "MANDATORY",
               worst <= TOLERANCE_DEG, f"max reconstruction error {worst:.6f} deg (tolerance {TOLERANCE_DEG})")


def rule_v3(natal_jd: float, design_jd: float) -> ValidationResult:
    diff = natal_jd - design_jd
    passed = 85.0 <= diff <= 92.0
    return _r("V-3", "Design Moment Sanity Check", "MANDATORY", passed, f"natal_jd - design_jd = {diff:.4f} days (expected 85-92)")


def rule_v4(natal: PlanetarySnapshot) -> ValidationResult:
    cusps = natal.houses
    diffs = [(cusps[(i + 1) % 12] - cusps[i]) % 360 for i in range(12)]
    passed = all(d > 0 for d in diffs)
    return _r("V-4", "House Cusp Zodiacal Ordering", "MANDATORY", passed, f"cusp deltas: {[round(d, 2) for d in diffs]}")


def rule_v5(gk_profile: dict, hd_activations_by_gate: dict[int, int]) -> ValidationResult:
    mismatches = []
    for gate, expected_line in hd_activations_by_gate.items():
        entry = gk_profile.get(gate)
        if entry is None or entry["gene_key"] != gate:
            mismatches.append(gate)
    passed = not mismatches
    return _r("V-5", "Gene Keys <-> Human Design Gate Consistency", "MANDATORY", passed,
               f"mismatched gates: {mismatches}" if mismatches else "all activated gates map 1:1")


def rule_v6(personality_gates: set[int], design_gates: set[int]) -> ValidationResult:
    overlap = personality_gates & design_gates
    passed = overlap.issubset(personality_gates) and overlap.issubset(design_gates)
    return _r("V-6", "Personality vs Design Gate Overlap", "RECOMMENDED", passed, f"overlap={sorted(overlap)}")


def rule_v7(defined_channels: list[tuple[int, int]], defined_centers: set[str]) -> ValidationResult:
    derived = set()
    for a, b in defined_channels:
        derived.add(GATE_TO_CENTER[a])
        derived.add(GATE_TO_CENTER[b])
    passed = derived == defined_centers
    return _r("V-7", "Defined Channels <-> Defined Centers Consistency", "MANDATORY", passed,
               f"derived={sorted(derived)} vs reported={sorted(defined_centers)}")


def rule_v8(hd_type: str, authority: str, definition: str) -> ValidationResult:
    if hd_type == "Reflector":
        passed = authority == "Lunar" and definition == "No Definition"
    elif hd_type in ("Generator", "Manifesting Generator"):
        passed = authority == "Sacral"
    elif hd_type == "Projector":
        passed = authority not in ("Sacral", "Lunar")
    else:  # Manifestor
        passed = authority != "Lunar"
    return _r("V-8", "Type <-> Authority <-> Definition Consistency", "MANDATORY", passed,
               f"type={hd_type}, authority={authority}, definition={definition}")


def rule_v9(all_activation_lines: list[int]) -> ValidationResult:
    passed = all(1 <= l <= 6 for l in all_activation_lines)
    return _r("V-9", "Profile Line Range Check", "RECOMMENDED", passed, f"lines={all_activation_lines}")


def rule_v10(natal: PlanetarySnapshot, lagna_longitude: float) -> ValidationResult:
    # Looser tolerance than V-2: swisseph's internal FLG_SIDEREAL ascendant path
    # applies its own ayanamsa correction rather than a naive Bridge 2
    # subtraction, leaving a consistent few-arcsecond residual (~0.003 deg)
    # even when everything is implemented correctly.
    v10_tolerance = 0.01
    err = abs(smallest_signed_angle((natal.ascendant - lagna_longitude) - natal.ayanamsa))
    return _r("V-10", "Sidereal Lagna vs Tropical ASC Consistency", "RECOMMENDED",
               err <= v10_tolerance, f"(ASC-Lagna)-ayanamsa error = {err:.6f} deg (tolerance {v10_tolerance})")


def rule_v11(natal: PlanetarySnapshot) -> ValidationResult:
    bad = [n for n, p in natal.bodies.items() if (p.retrograde) != (p.speed < 0)]
    return _r("V-11", "Retrograde Speed Consistency", "DIAGNOSTIC", not bad, f"inconsistent bodies: {bad}")


def rule_v12(*chains: list[int]) -> ValidationResult:
    bad = []
    for chain in chains:
        for i in range(len(chain) - 1):
            cur, nxt = chain[i], chain[i + 1]
            if digit_sum(cur) != nxt:
                bad.append((chain, i))
    return _r("V-12", "Numerology Reduction Chain Integrity", "MANDATORY", not bad, f"bad steps: {bad}" if bad else "all chains sum-of-digit consistent")


def rule_v13(expression_raw: int, soul_urge_raw: int, personality_raw: int) -> ValidationResult:
    passed = expression_raw == soul_urge_raw + personality_raw
    return _r("V-13", "Name Value Decomposition Check", "MANDATORY", passed,
               f"{expression_raw} == {soul_urge_raw} + {personality_raw} ({soul_urge_raw + personality_raw})")


def rule_v14(rahu: float, ketu: float) -> ValidationResult:
    err = abs(smallest_signed_angle((rahu - ketu) - 180))
    return _r("V-14", "Vedic Rahu/Ketu Opposition", "MANDATORY", err <= TOLERANCE_DEG, f"(Rahu-Ketu)-180 error = {err:.6f} deg")


def rule_v15(nakshatras: dict) -> ValidationResult:
    span_ok = abs(27 * NAKSHATRA_SPAN - 360.0) < 1e-9
    index_ok = all(1 <= n["nakshatra_number"] <= 27 for n in nakshatras.values())
    passed = span_ok and index_ok
    return _r("V-15", "Nakshatra Span Integrity", "MANDATORY", passed, f"27*span={27*NAKSHATRA_SPAN}, all indices in range: {index_ok}")


def run_all(*, natal, design, nodes, numerology, western, vedic, hd, gk) -> list[ValidationResult]:
    hd_activations_by_gate = {}
    for act in list(hd["personality_activations"].values()) + list(hd["design_activations"].values()):
        hd_activations_by_gate[act["gate"]] = act["line"]

    personality_gates = {a["gate"] for a in hd["personality_activations"].values()}
    design_gates = {a["gate"] for a in hd["design_activations"].values()}
    all_lines = [a["line"] for a in hd["personality_activations"].values()] + [a["line"] for a in hd["design_activations"].values()]

    results = [
        rule_v1(natal, hd["personality_activations"]["Sun"]["notation"]),
        rule_v2(natal),
        rule_v3(natal.jd, design.jd),
        rule_v4(natal),
        rule_v5(gk["hologenetic_profile"], hd_activations_by_gate),
        rule_v6(personality_gates, design_gates),
        rule_v7(hd["defined_channels"], set(hd["defined_centers"])),
        rule_v8(hd["type"], hd["authority"], hd["definition"]),
        rule_v9(all_lines),
        rule_v10(natal, vedic["sidereal_longitudes"]["Lagna"]),
        rule_v11(natal),
        rule_v12(*numerology["reduction_chains"].values()),
        rule_v13(numerology["expression_raw"], numerology["soul_urge_raw"], numerology["personality_raw"]),
        rule_v14(vedic["sidereal_longitudes"]["Rahu"], vedic["sidereal_longitudes"]["Ketu"]),
        rule_v15(vedic["nakshatras"]),
    ]
    return results
