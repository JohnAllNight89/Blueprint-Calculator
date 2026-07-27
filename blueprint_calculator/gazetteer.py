"""
Offline city gazetteer (Phase 2, Step 2 / Data Point P3-1).

Real production systems would back this with a full geonames database;
this is a compact offline lookup covering major world cities so the
pipeline can run with zero network dependency. Callers can always bypass
it entirely by supplying "lat,lon" directly.
"""
from __future__ import annotations

# name (lowercase, no punctuation) -> (latitude, longitude, display_name)
CITIES: dict[str, tuple[float, float, str]] = {
    "atlanta": (33.7490, -84.3880, "Atlanta, GA, USA"),
    "new york": (40.7128, -74.0060, "New York, NY, USA"),
    "los angeles": (34.0522, -118.2437, "Los Angeles, CA, USA"),
    "chicago": (41.8781, -87.6298, "Chicago, IL, USA"),
    "houston": (29.7604, -95.3698, "Houston, TX, USA"),
    "phoenix": (33.4484, -112.0740, "Phoenix, AZ, USA"),
    "philadelphia": (39.9526, -75.1652, "Philadelphia, PA, USA"),
    "san antonio": (29.4241, -98.4936, "San Antonio, TX, USA"),
    "san diego": (32.7157, -117.1611, "San Diego, CA, USA"),
    "dallas": (32.7767, -96.7970, "Dallas, TX, USA"),
    "austin": (30.2672, -97.7431, "Austin, TX, USA"),
    "seattle": (47.6062, -122.3321, "Seattle, WA, USA"),
    "denver": (39.7392, -104.9903, "Denver, CO, USA"),
    "boston": (42.3601, -71.0589, "Boston, MA, USA"),
    "miami": (25.7617, -80.1918, "Miami, FL, USA"),
    "detroit": (42.3314, -83.0458, "Detroit, MI, USA"),
    "washington": (38.9072, -77.0369, "Washington, DC, USA"),
    "las vegas": (36.1699, -115.1398, "Las Vegas, NV, USA"),
    "reno": (39.5296, -119.8138, "Reno, NV, USA"),
    "sacramento": (38.5816, -121.4944, "Sacramento, CA, USA"),
    "salt lake city": (40.7608, -111.8910, "Salt Lake City, UT, USA"),
    "albuquerque": (35.0844, -106.6504, "Albuquerque, NM, USA"),
    "tucson": (32.2226, -110.9747, "Tucson, AZ, USA"),
    "colorado springs": (38.8339, -104.8214, "Colorado Springs, CO, USA"),
    "kansas city": (39.0997, -94.5786, "Kansas City, MO, USA"),
    "st louis": (38.6270, -90.1994, "St. Louis, MO, USA"),
    "memphis": (35.1495, -90.0490, "Memphis, TN, USA"),
    "louisville": (38.2527, -85.7585, "Louisville, KY, USA"),
    "indianapolis": (39.7684, -86.1581, "Indianapolis, IN, USA"),
    "columbus": (39.9612, -82.9988, "Columbus, OH, USA"),
    "cleveland": (41.4993, -81.6944, "Cleveland, OH, USA"),
    "pittsburgh": (40.4406, -79.9959, "Pittsburgh, PA, USA"),
    "baltimore": (39.2904, -76.6122, "Baltimore, MD, USA"),
    "charlotte": (35.2271, -80.8431, "Charlotte, NC, USA"),
    "raleigh": (35.7796, -78.6382, "Raleigh, NC, USA"),
    "jacksonville": (30.3322, -81.6557, "Jacksonville, FL, USA"),
    "tampa": (27.9506, -82.4572, "Tampa, FL, USA"),
    "orlando": (28.5383, -81.3792, "Orlando, FL, USA"),
    "new orleans": (29.9511, -90.0715, "New Orleans, LA, USA"),
    "oklahoma city": (35.4676, -97.5164, "Oklahoma City, OK, USA"),
    "omaha": (41.2565, -95.9345, "Omaha, NE, USA"),
    "milwaukee": (43.0389, -87.9065, "Milwaukee, WI, USA"),
    "nashville": (36.1627, -86.7816, "Nashville, TN, USA"),
    "portland": (45.5152, -122.6784, "Portland, OR, USA"),
    "minneapolis": (44.9778, -93.2650, "Minneapolis, MN, USA"),
    "san francisco": (37.7749, -122.4194, "San Francisco, CA, USA"),
    "honolulu": (21.3069, -157.8583, "Honolulu, HI, USA"),
    "anchorage": (61.2181, -149.9003, "Anchorage, AK, USA"),
    "toronto": (43.6532, -79.3832, "Toronto, ON, Canada"),
    "vancouver": (49.2827, -123.1207, "Vancouver, BC, Canada"),
    "montreal": (45.5019, -73.5674, "Montreal, QC, Canada"),
    "mexico city": (19.4326, -99.1332, "Mexico City, Mexico"),
    "london": (51.5074, -0.1278, "London, UK"),
    "paris": (48.8566, 2.3522, "Paris, France"),
    "berlin": (52.5200, 13.4050, "Berlin, Germany"),
    "madrid": (40.4168, -3.7038, "Madrid, Spain"),
    "rome": (41.9028, 12.4964, "Rome, Italy"),
    "amsterdam": (52.3676, 4.9041, "Amsterdam, Netherlands"),
    "dublin": (53.3498, -6.2603, "Dublin, Ireland"),
    "lisbon": (38.7223, -9.1393, "Lisbon, Portugal"),
    "vienna": (48.2082, 16.3738, "Vienna, Austria"),
    "zurich": (47.3769, 8.5417, "Zurich, Switzerland"),
    "stockholm": (59.3293, 18.0686, "Stockholm, Sweden"),
    "oslo": (59.9139, 10.7522, "Oslo, Norway"),
    "copenhagen": (55.6761, 12.5683, "Copenhagen, Denmark"),
    "athens": (37.9838, 23.7275, "Athens, Greece"),
    "moscow": (55.7558, 37.6173, "Moscow, Russia"),
    "istanbul": (41.0082, 28.9784, "Istanbul, Turkey"),
    "cairo": (30.0444, 31.2357, "Cairo, Egypt"),
    "johannesburg": (-26.2041, 28.0473, "Johannesburg, South Africa"),
    "lagos": (6.5244, 3.3792, "Lagos, Nigeria"),
    "nairobi": (-1.2921, 36.8219, "Nairobi, Kenya"),
    "dubai": (25.2048, 55.2708, "Dubai, UAE"),
    "mumbai": (19.0760, 72.8777, "Mumbai, India"),
    "delhi": (28.7041, 77.1025, "Delhi, India"),
    "bangalore": (12.9716, 77.5946, "Bangalore, India"),
    "kolkata": (22.5726, 88.3639, "Kolkata, India"),
    "chennai": (13.0827, 80.2707, "Chennai, India"),
    "beijing": (39.9042, 116.4074, "Beijing, China"),
    "shanghai": (31.2304, 121.4737, "Shanghai, China"),
    "hong kong": (22.3193, 114.1694, "Hong Kong"),
    "tokyo": (35.6762, 139.6503, "Tokyo, Japan"),
    "osaka": (34.6937, 135.5023, "Osaka, Japan"),
    "seoul": (37.5665, 126.9780, "Seoul, South Korea"),
    "singapore": (1.3521, 103.8198, "Singapore"),
    "bangkok": (13.7563, 100.5018, "Bangkok, Thailand"),
    "jakarta": (-6.2088, 106.8456, "Jakarta, Indonesia"),
    "manila": (14.5995, 120.9842, "Manila, Philippines"),
    "sydney": (-33.8688, 151.2093, "Sydney, Australia"),
    "melbourne": (-37.8136, 144.9631, "Melbourne, Australia"),
    "auckland": (-36.8485, 174.7633, "Auckland, New Zealand"),
    "sao paulo": (-23.5505, -46.6333, "Sao Paulo, Brazil"),
    "rio de janeiro": (-22.9068, -43.1729, "Rio de Janeiro, Brazil"),
    "buenos aires": (-34.6037, -58.3816, "Buenos Aires, Argentina"),
    "lima": (-12.0464, -77.0428, "Lima, Peru"),
    "bogota": (4.7110, -74.0721, "Bogota, Colombia"),
    "santiago": (-33.4489, -70.6693, "Santiago, Chile"),
}


class PlaceNotFound(ValueError):
    pass


def normalize_city(raw: str) -> str:
    return " ".join(raw.strip().lower().replace(",", " ").split())


def lookup_city(raw: str) -> tuple[float, float, str]:
    """Look up a city by name. Raises PlaceNotFound if not in the gazetteer."""
    key = normalize_city(raw)
    if key in CITIES:
        return CITIES[key]
    # try matching just the first token group (e.g. "Atlanta, GA, USA" -> "atlanta")
    first = raw.split(",")[0].strip().lower()
    if first in CITIES:
        return CITIES[first]
    raise PlaceNotFound(
        f"'{raw}' is not in the offline gazetteer. "
        f"Pass coordinates directly as 'lat,lon' instead."
    )
