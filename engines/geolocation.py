"""Offline geocoding and timezone resolution.

Resolves a birth-place string to latitude/longitude and an IANA timezone
using a curated local city database — no network calls, so the dashboard
stays fully offline. Historical UTC offsets (including DST rules in force
on the birth date) come from the standard-library ``zoneinfo`` module.

Direct coordinates are also accepted: an input like ``"33.75, -84.39"``
is parsed as latitude/longitude, with the timezone resolved through
``timezonefinder`` when that optional library is installed.
"""

from __future__ import annotations

import difflib
import re
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo


def _city(display: str, lat: float, lon: float, tz: str) -> dict:
    return {"display": display, "latitude": lat, "longitude": lon, "timezone": tz}


# Curated offline gazetteer. Keys are normalized city names; aliases map
# alternate spellings onto the same entry.
CITY_DB = {
    # --- United States ---
    "atlanta": _city("Atlanta, Georgia, USA", 33.7490, -84.3880, "America/New_York"),
    "new york": _city("New York, New York, USA", 40.7128, -74.0060, "America/New_York"),
    "los angeles": _city("Los Angeles, California, USA", 34.0522, -118.2437, "America/Los_Angeles"),
    "chicago": _city("Chicago, Illinois, USA", 41.8781, -87.6298, "America/Chicago"),
    "houston": _city("Houston, Texas, USA", 29.7604, -95.3698, "America/Chicago"),
    "phoenix": _city("Phoenix, Arizona, USA", 33.4484, -112.0740, "America/Phoenix"),
    "philadelphia": _city("Philadelphia, Pennsylvania, USA", 39.9526, -75.1652, "America/New_York"),
    "san antonio": _city("San Antonio, Texas, USA", 29.4241, -98.4936, "America/Chicago"),
    "san diego": _city("San Diego, California, USA", 32.7157, -117.1611, "America/Los_Angeles"),
    "dallas": _city("Dallas, Texas, USA", 32.7767, -96.7970, "America/Chicago"),
    "austin": _city("Austin, Texas, USA", 30.2672, -97.7431, "America/Chicago"),
    "san francisco": _city("San Francisco, California, USA", 37.7749, -122.4194, "America/Los_Angeles"),
    "seattle": _city("Seattle, Washington, USA", 47.6062, -122.3321, "America/Los_Angeles"),
    "denver": _city("Denver, Colorado, USA", 39.7392, -104.9903, "America/Denver"),
    "miami": _city("Miami, Florida, USA", 25.7617, -80.1918, "America/New_York"),
    "boston": _city("Boston, Massachusetts, USA", 42.3601, -71.0589, "America/New_York"),
    "las vegas": _city("Las Vegas, Nevada, USA", 36.1699, -115.1398, "America/Los_Angeles"),
    "portland": _city("Portland, Oregon, USA", 45.5152, -122.6784, "America/Los_Angeles"),
    "detroit": _city("Detroit, Michigan, USA", 42.3314, -83.0458, "America/Detroit"),
    "memphis": _city("Memphis, Tennessee, USA", 35.1495, -90.0490, "America/Chicago"),
    "nashville": _city("Nashville, Tennessee, USA", 36.1627, -86.7816, "America/Chicago"),
    "charlotte": _city("Charlotte, North Carolina, USA", 35.2271, -80.8431, "America/New_York"),
    "columbus": _city("Columbus, Ohio, USA", 39.9612, -82.9988, "America/New_York"),
    "indianapolis": _city("Indianapolis, Indiana, USA", 39.7684, -86.1581, "America/Indiana/Indianapolis"),
    "washington": _city("Washington, D.C., USA", 38.9072, -77.0369, "America/New_York"),
    "baltimore": _city("Baltimore, Maryland, USA", 39.2904, -76.6122, "America/New_York"),
    "milwaukee": _city("Milwaukee, Wisconsin, USA", 43.0389, -87.9065, "America/Chicago"),
    "albuquerque": _city("Albuquerque, New Mexico, USA", 35.0844, -106.6504, "America/Denver"),
    "kansas city": _city("Kansas City, Missouri, USA", 39.0997, -94.5786, "America/Chicago"),
    "st louis": _city("St. Louis, Missouri, USA", 38.6270, -90.1994, "America/Chicago"),
    "new orleans": _city("New Orleans, Louisiana, USA", 29.9511, -90.0715, "America/Chicago"),
    "minneapolis": _city("Minneapolis, Minnesota, USA", 44.9778, -93.2650, "America/Chicago"),
    "salt lake city": _city("Salt Lake City, Utah, USA", 40.7608, -111.8910, "America/Denver"),
    "honolulu": _city("Honolulu, Hawaii, USA", 21.3099, -157.8581, "Pacific/Honolulu"),
    "anchorage": _city("Anchorage, Alaska, USA", 61.2181, -149.9003, "America/Anchorage"),
    "savannah": _city("Savannah, Georgia, USA", 32.0809, -81.0912, "America/New_York"),
    "augusta": _city("Augusta, Georgia, USA", 33.4735, -82.0105, "America/New_York"),
    "macon": _city("Macon, Georgia, USA", 32.8407, -83.6324, "America/New_York"),
    "columbus ga": _city("Columbus, Georgia, USA", 32.4610, -84.9877, "America/New_York"),
    # --- International ---
    "london": _city("London, United Kingdom", 51.5074, -0.1278, "Europe/London"),
    "paris": _city("Paris, France", 48.8566, 2.3522, "Europe/Paris"),
    "berlin": _city("Berlin, Germany", 52.5200, 13.4050, "Europe/Berlin"),
    "madrid": _city("Madrid, Spain", 40.4168, -3.7038, "Europe/Madrid"),
    "rome": _city("Rome, Italy", 41.9028, 12.4964, "Europe/Rome"),
    "amsterdam": _city("Amsterdam, Netherlands", 52.3676, 4.9041, "Europe/Amsterdam"),
    "dublin": _city("Dublin, Ireland", 53.3498, -6.2603, "Europe/Dublin"),
    "lisbon": _city("Lisbon, Portugal", 38.7223, -9.1393, "Europe/Lisbon"),
    "athens": _city("Athens, Greece", 37.9838, 23.7275, "Europe/Athens"),
    "vienna": _city("Vienna, Austria", 48.2082, 16.3738, "Europe/Vienna"),
    "zurich": _city("Zurich, Switzerland", 47.3769, 8.5417, "Europe/Zurich"),
    "prague": _city("Prague, Czech Republic", 50.0755, 14.4378, "Europe/Prague"),
    "stockholm": _city("Stockholm, Sweden", 59.3293, 18.0686, "Europe/Stockholm"),
    "oslo": _city("Oslo, Norway", 59.9139, 10.7522, "Europe/Oslo"),
    "copenhagen": _city("Copenhagen, Denmark", 55.6761, 12.5683, "Europe/Copenhagen"),
    "moscow": _city("Moscow, Russia", 55.7558, 37.6173, "Europe/Moscow"),
    "istanbul": _city("Istanbul, Türkiye", 41.0082, 28.9784, "Europe/Istanbul"),
    "cairo": _city("Cairo, Egypt", 30.0444, 31.2357, "Africa/Cairo"),
    "lagos": _city("Lagos, Nigeria", 6.5244, 3.3792, "Africa/Lagos"),
    "johannesburg": _city("Johannesburg, South Africa", -26.2041, 28.0473, "Africa/Johannesburg"),
    "nairobi": _city("Nairobi, Kenya", -1.2921, 36.8219, "Africa/Nairobi"),
    "dubai": _city("Dubai, United Arab Emirates", 25.2048, 55.2708, "Asia/Dubai"),
    "mumbai": _city("Mumbai, India", 19.0760, 72.8777, "Asia/Kolkata"),
    "new delhi": _city("New Delhi, India", 28.6139, 77.2090, "Asia/Kolkata"),
    "kolkata": _city("Kolkata, India", 22.5726, 88.3639, "Asia/Kolkata"),
    "chennai": _city("Chennai, India", 13.0827, 80.2707, "Asia/Kolkata"),
    "bangkok": _city("Bangkok, Thailand", 13.7563, 100.5018, "Asia/Bangkok"),
    "singapore": _city("Singapore", 1.3521, 103.8198, "Asia/Singapore"),
    "hong kong": _city("Hong Kong", 22.3193, 114.1694, "Asia/Hong_Kong"),
    "beijing": _city("Beijing, China", 39.9042, 116.4074, "Asia/Shanghai"),
    "shanghai": _city("Shanghai, China", 31.2304, 121.4737, "Asia/Shanghai"),
    "seoul": _city("Seoul, South Korea", 37.5665, 126.9780, "Asia/Seoul"),
    "tokyo": _city("Tokyo, Japan", 35.6762, 139.6503, "Asia/Tokyo"),
    "manila": _city("Manila, Philippines", 14.5995, 120.9842, "Asia/Manila"),
    "sydney": _city("Sydney, Australia", -33.8688, 151.2093, "Australia/Sydney"),
    "melbourne": _city("Melbourne, Australia", -37.8136, 144.9631, "Australia/Melbourne"),
    "auckland": _city("Auckland, New Zealand", -36.8509, 174.7645, "Pacific/Auckland"),
    "toronto": _city("Toronto, Ontario, Canada", 43.6532, -79.3832, "America/Toronto"),
    "vancouver": _city("Vancouver, British Columbia, Canada", 49.2827, -123.1207, "America/Vancouver"),
    "montreal": _city("Montreal, Quebec, Canada", 45.5019, -73.5674, "America/Toronto"),
    "mexico city": _city("Mexico City, Mexico", 19.4326, -99.1332, "America/Mexico_City"),
    "sao paulo": _city("São Paulo, Brazil", -23.5505, -46.6333, "America/Sao_Paulo"),
    "rio de janeiro": _city("Rio de Janeiro, Brazil", -22.9068, -43.1729, "America/Sao_Paulo"),
    "buenos aires": _city("Buenos Aires, Argentina", -34.6037, -58.3816, "America/Argentina/Buenos_Aires"),
    "lima": _city("Lima, Peru", -12.0464, -77.0428, "America/Lima"),
    "bogota": _city("Bogotá, Colombia", 4.7110, -74.0721, "America/Bogota"),
}

