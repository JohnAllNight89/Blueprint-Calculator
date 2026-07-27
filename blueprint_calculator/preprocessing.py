"""
Phase 1: Raw Inputs, Phase 2: Preprocessing.

Converts the four human-readable inputs (name, birth date, birth time,
birth place) into the machine-readable coordinates every downstream
branch depends on: a UTC datetime, a Julian Day, resolved lat/lon, and a
normalized letter sequence for numerology.
"""
from __future__ import annotations

import re
import urllib.parse
import urllib.request
import json
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

import swisseph as swe
from timezonefinder import TimezoneFinder

from . import gazetteer
from .provenance import Ledger, Status

_TF = TimezoneFinder()

VOWELS = set("AEIOU")


def letter_value(ch: str) -> int:
    """Pythagorean numerology value: A-I=1-9, J-R=1-9, S-Z=1-8 (mod-9 cycle)."""
    return ((ord(ch) - ord("A")) % 9) + 1


@dataclass(frozen=True)
class Coordinates:
    latitude: float
    longitude: float
    timezone: str
    display_name: str


@dataclass(frozen=True)
class Letter:
    char: str
    word_index: int
    value: int
    is_vowel: bool
    is_consonant: bool
    is_y_vowel: bool


@dataclass(frozen=True)
class NormalizedName:
    raw: str
    words: list[str]           # e.g. ["JOHNATHON", "ANTHONY", "LONG"]
    letters: list[Letter]      # every letter, in order, across all words


# ---------------------------------------------------------------- P3-1 ----

def _nominatim_lookup(place: str) -> tuple[float, float, str]:
    """Try OpenStreetMap Nominatim for places not in the offline gazetteer."""
    url = (
        "https://nominatim.openstreetmap.org/search?"
        + urllib.parse.urlencode({"q": place, "format": "json", "limit": "1"})
    )
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "blueprint-calculator/1.0 (mapping-the-human-condition)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            results = json.loads(resp.read().decode())
        if not results:
            raise gazetteer.PlaceNotFound(
                f"'{place}' not found via Nominatim. "
                f"Pass coordinates directly as 'lat,lon' instead."
            )
        r = results[0]
        return float(r["lat"]), float(r["lon"]), r.get("display_name", place)
    except gazetteer.PlaceNotFound:
        raise
    except Exception as exc:
        raise gazetteer.PlaceNotFound(
            f"'{place}' is not in the offline gazetteer and the online lookup failed ({exc}). "
            f"Pass coordinates directly as 'lat,lon' instead."
        ) from exc


def resolve_place(place: str) -> Coordinates:
    """Data Point P3-1 -- Resolved Geographic Coordinates.

    Accepts either 'lat,lon', a city name in the offline gazetteer, or any
    place name resolvable via Nominatim (OpenStreetMap) as a live fallback.
    """
    place = place.strip()
    latlon_match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", place)
    if latlon_match:
        lat, lon = float(latlon_match.group(1)), float(latlon_match.group(2))
        display_name = f"{lat:.4f}, {lon:.4f}"
    else:
        try:
            lat, lon, display_name = gazetteer.lookup_city(place)
        except gazetteer.PlaceNotFound:
            lat, lon, display_name = _nominatim_lookup(place)

    if not (-90.0 <= lat <= 90.0):
        raise ValueError(f"latitude {lat} out of range [-90, 90]")
    if not (-180.0 <= lon <= 180.0):
        raise ValueError(f"longitude {lon} out of range [-180, 180]")

    tz_name = _TF.timezone_at(lat=lat, lng=lon)
    if tz_name is None:
        # fall back to nearest timezone for ocean/edge coordinates
        tz_name = _TF.closest_timezone_at(lat=lat, lng=lon)
    if tz_name is None:
        raise ValueError(f"could not resolve an IANA timezone for ({lat}, {lon})")

    return Coordinates(latitude=lat, longitude=lon, timezone=tz_name, display_name=display_name)


# ---------------------------------------------------------------- P3-2 ----

