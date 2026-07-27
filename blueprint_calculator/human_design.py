"""
Phase 7: Human Design.

Parallel Branch D -- Steps 20 through 23b. A pure geometric mapping of
tropical longitudes onto the Rave Mandala (Bridge 3), followed by
graph-theoretic derivation (Type, Authority, Definition) on the
resulting gate/channel/center structure. No new orbital mechanics after
the two ephemeris queries (natal + Design) already done in Phase 3.

Step 23b (Color/Tone/Base, Variable, Determination, Environment,
Perspective, Motivation) and HD-15 (Incarnation Cross naming) are left
INVENTORY, exactly as the outline tags them -- they require either
sub-line lookup tables or a named-cross database not present here.
"""
from __future__ import annotations

from .constants.hd_wheel import (
    ACTIVATION_BODIES, CHANNELS, CENTER_GATES, GATE_TO_CENTER, MOTOR_CENTERS,
    ALL_CENTERS, LINE_NAMES, STRATEGY_TABLE, INDIVIDUAL_CIRCUIT, TRIBAL_CIRCUIT,
    COLLECTIVE_CIRCUIT, INTEGRATION_CHANNELS,
)
from .ephemeris import PlanetarySnapshot, bridge_tropical_to_hd_gate_line
from .provenance import Ledger, Status


def _activation_longitude(snapshot: PlanetarySnapshot, body: str) -> float:
    if body == "Earth":
        return (snapshot.bodies["Sun"].tropical_longitude + 180) % 360
    if body == "South Node":
        # caller passes true-node-derived north node separately; see compute_activations
        raise ValueError("South Node longitude must be supplied via nodes")
    return snapshot.bodies[body].tropical_longitude


def compute_activations(snapshot: PlanetarySnapshot, north_node_true: float) -> dict[str, dict]:
    """Data Points HD-1 / HD-4 -- 13-body activation set (Personality or Design)."""
    activations = {}
    for body in ACTIVATION_BODIES:
        if body == "Earth":
            lon = (snapshot.bodies["Sun"].tropical_longitude + 180) % 360
        elif body == "North Node":
            lon = north_node_true
        elif body == "South Node":
            lon = (north_node_true + 180) % 360
        else:
            lon = snapshot.bodies[body].tropical_longitude
        activations[body] = {"longitude": lon, **bridge_tropical_to_hd_gate_line(lon)}
    return activations


def active_gates(activations: dict[str, dict]) -> set[int]:
    return {a["gate"] for a in activations.values()}


def defined_channels(total_active_gates: set[int]) -> list[tuple[int, int]]:
    """Data Point HD-7 -- Defined Channels."""
    return [ch for ch in CHANNELS if ch[0] in total_active_gates and ch[1] in total_active_gates]


def defined_centers(channels: list[tuple[int, int]]) -> set[str]:
    """Data Point HD-8 -- Defined Centers."""
    centers = set()
    for a, b in channels:
        centers.add(GATE_TO_CENTER[a])
        centers.add(GATE_TO_CENTER[b])
    return centers


def derive_type(channels: list[tuple[int, int]], centers: set[str]) -> str:
    """Data Point HD-10 -- Type."""
    if not centers:
        return "Reflector"
    adjacency: dict[str, set[str]] = {c: set() for c in centers}
    for a, b in channels:
        ca, cb = GATE_TO_CENTER[a], GATE_TO_CENTER[b]
        adjacency[ca].add(cb)
        adjacency[cb].add(ca)

    def connected(start: str, targets: set[str]) -> bool:
        seen, stack = {start}, [start]
        while stack:
            cur = stack.pop()
            if cur in targets:
                return True
            for nxt in adjacency.get(cur, ()):
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        return False

    motor_to_throat = "Throat" in centers and any(
        m in centers and connected(m, {"Throat"}) for m in MOTOR_CENTERS
    )
    sacral_defined = "Sacral" in centers

    if sacral_defined:
        return "Manifesting Generator" if motor_to_throat else "Generator"
    if motor_to_throat:
        return "Manifestor"
    return "Projector"