ALIASES = {
    "nyc": "new york",
    "la": "los angeles",
    "dc": "washington",
    "washington dc": "washington",
    "saint louis": "st louis",
    "delhi": "new delhi",
    "bombay": "mumbai",
    "atl": "atlanta",
}

_COORD_PATTERN = re.compile(
    r"^\s*(-?\d+(?:\.\d+)?)\s*[,;]\s*(-?\d+(?:\.\d+)?)\s*$"
)


def _normalize(text: str) -> str:
    text = re.sub(r"[^a-z0-9,\s]", "", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def _lookup_coordinates_timezone(latitude: float, longitude: float) -> str:
    """Resolve an IANA timezone for raw coordinates via timezonefinder."""
    try:
        from timezonefinder import TimezoneFinder
    except ImportError as error:
        raise LookupError(
            "Raw coordinates need the 'timezonefinder' package for timezone "
            "lookup (pip install timezonefinder), or use a city name instead."
        ) from error
    tz_name = TimezoneFinder().timezone_at(lat=latitude, lng=longitude)
    if not tz_name:
        raise LookupError(
            f"No timezone found for coordinates {latitude}, {longitude}."
        )
    return tz_name


def resolve_location(place: str) -> dict:
    """Resolve a birth-place string to coordinates and an IANA timezone.

    Accepts a city name (matched against the offline database) or raw
    ``"latitude, longitude"`` coordinates. Raises LookupError when the
    place cannot be resolved.
    """
    if not place or not place.strip():
        raise LookupError("Birth place is empty.")

    coords = _COORD_PATTERN.match(place)
    if coords:
        latitude, longitude = float(coords.group(1)), float(coords.group(2))
        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            raise LookupError("Coordinates out of range (lat ±90, lon ±180).")
        tz_name = _lookup_coordinates_timezone(latitude, longitude)
        return {
            "display": f"{latitude:.4f}, {longitude:.4f}",
            "latitude": latitude,
            "longitude": longitude,
            "timezone": tz_name,
            "matched_by": "coordinates",
        }

    normalized = _normalize(place)
    candidates = [normalized]
    if "," in normalized:
        candidates.append(normalized.split(",")[0].strip())
    else:
        # "atlanta georgia usa" — walk the phrase down word by word.
        words = normalized.split()
        for cut in range(len(words), 0, -1):
            candidates.append(" ".join(words[:cut]))

    for candidate in candidates:
        key = ALIASES.get(candidate, candidate)
        if key in CITY_DB:
            return {**CITY_DB[key], "matched_by": key}

    close = difflib.get_close_matches(candidates[-1], CITY_DB.keys(), n=1, cutoff=0.8)
    if close:
        return {**CITY_DB[close[0]], "matched_by": f"fuzzy:{close[0]}"}

    raise LookupError(
        f"Unknown birth place '{place}'. Try a major city name (e.g. "
        f"'Atlanta, Georgia, USA') or raw coordinates like '33.75, -84.39'."
    )


def local_to_utc(birth_date: date, birth_time: str, tz_name: str) -> dict:
    """Convert local birth date + HH:MM time to UTC using historical rules.

    zoneinfo applies the DST rules in force on the birth date itself
    (e.g. June 1989 in Atlanta resolves to EDT, UTC-4).
    """
    match = re.match(r"^\s*(\d{1,2}):(\d{2})(?::(\d{2}))?\s*$", birth_time)
    if not match:
        raise ValueError(f"Birth time '{birth_time}' is not HH:MM.")
    hour, minute = int(match.group(1)), int(match.group(2))
    second = int(match.group(3) or 0)
    if hour > 23 or minute > 59 or second > 59:
        raise ValueError(f"Birth time '{birth_time}' is out of range.")

    local = datetime(
        birth_date.year, birth_date.month, birth_date.day,
        hour, minute, second, tzinfo=ZoneInfo(tz_name),
    )
    utc = local.astimezone(timezone.utc)
    offset_hours = local.utcoffset().total_seconds() / 3600

    return {
        "local": local,
        "utc": utc,
        "timezone": tz_name,
        "utc_offset_hours": offset_hours,
        "utc_offset_label": f"UTC{offset_hours:+.2g}",
    }
