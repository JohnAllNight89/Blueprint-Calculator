"""Verification tests for the Western and Vedic astrology engines.

Reference profile: Johnathon Anthony Long — June 23 1989, 21:55 local,
Atlanta, Georgia, USA (EDT, UTC-4 → 1989-06-24 01:55 UT).

Expected values are Swiss Ephemeris results for that instant,
cross-checked for coherence (Sun 2.5° Cancer sits 2.6 days after the
June-21 solstice; the Moon at 2.5° Pisces is consistent with the
June 19 1989 full moon at ~27° Sagittarius plus 4.8 days of motion).
"""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engines import geolocation, vedic_astrology, western_astrology

BIRTH_DATE = date(1989, 6, 23)
BIRTH_TIME = "21:55"
BIRTH_PLACE = "Atlanta, Georgia, USA"


def _chart_inputs():
    location = geolocation.resolve_location(BIRTH_PLACE)
    moment = geolocation.local_to_utc(BIRTH_DATE, BIRTH_TIME, location["timezone"])
    return moment, location


def test_atlanta_resolves_offline():
    location = geolocation.resolve_location(BIRTH_PLACE)
    assert abs(location["latitude"] - 33.7490) < 0.01
    assert abs(location["longitude"] + 84.3880) < 0.01
    assert location["timezone"] == "America/New_York"


def test_historical_dst_applied():
    # June 1989 in Atlanta was EDT (UTC-4), not EST.
    moment, _ = _chart_inputs()
    assert moment["utc_offset_hours"] == -4.0
    assert moment["utc"].strftime("%Y-%m-%d %H:%M") == "1989-06-24 01:55"


def _western():
    moment, location = _chart_inputs()
    return western_astrology.calculate_chart(
        moment["utc"], location["latitude"], location["longitude"]
    )


def _vedic():
    moment, location = _chart_inputs()
    return vedic_astrology.calculate_chart(
        moment["utc"], location["latitude"], location["longitude"]
    )


def test_western_planets():
    chart = _western()
    by_name = {planet["name"]: planet for planet in chart["planets"]}
    assert len(by_name) == 11
    expected = {
        "Sun": 92.5448,
        "Moon": 332.4902,
        "Chiron": 98.1266,
    }
    for name, longitude in expected.items():
        assert abs(by_name[name]["longitude"] - longitude) < 0.01, name
    assert by_name["Sun"]["sign"] == "Cancer"
    assert by_name["Moon"]["sign"] == "Pisces"


def test_western_angles_and_houses():
    chart = _western()
    ascendant = chart["angles"]["ascendant"]
    midheaven = chart["angles"]["midheaven"]
    assert abs(ascendant["longitude"] - 289.2700) < 0.05
    assert ascendant["sign"] == "Capricorn"
    assert abs(midheaven["longitude"] - 218.9568) < 0.05
    assert midheaven["sign"] == "Scorpio"
    assert len(chart["houses"]) == 12
    # House 1 cusp equals the Ascendant in Placidus.
    assert abs(chart["houses"][0]["longitude"] - ascendant["longitude"]) < 0.001


def test_lahiri_ayanamsa():
    chart = _vedic()
    assert abs(chart["ayanamsa"] - 23.7101) < 0.02


def test_vedic_moon_rashi_and_nakshatra():
    chart = _vedic()
    moon = next(graha for graha in chart["grahas"] if graha["name"] == "Moon")
    # Sidereal Moon = 332.4902 − 23.7101 = 308.78 → 8°47' Kumbha (Aquarius).
    assert abs(moon["longitude"] - 308.7801) < 0.02
    assert moon["rashi"] == "Kumbha"
    assert moon["nakshatra"] == "Shatabhisha"
    assert moon["pada"] == 1
    assert moon["nakshatra_lord"] == "Rahu"


def test_vedic_includes_nodes():
    chart = _vedic()
    names = [graha["name"] for graha in chart["grahas"]]
    assert "Rahu" in names and "Ketu" in names
    rahu = next(g for g in chart["grahas"] if g["name"] == "Rahu")
    ketu = next(g for g in chart["grahas"] if g["name"] == "Ketu")
    separation = abs(rahu["longitude"] - ketu["longitude"]) % 360
    assert abs(separation - 180) < 0.001
    assert rahu["retrograde"] and ketu["retrograde"]


def test_sidereal_equals_tropical_minus_ayanamsa():
    western = _western()
    vedic = _vedic()
    tropical_moon = next(p for p in western["planets"] if p["name"] == "Moon")
    sidereal_moon = next(g for g in vedic["grahas"] if g["name"] == "Moon")
    difference = (tropical_moon["longitude"] - sidereal_moon["longitude"]) % 360
    assert abs(difference - vedic["ayanamsa"]) < 0.01


if __name__ == "__main__":
    failures = 0
    for name, func in sorted(globals().items()):
        if name.startswith("test_") and callable(func):
            try:
                func()
                print(f"  ✓ {name}")
            except AssertionError as error:
                failures += 1
                print(f"  ✗ {name}: {error}")
    if failures:
        sys.exit(f"{failures} test(s) failed")
    print("All astrology verification tests passed.")