def to_utc(birth_date: str, birth_time: str, coords: Coordinates) -> datetime:
    """Data Point P3-2 -- UTC Datetime.

    birth_date: 'YYYY-MM-DD'. birth_time: 'HH:MM' (local time at coords).
    zoneinfo resolves the historical IANA offset, including DST, for the
    exact date rather than assuming today's rule applies retroactively.
    """
    y, m, d = (int(x) for x in birth_date.split("-"))
    hh, mm = (int(x) for x in birth_time.split(":"))
    local_dt = datetime(y, m, d, hh, mm, tzinfo=ZoneInfo(coords.timezone))
    return local_dt.astimezone(ZoneInfo("UTC"))


# ---------------------------------------------------------------- P3-3 ----

def to_julian_day(utc_dt: datetime) -> float:
    """Data Point P3-3 -- Julian Day (UT), via swe.julday with fractional hour."""
    decimal_hour = utc_dt.hour + utc_dt.minute / 60 + utc_dt.second / 3600
    return swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, decimal_hour)


# ------------------------------------------------------------- NP-1..4 ----

def normalize_name(raw_name: str) -> NormalizedName:
    """Data Points NP-1/NP-2/NP-4 -- strip, uppercase, split, classify letters."""
    cleaned = re.sub(r"[^A-Za-z\s]", "", raw_name).upper()
    words = [w for w in cleaned.split() if w]

    letters: list[Letter] = []
    for wi, word in enumerate(words):
        for i, ch in enumerate(word):
            if ch in VOWELS:
                is_vowel, is_y_vowel = True, False
            elif ch == "Y":
                prev_ch = word[i - 1] if i > 0 else None
                next_ch = word[i + 1] if i < len(word) - 1 else None
                neighbor_is_vowel = (prev_ch in VOWELS) or (next_ch in VOWELS)
                is_y_vowel = not neighbor_is_vowel
                is_vowel = is_y_vowel
            else:
                is_vowel, is_y_vowel = False, False
            letters.append(
                Letter(
                    char=ch,
                    word_index=wi,
                    value=letter_value(ch),
                    is_vowel=is_vowel,
                    is_consonant=not is_vowel,
                    is_y_vowel=is_y_vowel,
                )
            )
    return NormalizedName(raw=raw_name, words=words, letters=letters)


def record_preprocessing(
    ledger: Ledger, *, name: str, birth_date: str, birth_time: str, birth_place: str
) -> tuple[Coordinates, datetime, float, NormalizedName]:
    """Runs Phase 1 + Phase 2 and records every step in the ledger."""
    ledger.record(
        "P1", system="Preprocessing", phase="Phase 1", label="Raw Inputs",
        value={"name": name, "birth_date": birth_date, "birth_time": birth_time, "birth_place": birth_place},
        calculation="Four foundational inputs collected as-is.",
    )

    coords = resolve_place(birth_place)
    ledger.record(
        "P3-1", system="Preprocessing", phase="Phase 3, Step 3", label="Resolved Geographic Coordinates",
        value=coords.__dict__, source=["P1"],
        calculation="geocode(birth_place) -> {lat, lon, timezone}; validated against IANA tzdb.",
    )

    utc_dt = to_utc(birth_date, birth_time, coords)
    ledger.record(
        "P3-2", system="Preprocessing", phase="Phase 3, Step 3", label="UTC Datetime",
        value=utc_dt.isoformat(), source=["P1", "P3-1"],
        calculation="localize(birth_date + birth_time, P3-1.timezone).astimezone(UTC)",
    )

    jd = to_julian_day(utc_dt)
    ledger.record(
        "P3-3", system="Ephemeris Core", phase="Phase 3, Step 4", label="Julian Day (UT)",
        value=jd, source=["P3-2"],
        calculation="swe.julday(year, month, day, hour + minute/60 + second/3600)",
    )

    norm_name = normalize_name(name)
    ledger.record(
        "NP-1", system="Numerology", phase="Phase 2, Step 5", label="Normalized Birth Name",
        value={"words": norm_name.words}, source=["P1"],
        calculation="strip non-alphabetic chars; uppercase; split on whitespace.",
    )

    return coords, utc_dt, jd, norm_name
