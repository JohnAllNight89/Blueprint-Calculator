"""Shared Swiss Ephemeris plumbing for the astrology engines.

Configures pyswisseph to use the bundled ephemeris data files in
``ephe/`` (high-precision Swiss Ephemeris format, 1800–2400 AD, which
also enables Chiron) and provides longitude/sign/formatting helpers used
by both the Western (tropical) and Vedic (sidereal) engines.
"""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from pathlib import Path

import swisseph as swe

EPHE_PATH = Path(__file__).resolve().parent.parent / "ephe"

# Swiss Ephemeris state (including the ephemeris path) is thread-local in
# this pyswisseph build. FastAPI dispatches sync endpoints to a worker
# thread pool, so the path must be (re)applied in whichever thread does
# the calculating — a set-at-import-only approach silently falls back to
# the built-in default path in worker threads.
_thread_state = threading.local()


def ensure_ephemeris() -> None:
    """Point the Swiss Ephemeris at the bundled data files (per thread)."""
    if not getattr(_thread_state, "configured", False):
        swe.set_ephe_path(str(EPHE_PATH))
        _thread_state.configured = True


ensure_ephemeris()

# Sun through Pluto, plus Chiron.
PLANETS = [
    ("Sun", swe.SUN, "☉"),
    ("Moon", swe.MOON, "☽"),
    ("Mercury", swe.MERCURY, "☿"),
    ("Venus", swe.VENUS, "♀"),
    ("Mars", swe.MARS, "♂"),
    ("Jupiter", swe.JUPITER, "♃"),
    ("Saturn", swe.SATURN, "♄"),
    ("Uranus", swe.URANUS, "♅"),
    ("Neptune", swe.NEPTUNE, "♆"),
    ("Pluto", swe.PLUTO, "♇"),
    ("Chiron", swe.CHIRON, "⚷"),
]

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
# U+FE0E forces text presentation so browsers don't swap in emoji glyphs.
SIGN_GLYPHS = [
    glyph + "︎"
    for glyph in ["♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓"]
]

BASE_FLAGS = swe.FLG_SWIEPH | swe.FLG_SPEED


def julian_day_ut(utc_dt: datetime) -> float:
    """Julian day (UT) for a timezone-aware UTC datetime."""
    if utc_dt.tzinfo is None:
        raise ValueError("julian_day_ut requires a timezone-aware datetime")
    utc_dt = utc_dt.astimezone(timezone.utc)
    decimal_hour = utc_dt.hour + utc_dt.minute / 60 + utc_dt.second / 3600
    return swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, decimal_hour)


def format_dms(degrees_in_sign: float) -> str:
    """27.7621 → \"27°45'44\\\"\" (degrees within a sign)."""
    total_seconds = round(degrees_in_sign * 3600)
    deg, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{deg}°{minutes:02d}'{seconds:02d}\""


def split_longitude(longitude: float) -> dict:
    """Break an ecliptic longitude into sign + degrees-in-sign details."""
    longitude %= 360
    sign_index = int(longitude // 30)
    in_sign = longitude % 30
    return {
        "longitude": round(longitude, 4),
        "sign": SIGNS[sign_index],
        "sign_glyph": SIGN_GLYPHS[sign_index],
        "sign_index": sign_index,
        "degrees_in_sign": round(in_sign, 4),
        "position": f"{format_dms(in_sign)} {SIGNS[sign_index]}",
    }


def body_position(jd_ut: float, body_id: int, flags: int = BASE_FLAGS) -> dict:
    """Longitude and daily speed for one body (tropical unless flagged)."""
    ensure_ephemeris()
    values, _ = swe.calc_ut(jd_ut, body_id, flags)
    return {"longitude": values[0] % 360, "speed": values[3]}
