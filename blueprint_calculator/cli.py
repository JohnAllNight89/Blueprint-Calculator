"""
CLI entry point. Run a birth chart through the full pipeline and print
either a human-readable audit trail or a raw JSON provenance ledger.

Examples:
    python -m blueprint_calculator.cli --name "Ada Lovelace" --date 1815-12-10 \\
        --time 08:00 --place "London"

    python -m blueprint_calculator.cli --doc-example   # reproduces the
        Master Outline's own worked example (Johnathon Anthony Long)

    python -m blueprint_calculator.cli --name "..." --date ... --time ... \\
        --place ... --json > report.json   # full provenance ledger
"""
from __future__ import annotations

import argparse
import json
from datetime import date

from .pipeline import run_pipeline
from .provenance import DataPoint


def _json_default(o):
    if isinstance(o, DataPoint):
        return o.to_dict()
    return str(o)


def print_report(report) -> None:
    print("=" * 72)
    print(f"SOUL BLUEPRINT -- {report.name}")
    print(f"{report.birth_date} {report.birth_time} local, {report.coordinates.display_name}")
    print(f"  -> UTC: {report.utc_datetime.isoformat()}   JD: {report.julian_day:.6f}")
    print("=" * 72)

    n = report.numerology
    print("\n-- PHASE 4: NUMEROLOGY --")
    print(f"  Life Path {n['life_path']}  Expression {n['expression']}  Soul Urge {n['soul_urge']}  "
          f"Personality {n['personality']}  Maturity {n['maturity']}  Balance {n['balance']}")
    print(f"  Attitude {n['attitude']}  Birthday {n['birthday']}  Personal Year {n['personal_year']}"
          f"/Month {n['personal_month']}/Day {n['personal_day']}")
    print(f"  Karmic Debts {n['karmic_debts']}  Karmic Lessons {n['karmic_lessons']}  Subconscious Self {n['subconscious_self']}")

    w = report.western
    print("\n-- PHASE 5: WESTERN TROPICAL --")
    print(f"  Sun {w['sun_sign']}  Moon {w['moon_sign']}  Ascendant {w['ascendant']}  MC {w['midheaven']}  Chart Ruler {w['chart_ruler']}")
    print(f"  Elements {w['element_balance']}  Modalities {w['modality_balance']}")
    print(f"  Lunar phase: {w['lunar_phase_name']} ({w['lunar_phase_angle']:.2f} deg)")

    v = report.vedic
    print("\n-- PHASE 6: VEDIC SIDEREAL --")
    print(f"  Lagna {v['lagna']} (lord {v['lagna_lord']})  Moon {v['moon_rashi']} / {v['moon_nakshatra']} (lord {v['moon_nakshatra_lord']})")
    print(f"  Starting Mahadasha: {v['starting_mahadasha']}  ({v['dasha_balance']['years_remaining']:.2f} yrs remaining of {v['dasha_balance']['total_mahadasha_years']})")
    print(f"  Atmakaraka: {v['charakarakas']['Atmakaraka']}")

    h = report.human_design
    print("\n-- PHASE 7: HUMAN DESIGN --")
    print(f"  Type: {h['type']}  Authority: {h['authority']}  Profile: {h['profile']}  Definition: {h['definition']}")
    print(f"  Strategy: {h['strategy']} / Signature: {h['signature']} / Not-Self: {h['not_self_theme']}")
    print(f"  Defined Centers: {', '.join(h['defined_centers']) or 'none'}")
    print(f"  Open Centers: {', '.join(h['open_centers'])}")
    print(f"  Active Gates ({len(h['active_gates'])}): {h['active_gates']}")

    g = report.gene_keys
    print("\n-- PHASE 8: GENE KEYS --")
    print(f"  Life's Work {g['lifes_work']}  Evolution {g['evolution']}  Radiance {g['radiance']}  Purpose {g['purpose']}")

    print("\n-- PHASE 9: CROSS-SYSTEM VALIDATION --")
    summary = report.validation_summary()
    for sev in ("MANDATORY", "RECOMMENDED", "DIAGNOSTIC"):
        info = summary[sev]
        print(f"  {sev}: {info['passed']}/{info['total']} passed" + (f"  FAILED: {info['failures']}" if info["failures"] else ""))
    total_passed = sum(v.passed for v in report.validations)
    print(f"  TOTAL: {total_passed}/{len(report.validations)} rules pass")

    print("\n-- PHASE 10: SYNTHESIS --")
    print(report.synthesis["paragraph"])
    print()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Blueprint Calculator -- run the full Human Condition pipeline.")
    p.add_argument("--name", help="Full birth name")
    p.add_argument("--date", dest="birth_date", help="Birth date, YYYY-MM-DD")
    p.add_argument("--time", dest="birth_time", help="Birth time, HH:MM (local, 24h)")
    p.add_argument("--place", dest="birth_place", help="Birth place: city name (offline gazetteer) or 'lat,lon'")
    p.add_argument("--current-name", default=None, help="Optional current/stage name for NCN-1..4")
    p.add_argument("--today", default=None, help="Override 'today' for timing cycles, YYYY-MM-DD")
    p.add_argument("--json", action="store_true", help="Dump the full provenance ledger as JSON instead of a text report")
    p.add_argument("--trace", metavar="DATA_POINT_ID", help="Print the full ancestry chain for one data point (e.g. HD-10) and exit")
    p.add_argument("--doc-example", action="store_true",
                    help="Run the Master Outline's own worked example (Johnathon Anthony Long, 1989-06-23 21:55, Atlanta)")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.doc_example:
        args.name = "Johnathon Anthony Long"
        args.birth_date = "1989-06-23"
        args.birth_time = "21:55"
        args.birth_place = "Atlanta"

    if not (args.name and args.birth_date and args.birth_time and args.birth_place):
        build_parser().error("--name, --date, --time, --place are required (or pass --doc-example)")

    today = date.fromisoformat(args.today) if args.today else None
    report = run_pipeline(
        name=args.name, birth_date=args.birth_date, birth_time=args.birth_time,
        birth_place=args.birth_place, today=today, current_name=args.current_name,
    )

    if args.trace:
        chain = report.ledger.trace(args.trace)
        if not chain:
            print(f"No such data point: {args.trace}")
            return 1
        for dp in chain:
            print(f"[{dp.id}] {dp.label} = {dp.value}")
            if dp.calculation:
                print(f"    calc: {dp.calculation}")
            if dp.source:
                print(f"    from: {dp.source}")
        return 0

    if args.json:
        print(json.dumps(report.ledger.to_dict(), indent=2, default=_json_default))
        return 0

    print_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
