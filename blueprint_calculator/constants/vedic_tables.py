"""Vedic (Jyotish) lookup tables, transcribed from Phase 6 of the Master Outline."""

RASHI_NAMES = [
    "Mesha (Aries)", "Vrishabha (Taurus)", "Mithuna (Gemini)", "Karka (Cancer)",
    "Simha (Leo)", "Kanya (Virgo)", "Tula (Libra)", "Vrishchika (Scorpio)",
    "Dhanu (Sagittarius)", "Makara (Capricorn)", "Kumbha (Aquarius)", "Meena (Pisces)",
]
assert len(RASHI_NAMES) == 12

# Rulership: sidereal rashi -> ruling graha (Vedic table excludes outer planets)
RASHI_LORDS = [
    "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
    "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter",
]

NAKSHATRA_SPAN = 360.0 / 27.0   # 13.3333 degrees
PADA_SPAN = NAKSHATRA_SPAN / 4  # 3.3333 degrees

# 27 nakshatras with their Vimshottari dasha lord (Phase 6, Step 18)
NAKSHATRAS = [
    ("Ashwini", "Ketu"), ("Bharani", "Venus"), ("Krittika", "Sun"),
    ("Rohini", "Moon"), ("Mrigashira", "Mars"), ("Ardra", "Rahu"),
    ("Punarvasu", "Jupiter"), ("Pushya", "Saturn"), ("Ashlesha", "Mercury"),
    ("Magha", "Ketu"), ("Purva Phalguni", "Venus"), ("Uttara Phalguni", "Sun"),
    ("Hasta", "Moon"), ("Chitra", "Mars"), ("Swati", "Rahu"),
    ("Vishakha", "Jupiter"), ("Anuradha", "Saturn"), ("Jyeshtha", "Mercury"),
    ("Mula", "Ketu"), ("Purva Ashadha", "Venus"), ("Uttara Ashadha", "Sun"),
    ("Shravana", "Moon"), ("Dhanishta", "Mars"), ("Shatabhisha", "Rahu"),
    ("Purva Bhadrapada", "Jupiter"), ("Uttara Bhadrapada", "Saturn"), ("Revati", "Mercury"),
]
assert len(NAKSHATRAS) == 27

# Vimshottari Mahadasha lengths in years (fixed 120-year cycle), in dasha order
VIMSOTTARI_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
VIMSOTTARI_YEARS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}
assert sum(VIMSOTTARI_YEARS.values()) == 120
