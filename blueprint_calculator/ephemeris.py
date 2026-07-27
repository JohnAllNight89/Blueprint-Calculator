"""
Phase 3: Ephemeris Core + Coordinate Bridges.

This is "the Mathematical Singularity" of the whole pipeline: the one
place that performs actual orbital mechanics. Everything in Western,
Vedic, and Human Design downstream is a pure re-slicing of the tropical
longitudes computed here. See Data Points P3-4 through P3-12 and the
three Bridges in the Master Outline, Phase 3 Steps 5-6c.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

import swisseph as swe

from .constants.hd_wheel import WHEEL_START, GATE_SPAN, LINE_SPAN, GATE_WHEEL, DESIGN_ARC, MEAN_SOLAR_MOTION
from .provenance import Ledger, Status

_EPHE_PATH = os.path.join(os.path.dirname(__file__), "ephe")
swe.set_ephe_path(_EPHE_PATH)

BASE_FLAGS = swe.FLG_SWIEPH | swe.FLG_SPEED

# Data Point P3-4 -- the 11-body standard set
BODY_IDS: dict[str, int] = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY, "Venus": swe.VENUS,
    "Mars": swe.MARS, "Jupiter": swe.JUPITER, "Saturn": swe.SATURN,
    "Uranus": swe.URANUS, "Neptune": swe.NEPTUNE, "Pluto": swe.PLUTO, "Chiron": swe.CHIRON,
}

SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


def smallest_signed_angle(delta: float) -> float:
    """Wrap an angular delta to [-180, 180)."""
    return (delta + 180) % 360 - 180


@dataclass(frozen=True)
class BodyPosition:
    tropical_longitude: float
    latitude: float
    distance: float
    speed: float
    retrograde: bool


@dataclass(frozen=True)
class PlanetarySnapshot:
    jd: float
    latitude: float
    longitude: float
    bodies: dict[str, BodyPosition]
    ascendant: float
    midheaven: float
    descendant: float
    imum_coeli: float
    houses: list[float]
    ayanamsa: float

    def get_body(self, name: str) -> BodyPosition:
        return self.bodies[name]


def _body_position(jd: float, body_id: int) -> BodyPosition:
    # swe.calc_ut result tuple is (lon, lat, dist, speed_lon, speed_lat, speed_dist);
    # Data Point P3-6 specifies index 3 (speed_lon) as "Daily Speed".
    (lon, lat, dist, speed_lon, _speed_lat, _speed_dist), _flags = swe.calc_ut(jd, body_id, BASE_FLAGS)
    return BodyPosition(tropical_longitude=lon % 360, latitude=lat, distance=dist, speed=speed_lon, retrograde=speed_lon < 0)


def _sun_longitude_and_speed(jd: float) -> tuple[float, float]:
    pos = _body_position(jd, swe.SUN)
    return pos.tropical_longitude, pos.speed


# ------------------------------------------------------------- P3-4..8 ----

def compute_planetary_snapshot(jd: float, lat: float, lon: float) -> PlanetarySnapshot:
    """Data Point P3-4 -- PlanetarySnapshot (Natal or Design).

    Also yields P3-5 (tropical longitude), P3-6 (daily speed), P3-7 (house
    cusps), P3-8 (Lahiri ayanamsa) as fields of the returned structure.
    """
    bodies = {name: _body_position(jd, bid) for name, bid in BODY_IDS.items()}

    cusps, ascmc = swe.houses(jd, lat, lon, b"P")
    ascendant, midheaven = ascmc[0], ascmc[1]
    descendant = (ascendant + 180) % 360
    imum_coeli = (midheaven + 180) % 360

    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    ayanamsa = swe.get_ayanamsa_ut(jd)

    return PlanetarySnapshot(
        jd=jd, latitude=lat, longitude=lon, bodies=bodies,
        ascendant=ascendant, midheaven=midheaven, descendant=descendant, imum_coeli=imum_coeli,
        houses=list(cusps), ayanamsa=ayanamsa,
    )


# ---------------------------------------------------------- P3-11 / 12 ----

def compute_nodes(jd: float) -> dict[str, float]:
    """Data Points P3-11 (True Node) and P3-12 (Mean Node), tropical.

    True Node feeds Western/Human Design; Mean Node feeds Vedic (which
    then applies the same ayanamsa subtraction, Bridge 2, as every other
    body -- avoiding computing the ayanamsa shift twice).
    """
    true_node, _ = swe.calc_ut(jd, swe.TRUE_NODE, BASE_FLAGS)
    mean_node, _ = swe.calc_ut(jd, swe.MEAN_NODE, BASE_FLAGS)
    north_true = true_node[0] % 360
    north_mean = mean_node[0] % 360
    return {
        "north_node_true": north_true,
        "south_node_true": (north_true + 180) % 360,
        "rahu_mean": north_mean,
        "ketu_mean": (north_mean + 180) % 360,
    }


# ------------------------------------------------------------- Bridges ----

def bridge_tropical_to_sign(longitude: float) -> dict:
    """Bridge 1 -- Tropical (or sidereal) Longitude to Zodiac Sign + Degrees."""
    longitude = longitude % 360
    sign_index = int(longitude // 30)
    degrees_in_sign = longitude % 30
    deg = int(degrees_in_sign)
    min_float = (degrees_in_sign - deg) * 60
    minute = int(min_float)
    second = round((min_float - minute) * 60)
    return {
        "sign_index": sign_index,
        "sign_name": SIGN_NAMES[sign_index],
        "degrees_in_sign": degrees_in_sign,
        "dms_string": f"{deg}°{minute:02d}'{second:02d}\" {SIGN_NAMES[sign_index]}",
    }


def bridge_tropical_to_sidereal(tropical_longitude: float, ayanamsa: float) -> float:
    """Bridge 2 -- Tropical Longitude to Sidereal Longitude."""
    return (tropical_longitude - ayanamsa) % 360


def bridge_tropical_to_hd_gate_line(longitude: float) -> dict:
    """Bridge 3 -- Tropical Longitude to Human Design Gate + Line."""
    offset = (longitude - WHEEL_START) % 360
    gate_index = int(offset // GATE_SPAN)
    gate = GATE_WHEEL[gate_index]
    within_gate = offset % GATE_SPAN
    line = min(int(within_gate // LINE_SPAN) + 1, 6)
    return {"gate": gate, "line": line, "notation": f"{gate}.{line}"}


# --------------------------------------------------------------- P3-9 ----

def solve_design_jd(natal_jd: float, natal_sun_longitude: float) -> float:
    """Data Point P3-9 -- Design Julian Day, via Newton-Raphson.

    Finds the JD at which the Sun's tropical longitude was exactly
    DESIGN_ARC (88 degrees) behind its natal position.
    """
    target = (natal_sun_longitude - DESIGN_ARC) % 360
    jd = natal_jd - DESIGN_ARC / MEAN_SOLAR_MOTION

    for _ in range(60):
        sun_lon, sun_speed = _sun_longitude_and_speed(jd)
        residual = smallest_signed_angle(target - sun_lon)
        if abs(residual) < 1e-9:
            return jd
        jd += residual / sun_speed

    raise RuntimeError("Design moment solver failed to converge within 60 iterations")


# ------------------------------------------------------- ledger driver ----

def record_ephemeris_core(ledger: Ledger, jd: float, lat: float, lon: float) -> tuple[PlanetarySnapshot, PlanetarySnapshot, dict]:
    """Runs all of Phase 3 (Steps 5-6c) and records the chain in the ledger.

    Returns (natal_snapshot, design_snapshot, nodes).
    """
    natal = compute_planetary_snapshot(jd, lat, lon)
    ledger.record(
        "P3-4", system="Ephemeris Core", phase="Phase 3, Step 5", label="PlanetarySnapshot (Natal)",
        value={"ayanamsa": natal.ayanamsa, "ascendant": natal.ascendant, "midheaven": natal.midheaven},
        source=["P3-3", "P3-1"],
        calculation="swe.calc_ut for 11 bodies + swe.houses (Placidus) + swe.get_ayanamsa_ut (Lahiri)",
    )
    for name, pos in natal.bodies.items():
        ledger.record(
            f"P3-5:{name}", system="Ephemeris Core", phase="Phase 3, Step 5",
            label=f"Tropical Longitude -- {name}", value=pos.tropical_longitude, source=["P3-4"],
            calculation="swe.calc_ut() output index 0, normalized mod 360",
        )
        ledger.record(
            f"P3-6:{name}", system="Ephemeris Core", phase="Phase 3, Step 5",
            label=f"Daily Speed -- {name}", value=pos.speed, source=["P3-4"],
            calculation="swe.calc_ut() output index 3; retrograde iff speed < 0",
        )
    ledger.record(
        "P3-7", system="Ephemeris Core", phase="Phase 3, Step 5", label="House Cusps (Placidus)",
        value=natal.houses, source=["P3-3", "P3-1"],
        calculation="swe.houses(jd, lat, lon, b'P')",
    )
    ledger.record(
        "P3-8", system="Ephemeris Core", phase="Phase 3, Step 5", label="Lahiri Ayanamsa",
        value=natal.ayanamsa, source=["P3-3"],
        calculation="swe.set_sid_mode(SIDM_LAHIRI); swe.get_ayanamsa_ut(jd)",
    )

    natal_sun = natal.bodies["Sun"].tropical_longitude
    design_jd = solve_design_jd(jd, natal_sun)
    ledger.record(
        "P3-9", system="Ephemeris Core", phase="Phase 3, Step 6b", label="Design Julian Day",
        value=design_jd, source=["P3-3", "P3-5:Sun", "P3-6:Sun"],
        calculation="Newton-Raphson solve for JD where Sun longitude = natal Sun - 88deg",
    )

    design = compute_planetary_snapshot(design_jd, lat, lon)
    ledger.record(
        "P3-10", system="Ephemeris Core", phase="Phase 3, Step 6b", label="PlanetarySnapshot (Design)",
        value={"ayanamsa": design.ayanamsa}, source=["P3-9", "P3-1"],
        calculation="same as P3-4, evaluated at the Design JD",
    )

    nodes = compute_nodes(jd)
    ledger.record(
        "P3-11", system="Ephemeris Core", phase="Phase 3, Step 6c", label="North Node Longitude (True)",
        value=nodes["north_node_true"], source=["P3-3"],
        calculation="swe.calc_ut(jd, swe.TRUE_NODE); South Node = North + 180",
    )
    ledger.record(
        "P3-12", system="Ephemeris Core", phase="Phase 3, Step 6c", label="Rahu Longitude (Mean, tropical)",
        value=nodes["rahu_mean"], source=["P3-3"],
        calculation="swe.calc_ut(jd, swe.MEAN_NODE); Ketu = Rahu + 180; sidereal form via Bridge 2",
    )

    return natal, design, nodes
