"""
The Chain of Command (orchestrator).

INPUTS -> PREPROCESS -> EPHEMERIS -> branches run in parallel:
  NUMEROLOGY (name + date)
  WESTERN TROPICAL (tropical longitudes)
    -> HUMAN DESIGN (tropical -> gates/lines)
       -> GENE KEYS (gate -> key mapping)
  VEDIC SIDEREAL (tropical - ayanamsa), independently
-> all branches feed CROSS-SYSTEM VALIDATION
-> SYNTHESIS (narrative)

Every step below is a direct call into the phase module that owns it;
this function's only job is sequencing and threading the Ledger through.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

from . import ephemeris as eph
from . import numerology as num
from . import western as west
from . import vedic as ved
from . import human_design as hd_mod
from . import gene_keys as gk_mod
from . import synthesis as synth
from . import validation as val
from .communication import record_communication
from .big_five import record_big_five
from .preprocessing import Coordinates, record_preprocessing
from .provenance import Ledger


@dataclass
class BlueprintReport:
    name: str
    birth_date: str
    birth_time: str
    birth_place: str
    coordinates: Coordinates
    utc_datetime: datetime
    julian_day: float
    numerology: dict
    western: dict
    vedic: dict
    human_design: dict
    gene_keys: dict
    validations: list
    synthesis: dict
    ledger: Ledger
    communication: dict = field(default_factory=dict)
    big_five: dict = field(default_factory=dict)

    def validation_summary(self) -> dict:
        by_severity = {"MANDATORY": [], "RECOMMENDED": [], "DIAGNOSTIC": []}
        for v in self.validations:
            by_severity[v.severity].append(v)
        return {
            sev: {"passed": sum(1 for v in items if v.passed), "total": len(items),
                  "failures": [v.rule_id for v in items if not v.passed]}
            for sev, items in by_severity.items()
        }


def run_pipeline(
    *, name: str, birth_date: str, birth_time: str, birth_place: str,
    today: date | None = None, current_name: str | None = None,
) -> BlueprintReport:
    today = today or date.today()
    ledger = Ledger()

    # Phase 1-2
    coords, utc_dt, jd, norm_name = record_preprocessing(
        ledger, name=name, birth_date=birth_date, birth_time=birth_time, birth_place=birth_place
    )

    # Phase 3
    natal, design, nodes = eph.record_ephemeris_core(ledger, jd, coords.latitude, coords.longitude)

    # Phase 4 (independent of ephemeris)
    numerology_result = num.record_numerology(
        ledger, name=norm_name, birth_date=birth_date, today=today, current_name=current_name
    )

    # Phase 5
    western_result = west.record_western(ledger, natal)

    # Phase 6 (independent branch off the same ephemeris core)
    vedic_result = ved.record_vedic(ledger, natal, nodes)

    # Phase 7 (depends on natal + design snapshots + nodes)
    hd_result = hd_mod.record_human_design(ledger, natal, design, nodes)

    # Phase 8 (depends only on Phase 7's gate activations)
    gk_result = gk_mod.record_gene_keys(ledger, hd_result)

    # Phase 9 (depends on everything above)
    validations = val.run_all(
        natal=natal, design=design, nodes=nodes,
        numerology=numerology_result, western=western_result, vedic=vedic_result,
        hd=hd_result, gk=gk_result,
    )

    # Phase 10
    synthesis_result = synth.record_synthesis(ledger, numerology_result, western_result, vedic_result, hd_result, gk_result)

    # Communication profile (cross-system, deterministic)
    communication_result = record_communication(numerology_result, western_result, hd_result, gk_result)

    # Big Five traits (read-only interpretive layer)
    big_five_result = record_big_five(numerology_result, hd_result, western_result)

    return BlueprintReport(
        name=name, birth_date=birth_date, birth_time=birth_time, birth_place=birth_place,
        coordinates=coords, utc_datetime=utc_dt, julian_day=jd,
        numerology=numerology_result, western=western_result, vedic=vedic_result,
        human_design=hd_result, gene_keys=gk_result, validations=validations,
        synthesis=synthesis_result, ledger=ledger, communication=communication_result,
        big_five=big_five_result,
    )