def derive_authority(centers: set[str], hd_type: str) -> str:
    """Data Point HD-11 -- Authority (hierarchical, first match wins)."""
    if hd_type == "Reflector":
        return "Lunar"
    if "Solar Plexus" in centers:
        return "Emotional"
    if "Sacral" in centers:
        return "Sacral"
    if "Spleen" in centers:
        return "Splenic"
    if "Heart" in centers:
        return "Ego"
    if "G" in centers:
        return "Self-Projected"
    return "Mental/Environment"


def derive_definition(channels: list[tuple[int, int]], centers: set[str]) -> str:
    """Data Point HD-12 -- Definition, by counting connected components."""
    if not centers:
        return "No Definition"
    parent = {c: c for c in centers}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[rx] = ry

    for a, b in channels:
        union(GATE_TO_CENTER[a], GATE_TO_CENTER[b])

    components = len({find(c) for c in centers})
    names = {1: "Single", 2: "Split", 3: "Triple Split", 4: "Quadruple Split Definition"}
    return names.get(components, f"{components}-way Split")


def circuit_grouping(channels: list[tuple[int, int]]) -> dict:
    """Data Point HD-16 -- Circuit Grouping."""
    ch_set = set(channels)
    return {
        "individual": sorted(ch_set & INDIVIDUAL_CIRCUIT),
        "tribal": sorted(ch_set & TRIBAL_CIRCUIT),
        "collective": sorted(ch_set & COLLECTIVE_CIRCUIT),
        "integration": sorted(ch_set & INTEGRATION_CHANNELS),
    }


