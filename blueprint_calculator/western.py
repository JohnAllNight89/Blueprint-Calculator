"""
Phase 5: Western Tropical Astrology.

Parallel Branch B -- Steps 12 through 15. The Master Outline documents
this phase only at the outline level (a "Shell" of W-1 through W-10a,
never expanded into full Data Point entries the way Phases 3, 4, 6-10
were). This module fills that shell in, following exactly the
step-by-step algorithm the outline *does* give (12.1-15.5), and is
explicit in its docstrings about the one place the outline leaves a
free parameter: aspect orb widths (W-4), which it flags as
undocumented. The orb table below is the standard convention used by
most Western tribes of astrology; treat it as a filled-in default, not
a claim about the "one true" orb.
"""
from __future__ import annotations

from .ephemeris import PlanetarySnapshot, bridge_tropical_to_sign, smallest_signed_angle
from .provenance import Ledger, Status

ELEMENTS = ["Fire", "Earth", "Air", "Water"] * 3
MODALITIES = ["Cardinal", "Fixed", "Mutable"] * 4

# Modern Western rulership (includes the outer planets, unlike the Vedic table)
SIGN_RULERS = [
    "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
    "Venus", "Pluto", "Jupiter", "Saturn", "Uranus", "Neptune",
]

# Aspect angle -> (name, default orb in degrees). Orb widths are a filled-in
# convention (see module docstring) -- the outline left this undocumented.
ASPECTS = {
    0: ("conjunction", 8.0),
    60: ("sextile", 6.0),
    90: ("square", 8.0),
    120: ("trine", 8.0),
    180: ("opposition", 8.0),
}

LUNAR_PHASES = [
    "New Moon", "Waxing Crescent", "First Quarter", "Waxing Gibbous",
    "Full Moon", "Waning Gibbous", "Last Quarter", "Waning Crescent",
]

EASTERN_HOUSES = {10, 11, 12, 1, 2, 3}   # near the Ascendant
NORTHERN_HOUSES = {1, 2, 3, 4, 5, 6}     # below the horizon


def sign_placements(snapshot: PlanetarySnapshot) -> dict:
    """Step 12 -- divide each body's tropical longitude into sign + degree."""
    placements = {name: bridge_tropical_to_sign(pos.tropical_longitude) for name, pos in snapshot.bodies.items()}
    placements["Ascendant"] = bridge_tropical_to_sign(snapshot.ascendant)
    placements["Midheaven"] = bridge_tropical_to_sign(snapshot.midheaven)
    return placements


def house_of(longitude: float, cusps: list[float]) -> int:
    """Step 13 -- which of the 12 Placidus houses a longitude falls in."""
    for i in range(12):
        start = cusps[i]
        end = cusps[(i + 1) % 12]
        span = (end - start) % 360
        offset = (longitude - start) % 360
        if offset < span:
            return i + 1
    return 12  # boundary fallback


def house_placements(snapshot: PlanetarySnapshot) -> dict[str, int]:
    return {name: house_of(pos.tropical_longitude, snapshot.houses) for name, pos in snapshot.bodies.items()}


def compute_aspects(snapshot: PlanetarySnapshot) -> list[dict]:
    """Step 14 -- angular separation between every planet pair, matched to standard aspects."""
    names = list(snapshot.bodies)
    results = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            sep = abs(smallest_signed_angle(snapshot.bodies[a].tropical_longitude - snapshot.bodies[b].tropical_longitude))
            for angle, (aspect_name, orb) in ASPECTS.items():
                if abs(sep - angle) <= orb:
                    results.append({
                        "bodies": [a, b], "aspect": aspect_name, "exact_angle": angle,
                        "actual_separation": sep, "orb_used": round(abs(sep - angle), 4),
                        "applying": snapshot.bodies[a].speed > snapshot.bodies[b].speed,
                    })
                    break
    return results


def element_modality_balance(placements: dict) -> tuple[dict, dict]:
    """Step 15.1 / 15.2 -- Fire/Earth/Air/Water and Cardinal/Fixed/Mutable counts."""
    body_names = [n for n in placements if n not in ("Ascendant", "Midheaven")]
    elements = {"Fire": 0, "Earth": 0, "Air": 0, "Water": 0}
    modalities = {"Cardinal": 0, "Fixed": 0, "Mutable": 0}
    for name in body_names:
        idx = placements[name]["sign_index"]
        elements[ELEMENTS[idx]] += 1
        modalities[MODALITIES[idx]] += 1
    return elements, modalities


def hemisphere_emphasis(houses: dict[str, int]) -> dict:
    """Step 15.3 -- quadrant/hemisphere weighting by house occupation."""
    eastern = sum(1 for h in houses.values() if h in EASTERN_HOUSES)
    western = len(houses) - eastern
    northern = sum(1 for h in houses.values() if h in NORTHERN_HOUSES)
    southern = len(houses) - northern
    return {"eastern": eastern, "western": western, "northern": northern, "southern": southern}


