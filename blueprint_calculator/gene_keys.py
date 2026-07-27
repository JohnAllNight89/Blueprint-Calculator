"""
Phase 8: Gene Keys.

Parallel Branch E -- Steps 24 through 26b. Pure semantic mapping layer:
zero new mathematics. Every Gene Key is isomorphic to its Human Design
gate (gate N -> key N, line N -> line N); this module only reselects
and relabels activations already computed in Phase 7.

GK-2 (Frequency Bands text), GK-10 (Prime Gifts, HEURISTIC), and
GK-11..14 (Venus/Pearl Sequences, Codon Rings, Pathway Connections) are
left INVENTORY -- they require either a full 64-key text database or
interpretive judgment the outline explicitly defers to a Synthesis layer.
"""
from __future__ import annotations

from .provenance import Ledger, Status


def programming_partner(gene_key: int) -> int:
    """Data Point GK-3 -- Programming Partner (I Ching opposite, 180 degrees on the wheel)."""
    return ((gene_key - 1 + 32) % 64) + 1


def build_hologenetic_profile(total_active_gates: set[int], personality_gates: set[int], design_gates: set[int]) -> dict[int, dict]:
    """Data Point GK-9 -- Full 64-Key Hologenetic Profile."""
    profile = {}
    for key in range(1, 65):
        activated = key in total_active_gates
        source = None
        if activated:
            in_p, in_d = key in personality_gates, key in design_gates
            source = "Both" if (in_p and in_d) else ("Personality" if in_p else "Design")
        profile[key] = {
            "gene_key": key, "activated": activated, "source": source,
            "programming_partner": programming_partner(key),
        }
    return profile


def record_gene_keys(ledger: Ledger, hd: dict) -> dict:
    personality_gates = {a["gate"] for a in hd["personality_activations"].values()}
    design_gates = {a["gate"] for a in hd["design_activations"].values()}
    total_gates = set(hd["active_gates"])

    gk1 = {}
    for body, act in hd["personality_activations"].items():
        gk1[f"Personality:{body}"] = {"gene_key": act["gate"], "line": act["line"], "source": "Personality"}
    for body, act in hd["design_activations"].items():
        gk1[f"Design:{body}"] = {"gene_key": act["gate"], "line": act["line"], "source": "Design"}
    ledger.record(
        "GK-1", system="Gene Keys", phase="Phase 8, Step 24", label="Gene Key per Activated Gate",
        value={k: f"{v['gene_key']}.{v['line']}" for k, v in gk1.items()}, source=["HD-1", "HD-4"],
        calculation="gene_key = gate; gene_line = line (1:1 isomorphism with Human Design)",
    )
    ledger.record(
        "GK-2", system="Gene Keys", phase="Phase 8, Step 24", label="Frequency Bands per Gene Key",
        value=None, source=["GK-1"], status=Status.INVENTORY,
        calculation="Requires the full 64-key Shadow/Gift/Siddhi text database; not embedded in the outline.",
    )
    partners = {k: programming_partner(k) for k in sorted(total_gates)}
    ledger.record(
        "GK-3", system="Gene Keys", phase="Phase 8, Step 24", label="Programming Partner per Gene Key",
        value=partners, source=["GK-1"], calculation="((gene_key - 1 + 32) % 64) + 1",
    )

    lifes_work = hd["personality_activations"]["Sun"]
    evolution = hd["personality_activations"]["Earth"]
    radiance = hd["design_activations"]["Sun"]
    purpose = hd["design_activations"]["Earth"]
    ledger.record(
        "GK-4", system="Gene Keys", phase="Phase 8, Step 25", label="Life's Work",
        value=lifes_work["notation"], source=["HD-1"], calculation="gene_key.line = personality Sun activation",
    )
    ledger.record(
        "GK-5", system="Gene Keys", phase="Phase 8, Step 25", label="Evolution",
        value=evolution["notation"], source=["HD-1"], calculation="gene_key.line = personality Earth activation",
    )
    ledger.record(
        "GK-6", system="Gene Keys", phase="Phase 8, Step 25", label="Radiance",
        value=radiance["notation"], source=["HD-4"], calculation="gene_key.line = design Sun activation",
    )
    ledger.record(
        "GK-7", system="Gene Keys", phase="Phase 8, Step 25", label="Purpose",
        value=purpose["notation"], source=["HD-4"], calculation="gene_key.line = design Earth activation",
    )
    sequence = [
        {"sphere": "Life's Work", **lifes_work}, {"sphere": "Evolution", **evolution},
        {"sphere": "Radiance", **radiance}, {"sphere": "Purpose", **purpose},
    ]
    ledger.record(
        "GK-8", system="Gene Keys", phase="Phase 8, Step 25", label="Activation Sequence (Composite)",
        value=[s["sphere"] + ": " + s["notation"] for s in sequence], source=["GK-4", "GK-5", "GK-6", "GK-7"],
        calculation="[Life's Work, Evolution, Radiance, Purpose]",
    )

    profile64 = build_hologenetic_profile(total_gates, personality_gates, design_gates)
    ledger.record(
        "GK-9", system="Gene Keys", phase="Phase 8, Step 26", label="Full 64-Key Hologenetic Profile",
        value={k: v for k, v in profile64.items() if v["activated"]}, source=["HD-6", "GK-1", "GK-3"],
        calculation="iterate all 64 keys; populate activation/source/programming_partner where gate is in HD-6",
    )
    ledger.record(
        "GK-10", system="Gene Keys", phase="Phase 8, Step 26", label="Prime Gifts",
        value=None, source=["GK-9"], status=Status.HEURISTIC,
        calculation="Requires interpretive assessment of 'highest frequency' keys; deferred to Synthesis layer per the outline.",
    )
    for id_, label in [
        ("GK-11", "Venus Sequence"), ("GK-12", "Pearl Sequence"),
        ("GK-13", "Codon Ring Membership"), ("GK-14", "Pathway Connections"),
    ]:
        ledger.record(
            id_, system="Gene Keys", phase="Phase 8, Step 26b", label=label, value=None,
            source=["GK-9"], status=Status.INVENTORY,
            calculation="Sphere-to-planet mapping / biological / contemplative lookup table not embedded in the outline.",
        )

    return {
        "lifes_work": lifes_work["notation"], "evolution": evolution["notation"],
        "radiance": radiance["notation"], "purpose": purpose["notation"],
        "programming_partners": partners, "activation_sequence": sequence,
        "hologenetic_profile": {k: v for k, v in profile64.items() if v["activated"]},
    }
