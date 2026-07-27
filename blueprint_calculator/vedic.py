"""
Phase 6: Vedic Sidereal Astrology.

Parallel Branch C -- Steps 16 through 19. Introduces zero new orbital
mechanics: every data point here is Bridge 2 (tropical - ayanamsa)
applied to the Phase 3 ephemeris output, followed by lookup tables and
geometric rules on the resulting sidereal placements.

V-13 (Yogas), V-14 (Vargas / divisional charts), V-15 (Bhava Chalit),
and V-16 (Arudha Padas) are left as INVENTORY: the outline itself notes
these require either large classical-text lookup tables or additional
house-cusp machinery beyond what Phase 3 provides, and were not
expanded into full formulas in the source document.
"""
from __future__ import annotations

import swisseph as swe

from .constants.vedic_tables import (
    RASHI_NAMES, RASHI_LORDS, NAKSHATRA_SPAN, PADA_SPAN, NAKSHATRAS,
    VIMSOTTARI_ORDER, VIMSOTTARI_YEARS,
)
from .ephemeris import PlanetarySnapshot, bridge_tropical_to_sidereal, smallest_signed_angle
from .provenance import Ledger, Status

# Exaltation / debilitation sign index + exact degree, per the outline's V-10 table
DIGNITY_TABLE = {
    "Sun": {"exalt_sign": 0, "exalt_deg": 10, "debil_sign": 6, "debil_deg": 10},
    "Moon": {"exalt_sign": 1, "exalt_deg": 3, "debil_sign": 7, "debil_deg": 3},
    "Mars": {"exalt_sign": 9, "exalt_deg": 28, "debil_sign": 3, "debil_deg": 28},
    "Mercury": {"exalt_sign": 5, "exalt_deg": 15, "debil_sign": 11, "debil_deg": 15},
    "Jupiter": {"exalt_sign": 3, "exalt_deg": 5, "debil_sign": 9, "debil_deg": 5},
    "Venus": {"exalt_sign": 11, "exalt_deg": 27, "debil_sign": 5, "debil_deg": 27},
    "Saturn": {"exalt_sign": 6, "exalt_deg": 20, "debil_sign": 0, "debil_deg": 20},
}

# Combustion orb per graha, degrees of separation from the Sun (V-11)
COMBUSTION_ORBS = {
    "Moon": 12.0, "Mars": 17.0, "Mercury": 14.0, "Jupiter": 11.0, "Venus": 10.0, "Saturn": 15.0,
}
COMBUSTION_ORBS_RETROGRADE = {"Mercury": 12.0, "Venus": 8.0}

# Charakaraka rank order (V-9): highest degree-in-rashi -> Atmakaraka, etc.
CHARAKARAKA_NAMES = [
    "Atmakaraka", "Amatyakaraka", "Bhratrikaraka", "Matrukaraka",
    "Putrakaraka", "Gnatikaraka", "Darakaraka",
]
CHARAKARAKA_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
_NATURAL_ORDER_RANK = {p: i for i, p in enumerate(CHARAKARAKA_PLANETS)}


