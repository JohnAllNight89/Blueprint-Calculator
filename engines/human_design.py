"""Human Design calculation engine.

Maps ecliptic longitudes onto the Rave Mandala: 64 gates of 5.625° each,
six lines of 0.9375° per gate. The wheel is anchored at Gate 41 which
begins at 02°00'00" Aquarius (302° absolute) — the canonical alignment,
which places the Rave New Year at the Sun's Gate-41 ingress (~Jan 22)
and the spring equinox point inside Gate 25.

Two activation sets are computed:

* Personality — planetary positions at the natal moment.
* Design      — positions at the moment the Sun sat exactly 88° of solar
  longitude before the natal Sun (~88 days prenatal), found by Newton
  iteration on the solar equation using the smallest signed angle, which
  converges cleanly across the 0° Aries boundary.

From the union of activated gates the engine derives defined channels,
defined centers, Type, Strategy, Authority, Profile, and Definition.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import swisseph as swe

from engines.ephemeris import BASE_FLAGS, body_position, julian_day_ut, split_longitude
from engines.gene_keys import GENE_KEYS

# Zodiacal order of gates around the Rave Mandala, starting at WHEEL_START.
GATE_WHEEL = [
    41, 19, 13, 49, 30, 55, 37, 63, 22, 36, 25, 17, 21, 51, 42, 3,
    27, 24, 2, 23, 8, 20, 16, 35, 45, 12, 15, 52, 39, 53, 62, 56,
    31, 33, 7, 4, 29, 59, 40, 64, 47, 6, 46, 18, 48, 57, 32, 50,
    28, 44, 1, 43, 14, 34, 9, 5, 26, 11, 10, 58, 38, 54, 61, 60,
]
WHEEL_START = 302.0          # Gate 41 begins at 02°00' Aquarius.
GATE_SPAN = 360 / 64         # 5.625°
LINE_SPAN = GATE_SPAN / 6    # 0.9375°

DESIGN_ARC = 88.0            # Degrees of solar longitude before birth.
MEAN_SOLAR_MOTION = 0.98564736  # Degrees per day.

CENTERS = {
    "Head": [64, 61, 63],
    "Ajna": [47, 24, 4, 17, 43, 11],
    "Throat": [62, 23, 56, 35, 12, 45, 33, 8, 31, 20, 16],
    "G": [1, 13, 25, 46, 2, 15, 10, 7],
    "Heart": [21, 40, 26, 51],
    "Sacral": [34, 5, 14, 29, 59, 9, 3, 42, 27],
    "Spleen": [48, 57, 44, 50, 32, 28, 18],
    "Solar Plexus": [36, 22, 37, 6, 49, 55, 30],
    "Root": [58, 38, 54, 53, 60, 52, 19, 39, 41],
}
GATE_TO_CENTER = {
    gate: center for center, gates in CENTERS.items() for gate in gates
}

CHANNELS = [
    (1, 8), (2, 14), (3, 60), (4, 63), (5, 15), (6, 59), (7, 31),
    (9, 52), (10, 20), (10, 34), (10, 57), (11, 56), (12, 22), (13, 33),
    (16, 48), (17, 62), (18, 58), (19, 49), (20, 34), (20, 57), (21, 45),
    (23, 43), (24, 61), (25, 51), (26, 44), (27, 50), (28, 38), (29, 46),
    (30, 41), (32, 54), (34, 57), (35, 36), (37, 40), (39, 55), (42, 53),
    (47, 64),
]

MOTOR_CENTERS = {"Sacral", "Solar Plexus", "Heart", "Root"}

TYPE_DETAILS = {
    "Manifestor": {"strategy": "To Inform", "signature": "Peace", "not_self": "Anger"},
    "Generator": {"strategy": "To Respond", "signature": "Satisfaction", "not_self": "Frustration"},
    "Manifesting Generator": {"strategy": "To Respond", "signature": "Satisfaction", "not_self": "Frustration"},
    "Projector": {"strategy": "Wait for the Invitation", "signature": "Success", "not_self": "Bitterness"},
    "Reflector": {"strategy": "Wait a Lunar Cycle", "signature": "Surprise", "not_self": "Disappointment"},
}

PROFILE_LINE_NAMES = {
    1: "Investigator", 2: "Hermit", 3: "Martyr",
    4: "Opportunist", 5: "Heretic", 6: "Role Model",
}

# Activation bodies in traditional Human Design order.
HD_BODIES = [
    ("Sun", "☉"), ("Earth", "⊕"), ("North Node", "☊"), ("South Node", "☋"),
    ("Moon", "☽"), ("Mercury", "☿"), ("Venus", "♀"), ("Mars", "♂"),
    ("Jupiter", "♃"), ("Saturn", "♄"), ("Uranus", "♅"), ("Neptune", "♆"),
    ("Pluto", "♇"),
]

_SWE_IDS = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY,
    "Venus": swe.VENUS, "Mars": swe.MARS, "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN, "Uranus": swe.URANUS, "Neptune": swe.NEPTUNE,
    "Pluto": swe.PLUTO, "North Node": swe.TRUE_NODE,
}


def gate_and_line(longitude: float) -> dict:
    """Map an ecliptic longitude onto its gate and line."""
    offset = (longitude - WHEEL_START) % 360
    gate_index = int(offset // GATE_SPAN)
    within_gate = offset - gate_index * GATE_SPAN
    line = min(int(within_gate // LINE_SPAN) + 1, 6)
    gate = GATE_WHEEL[gate_index]
    return {
        "gate": gate,
        "line": line,
        "gate_name": GENE_KEYS[gate][0],
        "notation": f"{gate}.{line}",
    }


def _smallest_signed_angle(delta: float) -> float:
    """Wrap an angle difference into [-180, 180)."""
    return (delta + 180) % 360 - 180


def solve_design_jd(natal_jd: float) -> float:
    """Julian day when the Sun was exactly DESIGN_ARC° behind its natal spot.

    Newton iteration on solar longitude. Because the residual is always
    the smallest signed angle, crossing 0° Aries cannot trap the loop —
    the correction simply changes sign and the iteration converges
    (typically in 3–5 steps to sub-milliarcsecond precision).
    """
    natal_sun = body_position(natal_jd, swe.SUN)["longitude"]
    target = (natal_sun - DESIGN_ARC) % 360

    jd = natal_jd - DESIGN_ARC / MEAN_SOLAR_MOTION
    for _ in range(60):
        sun = body_position(jd, swe.SUN)
        residual = _smallest_signed_angle(target - sun["longitude"])
        if abs(residual) < 1e-9:
            return jd
        jd += residual / sun["speed"]
    raise RuntimeError("Design-time solar equation did not converge.")


def _jd_to_datetime(jd: float) -> datetime:
    year, month, day, decimal_hour = swe.revjul(jd)
    return datetime(year, month, day, tzinfo=timezone.utc) + timedelta(
        hours=decimal_hour
    )


def _activations(jd: float) -> list[dict]:
    """The 13 Human Design activations for one moment."""
    positions = {}
    for name, swe_id in _SWE_IDS.items():
        positions[name] = body_position(jd, swe_id, BASE_FLAGS)["longitude"]
    positions["Earth"] = (positions["Sun"] + 180) % 360
    positions["South Node"] = (positions["North Node"] + 180) % 360

    entries = []
    for body, glyph in HD_BODIES:
        longitude = positions[body]
        placement = split_longitude(longitude)
        entries.append({
            "body": body,
            "glyph": glyph,
            "longitude": placement["longitude"],
            "zodiac": placement["position"],
            **gate_and_line(longitude),
        })
    return entries


def _derive_mechanics(active_gates: set[int]) -> dict:
    """Defined channels/centers, Type, Authority, and Definition."""
    defined_channels = []
    center_edges = []
    for gate_a, gate_b in CHANNELS:
        if gate_a in active_gates and gate_b in active_gates:
            center_a, center_b = GATE_TO_CENTER[gate_a], GATE_TO_CENTER[gate_b]
            defined_channels.append({
                "gates": [gate_a, gate_b],
                "label": f"{gate_a}–{gate_b}",
                "centers": [center_a, center_b],
                "name": f"{GENE_KEYS[gate_a][0]} / {GENE_KEYS[gate_b][0]}",
            })
            center_edges.append((center_a, center_b))

    defined_centers = sorted({c for edge in center_edges for c in edge})

    # Adjacency between defined centers through defined channels.
    adjacency: dict[str, set[str]] = {center: set() for center in defined_centers}
    for center_a, center_b in center_edges:
        adjacency[center_a].add(center_b)
        adjacency[center_b].add(center_a)

    def reachable(start: str) -> set[str]:
        seen, stack = set(), [start]
        while stack:
            node = stack.pop()
            if node not in seen:
                seen.add(node)
                stack.extend(adjacency[node] - seen)
        return seen

    # Motor-to-Throat connectivity decides manifestation capability.
    motor_to_throat = (
        "Throat" in adjacency
        and bool(reachable("Throat") & MOTOR_CENTERS)
    )

    sacral_defined = "Sacral" in defined_centers
    if not defined_centers:
        hd_type = "Reflector"
    elif sacral_defined:
        hd_type = "Manifesting Generator" if motor_to_throat else "Generator"
    elif motor_to_throat:
        hd_type = "Manifestor"
    else:
        hd_type = "Projector"

    if hd_type == "Reflector":
        authority = "Lunar (wait a full Moon cycle)"
    elif "Solar Plexus" in defined_centers:
        authority = "Emotional (Solar Plexus)"
    elif sacral_defined:
        authority = "Sacral"
    elif "Spleen" in defined_centers:
        authority = "Splenic"
    elif "Heart" in defined_centers:
        authority = "Ego"
    elif "G" in defined_centers:
        authority = "Self-Projected"
    else:
        authority = "Mental (sounding board / environment)"

    # Definition: connected components among defined centers.
    components = 0
    unvisited = set(defined_centers)
    while unvisited:
        components += 1
        unvisited -= reachable(next(iter(unvisited)))
    definition = {
        0: "No Definition", 1: "Single Definition", 2: "Split Definition",
        3: "Triple Split Definition", 4: "Quadruple Split Definition",
    }.get(components, f"{components}-fold Definition")

    return {
        "channels": defined_channels,
        "defined_centers": defined_centers,
        "open_centers": sorted(set(CENTERS) - set(defined_centers)),
        "type": hd_type,
        "authority": authority,
        "definition": definition,
        **TYPE_DETAILS[hd_type],
    }


def calculate_chart(utc_dt: datetime) -> dict:
    """Full Human Design bodygraph data for a UTC birth moment."""
    natal_jd = julian_day_ut(utc_dt)
    design_jd = solve_design_jd(natal_jd)
    design_dt = _jd_to_datetime(design_jd)

    personality = _activations(natal_jd)
    design = _activations(design_jd)

    active_gates = {entry["gate"] for entry in personality + design}
    mechanics = _derive_mechanics(active_gates)

    personality_sun = next(e for e in personality if e["body"] == "Sun")
    design_sun = next(e for e in design if e["body"] == "Sun")
    profile_lines = (personality_sun["line"], design_sun["line"])

    return {
        "personality": {
            "moment_utc": utc_dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M"),
            "activations": personality,
        },
        "design": {
            "moment_utc": design_dt.strftime("%Y-%m-%d %H:%M"),
            "solar_arc": DESIGN_ARC,
            "activations": design,
        },
        "active_gates": sorted(active_gates),
        "profile": f"{profile_lines[0]}/{profile_lines[1]}",
        "profile_label": (
            f"{PROFILE_LINE_NAMES[profile_lines[0]]} / "
            f"{PROFILE_LINE_NAMES[profile_lines[1]]}"
        ),
        **mechanics,
    }
