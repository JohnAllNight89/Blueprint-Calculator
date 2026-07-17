"""Western (tropical) astrology engine.

Computes exact tropical ecliptic longitudes for Sun through Pluto plus
Chiron, the Placidus house cusps, and the four chart angles (ASC, MC,
DSC, IC) using the Swiss Ephemeris.
"""

from __future__ import annotations

from datetime import datetime

import swisseph as swe

from engines.ephemeris import (
    BASE_FLAGS,
    PLANETS,
    body_position,
    ensure_ephemeris,
    julian_day_ut,
    split_longitude,
)

PLACIDUS = b"P"


def calculate_chart(utc_dt: datetime, latitude: float, longitude: float) -> dict:
    """Full tropical chart for a UTC birth moment and geographic position."""
    ensure_ephemeris()
    jd_ut = julian_day_ut(utc_dt)

    planets = []
    for name, body_id, glyph in PLANETS:
        raw = body_position(jd_ut, body_id, BASE_FLAGS)
        planets.append({
            "name": name,
            "glyph": glyph,
            **split_longitude(raw["longitude"]),
            "speed": round(raw["speed"], 6),
            "retrograde": raw["speed"] < 0,
        })

    cusps, ascmc = swe.houses(jd_ut, latitude, longitude, PLACIDUS)
    houses = [
        {"house": index, **split_longitude(cusp)}
        for index, cusp in enumerate(cusps[:12], start=1)
    ]

    asc, mc = ascmc[0], ascmc[1]
    angles = {
        "ascendant": split_longitude(asc),
        "midheaven": split_longitude(mc),
        "descendant": split_longitude(asc + 180),
        "imum_coeli": split_longitude(mc + 180),
    }

    return {
        "system": "Tropical (Western)",
        "house_system": "Placidus",
        "julian_day_ut": round(jd_ut, 6),
        "planets": planets,
        "houses": houses,
        "angles": angles,
    }