def rashi_of(sidereal_longitude: float) -> dict:
    """Data Point V-3 -- Rashi Placement per Graha (Bridge 1 applied to sidereal)."""
    idx = int(sidereal_longitude // 30)
    return {"rashi_index": idx, "rashi_name": RASHI_NAMES[idx], "degrees_in_rashi": sidereal_longitude % 30}


def nakshatra_of(sidereal_longitude: float) -> dict:
    """Data Point V-5 -- Nakshatra + Pada per Graha."""
    idx = int(sidereal_longitude // NAKSHATRA_SPAN)
    within = sidereal_longitude - idx * NAKSHATRA_SPAN
    pada = int(within // PADA_SPAN) + 1
    name, lord = NAKSHATRAS[idx]
    return {"nakshatra_number": idx + 1, "nakshatra_name": name, "lord": lord, "pada": pada, "degrees_in_nakshatra": within}


def lagna_lord(lagna_rashi_index: int) -> str:
    """Data Point V-7 -- Lagna Lord."""
    return RASHI_LORDS[lagna_rashi_index]


def charakaraka_set(sidereal_degrees_in_rashi: dict[str, float]) -> dict:
    """Data Point V-9 -- Charakaraka Set (Atmakaraka, etc.), ranked by degrees-in-rashi."""
    ranked = sorted(
        CHARAKARAKA_PLANETS,
        key=lambda p: (-sidereal_degrees_in_rashi[p], _NATURAL_ORDER_RANK[p]),
    )
    return {CHARAKARAKA_NAMES[i]: ranked[i] for i in range(7)}


def dignity_of(body: str, sidereal_longitude: float) -> dict:
    """Data Point V-10 -- Planetary Dignity (simplified: Exaltation / Own Sign / Debilitation / Neutral).

    The outline's dignity table only gives exaltation/debilitation points and
    the rulership table; classical Friend/Enemy/Moolatrikona states require
    a planetary-friendship table not present in the source document, so
    those two states are intentionally not distinguished here.
    """
    if body not in DIGNITY_TABLE:
        return {"dignity": "N/A"}
    t = DIGNITY_TABLE[body]
    rashi = int(sidereal_longitude // 30)
    deg = sidereal_longitude % 30
    if rashi == t["exalt_sign"]:
        state = "Exaltation" if abs(deg - t["exalt_deg"]) <= 1 else "Exaltation Sign"
    elif rashi == t["debil_sign"]:
        state = "Debilitation" if abs(deg - t["debil_deg"]) <= 1 else "Debilitation Sign"
    elif RASHI_LORDS[rashi] == body:
        state = "Own Sign"
    else:
        state = "Neutral"
    return {"dignity": state, "rashi_index": rashi, "degrees_in_rashi": deg}


def combustion_of(body: str, sun_sidereal: float, body_sidereal: float, retrograde: bool) -> dict:
    """Data Point V-11 -- Combustion Status."""
    if body not in COMBUSTION_ORBS:
        return {"combust": False, "separation": None}
    separation = abs(smallest_signed_angle(body_sidereal - sun_sidereal))
    orb = COMBUSTION_ORBS_RETROGRADE.get(body, COMBUSTION_ORBS[body]) if retrograde else COMBUSTION_ORBS[body]
    return {"combust": separation <= orb, "separation": separation, "orb_used": orb}


def dasha_balance_at_birth(moon_nakshatra: dict) -> dict:
    """Data Point V-12 -- Vimsottari Dasha Balance at Birth."""
    lord = moon_nakshatra["lord"]
    total_years = VIMSOTTARI_YEARS[lord]
    portion_traversed = moon_nakshatra["degrees_in_nakshatra"] / NAKSHATRA_SPAN
    years_elapsed = portion_traversed * total_years
    years_remaining = total_years - years_elapsed
    return {"starting_mahadasha": lord, "total_mahadasha_years": total_years, "years_remaining": years_remaining}


def record_vedic(ledger: Ledger, snapshot: PlanetarySnapshot, nodes: dict) -> dict:
    ayanamsa = snapshot.ayanamsa
    ledger.record(
        "V-1", system="Vedic", phase="Phase 6, Step 16", label="Lahiri Ayanamsa Value",
        value=ayanamsa, source=["P3-8"], calculation="swe.set_sid_mode(SIDM_LAHIRI); swe.get_ayanamsa_ut(jd)",
    )

    sidereal = {}
    for name, pos in snapshot.bodies.items():
        sidereal[name] = bridge_tropical_to_sidereal(pos.tropical_longitude, ayanamsa)
    sidereal["Rahu"] = bridge_tropical_to_sidereal(nodes["rahu_mean"], ayanamsa)
    sidereal["Ketu"] = bridge_tropical_to_sidereal(nodes["ketu_mean"], ayanamsa)

    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    _, ascmc_sid = swe.houses_ex(snapshot.jd, snapshot.latitude, snapshot.longitude, b"W", swe.FLG_SIDEREAL)
    lagna_longitude = ascmc_sid[0] % 360
    sidereal["Lagna"] = lagna_longitude

    ledger.record(
        "V-2", system="Vedic", phase="Phase 6, Step 16", label="Sidereal Longitude per Graha",
        value=sidereal, source=["P3-5:Sun", "V-1"], calculation="(tropical_longitude - ayanamsa) % 360, all bodies + Rahu/Ketu/Lagna",
    )

    rashis = {name: rashi_of(lon) for name, lon in sidereal.items()}
    ledger.record(
        "V-3", system="Vedic", phase="Phase 6, Step 17", label="Rashi Placement per Graha",
        value={n: r["rashi_name"] for n, r in rashis.items()}, source=["V-2"],
        calculation="rashi_index = floor(sidereal_longitude / 30)",
    )
    ledger.record(
        "V-4", system="Vedic", phase="Phase 6, Step 17", label="Lagna (Sidereal Ascendant)",
        value=lagna_longitude, source=["P3-3", "P3-1", "V-1"],
        calculation="swe.houses_ex(jd, lat, lon, b'W', FLG_SIDEREAL); ascmc[0]",
    )

    nakshatras = {name: nakshatra_of(lon) for name, lon in sidereal.items() if name not in ("Lagna",)}
    ledger.record(
        "V-5", system="Vedic", phase="Phase 6, Step 18", label="Nakshatra + Pada per Graha",
        value={n: f"{v['nakshatra_name']} pada {v['pada']}" for n, v in nakshatras.items()}, source=["V-2"],
        calculation="nakshatra_index = floor(sidereal_longitude / 13.3333); pada = floor(within / 3.3333) + 1",
    )
    ledger.record(
        "V-6", system="Vedic", phase="Phase 6, Step 18", label="Rahu & Ketu (Mean Node)",
        value={"rahu": sidereal["Rahu"], "ketu": sidereal["Ketu"]}, source=["P3-3", "V-1"],
        calculation="swe.calc_ut(jd, MEAN_NODE) then Bridge 2; Ketu = Rahu + 180",
    )

    lord = lagna_lord(rashis["Lagna"]["rashi_index"])
    ledger.record(
        "V-7", system="Vedic", phase="Phase 6, Step 19", label="Lagna Lord",
        value=lord, source=["V-4"], calculation="RASHI_LORDS[lagna_rashi_index]", status=Status.IMPLEMENTED,
    )

    moon_nak = nakshatras["Moon"]
    ledger.record(
        "V-8", system="Vedic", phase="Phase 6, Step 19", label="Moon Nakshatra Lord (Janma Nakshatra Lord)",
        value=moon_nak["lord"], source=["V-5"], calculation="lookup nakshatra lord for Moon's nakshatra",
    )

    degrees_in_rashi = {p: rashis[p]["degrees_in_rashi"] for p in CHARAKARAKA_PLANETS}
    karakas = charakaraka_set(degrees_in_rashi)
    ledger.record(
        "V-9", system="Vedic", phase="Phase 6, Step 19", label="Charakaraka Set",
        value=karakas, source=["V-2", "V-3"],
        calculation="rank 7 classical planets by degrees_in_rashi descending; tie-break by natural order",
    )

    dignities = {p: dignity_of(p, sidereal[p]) for p in DIGNITY_TABLE}
    ledger.record(
        "V-10", system="Vedic", phase="Phase 6, Step 19", label="Planetary Dignity (simplified)",
        value={p: d["dignity"] for p, d in dignities.items()}, source=["V-3"],
        calculation="compare sidereal sign/degree against exaltation, debilitation, own-sign tables",
        status=Status.DERIVED,
    )

    combustions = {
        p: combustion_of(p, sidereal["Sun"], sidereal[p], snapshot.bodies[p].retrograde)
        for p in COMBUSTION_ORBS
    }
    ledger.record(
        "V-11", system="Vedic", phase="Phase 6, Step 19", label="Combustion Status",
        value={p: c["combust"] for p, c in combustions.items()}, source=["V-2"],
        calculation="abs(smallest_signed_angle(body - Sun)) <= combustion_orb[body]",
    )

    dasha = dasha_balance_at_birth(moon_nak)
    ledger.record(
        "V-12", system="Vedic", phase="Phase 6, Step 19", label="Vimsottari Dasha Balance at Birth",
        value=dasha, source=["V-5", "V-8"],
        calculation="portion_traversed = moon_degrees_in_nakshatra / 13.3333; years_remaining = total - portion*total",
    )

    for id_, label in [
        ("V-13", "Yogas Present"), ("V-14", "Divisional Charts (Vargas)"),
        ("V-15", "Bhava Chalit (Chalit Chart)"), ("V-16", "Arudha Padas"),
    ]:
        ledger.record(
            id_, system="Vedic", phase="Phase 6, Step 19", label=label, value=None,
            source=["V-3"], status=Status.INVENTORY,
            calculation="Requires classical-text lookup tables / additional house machinery not specified in the outline.",
        )

    return {
        "sidereal_longitudes": sidereal,
        "rashis": {n: r["rashi_name"] for n, r in rashis.items()},
        "nakshatras": nakshatras,
        "lagna": rashis["Lagna"]["rashi_name"],
        "lagna_lord": lord,
        "moon_rashi": rashis["Moon"]["rashi_name"],
        "moon_nakshatra": moon_nak["nakshatra_name"],
        "moon_nakshatra_lord": moon_nak["lord"],
        "charakarakas": karakas,
        "dignities": dignities,
        "combustions": combustions,
        "starting_mahadasha": dasha["starting_mahadasha"],
        "dasha_balance": dasha,
    }
