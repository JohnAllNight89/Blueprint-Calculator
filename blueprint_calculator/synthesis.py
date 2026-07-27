"""
Phase 10: Synthesis -- The Narrative Weave.

Steps 29-30b. This is the ONLY layer in the entire pipeline where
meaning is assigned. Everything upstream (Phases 3-9) is pure
calculation and pure validation; nothing here invents a number -- it
only selects, labels, and narrates numbers already computed and
verified. The cross-system relationship table (S-6) is the load-bearing
piece: it explicitly separates "deterministic" correspondences (an
algebraic identity holds, provably) from "narrative correlation only"
(two systems say something thematically similar about the same person,
but no formula connects them). Conflating those two categories is
exactly the mistake this whole outline exists to prevent.

Step 30b's dynamic queries (transits, progressions, solar returns, the
full Vedic dasha timeline) are left INVENTORY -- they reuse machinery
this build already has (the ephemeris core, the Newton-Raphson solver,
the Vimshottari sequence) but applying it to a query date other than
birth is future scope, exactly as Phase 12 frames it.
"""
from __future__ import annotations

from .provenance import Ledger, Status

# S-6: known correspondences and whether they are provable identities
# or merely thematic. "deterministic" means: a formula in this codebase
# actually enforces the relationship (and Phase 9 validates it).
CROSS_SYSTEM_RELATIONSHIPS = [
    {"system_a": "Western", "point_a": "Sun sign", "system_b": "Human Design", "point_b": "Personality Sun gate",
     "relationship": "Bridge 3, deterministic (enforced by Rule V-1)"},
    {"system_a": "Western", "point_a": "Sun sign", "system_b": "Gene Keys", "point_b": "Life's Work",
     "relationship": "GK-4 = Personality Sun gate, deterministic"},
    {"system_a": "Human Design", "point_a": "Personality Sun gate", "system_b": "Gene Keys", "point_b": "Life's Work",
     "relationship": "direct isomorphism, deterministic (enforced by Rule V-5)"},
    {"system_a": "Human Design", "point_a": "Design Sun gate", "system_b": "Gene Keys", "point_b": "Radiance",
     "relationship": "direct isomorphism, deterministic (enforced by Rule V-5)"},
    {"system_a": "Vedic", "point_a": "Moon nakshatra", "system_b": "Human Design", "point_b": "Moon gate",
     "relationship": "same longitude, different bridges (Bridge 1+2 vs Bridge 3) -- both trace to P3-5:Moon"},
    {"system_a": "Numerology", "point_a": "Life Path", "system_b": "Western", "point_b": "Sun sign",
     "relationship": "same raw input (birth date), no algebraic bridge -- narrative correlation only"},
    {"system_a": "Numerology", "point_a": "Expression", "system_b": "Human Design", "point_b": "Type",
     "relationship": "parallel, narrative correlation only"},
    {"system_a": "Numerology", "point_a": "Soul Urge", "system_b": "Gene Keys", "point_b": "Radiance",
     "relationship": "parallel, narrative correlation only"},
]


def headlines(numerology: dict, western: dict, vedic: dict, hd: dict, gk: dict) -> dict:
    """Data Points S-1 through S-5 -- pull the headline field from each system."""
    s1 = {
        "life_path": numerology["life_path"], "expression": numerology["expression"],
        "soul_urge": numerology["soul_urge"], "personality": numerology["personality"],
        "maturity": numerology["maturity"], "attitude": numerology["attitude"],
        "birthday": numerology["birthday"], "karmic_debts": numerology["karmic_debts"],
        "karmic_lessons": numerology["karmic_lessons"], "subconscious_self": numerology["subconscious_self"],
        "personal_year": numerology["personal_year"], "personal_month": numerology["personal_month"],
        "personal_day": numerology["personal_day"],
    }
    s2 = {
        "sun_sign": western["sun_sign"], "moon_sign": western["moon_sign"], "ascendant": western["ascendant"],
        "midheaven": western["midheaven"], "chart_ruler": western["chart_ruler"],
        "element_balance": western["element_balance"], "modality_balance": western["modality_balance"],
        "lunar_phase_angle": western["lunar_phase_angle"], "dominant_retrogrades": western["dominant_retrogrades"],
    }
    s3 = {
        "moon_rashi": vedic["moon_rashi"], "moon_nakshatra": vedic["moon_nakshatra"],
        "moon_nakshatra_lord": vedic["moon_nakshatra_lord"], "lagna": vedic["lagna"],
        "lagna_lord": vedic["lagna_lord"], "starting_mahadasha": vedic["starting_mahadasha"],
        "charakaraka_atmakaraka": vedic["charakarakas"]["Atmakaraka"],
    }
    s4 = {
        "type": hd["type"], "authority": hd["authority"], "profile": hd["profile"], "definition": hd["definition"],
        "strategy": hd["strategy"], "signature": hd["signature"], "not_self_theme": hd["not_self_theme"],
        "defined_centers": hd["defined_centers"], "open_centers": hd["open_centers"],
        "defined_channels": [f"{a}-{b}" for a, b in hd["defined_channels"]],
    }
    s5 = {
        "lifes_work": gk["lifes_work"], "evolution": gk["evolution"], "radiance": gk["radiance"],
        "purpose": gk["purpose"],
        "programming_partners": {k: gk["programming_partners"][k] for k in list(gk["programming_partners"])[:8]},
    }
    return {"numerology": s1, "western": s2, "vedic": s3, "human_design": s4, "gene_keys": s5}


