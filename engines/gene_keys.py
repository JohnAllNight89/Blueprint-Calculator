"""Gene Keys engine.

The 64 Gene Keys correspond one-to-one with the 64 Human Design gates
(and the 64 I Ching hexagrams). Each key carries a frequency spectrum of
Shadow → Gift → Siddhi. The Activation Sequence maps the four prime
spheres from the Human Design Sun/Earth activations:

* Life's Work — Personality Sun
* Evolution   — Personality Earth
* Radiance    — Design Sun
* Purpose     — Design Earth
"""

from __future__ import annotations

# key: (I Ching name, Shadow, Gift, Siddhi)
GENE_KEYS = {
    1: ("The Creative", "Entropy", "Freshness", "Beauty"),
    2: ("The Receptive", "Dislocation", "Orientation", "Unity"),
    3: ("Difficulty at the Beginning", "Chaos", "Innovation", "Innocence"),
    4: ("Youthful Folly", "Intolerance", "Understanding", "Forgiveness"),
    5: ("Waiting", "Impatience", "Patience", "Timelessness"),
    6: ("Conflict", "Conflict", "Diplomacy", "Peace"),
    7: ("The Army", "Division", "Guidance", "Virtue"),
    8: ("Holding Together", "Mediocrity", "Style", "Exquisiteness"),
    9: ("The Taming Power of the Small", "Inertia", "Determination", "Invincibility"),
    10: ("Treading", "Self-Obsession", "Naturalness", "Being"),
    11: ("Peace", "Obscurity", "Idealism", "Light"),
    12: ("Standstill", "Vanity", "Discrimination", "Purity"),
    13: ("Fellowship with Men", "Discord", "Discernment", "Empathy"),
    14: ("Possession in Great Measure", "Compromise", "Competence", "Bounteousness"),
    15: ("Modesty", "Dullness", "Magnetism", "Florescence"),
    16: ("Enthusiasm", "Indifference", "Versatility", "Mastery"),
    17: ("Following", "Opinion", "Far-Sightedness", "Omniscience"),
    18: ("Work on What Has Been Spoiled", "Judgment", "Integrity", "Perfection"),
    19: ("Approach", "Co-dependence", "Sensitivity", "Sacrifice"),
    20: ("Contemplation", "Superficiality", "Self-Assurance", "Presence"),
    21: ("Biting Through", "Control", "Authority", "Valor"),
    22: ("Grace", "Dishonor", "Graciousness", "Grace"),
    23: ("Splitting Apart", "Complexity", "Simplicity", "Quintessence"),
    24: ("Return", "Addiction", "Invention", "Silence"),
    25: ("Innocence", "Constriction", "Acceptance", "Universal Love"),
    26: ("The Taming Power of the Great", "Pride", "Artfulness", "Invisibility"),
    27: ("The Corners of the Mouth", "Selfishness", "Altruism", "Selflessness"),
    28: ("Preponderance of the Great", "Purposelessness", "Totality", "Immortality"),
    29: ("The Abysmal", "Half-Heartedness", "Commitment", "Devotion"),
    30: ("The Clinging Fire", "Desire", "Lightness", "Rapture"),
    31: ("Influence", "Arrogance", "Leadership", "Humility"),
    32: ("Duration", "Failure", "Preservation", "Veneration"),
    33: ("Retreat", "Forgetting", "Mindfulness", "Revelation"),
    34: ("The Power of the Great", "Force", "Strength", "Majesty"),
    35: ("Progress", "Hunger", "Adventure", "Boundlessness"),
    36: ("Darkening of the Light", "Turbulence", "Humanity", "Compassion"),
    37: ("The Family", "Weakness", "Equality", "Tenderness"),
    38: ("Opposition", "Struggle", "Perseverance", "Honor"),
    39: ("Obstruction", "Provocation", "Dynamism", "Liberation"),
    40: ("Deliverance", "Exhaustion", "Resolve", "Divine Will"),
    41: ("Decrease", "Fantasy", "Anticipation", "Emanation"),
    42: ("Increase", "Expectation", "Detachment", "Celebration"),
    43: ("Breakthrough", "Deafness", "Insight", "Epiphany"),
    44: ("Coming to Meet", "Interference", "Teamwork", "Synarchy"),
    45: ("Gathering Together", "Dominance", "Synergy", "Communion"),
    46: ("Pushing Upward", "Seriousness", "Delight", "Ecstasy"),
    47: ("Oppression", "Oppression", "Transmutation", "Transfiguration"),
    48: ("The Well", "Inadequacy", "Resourcefulness", "Wisdom"),
    49: ("Revolution", "Reaction", "Revolution", "Rebirth"),
    50: ("The Cauldron", "Corruption", "Equilibrium", "Harmony"),
    51: ("The Arousing", "Agitation", "Initiative", "Awakening"),
    52: ("Keeping Still", "Stress", "Restraint", "Stillness"),
    53: ("Development", "Immaturity", "Expansion", "Superabundance"),
    54: ("The Marrying Maiden", "Greed", "Aspiration", "Ascension"),
    55: ("Abundance", "Victimization", "Freedom", "Freedom"),
    56: ("The Wanderer", "Distraction", "Enrichment", "Intoxication"),
    57: ("The Gentle", "Unease", "Intuition", "Clarity"),
    58: ("The Joyous", "Dissatisfaction", "Vitality", "Bliss"),
    59: ("Dispersion", "Dishonesty", "Intimacy", "Transparency"),
    60: ("Limitation", "Limitation", "Realism", "Justice"),
    61: ("Inner Truth", "Psychosis", "Inspiration", "Sanctity"),
    62: ("Preponderance of the Small", "Intellect", "Precision", "Impeccability"),
    63: ("After Completion", "Doubt", "Inquiry", "Truth"),
    64: ("Before Completion", "Confusion", "Imagination", "Illumination"),
}