def chart_ruler(ascendant_sign_index: int) -> str:
    """Step 15.4 -- planet ruling the Ascendant sign."""
    return SIGN_RULERS[ascendant_sign_index]


def lunar_phase(snapshot: PlanetarySnapshot) -> dict:
    """Step 15.5 -- degrees between Sun and Moon, classified into one of 8 phases."""
    angle = (snapshot.bodies["Moon"].tropical_longitude - snapshot.bodies["Sun"].tropical_longitude) % 360
    phase_index = int((angle + 22.5) // 45) % 8
    return {"phase_angle": angle, "phase_name": LUNAR_PHASES[phase_index]}


def record_western(ledger: Ledger, snapshot: PlanetarySnapshot) -> dict:
    placements = sign_placements(snapshot)
    houses = house_placements(snapshot)
    aspects = compute_aspects(snapshot)
    elements, modalities = element_modality_balance(placements)
    hemispheres = hemisphere_emphasis(houses)
    ruler = chart_ruler(placements["Ascendant"]["sign_index"])
    moon_phase = lunar_phase(snapshot)

    ledger.record(
        "W-1", system="Western", phase="Phase 5, Step 12", label="Planet-to-Sign Placements",
        value={k: v["dms_string"] for k, v in placements.items()}, source=["P3-5:Sun", "P3-4"],
        calculation="sign_index = floor(tropical_longitude / 30); degrees_in_sign = longitude % 30",
    )
    ledger.record(
        "W-2", system="Western", phase="Phase 5, Step 13", label="House Placements",
        value=houses, source=["P3-7"], calculation="for each planet, find the Placidus cusp interval containing its longitude",
    )
    ledger.record(
        "W-3", system="Western", phase="Phase 5, Step 14", label="Aspect List",
        value=aspects, source=["P3-5:Sun"],
        calculation="angular separation between every planet pair, matched against W-4 orb table",
        status=Status.DERIVED,
    )
    ledger.record(
        "W-4", system="Western", phase="Phase 5, Step 14", label="Aspect Orb Table (filled convention)",
        value={name: orb for name, orb in ASPECTS.values()}, source=[],
        calculation="Outline leaves orb widths undocumented (W-4 shell item); standard 6-8 degree convention applied here.",
        status=Status.DERIVED,
    )
    ledger.record(
        "W-5", system="Western", phase="Phase 5, Step 14", label="Retrograde Flags",
        value={n: p.retrograde for n, p in snapshot.bodies.items()}, source=["P3-6:Sun"],
        calculation="speed < 0",
    )
    ledger.record(
        "W-6", system="Western", phase="Phase 5, Step 15", label="Element Balance",
        value=elements, source=["W-1"], calculation="tally ELEMENTS[sign_index] across all bodies",
    )
    ledger.record(
        "W-7", system="Western", phase="Phase 5, Step 15", label="Modality Balance",
        value=modalities, source=["W-1"], calculation="tally MODALITIES[sign_index] across all bodies",
    )
    ledger.record(
        "W-8", system="Western", phase="Phase 5, Step 15", label="Hemisphere Emphasis",
        value=hemispheres, source=["W-2"], calculation="count planets in Eastern/Western and Northern/Southern house groups",
    )
    ledger.record(
        "W-9", system="Western", phase="Phase 5, Step 15", label="Chart Ruler",
        value=ruler, source=["W-1"], calculation="SIGN_RULERS[ascendant_sign_index] (modern rulership)",
    )
    ledger.record(
        "W-10", system="Western", phase="Phase 5, Step 15", label="Lunar Phase",
        value=moon_phase, source=["P3-5:Sun"], calculation="(Moon_longitude - Sun_longitude) % 360, binned into 8 phases",
    )

    return {
        "sun_sign": placements["Sun"]["sign_name"],
        "moon_sign": placements["Moon"]["sign_name"],
        "ascendant": placements["Ascendant"]["sign_name"],
        "midheaven": placements["Midheaven"]["sign_name"],
        "chart_ruler": ruler,
        "element_balance": elements,
        "modality_balance": modalities,
        "hemisphere_emphasis": hemispheres,
        "lunar_phase_angle": moon_phase["phase_angle"],
        "lunar_phase_name": moon_phase["phase_name"],
        "aspects": aspects,
        "houses": houses,
        "house_cusps": [
            {"house": i + 1, "longitude": snapshot.houses[i], **bridge_tropical_to_sign(snapshot.houses[i])}
            for i in range(12)
        ],
        "placements": placements,
        "dominant_retrogrades": [n for n, p in snapshot.bodies.items() if p.retrograde],
    }