def cross_system_scorecard(s: dict) -> dict:
    """Data Point S-8 -- HEURISTIC thematic weighting, explicitly not a conclusion."""
    life_path = s["numerology"]["life_path"]
    return {
        "numerology_master_number_present": life_path in (11, 22, 33),
        "hd_definition_style": s["human_design"]["definition"],
        "note": "Heuristic aggregation for thematic color only -- not a definitive claim. Tag: HEURISTIC.",
    }


def synthesis_paragraph(s: dict) -> str:
    """Data Point S-9 -- the one place in the pipeline prose is generated,
    and every clause below is traceable to a specific headline field above."""
    n, w, v, h, g = s["numerology"], s["western"], s["vedic"], s["human_design"], s["gene_keys"]
    return (
        f"Core Identity: {w['sun_sign']} Sun with {w['ascendant']} rising and a {w['moon_sign']} Moon (Western); "
        f"{h['type']} with {h['authority']} Authority, Profile {h['profile']} (Human Design); "
        f"Life Path {n['life_path']}, Expression {n['expression']} (Numerology).\n"
        f"Emotional Architecture: Moon in {v['moon_rashi']}, nakshatra {v['moon_nakshatra']} ruled by {v['moon_nakshatra_lord']} (Vedic); "
        f"defined centers {', '.join(h['defined_centers']) or 'none'}, open centers {', '.join(h['open_centers'])} (Human Design).\n"
        f"Vocational Trajectory: chart ruler {w['chart_ruler']} (Western); Gene Keys Life's Work {g['lifes_work']}; "
        f"Numerology Expression {n['expression']}, Maturity {n['maturity']}.\n"
        f"Timing & Cycles: Personal Year {n.get('personal_year', 'n/a')} (Numerology); starting Mahadasha {v['starting_mahadasha']} (Vedic).\n"
        f"Current Conditioning: open centers {', '.join(h['open_centers'])} (Human Design); "
        f"karmic lessons {n['karmic_lessons']} (Numerology)."
    )


def record_synthesis(ledger: Ledger, numerology: dict, western: dict, vedic: dict, hd: dict, gk: dict) -> dict:
    s = headlines(numerology, western, vedic, hd, gk)
    ledger.record("S-1", system="Synthesis", phase="Phase 10, Step 29", label="Numerology Headlines",
                  value=s["numerology"], source=["NBD-1", "NC-1", "NC-2", "NC-3", "ND-1"])
    ledger.record("S-2", system="Synthesis", phase="Phase 10, Step 29", label="Western Tropical Headlines",
                  value=s["western"], source=["W-1", "W-9", "W-6", "W-7", "W-10"])
    ledger.record("S-3", system="Synthesis", phase="Phase 10, Step 29", label="Vedic Sidereal Headlines",
                  value=s["vedic"], source=["V-3", "V-5", "V-7", "V-8", "V-9", "V-12"])
    ledger.record("S-4", system="Synthesis", phase="Phase 10, Step 29", label="Human Design Headlines",
                  value=s["human_design"], source=["HD-10", "HD-11", "HD-12", "HD-13", "HD-14"])
    ledger.record("S-5", system="Synthesis", phase="Phase 10, Step 29", label="Gene Keys Headlines",
                  value=s["gene_keys"], source=["GK-4", "GK-5", "GK-6", "GK-7", "GK-3"])

    ledger.record("S-6", system="Synthesis", phase="Phase 10, Step 30", label="Cross-System Relationship Table",
                  value=CROSS_SYSTEM_RELATIONSHIPS, source=["S-1", "S-2", "S-3", "S-4", "S-5"])
    ledger.record("S-7", system="Synthesis", phase="Phase 10, Step 30", label="Narrative Composition Rules",
                  value="Every sentence in S-9 must cite a specific headline field from S-1..S-6.", source=["S-1", "S-2", "S-3", "S-4", "S-5", "S-6"])

    scorecard = cross_system_scorecard(s)
    ledger.record("S-8", system="Synthesis", phase="Phase 10, Step 30", label="Cross-System Scorecard",
                  value=scorecard, source=["S-1", "S-2", "S-3", "S-4", "S-5", "S-6", "S-7"], status=Status.HEURISTIC)

    paragraph = synthesis_paragraph(s)
    ledger.record("S-9", system="Synthesis", phase="Phase 10, Step 30", label="The Synthesis Paragraph",
                  value=paragraph, source=["S-6", "S-7", "S-8"])

    for id_, label in [
        ("S-10", "Transit Overlay"), ("S-11", "Progressed Positions"),
        ("S-12", "Solar Return Chart"), ("S-13", "Vedic Dasha Timeline"), ("S-14", "HD Transit Gates"),
    ]:
        ledger.record(id_, system="Synthesis", phase="Phase 10, Step 30b", label=label, value=None,
                      source=["P3-4"], status=Status.INVENTORY,
                      calculation="Reuses the Phase 3 ephemeris core / Newton-Raphson solver against a query date other than birth; not wired into this build's CLI.")

    return {"headlines": s, "relationships": CROSS_SYSTEM_RELATIONSHIPS, "scorecard": scorecard, "paragraph": paragraph}
