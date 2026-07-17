"""Vedic (sidereal) astrology engine.

Takes the raw Swiss Ephemeris coordinates, applies the Lahiri Ayanamsa
(Chitrapaksha), and maps every graha — Sun through Saturn, the outer
planets, and Rahu/Ketu (mean lunar nodes) — onto the 12 sidereal rashis
and the 27 nakshatras with pada subdivisions. The sidereal Lagna
(Ascendant) is computed with the same ayanamsa.
"""

from __future__ import annotations

from datetime import datetime

import swisseph as swe

from engines.ephemeris import (
    BASE_FLAGS,
    PLANETS,
    body_position,
    ensure_ephemeris,
    format_dms,
    julian_day_ut,
    split_longitude,
)

SIDEREAL_FLAGS = BASE_FLAGS | swe.FLG_SIDEREAL

RASHIS = [
    "Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya",
    "Tula", "Vrishchika", "Dhanu", "Makara", "Kumbha", "Meena",
]

# The 27 nakshatras with their ruling planets (Vimshottari lords).
NAKSHATRAS = [
    ("Ashwini", "Ketu"), ("Bharani", "Venus"), ("Krittika", "Sun"),
    ("Rohini", "Moon"), ("Mrigashira", "Mars"), ("Ardra", "Rahu"),
    ("Punarvasu", "Jupiter"), ("Pushya", "Saturn"), ("Ashlesha", "Mercury"),
    ("Magha", "Ketu"), ("Purva Phalguni", "Venus"), ("Uttara Phalguni", "Sun"),
    ("Hasta", "Moon"), ("Chitra", "Mars"), ("Swati", "Rahu"),
    ("Vishakha", "Jupiter"), ("Anuradha", "Saturn"), ("Jyeshtha", "Mercury"),
    ("Mula", "Ketu"), ("Purva Ashadha", "Venus"), ("Uttara Ashadha", "Sun"),
    ("Shravana", "Moon"), ("Dhanishta", "Mars"), ("Shatabhisha", "Rahu"),
    ("Purva Bhadrapada", "Jupiter"), ("Uttara Bhadrapada", "Saturn"),
    ("Revati", "Mercury"),
]

NAKSHATRA_SPAN = 360 / 27          # 13°20'
PADA_SPAN = NAKSHATRA_SPAN / 4     # 3°20'


def _nakshatra_details(sidereal_longitude: float) -> dict:
    sidereal_longitude %= 360
    index = int(sidereal_longitude // NAKSHATRA_SPAN)
    within = sidereal_longitude - index * NAKSHATRA_SPAN
    name, lord = NAKSHATRAS[index]
    return {
        "nakshatra": name,
        "nakshatra_lord": lord,
        "nakshatra_number": index + 1,
        "pada": int(within // PADA_SPAN) + 1,
        "degrees_in_nakshatra": format_dms(within),
    }


def _sidereal_entry(name: str, glyph: str, longitude: float, speed: float) -> dict:
    placement = split_longitude(longitude)
    rashi = RASHIS[placement["sign_index"]]
    return {
        "name": name,
        "glyph": glyph,
        **placement,
        "rashi": rashi,
        "position": f"{format_dms(placement['degrees_in_sign'])} {rashi}",
        "speed": round(speed, 6),
        "retrograde": speed < 0,
        **_nakshatra_details(placement["longitude"]),
    }


def calculate_chart(utc_dt: datetime, latitude: float, longitude: float) -> dict:
    """Full sidereal (Lahiri) chart for a UTC birth moment and location."""
    ensure_ephemeris()
    jd_ut = julian_day_ut(utc_dt)

    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    ayanamsa = swe.get_ayanamsa_ut(jd_ut)

    grahas = []
    for name, body_id, glyph in PLANETS:
        raw = body_position(jd_ut, body_id, SIDEREAL_FLAGS)
        grahas.append(_sidereal_entry(name, glyph, raw["longitude"], raw["speed"]))

    # Rahu (mean north node) and Ketu (its opposite point).
    rahu = body_position(jd_ut, swe.MEAN_NODE, SIDEREAL_FLAGS)
    grahas.append(_sidereal_entry("Rahu", "☊", rahu["longitude"], rahu["speed"]))
    grahas.append(
        _sidereal_entry("Ketu", "☋", (rahu["longitude"] + 180) % 360, rahu["speed"])
    )

    # Sidereal Lagna (Ascendant) via whole-sign houses with the same ayanamsa.
    _, ascmc = swe.houses_ex(jd_ut, latitude, longitude, b"W", swe.FLG_SIDEREAL)
    lagna = _sidereal_entry("Lagna", "↑", ascmc[0], 0.0)
    lagna.pop("retrograde")

    return {
        "system": "Sidereal (Vedic)",
        "ayanamsa_name": "Lahiri (Chitrapaksha)",
        "ayanamsa": round(ayanamsa, 4),
        "ayanamsa_dms": format_dms(ayanamsa),
        "julian_day_ut": round(jd_ut, 6),
        "lagna": lagna,
        "grahas": grahas,
    }