def record_human_design(ledger: Ledger, natal: PlanetarySnapshot, design: PlanetarySnapshot, nodes: dict) -> dict:
    personality = compute_activations(natal, nodes["north_node_true"])
    ledger.record(
        "HD-1", system="Human Design", phase="Phase 7, Step 20", label="Personality Activations (13 Bodies)",
        value={b: a["notation"] for b, a in personality.items()}, source=["P3-5:Sun"],
        calculation="Bridge 3 applied to each of the 13 canonical bodies at natal JD",
    )
    pers_gates = active_gates(personality)
    ledger.record(
        "HD-2", system="Human Design", phase="Phase 7, Step 20", label="Personality Active Gates",
        value=sorted(pers_gates), source=["HD-1"], calculation="set of gates across all 13 Personality activations",
    )

    ledger.record(
        "HD-3", system="Human Design", phase="Phase 7, Step 21", label="Design Julian Day",
        value=design.jd, source=["P3-9"], calculation="see P3-9",
    )

    design_activations = compute_activations(design, nodes["north_node_true"])
    ledger.record(
        "HD-4", system="Human Design", phase="Phase 7, Step 22", label="Design Activations (13 Bodies)",
        value={b: a["notation"] for b, a in design_activations.items()}, source=["P3-10"],
        calculation="Bridge 3 applied to each of the 13 canonical bodies at Design JD",
    )
    design_gates = active_gates(design_activations)
    ledger.record(
        "HD-5", system="Human Design", phase="Phase 7, Step 22", label="Design Active Gates",
        value=sorted(design_gates), source=["HD-4"], calculation="set of gates across all 13 Design activations",
    )

    total_gates = pers_gates | design_gates
    ledger.record(
        "HD-6", system="Human Design", phase="Phase 7, Step 22", label="Total Active Gates",
        value=sorted(total_gates), source=["HD-2", "HD-5"], calculation="personality_active_gates union design_active_gates",
    )

    channels = defined_channels(total_gates)
    ledger.record(
        "HD-7", system="Human Design", phase="Phase 7, Step 23", label="Defined Channels",
        value=[f"{a}-{b}" for a, b in channels], source=["HD-6"],
        calculation="both gates of a canonical channel pair present in total_active_gates",
    )
    centers = defined_centers(channels)
    ledger.record(
        "HD-8", system="Human Design", phase="Phase 7, Step 23", label="Defined Centers",
        value=sorted(centers), source=["HD-7"], calculation="union of centers referenced by defined channels",
    )
    open_centers = ALL_CENTERS - centers
    ledger.record(
        "HD-9", system="Human Design", phase="Phase 7, Step 23", label="Open Centers",
        value=sorted(open_centers), source=["HD-8"], calculation="ALL_CENTERS - defined_centers",
    )

    hd_type = derive_type(channels, centers)
    ledger.record(
        "HD-10", system="Human Design", phase="Phase 7, Step 23", label="Type",
        value=hd_type, source=["HD-7", "HD-8"],
        calculation="motor-to-throat connectivity + sacral definition, per the Type decision tree",
    )
    authority = derive_authority(centers, hd_type)
    ledger.record(
        "HD-11", system="Human Design", phase="Phase 7, Step 23", label="Authority",
        value=authority, source=["HD-8", "HD-10"], calculation="hierarchical first-match on defined centers",
    )
    definition = derive_definition(channels, centers)
    ledger.record(
        "HD-12", system="Human Design", phase="Phase 7, Step 23", label="Definition",
        value=definition, source=["HD-7", "HD-8"], calculation="connected components in the defined-center adjacency graph",
    )

    profile = f"{personality['Sun']['line']}/{design_activations['Sun']['line']}"
    ledger.record(
        "HD-13", system="Human Design", phase="Phase 7, Step 23", label="Profile",
        value=profile, source=["HD-1", "HD-4"],
        calculation=f"{{personality Sun line}}/{{design Sun line}} = {LINE_NAMES[personality['Sun']['line']]}/{LINE_NAMES[design_activations['Sun']['line']]}",
    )

    strategy, signature, not_self = STRATEGY_TABLE[hd_type]
    ledger.record(
        "HD-14", system="Human Design", phase="Phase 7, Step 23", label="Strategy & Signature / Not-Self Theme",
        value={"strategy": strategy, "signature": signature, "not_self": not_self}, source=["HD-10"],
        calculation="lookup by Type",
    )

    ledger.record(
        "HD-15", system="Human Design", phase="Phase 7, Step 23", label="Incarnation Cross",
        value=None, source=["HD-1", "HD-4"], status=Status.INVENTORY,
        calculation="Requires a named-cross lookup table not present in the outline; cross TYPE (Right/Left Angle, Juxtaposition) is geometrically derivable but not computed here.",
    )

    circuits = circuit_grouping(channels)
    ledger.record(
        "HD-16", system="Human Design", phase="Phase 7, Step 23", label="Circuit Grouping",
        value={k: [f"{a}-{b}" for a, b in v] for k, v in circuits.items()}, source=["HD-7"],
        calculation="classify each defined channel as Individual / Tribal / Collective (+ Integration subset)",
    )

    for id_, label in [
        ("HD-17", "Color, Tone, Base per Activation"), ("HD-18", "Variable (Four Arrows)"),
        ("HD-19", "Determination (Digestion)"), ("HD-20", "Environment"),
        ("HD-21", "Perspective/View"), ("HD-22", "Motivation"),
    ]:
        ledger.record(
            id_, system="Human Design", phase="Phase 7, Step 23b", label=label, value=None,
            source=["HD-1"], status=Status.INVENTORY,
            calculation="Requires sub-line (Color/Tone/Base) precision analysis beyond current engine scope, per the outline.",
        )

    return {
        "personality_activations": personality,
        "design_activations": design_activations,
        "active_gates": sorted(total_gates),
        "defined_channels": channels,
        "defined_centers": sorted(centers),
        "open_centers": sorted(open_centers),
        "type": hd_type,
        "authority": authority,
        "definition": definition,
        "profile": profile,
        "strategy": strategy,
        "signature": signature,
        "not_self_theme": not_self,
        "circuits": circuits,
    }
