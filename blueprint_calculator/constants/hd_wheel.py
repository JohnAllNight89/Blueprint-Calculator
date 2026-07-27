"""
Human Design constants, transcribed verbatim from Phase 3 (Bridge 3) and
Phase 7 of the Master Outline. These are the fixed geometric facts of the
Rave Mandala -- nobody tunes these per-person; they are the wheel itself.
"""

# Bridge 3 constants (Phase 3, Step 6)
WHEEL_START = 302.0        # Gate 41 begins at 02*00' Aquarius (302 degrees ecliptic)
GATE_SPAN = 5.625          # 360 / 64 gates
LINE_SPAN = GATE_SPAN / 6  # 0.9375 degrees per line

# Gate wheel order: the 64 gates in zodiacal sequence starting at WHEEL_START
GATE_WHEEL = [
    41, 19, 13, 49, 30, 55, 37, 63, 22, 36, 25, 17, 21, 51, 42, 3,
    27, 24, 2, 23, 8, 20, 16, 35, 45, 12, 15, 52, 39, 53, 62, 56,
    31, 33, 7, 4, 29, 59, 40, 64, 47, 6, 46, 18, 48, 57, 32, 50,
    28, 44, 1, 43, 14, 34, 9, 5, 26, 11, 10, 58, 38, 54, 61, 60,
]
assert len(GATE_WHEEL) == 64
assert set(GATE_WHEEL) == set(range(1, 65))

# Design Moment Solver constants (Phase 3, Step 6b)
DESIGN_ARC = 88.0                    # degrees of solar longitude, prenatal
MEAN_SOLAR_MOTION = 0.98564736       # degrees/day, average

# Line archetypes (Human Design profile names)
LINE_NAMES = {
    1: "Investigator",
    2: "Hermit",
    3: "Martyr",
    4: "Opportunist",
    5: "Heretic",
    6: "Role Model",
}

# The 36 canonical channels connecting two gates
CHANNELS = [
    (1, 8), (2, 14), (3, 60), (4, 63), (5, 15), (6, 59), (7, 31), (9, 52),
    (10, 20), (10, 34), (10, 57), (11, 56), (12, 22), (13, 33), (16, 48),
    (17, 62), (18, 58), (19, 49), (20, 34), (20, 57), (21, 45), (23, 43),
    (24, 61), (25, 51), (26, 44), (27, 50), (28, 38), (29, 46), (30, 41),
    (32, 54), (34, 57), (35, 36), (37, 40), (39, 55), (42, 53), (47, 64),
]
assert len(CHANNELS) == 36

# Center-to-gate mapping: which gates sit on which of the 9 energy centers
CENTER_GATES = {
    "Head": {64, 61, 63},
    "Ajna": {47, 24, 4, 17, 43, 11},
    "Throat": {62, 23, 56, 35, 12, 45, 33, 8, 31, 20, 16},
    "G": {1, 13, 25, 46, 2, 15, 10, 7},
    "Heart": {21, 40, 26, 51},
    "Sacral": {34, 5, 14, 29, 59, 9, 3, 42, 27},
    "Solar Plexus": {36, 22, 37, 6, 49, 55, 30},
    "Spleen": {48, 57, 44, 50, 32, 28, 18},
    "Root": {58, 38, 54, 53, 60, 52, 19, 39, 41},
}
_all_center_gates = set()
for _gates in CENTER_GATES.values():
    _all_center_gates |= _gates
assert _all_center_gates == set(range(1, 65))

GATE_TO_CENTER = {g: c for c, gates in CENTER_GATES.items() for g in gates}

MOTOR_CENTERS = {"Sacral", "Solar Plexus", "Heart", "Root"}
ALL_CENTERS = set(CENTER_GATES)

# Circuit groupings (Phase 7, HD-16)
INDIVIDUAL_CIRCUIT = {
    (1, 8), (2, 14), (3, 60), (4, 63), (10, 20), (10, 34), (10, 57),
    (20, 34), (20, 57), (28, 38), (32, 54), (34, 57),
}
TRIBAL_CIRCUIT = {
    (5, 15), (6, 59), (9, 52), (12, 22), (19, 49), (21, 45), (26, 44),
    (27, 50), (29, 46), (30, 41), (37, 40), (39, 55), (42, 53),
}
COLLECTIVE_CIRCUIT = set(CHANNELS) - INDIVIDUAL_CIRCUIT - TRIBAL_CIRCUIT
INTEGRATION_CHANNELS = {(20, 34), (10, 34), (20, 57), (10, 57)}
assert INDIVIDUAL_CIRCUIT | TRIBAL_CIRCUIT | COLLECTIVE_CIRCUIT == set(CHANNELS)

# Type -> Strategy / Signature / Not-Self theme (Phase 7, HD-14)
STRATEGY_TABLE = {
    "Manifestor": ("To Inform", "Peace", "Anger"),
    "Generator": ("To Respond", "Satisfaction", "Frustration"),
    "Manifesting Generator": ("To Respond", "Satisfaction", "Frustration"),
    "Projector": ("Wait for the Invitation", "Success", "Bitterness"),
    "Reflector": ("Wait a Lunar Cycle", "Surprise", "Disappointment"),
}

# The 13-body canonical activation set (Phase 7, HD-1), in canonical HD order.
# "Earth"/"South Node" are derived (+180 deg) from Sun/North Node respectively.
ACTIVATION_BODIES = [
    "Sun", "Earth", "North Node", "South Node", "Moon", "Mercury", "Venus",
    "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
]