ACTIVATION_SEQUENCE = [
    ("Life's Work", "personality", "Sun", "What you are here to do — your outer purpose."),
    ("Evolution", "personality", "Earth", "What life is teaching you — your inner growth."),
    ("Radiance", "design", "Sun", "What keeps you healthy and vital — your presence."),
    ("Purpose", "design", "Earth", "What grounds you — your deepest inner purpose."),
]


def _spectrum(key: int, line: int) -> dict:
    name, shadow, gift, siddhi = GENE_KEYS[key]
    return {
        "gene_key": key,
        "line": line,
        "notation": f"{key}.{line}",
        "name": name,
        "shadow": shadow,
        "gift": gift,
        "siddhi": siddhi,
    }


def calculate_profile(human_design_chart: dict) -> dict:
    """Derive the Gene Keys profile from a computed Human Design chart."""
    activations = {
        "personality": {
            entry["body"]: entry
            for entry in human_design_chart["personality"]["activations"]
        },
        "design": {
            entry["body"]: entry
            for entry in human_design_chart["design"]["activations"]
        },
    }

    sequence = []
    for sphere, side, body, meaning in ACTIVATION_SEQUENCE:
        activation = activations[side][body]
        sequence.append({
            "sphere": sphere,
            "source": f"{side.capitalize()} {body}",
            "meaning": meaning,
            **_spectrum(activation["gate"], activation["line"]),
        })

    # Every activated gate, viewed through the Gene Keys lens.
    seen: dict[int, dict] = {}
    for side in ("personality", "design"):
        for entry in human_design_chart[side]["activations"]:
            key = entry["gate"]
            slot = seen.setdefault(key, {**_spectrum(key, entry["line"]), "sources": []})
            slot["sources"].append(f"{side.capitalize()} {entry['body']}")

    return {
        "activation_sequence": sequence,
        "all_keys": sorted(seen.values(), key=lambda item: item["gene_key"]),
    }
