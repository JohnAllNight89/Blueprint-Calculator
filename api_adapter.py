"""
API Adapter — translates BlueprintReport into the frontend JSON contract.

The frontend (templates/index.html) expects a specific nested JSON shape.
This module performs all structural translations without adding new data;
every value in the output traces to a field already computed by the pipeline.
"""
from __future__ import annotations

import re
from collections import Counter

import swisseph as swe
from zoneinfo import ZoneInfo

from blueprint_calculator.ephemeris import bridge_tropical_to_sign
from blueprint_calculator.constants.hd_wheel import GATE_TO_CENTER, LINE_NAMES
from blueprint_calculator.constants.vedic_tables import RASHI_NAMES
from blueprint_calculator.gene_keys import programming_partner
from blueprint_calculator.pipeline import BlueprintReport

# ---- Glyph lookup tables ----

BODY_GLYPHS: dict[str, str] = {
    "Sun": "☉", "Moon": "☽", "Mercury": "☿", "Venus": "♀", "Mars": "♂",
    "Jupiter": "♃", "Saturn": "♄", "Uranus": "♅", "Neptune": "♆",
    "Pluto": "♇", "Chiron": "⚷", "North Node": "☊", "South Node": "☋",
    "Earth": "⊕", "Rahu": "☊", "Ketu": "☋",
}

SIGN_GLYPHS: dict[str, str] = {
    "Aries": "♈", "Taurus": "♉", "Gemini": "♊", "Cancer": "♋",
    "Leo": "♌", "Virgo": "♍", "Libra": "♎", "Scorpio": "♏",
    "Sagittarius": "♐", "Capricorn": "♑", "Aquarius": "♒", "Pisces": "♓",
}

HD_AUTHORITY_LABELS: dict[str, str] = {
    "Emotional": "Emotional (Solar Plexus)",
    "Sacral": "Sacral",
    "Splenic": "Splenic",
    "Ego": "Ego (Heart)",
    "Self-Projected": "Self-Projected (G Center)",
    "Mental/Environment": "Mental / Environment",
    "Lunar": "Lunar (Reflector)",
}

LP_ARCHETYPES: dict[int, str] = {
    1: "The Pioneer", 2: "The Diplomat", 3: "The Creative", 4: "The Builder",
    5: "The Freedom Seeker", 6: "The Nurturer", 7: "The Mystic", 8: "The Powerhouse",
    9: "The Humanitarian", 11: "Master Illuminator", 22: "Master Builder",
    33: "Master Teacher",
}

# Karmic debt raw-value overrides (chain[0] check before reducing)
KARMIC_ARCHETYPES: dict[int, str] = {
    13: "Karmic Foundation — Work Through Transformation",
    14: "Karmic Freedom — Temptation and Self-Mastery",
    16: "Karmic Tower — Truth Through Disruption",
    19: "Karmic Ego — Leadership Through Humility",
}

# Expression — same base names; karmic debts override via KARMIC_ARCHETYPES
EXPR_ARCHETYPES: dict[int, str] = {
    1: "The Pioneer Voice", 2: "The Harmonizing Voice", 3: "The Creative Communicator",
    4: "The Grounded Achiever", 5: "The Versatile Messenger", 6: "The Nurturing Voice",
    7: "The Depth Seeker", 8: "The Empowered Achiever", 9: "The Humanitarian Voice",
    11: "Master Illuminator", 22: "Master Builder", 33: "Master Teacher",
}

# Soul Urge — the interior engine flavor
SOUL_ARCHETYPES: dict[int, str] = {
    1: "Driven by Independence and Self-Direction",
    2: "Driven by Connection and Harmony",
    3: "Driven by Creative Expression",
    4: "Driven by Stability and Foundation",
    5: "Driven by Freedom and Experience",
    6: "Driven by Love and Nurturing Service",
    7: "Driven by Truth and Depth",
    8: "Driven by Mastery and Impact",
    9: "Driven by Universal Compassion",
    11: "Master Messenger — Inspired Spiritual Vision",
    22: "Master Builder — World-Scale Creation",
    33: "Master Teacher — Compassionate Service",
}

# Personality — the outer face / mask projection
PERS_ARCHETYPES: dict[int, str] = {
    1: "The Pioneer Face — Projects Independent Authority",
    2: "The Diplomat Face — Projects Sensitivity and Receptivity",
    3: "The Expressive Face — Projects Warmth and Charm",
    4: "The Reliable Face — Projects Grounded Competence",
    5: "The Magnetic Face — Projects Dynamic Energy",
    6: "The Caring Face — Projects Warmth and Responsibility",
    7: "The Mysterious Face — Projects Depth and Perception",
    8: "The Executive Face — Projects Power and Competence",
    9: "The Wise Face — Projects Compassionate Authority",
    11: "Master Intuitive Face — Projects Inspired Intelligence",
    22: "Master Visionary Face — Projects Monumental Purpose",
    33: "Master Healer Face — Projects Inspiring Presence",
}

# Attitude — the instinctive first-response register
ATT_ARCHETYPES: dict[int, str] = {
    1: "Self-Reliant First Impression",
    2: "Intuitive First Impression",
    3: "Expressive First Impression",
    4: "Grounded First Impression",
    5: "Dynamic First Impression",
    6: "Caring First Impression",
    7: "Perceptive First Impression",
    8: "Commanding First Impression",
    9: "Wise First Impression",
    11: "Master Intuitive First Impression",
    22: "Master Visionary First Impression",
}

# Birthday — the birth-day energy (keyed by reduced day value 1–9, 11, 22)
BDAY_ARCHETYPES: dict[int, str] = {
    1: "The Independent Initiator",
    2: "The Sensitive Collaborator",
    3: "The Expressive Communicator",
    4: "The Disciplined Builder",
    5: "Freedom — Dynamic Change",
    6: "The Responsible Nurturer",
    7: "The Analytical Seeker",
    8: "The Ambitious Leader",
    9: "The Compassionate Server",
    11: "Master Intuitive",
    22: "Master Builder",
}

# Maturity — the destination crystallizing in midlife
MAT_ARCHETYPES: dict[int, str] = {
    1: "Maturing Into Pioneer Leadership",
    2: "Maturing Into Diplomatic Wisdom",
    3: "Maturing Into Creative Mastery",
    4: "Maturing Into Grounded Authority",
    5: "Maturing Into Freedom and Fluency",
    6: "Maturing Into Nurturing Legacy",
    7: "Maturing Into Spiritual Mastery",
    8: "Maturing Into Material Authority",
    9: "Humanitarian Completion",
    11: "Maturing Into Master Illumination",
    22: "Maturing Into Master Building",
    33: "Maturing Into Master Teaching",
}

# Generation — birth-year digit sum (always reduces to 1–9, no masters)
GEN_ARCHETYPES: dict[int, str] = {
    1: "The Pioneer Generation — Originators",
    2: "The Diplomatic Generation — Bridge Builders",
    3: "The Creative Generation — Communicators",
    4: "The Builder Generation — Reformers",
    5: "The Freedom Generation — Change Agents",
    6: "Legacy and Responsibility",
    7: "The Seeker Generation — Philosophers",
    8: "The Power Generation — Transformers",
    9: "The Humanitarian Generation — Completers",
}

# Personal Year — the active annual cycle
PY_ARCHETYPES: dict[int, str] = {
    1: "Year of New Beginnings",
    2: "Year of Partnership and Patience",
    3: "Year of Expression and Visibility",
    4: "Year of Foundation and Discipline",
    5: "Year of Change and Freedom",
    6: "Year of Responsibility and Love",
    7: "Year of Introspection and Inner Authority",
    8: "Year of Power and Manifestation",
    9: "Year of Completion and Release",
    11: "Year of Heightened Intuition",
    22: "Year of Master Building",
    33: "Year of Master Service",
}

PROFILE_LABELS: dict[str, str] = {
    "1/3": "Investigator / Martyr", "1/4": "Investigator / Opportunist",
    "2/4": "Hermit / Opportunist", "2/5": "Hermit / Heretic",
    "3/5": "Martyr / Heretic", "3/6": "Martyr / Role Model",
    "4/6": "Opportunist / Role Model", "4/1": "Opportunist / Investigator",
    "5/1": "Heretic / Investigator", "5/2": "Heretic / Hermit",
    "6/2": "Role Model / Hermit", "6/3": "Role Model / Martyr",
}

# Activation Sequence + Venus Sequence + Pearl sphere → source label
SPHERE_SOURCE: dict[str, str] = {
    "Life's Work": "Personality Sun",
    "Evolution": "Personality Earth",
    "Radiance": "Design Sun",
    "Purpose": "Design Earth",
    "Attraction": "Design Moon",
    "IQ": "Personality Venus",
    "EQ": "Personality Mars",
    "SQ": "Design Venus",
    "Vocation (Core)": "Design Mars",
    "Culture": "Design Jupiter",
    "Pearl": "Personality Jupiter",
}

SPHERE_MEANING: dict[str, str] = {
    "Life's Work": "What you are here to do — your outer purpose.",
    "Evolution": "What life is teaching you — your inner growth.",
    "Radiance": "What keeps you healthy and vital — your presence.",
    "Purpose": "What grounds you — your deepest inner purpose.",
    "Attraction": "What draws you into relationship — your core relational pattern.",
    "IQ": "How you think — your mental signature in love and partnership.",
    "EQ": "How you feel — your emotional signature in love and partnership.",
    "SQ": "The deeper archetype you're growing toward within relationship.",
    "Vocation (Core)": "The underlying skill or role that grounds your work in the world.",
    "Culture": "The people and environments that amplify your gifts.",
    "Pearl": "Where your gifts convert into lasting prosperity — your destiny point.",
}

# Preferred display order for Vedic grahas
_VEDIC_ORDER = [
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
    "Rahu", "Ketu", "Uranus", "Neptune", "Pluto", "Chiron",
]

# Gene Keys: (I Ching name, Shadow, Gift, Siddhi)
GENE_KEYS: dict[int, tuple[str, str, str, str]] = {
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


# ---- Headline descriptions (personalized, 2+ data points each) ----

_LP_THEMES: dict[int, tuple[str, str]] = {
    1:  ("independence and original initiative",     "a recurring restlessness until you're driving your own direction"),
    2:  ("partnership and diplomatic sensitivity",    "a pull toward finding the bridge between opposing forces"),
    3:  ("creative expression and joyful communication", "the need to bring something beautiful or connected into the world through your own voice"),
    4:  ("discipline, structure, and enduring foundation", "the drive to build something solid that genuinely lasts"),
    5:  ("freedom, versatility, and transformative change", "the restlessness that keeps moving until enough of life has been tasted"),
    6:  ("responsibility, beauty, and nurturing service", "the pull toward caretaking, harmony, and aligning what you do with what you value"),
    7:  ("introspection, spiritual inquiry, and truth-seeking", "the need to understand the underlying mechanics of things, not just the surface"),
    8:  ("material mastery and executive authority",  "the drive toward tangible achievement, power, and impact that others can see and feel"),
    9:  ("universal compassion and humanitarian completion", "the call toward something larger than personal gain — the final chapter before a new cycle"),
    11: ("visionary illumination and inspired transmission", "a channel for frequencies that arrive whole, not reasoned step-by-step"),
    22: ("master-builder synthesis of vision and structure", "the rare capacity to hold both an elevated vision and the discipline to ground it into reality"),
    33: ("master healing and selfless elevation",    "the call toward uplifting and healing others — service as the deepest form of self-expression"),
}

_SIGN_THEMES: dict[str, tuple[str, str]] = {
    "Aries":       ("The Initiator",     "identity forged through action and pioneering"),
    "Taurus":      ("The Builder",       "identity anchored in stability, beauty, and material security"),
    "Gemini":      ("The Communicator",  "identity expressed through curiosity, adaptability, and connection"),
    "Cancer":      ("The Nurturer",      "identity formed through emotional depth, protection, and belonging"),
    "Leo":         ("The Creator",       "identity expressed through creativity, courage, and generous self-expression"),
    "Virgo":       ("The Analyst",       "identity refined through precision, service, and discernment"),
    "Libra":       ("The Harmonizer",    "identity shaped by relationship, balance, and aesthetic intelligence"),
    "Scorpio":     ("The Transformer",   "identity formed through depth, intensity, and the willingness to go where others won't"),
    "Sagittarius": ("The Philosopher",   "identity expressed through expansion, meaning-making, and the pursuit of truth"),
    "Capricorn":   ("The Architect",     "identity built through discipline, mastery, and long-term achievement"),
    "Aquarius":    ("The Visionary",     "identity expressed through originality, humanitarianism, and systemic thinking"),
    "Pisces":      ("The Dreamer",       "identity formed through empathy, creativity, and spiritual sensitivity"),
}

_MOON_EMOTIONAL: dict[str, str] = {
    "Aries":       "instinctively initiates — processes emotion through action and immediate expression",
    "Taurus":      "needs security and sensory grounding before feeling stable — resists being rushed",
    "Gemini":      "processes emotion through language and connection — needs to talk through what's felt",
    "Cancer":      "feels deeply and protects that depth — cycles between openness and self-protection",
    "Leo":         "needs recognition and warmth to feel safe — generates enormous loyalty when honored",
    "Virgo":       "processes through analysis and service — manages anxiety by finding what can be improved",
    "Libra":       "needs harmony and beauty in the environment to feel at ease — conflict costs real energy",
    "Scorpio":     "feels at the depths and doesn't surface easily — intensity is the natural emotional register",
    "Sagittarius": "needs freedom and philosophical distance from whatever is felt — humor as a coping mechanism",
    "Capricorn":   "controls and structures the emotional body — processes through doing and achieving",
    "Aquarius":    "holds emotion at a mental distance — needs to understand feelings before experiencing them",
    "Pisces":      "absorbs and merges with the emotional field — boundaries are diffuse by design",
}

_ASC_THEMES: dict[str, str] = {
    "Aries":       "meets the world as a direct, immediate force — first impressions are bold and energizing",
    "Taurus":      "meets the world with calm, steady presence — projects reliability before anything else",
    "Gemini":      "meets the world through words and curiosity — instantly engaging, light, and adaptive",
    "Cancer":      "meets the world through feeling — the protective shell is what others see first",
    "Leo":         "meets the world with radiance and warmth — presence is felt before words are spoken",
    "Virgo":       "meets the world with precision and helpfulness — details noticed that others overlook",
    "Libra":       "meets the world through beauty and diplomacy — instinctively softens edges and creates harmony",
    "Scorpio":     "meets the world with depth and intensity — magnetic but with an edge that keeps others slightly uncertain",
    "Sagittarius": "meets the world with enthusiasm and directness — honesty that can surprise before it lands",
    "Capricorn":   "meets the world through competence and composure — authority projects before credentials are given",
    "Aquarius":    "meets the world as the observer — a quality of 'outside looking in' that others find hard to pin down",
    "Pisces":      "meets the world through sensitivity and adaptability — shape-shifts to fit context almost unconsciously",
}

_TYPE_GIFTS: dict[str, str] = {
    "Generator":           "sustainable life-force, mastery built through genuine engagement, and the full-body YES that others trust as an honest signal",
    "Manifesting Generator": "multi-dimensional speed, the ability to pioneer several lanes simultaneously, and showing others what's possible before asking permission",
    "Projector":           "penetrating insight into systems and people, the gift of guiding others toward greater efficiency, and wisdom that arrives through deep observation",
    "Manifestor":          "initiatory power, the ability to catalyze new realities without needing external approval, and opening doors others then walk through",
    "Reflector":           "environmental attunement, the gift of sampling and reflecting the full spectrum of human possibility, and wisdom calibrated through lunar-cycle timing",
}

_AUTH_DESCRIPTIONS: dict[str, str] = {
    "Sacral":              "the gut response — the immediate body-yes or body-no that knows before the mind constructs a reason. For you, if the gut doesn't respond, the answer is wait",
    "Splenic":             "a spontaneous in-the-moment signal — a quiet, single-frequency tone that doesn't repeat. It's not loud, it doesn't argue with you, and it only arrives once",
    "Emotional":           "the emotional wave — you need to ride the full arc of an emotional state before committing. The clarity lives at the crest, never in the valley, never in the peak of enthusiasm",
    "Ego":                 "the will center — you speak from the heart and the promises you make are reliable precisely because your heart-energy backed them. If you can't find the will to say it, the answer is no",
    "Self-Projected":      "the sound of your own voice as you talk through a decision — you need trusted people who will listen without advising. The answer reveals itself in what you hear yourself say",
    "Mental/Environment":  "the environment and trusted people — not an inner signal but the clarity that emerges over time across multiple conversations and settings",
    "Lunar":               "the full lunar cycle — 28 days of living with a decision across every signature of the moon before committing. What feels right at the new moon may feel different at the full",
}


def _headline_descriptions(
    num: dict, west: dict, hd: dict, ved: dict | None, gk: dict, comm: dict | None
) -> dict:
    """Return personalized one-paragraph explanations for each headline chip.

    Each description weaves 2+ of the person's specific data points so
    it can never be mistaken for a generic category definition.
    """
    lp = num.get("life_path", 0)
    expr = num.get("expression", 0)
    soul = num.get("soul_urge", 0)

    sun  = west.get("sun_sign", "") if isinstance(west, dict) else ""
    moon = west.get("moon_sign", "") if isinstance(west, dict) else ""
    asc  = west.get("ascendant", "") if isinstance(west, dict) else ""
    chart_ruler = west.get("chart_ruler", "") if isinstance(west, dict) else ""
    lunar_phase = west.get("lunar_phase_name", "") if isinstance(west, dict) else ""
    elem_bal = west.get("element_balance", {}) if isinstance(west, dict) else {}
    dom_elem = max(elem_bal, key=elem_bal.get) if elem_bal else ""

    hd_type   = hd.get("type", "") if isinstance(hd, dict) else ""
    authority = hd.get("authority", "") if isinstance(hd, dict) else ""
    profile   = hd.get("profile", "") if isinstance(hd, dict) else ""
    strategy  = hd.get("strategy", "") if isinstance(hd, dict) else ""
    signature = hd.get("signature", "") if isinstance(hd, dict) else ""
    not_self  = hd.get("not_self_theme", "") if isinstance(hd, dict) else ""
    profile_label = PROFILE_LABELS.get(profile, "") if profile else ""

    lifes_work_notation = gk.get("lifes_work", "") if isinstance(gk, dict) else ""
    lw_gate = 0
    lw_name = lw_shadow = lw_gift = lw_siddhi = ""
    if lifes_work_notation and "." in lifes_work_notation:
        try:
            lw_gate = int(lifes_work_notation.split(".")[0])
            info = GENE_KEYS.get(lw_gate, ("", "", "", ""))
            lw_name, lw_shadow, lw_gift, lw_siddhi = info
        except (ValueError, IndexError):
            pass

    lp_arch  = LP_ARCHETYPES.get(lp, "unique frequency")
    lp_theme, lp_pull = _LP_THEMES.get(lp, ("a unique soul path", "a persistent calling you can't fully explain"))
    sun_arch, sun_theme = _SIGN_THEMES.get(sun, ("", ""))
    moon_emotional = _MOON_EMOTIONAL.get(moon, "processes emotion through a unique internal rhythm")
    asc_theme = _ASC_THEMES.get(asc, "meets the world with a distinctive presence")

    out: dict = {}

    # Life Path
    out["life_path"] = {
        "title": f"Life Path {lp}",
        "subtitle": lp_arch,
        "body": (
            f"Life Path {lp} is the primary frequency your entire existence is built around — "
            f"the recurring theme that shows up in your relationships, your work, your crises, your breakthroughs. "
            f"Every major chapter of your life, looked at honestly, is some version of the same arc: {lp_theme}. "
            f"Not a role you chose. A frequency you carry. It was encoded before you had a name for it. "
            f"You've felt it as {lp_pull}. "
            f"Your Expression {expr} is the instrument through which this path broadcasts outwardly — "
            f"the specific voice and gift others have always recognized in you, before you consciously developed it. "
            f"Your Soul Urge {soul} is the engine underneath both — the interior hunger that makes this feel like a calling "
            f"rather than a career choice. "
            f"When Life Path ({lp}), Expression ({expr}), and Soul Urge ({soul}) are running in concert, "
            f"effort stops feeling like effort. The friction is always in the gap between what these three are pointing toward "
            f"and what you're actually doing."
        ),
    }

    # Expression
    out["expression"] = {
        "title": f"Expression {expr}",
        "subtitle": "Expression",
        "body": (
            f"Your Expression number is calculated from every letter of your full birth name — "
            f"the sum of who you were named to be. Expression {expr} is not something you develop. "
            f"It is something you already are, and have always been — the natural gifts and voice that others have "
            f"consistently encountered in you before you had language to describe them. "
            f"Where Life Path {lp} ({lp_arch}) is the road you walk, Expression {expr} is your stride — "
            f"the distinctive, recognizable quality of how you move through experience. "
            f"Your Soul Urge {soul} is the reason you keep walking. "
            f"The work is not to become this. The work is to stop apologizing for it — "
            f"to recognize your Expression running in real time and let it operate without editing it down "
            f"to fit what the room thinks you should be."
        ),
    }

    # Sun Sign
    if sun:
        out["sun_sign"] = {
            "title": f"{sun} Sun",
            "subtitle": f"{sun_arch} — {sun_theme}" if sun_arch else "The conscious identity archetype",
            "body": (
                f"Your {sun} Sun is not a personality label. It is the conscious identity archetype "
                f"you grow into — the version of yourself that becomes more fully expressed with each decade. "
                f"{sun_theme.capitalize() if sun_theme else 'Your solar identity'} "
                f"defines the creative register of your public self. "
                f"Your {moon} Moon is the emotional body underneath it — the layer that activates "
                f"before your {sun} Sun has had a chance to vote. "
                f"Sun is who you're becoming; Moon is what you're feeling while you do it. "
                f"Your {asc} Ascendant is how all of it arrives in the world — "
                f"the energy people encounter first, before they know your name or have heard you speak. "
                f"The {lunar_phase or 'lunar phase'} at your birth set the underlying relationship between Sun and Moon — "
                f"the specific tension or harmony between your conscious direction and your emotional body "
                f"that colors the lived texture of every day. "
                f"That texture was not random. It was present at the first breath."
            ),
        }

    # Moon Sign
    if moon:
        out["moon_sign"] = {
            "title": f"{moon} Moon",
            "subtitle": "The emotional architecture — the layer that activates before you decide anything",
            "body": (
                f"Your {moon} Moon is the emotional body — the layer of you that responds before the mind "
                f"has had a chance to decide. A {moon} Moon {moon_emotional}. "
                f"This is not a character flaw. This is not a strength. "
                f"It is the texture of your interior weather — the automatic register that has been running "
                f"since birth, whether it was ever named or not. "
                f"People who know you well have felt it, even when they couldn't describe it precisely. "
                f"Your {sun} Sun is the identity you're building toward. "
                f"Your {moon} Moon is the emotional soil that identity is growing out of. "
                f"You cannot resolve the Moon. You cannot override it. "
                f"But you can learn to recognize its patterns fast enough to choose your response "
                f"rather than simply enact it. "
                f"That speed of recognition is the difference between the Moon running you "
                f"and you running the Moon."
            ),
        }

    # Ascendant
    if asc:
        out["ascendant"] = {
            "title": f"{asc} Rising",
            "subtitle": "The threshold through which all experience arrives",
            "body": (
                f"Your {asc} Ascendant is the mask the soul chose for this incarnation — "
                f"not a performance, but the genuine first layer of how you interface with experience itself. "
                f"A {asc} Ascendant {asc_theme}. "
                f"This is what people feel before they know your history, "
                f"before you've established context, before you've said a single word. "
                f"Your chart ruler — {chart_ruler} — is the planetary governor of your entire birth map. "
                f"Its placement, its sign, its aspects color everything the chart describes "
                f"about how life flows through you. "
                f"When life feels like it's moving — when things open and synchronize — {chart_ruler} is in play. "
                f"When things feel blocked, that planet's condition in the chart is almost always part of the answer. "
                f"The Ascendant is not just a first impression. "
                f"It is the threshold through which all experience arrives."
            ),
        }

    # HD Type
    if hd_type:
        out["hd_type"] = {
            "title": hd_type,
            "subtitle": f"Strategy: {strategy}",
            "body": (
                f"As a {hd_type}, your gift is {_TYPE_GIFTS.get(hd_type, 'a unique energetic intelligence')}. "
                f"This is not a category. It is a body-type — a specific architecture of how energy moves through you, "
                f"how you interact with the field around you, and how you were designed to operate correctly. "
                f"Your strategy — {strategy} — is the mechanism. Not a rule to follow consciously. "
                f"A rhythm that, when honored, removes resistance from the path. "
                f"When bypassed, the friction is unmistakable and consistent. "
                f"Your signature is {signature}: the feeling that confirms you're in alignment. "
                f"Your not-self is {not_self}: the signal that you've drifted. "
                f"Profile {profile} ({profile_label}) is the archetype your soul chose for this incarnation — "
                f"the specific way you learn, engage, and fulfill your role. "
                f"Strategy, Authority, Definition, Profile — four coordinates. One design. "
                f"Not a belief system. An energetic blueprint."
            ),
        }

    # Authority
    if authority:
        auth_key = authority.split(" (")[0] if "(" in authority else authority
        auth_body = _AUTH_DESCRIPTIONS.get(auth_key, f"the {authority} signal — your body knows before your mind constructs a reason")
        out["authority"] = {
            "title": authority,
            "subtitle": "The body signal that knows before the mind finishes the sentence",
            "body": (
                f"Your {authority} Authority is {auth_body}. "
                f"This is not abstract. It is the specific, somatic mechanism built into your body "
                f"to make decisions that are actually correct for your design — "
                f"not correct in theory, correct in practice. "
                f"As a {hd_type}, this is the tool your architecture provides. "
                f"The mind makes excellent after-the-fact justifications. "
                f"It will always give you a reason. It will always construct logic. "
                f"But the logic arrives after the Authority has already signaled. "
                f"Every major decision made through your {auth_key} Authority tends toward your signature: {signature}. "
                f"Every decision made over it — through social pressure, urgency, or pure intellect — "
                f"tends toward your not-self: {not_self}. "
                f"Learning to hear the Authority before the mind starts arguing is the whole practice."
            ),
        }

    # Profile
    if profile:
        lines = profile.split("/") if "/" in profile else []
        out["profile"] = {
            "title": f"Profile {profile}",
            "subtitle": profile_label or "The archetype the soul chose for this lifetime",
            "body": (
                f"Profile {profile} — {profile_label} — is not a personality description. "
                f"It is the specific archetype, learning strategy, and social role "
                f"through which you were designed to move through the world. "
                + (
                    f"Line {lines[0]} is your conscious profile — the face you know and show. "
                    f"Line {lines[1]} is your unconscious design — the role others consistently see in you "
                    f"that you may not fully recognize in yourself. "
                    f"The gap between those two is where much of the interesting friction in your life lives. "
                    if len(lines) == 2 else ""
                ) +
                f"As a {hd_type} with Profile {profile}, the way your type operates and the way your profile "
                f"engages with others are not separate — they compound each other. "
                f"Your numerological Life Path {lp} ({lp_arch}) and your Human Design Profile {profile} "
                f"are two independent methodologies describing the same soul in motion: "
                f"one found it through numbers, one through the bodygraph. They arrived at the same place."
            ),
        }

    # Life's Work
    if lw_gate:
        out["lifes_work"] = {
            "title": f"Life's Work: Gate {lw_gate}",
            "subtitle": lw_name,
            "body": (
                f"Gate {lw_gate} — {lw_name} — is the Gene Key of your Life's Work: "
                f"the outward purpose your design is encoded to express. "
                f"It occupies your Personality Sun — the single most visible, most conscious position "
                f"in the entire bodygraph. You broadcast this frequency whether or not you're aware of it. "
                f"People have felt it in you long before it was ever named. "
                f"The shadow you'll wrestle with: {lw_shadow}. "
                f"This is the low-frequency expression of the same energy — "
                f"what Gate {lw_gate} looks like when the Gift isn't flowing. "
                f"It is not the enemy. It is the doorway. "
                f"The gift that emerges when the shadow is no longer running the show: {lw_gift}. "
                f"The siddhi — the highest possible expression — is {lw_siddhi}. "
                f"Life Path {lp} ({lp_arch}) and Life's Work Gate {lw_gate} ({lw_gift}) "
                f"are two independent systems pointing at the same frequency your birth moment was encoded to transmit. "
                f"One found it through numbers. The other through the neutrino field at the moment you were born. "
                f"They arrived at the same place."
            ),
        }

    # Soul Urge
    if soul:
        out["soul_urge"] = {
            "title": f"Soul Urge {soul}",
            "subtitle": "Soul Urge",
            "body": (
                f"Your Soul Urge is calculated from the vowels of your full birth name — "
                f"the breath in the letters, the sound underneath the consonant structure. "
                f"Soul Urge {soul} is the interior engine: the deep need that shapes your choices "
                f"before logic has a say, before strategy is deployed, before you've had a moment to consider. "
                f"Life Path {lp} ({lp_arch}) is the road. Expression {expr} is your stride. "
                f"Soul Urge {soul} is why you keep walking — the hunger that makes this path feel like a calling "
                f"rather than a decision you made. "
                f"This number rarely surfaces publicly. It lives in what you need most from the people closest to you, "
                f"what work genuinely sustains you versus what exhausts you regardless of the outcome, "
                f"and what feels hollow when it's consistently absent from your life. "
                f"When Expression ({expr}) and Soul Urge ({soul}) are running simultaneously — "
                f"when you're broadcasting your gifts while feeding your inner drive — "
                f"effort transforms into something closer to devotion. "
                f"When they diverge, the result is accomplishment without fulfillment. "
                f"You can do everything right on the outside and feel it empty on the inside. "
                f"The Soul Urge is the compass. Not which option looks best — which path feeds the deeper hunger."
            ),
        }

    # Gene Keys: Evolution (second activation sphere)
    act_seq_gk = gk.get("activation_sequence", []) if isinstance(gk, dict) else []
    if len(act_seq_gk) > 1:
        evo_ent = act_seq_gk[1]
        evo_gate = evo_ent.get("gate", 0)
        evo_info = GENE_KEYS.get(evo_gate, ("", "", "", ""))
        evo_name_h, evo_shadow_h, evo_gift_h, _ = evo_info
        if evo_gate:
            out["gk_evolution"] = {
                "title": f"Evolution: Gate {evo_gate}",
                "subtitle": f"{evo_name_h} — what life keeps returning you to",
                "body": (
                    f"Gate {evo_gate} — {evo_name_h} — is the Evolution sphere: "
                    f"the inner teaching that life returns you to, the refinement running beneath every major chapter "
                    f"whether you're consciously participating in it or not. "
                    f"Where Life's Work (Gate {lw_gate}) is what you do in the world, "
                    f"Evolution is what the world does to you — the specific pattern that life keeps placing in your path. "
                    f"The shadow here: {evo_shadow_h}. "
                    f"When this pattern is operating, the cycles repeat — subtly or dramatically — "
                    f"until there is genuine engagement rather than reaction or avoidance. "
                    f"The gift that emerges through that honest engagement: {evo_gift_h}. "
                    f"Life's Work and Evolution are not separate frequencies. "
                    f"They're the same energy at two different depths. "
                    f"What you're learning inside (Gate {evo_gate}) shapes how your purpose expresses outwardly (Gate {lw_gate}). "
                    f"The outer and inner move together. They always have."
                ),
            }

    # Vedic: Moon Nakshatra
    moon_rashi_v = ved.get("moon_rashi", "") if isinstance(ved, dict) else ""
    moon_nak_v = ved.get("moon_nakshatra", "") if isinstance(ved, dict) else ""
    moon_nak_lord_v = ved.get("moon_nakshatra_lord", "") if isinstance(ved, dict) else ""
    if moon_nak_v:
        _N_GIFT: dict[str, str] = {
            "Ashwini": "healing instincts and swift pioneering energy",
            "Bharani": "creative force and the capacity to hold and transform",
            "Krittika": "purifying intensity and fearless truth-telling",
            "Rohini": "sensual richness, creative fertility, and magnetic presence",
            "Mrigashira": "perpetual curiosity and refined aesthetic sense",
            "Ardra": "storm-weathering strength and transformative intelligence",
            "Punarvasu": "renewal, optimism, and restoring what has been lost",
            "Pushya": "nurturing wisdom and the gift of sustaining others",
            "Ashlesha": "penetrating insight and the ability to see beneath surfaces",
            "Magha": "ancestral authority and command that others follow naturally",
            "Purva Phalguni": "creative joy and the gift of bringing delight",
            "Uttara Phalguni": "steadfast service and executive capability",
            "Hasta": "craftsmanship, healing hands, and practical intelligence",
            "Chitra": "architectural brilliance and the eye that sees design in everything",
            "Swati": "independent spirit and the ability to bend without breaking",
            "Vishakha": "focused purpose and harvest at the end of long effort",
            "Anuradha": "devotion and loyalty that outlasts difficulty",
            "Jyeshtha": "elder wisdom and leadership earned through ordeal",
            "Mula": "root-level truth-seeking and metaphysical intelligence",
            "Purva Ashadha": "invincible spirit and confidence that cannot be shaken",
            "Uttara Ashadha": "ultimate victory through right action",
            "Shravana": "listening intelligence and the gift of transmitting wisdom",
            "Dhanishta": "rhythmic power and the ability to prosper through community",
            "Shatabhisha": "healing at the deepest level and the medicine of truth",
            "Purva Bhadrapada": "fierce idealism and the purification of what no longer serves",
            "Uttara Bhadrapada": "depth of compassion and patient mastery",
            "Revati": "spiritual completion and the wisdom of the journey's end",
        }
        nak_gift_v = _N_GIFT.get(moon_nak_v, "a unique lunar intelligence")
        moon_rashi_sk_v = moon_rashi_v.split("(")[0].strip() if moon_rashi_v else ""
        out["vedic_moon_nak"] = {
            "title": f"{moon_nak_v} Nakshatra",
            "subtitle": f"Moon in {moon_rashi_sk_v} · Ruled by {moon_nak_lord_v}",
            "body": (
                f"{moon_nak_v} is one of the 27 lunar mansions — 13.3° arcs of sky that give Vedic astrology "
                f"far more precision than the zodiac sign alone. "
                f"Moon placed in {moon_nak_v} means your emotional intelligence carries the specific quality of: {nak_gift_v}. "
                f"People who have known you well have felt this in you, whether or not they ever had language for it. "
                f"The ruling planet of this nakshatra is {moon_nak_lord_v} — "
                f"whose frequency colors how this lunar quality expresses and what activates or disturbs it. "
                f"In Jyotish, the Moon governs manas — the thinking-feeling layer that processes all experience "
                f"before the conscious self has a chance to respond. "
                f"This is why Vedic astrology gives more weight to the Moon than the Sun. "
                f"Your Moon sign ({moon_rashi_sk_v}) describes the broad register; "
                f"{moon_nak_v} is the specific frequency inside that sign — "
                f"the quality of your inner weather at the finest resolution available. "
                f"And the entire Vimshottari Dasha timeline — the 120-year map of your life's unfolding — "
                f"is calculated from this exact point. Everything that follows in time derives from here."
            ),
        }

    # Vedic: Rahu/Ketu axis
    rahu_rashi_v = ved.get("rashis", {}).get("Rahu", "") if isinstance(ved, dict) else ""
    ketu_rashi_v = ved.get("rashis", {}).get("Ketu", "") if isinstance(ved, dict) else ""
    if rahu_rashi_v:
        rahu_sk_v = rahu_rashi_v.split("(")[0].strip()
        ketu_sk_v = ketu_rashi_v.split("(")[0].strip() if ketu_rashi_v else ""
        _R_H: dict[str, str] = {
            "Mesha (Aries)": "independence, self-authorship, and the courage to initiate without waiting for permission",
            "Vrishabha (Taurus)": "material stability, sensual grounding, and the slow-earned security of building something real",
            "Mithuna (Gemini)": "information, communication, and the versatility to navigate multiple worlds at once",
            "Karka (Cancer)": "belonging, deep emotional connection, and a sense of home that feels genuinely yours",
            "Simha (Leo)": "recognition, creative authorship, and the confidence to be seen fully without apology",
            "Kanya (Virgo)": "mastery, precision, and the quiet satisfaction of service that actually works",
            "Tula (Libra)": "partnership, aesthetic harmony, and the art of genuine relational exchange",
            "Vrishchika (Scorpio)": "depth, transformation, and the territory of hidden truth that most people won't enter",
            "Dhanu (Sagittarius)": "meaning, philosophical expansion, and the horizon that keeps receding just as you reach it",
            "Makara (Capricorn)": "earned authority, structural mastery, and the long-game achievement that outlasts trends",
            "Kumbha (Aquarius)": "originality, collective vision, and the freedom to exist entirely outside conventional frameworks",
            "Meena (Pisces)": "transcendence, mystical experience, and the dissolution of the boundary between self and everything",
        }
        _K_H: dict[str, str] = {
            "Mesha (Aries)": "initiating, asserting, and acting independently — native, effortless fluency you can draw on without effort",
            "Vrishabha (Taurus)": "building, accumulating, and creating material stability — deeply natural and available",
            "Mithuna (Gemini)": "gathering information, adapting your register, networking across contexts — built-in versatility",
            "Karka (Cancer)": "nurturing, protecting, and creating emotional safety for others — entirely second nature",
            "Simha (Leo)": "leading, performing, and holding center through presence and personality — effortless",
            "Kanya (Virgo)": "analyzing, organizing, and solving practical problems with precision — a natural master",
            "Tula (Libra)": "mediating, harmonizing, and maintaining relational balance — second nature",
            "Vrishchika (Scorpio)": "investigating, transforming, and navigating intensity and power — deeply familiar territory",
            "Dhanu (Sagittarius)": "philosophizing, teaching, seeking meaning — naturally expansive and available",
            "Makara (Capricorn)": "building structure, maintaining discipline, carrying institutional responsibility — built in",
            "Kumbha (Aquarius)": "holding community, thinking systemically, operating outside conventional norms — entirely fluent",
            "Meena (Pisces)": "dissolving, surrendering, and attuning to invisible currents — a native frequency",
        }
        rahu_hunger_v = _R_H.get(rahu_rashi_v, "an unfamiliar but irresistible direction")
        ketu_fluency_v = _K_H.get(ketu_rashi_v, "accumulated past-life mastery that arrives without effort")
        out["vedic_rahu"] = {
            "title": f"Rahu in {rahu_sk_v}",
            "subtitle": f"Ketu in {ketu_sk_v} · The soul's karmic axis",
            "body": (
                f"Rahu and Ketu are always exactly opposite each other, forming the soul's karmic axis across lifetimes. "
                f"They are not planets but points — where the Moon's orbit crosses the ecliptic — "
                f"and they describe what the soul carried in (Ketu) and where it is genuinely growing (Rahu). "
                f"Ketu in {ketu_sk_v} is the past-life mastery: {ketu_fluency_v}. "
                f"This fluency is real and available — but its shadow is comfort becoming a substitute for growth. "
                f"What is already mastered feels safe in a way that genuinely new territory never does. "
                f"Rahu in {rahu_sk_v} is the hunger this lifetime — "
                f"the pull toward: {rahu_hunger_v}. "
                f"The discomfort Rahu brings is not a warning sign. It is the precise feeling of growth itself. "
                f"You are not drawing on prior-life fluency here. You are building new capacity from the ground up. "
                f"This is why Rahu always feels slightly foreign: you are supposed to be an outsider to this territory at first. "
                f"The soul chose this axis deliberately. "
                f"Leaning into Rahu — even when it feels unfamiliar, even when Ketu's ease calls you back — "
                f"is the path this incarnation was designed to walk."
            ),
        }

    return out


# ---- Section summary generator ----

def _derive_voice(comm: dict) -> dict:
    """Read the communication profile and extract voice parameters for adaptive summaries.

    Before writing a single word of section analysis, we assess how this person
    actually receives information — their processing style, elemental format
    preference, and cognitive wiring — then speak through their native channel.
    """
    delivery = comm.get("delivery", {}) or {}
    fmt = delivery.get("format", "").lower()
    proc = (comm.get("processing_style", "") or "").lower()

    if any(w in fmt for w in ("fire", "story", "inspir", "vision", "narrative")):
        style = "fire"
    elif any(w in fmt for w in ("earth", "practical", "step", "tangible", "concrete")):
        style = "earth"
    elif any(w in fmt for w in ("water", "metaphor", "emotion", "feeling", "resonan")):
        style = "water"
    elif any(w in proc for w in ("intuitive", "holistic", "feeling", "emotional")):
        style = "water"
    else:
        style = "air"  # frameworks / concepts / systems thinking

    return {"style": style, "arch": comm.get("archetype", "")}


# Per-style sentence hooks injected at the top of each paragraph and the end
# of every synthesis — this is the adaptive voice layer that makes each summary
# feel like it was written specifically for the way this person processes information.
_LIGHT_OPENERS = {
    "fire":  "The signal is unmistakable — ",
    "earth": "In concrete terms — ",
    "air":   "The architecture of it — ",
    "water": "The current running through all of this — ",
}
_SHADOW_OPENERS = {
    "fire":  "The shadow is not the problem. It is the same energy at a lower frequency. ",
    "earth": "The pattern to recognize in real situations — ",
    "air":   "Where the architecture breaks down — ",
    "water": "The undertow — ",
}
_SYNTH_OPENERS = {
    "fire":  "The through-line — ",
    "earth": "What this means in practice — ",
    "air":   "The convergence — ",
    "water": "The current beneath all of it — ",
}
_SYNTH_CLOSERS = {
    "fire":  " You were encoded with this on purpose.",
    "earth": " This is yours. Build with it.",
    "air":   " The design is complete. Every piece is accounted for.",
    "water": " Let this land. You already know it's true.",
}
_GRAND_OPENERS = {
    "fire":  "Four independent systems. One undeniable frequency — ",
    "earth": "Four independent calculations from the same birth data — each arriving at the same conclusion — ",
    "air":   "Four methodologies, each calculated independently, resolving to a single coherent profile — ",
    "water": "Four traditions looked at your birth moment and felt the same thing — ",
}
_GRAND_CLOSERS = {
    "fire":  " The frequency is unmistakable. You were designed for this.",
    "earth": " Four systems. One birth moment. The evidence is solid.",
    "air":   " Four independent methodologies. One coherent design. The logic is closed.",
    "water": " Four different traditions. The same truth, each time. Trust what resonates.",
}


def _section_summaries(report: BlueprintReport) -> dict:  # noqa: C901
    """Deterministic 3-paragraph (light/shadow/synthesis) analysis for each tab.

    Voice is determined FIRST by reading the person's communication profile —
    their processing style, delivery format, and cognitive wiring — then every
    summary is written in the voice that reaches them specifically.
    """
    num = report.numerology
    west = report.western
    ved = report.vedic
    hd = report.human_design
    gk = report.gene_keys
    comm = report.communication or {}

    voice = _derive_voice(comm)
    vs = voice["style"]

    lp = num["life_path"]
    expr = num["expression"]
    soul = num["soul_urge"]
    maturity = num["maturity"]
    py = num["personal_year"]
    karmic_debts = num["karmic_debts"]
    karmic_lessons = num["karmic_lessons"]
    subcon = num["subconscious_self"]
    challenges = num["challenges"]
    lp_arch = LP_ARCHETYPES.get(lp, "unique frequency")

    _PY = {
        1: "new beginnings — seeds planted now carry a nine-year arc",
        2: "partnership, patience, and relational deepening",
        3: "creative expression and social expansion",
        4: "discipline, foundation-building, and structured effort",
        5: "change, freedom, and unexpected breakthroughs",
        6: "responsibility, home, and alignment of work with values",
        7: "introspection, spiritual deepening, and inner knowing",
        8: "power, ambition, and material manifestation",
        9: "completion, release, and clearing space for the next cycle",
        11: "heightened intuition and visionary sensitivity",
        22: "master-builder energy — turning elevated vision into structure",
        33: "service, healing, and elevating those around you",
    }
    py_meaning = _PY.get(py, "deep reflection and integration")
    debt_str = (
        f"Karmic debts {', '.join(str(d) for d in karmic_debts)} surface as recurring patterns demanding conscious reckoning before they release."
        if karmic_debts else
        "No karmic debt numbers appear in your chains — the core path carries no inherited ancestral obligations."
    )
    lesson_str = (
        f"Karmic lessons {', '.join(str(l) for l in karmic_lessons)} — the digits absent from your name — are not weaknesses but uncultivated territories requiring deliberate development."
        if karmic_lessons else
        "All nine digits appear in your name — no karmic lesson gaps exist."
    )
    ch = challenges
    ch_str = f"{ch[0]}, {ch[1]}, {ch[2]}, {ch[3]}" if len(ch) >= 4 else str(ch)

    num_summ = {
        "light": (
            f"{_LIGHT_OPENERS[vs]}"
            f"Life Path {lp} — {lp_arch} — is the recurring theme connecting every major chapter of your life, "
            f"whether you recognized it as such or not. "
            f"Expression {expr} is the voice and gift others have always encountered in you — "
            f"before you consciously developed it, before you had a name for it. "
            f"If people have consistently come to you for a particular kind of help or energy, that's your {expr} operating. "
            f"Soul Urge {soul} is the engine underneath all of it — "
            f"the interior pull that makes you choose what you choose even when you can't explain the logic. "
            f"These three are not arbitrary calculations. They are the numerological frequency of your birth moment."
        ),
        "shadow": (
            f"{_SHADOW_OPENERS[vs]}"
            f"{debt_str} "
            f"{lesson_str} "
            f"Your challenge numbers — {ch_str} — are the recurring friction at each major life threshold. "
            f"Not failures. Not evidence that something is wrong with you. "
            f"The exact pressures that forge the character your Life Path requires to operate at full voltage."
        ),
        "synthesis": (
            f"{_SYNTH_OPENERS[vs]}"
            f"Life Path {lp} and Expression {expr} are two rails of the same track — "
            f"when they're aligned, effort turns into something closer to devotion; "
            f"where they diverge is precisely where the growth lives. "
            f"You're currently in Personal Year {py}: a cycle of {py_meaning}. "
            f"Everything happening right now makes more sense through that lens. "
            f"Subconscious Self {subcon} means those frequencies are already your bedrock — "
            f"integrated and available without effort. "
            f"Life Purpose ({lp}), Natural Expression ({expr}), Inner Drive ({soul}), Present Timing (Year {py}) — "
            f"four coordinates of one coherent design."
            f"{_SYNTH_CLOSERS[vs]}"
        ),
    }

    # --- Western ---
    sun = west.get("sun_sign", "")
    moon = west.get("moon_sign", "")
    asc = west.get("ascendant", "")
    chart_ruler = west.get("chart_ruler", "")
    retrogrades = west.get("dominant_retrogrades", [])
    elem_bal = west.get("element_balance", {})
    mod_bal = west.get("modality_balance", {})
    lunar_phase = west.get("lunar_phase_name", "")
    dom_elem = max(elem_bal, key=elem_bal.get) if elem_bal else ""
    dom_mod = max(mod_bal, key=mod_bal.get) if mod_bal else ""
    _ELEM_GIFT = {
        "Fire": "initiative, inspiration, and the courage to act before the path is fully clear",
        "Earth": "pragmatism, endurance, and the ability to build things that last",
        "Air": "intellectual versatility, communication, and connecting disparate ideas",
        "Water": "emotional depth, intuition, and profound empathy and healing",
    }
    _ELEM_SHADOW = {
        "Fire": "impulsivity, burnout from leading without replenishing, and difficulty sitting with discomfort",
        "Earth": "rigidity, resistance to change, and hoarding energy out of fear",
        "Air": "overthinking, emotional detachment, and scattering focus across too many directions",
        "Water": "absorbing others' emotional states, boundary erosion, and conflating intuition with anxiety",
    }
    retro_str = (
        f"Retrograde planets — {', '.join(retrogrades)} — internalize those energies: their work happens in depth and in private before becoming visible."
        if retrogrades else
        "No dominant retrograde planets — all planetary energies flow outwardly and expressively."
    )
    west_summ = {
        "light": (
            f"{_LIGHT_OPENERS[vs]}"
            f"Your {sun} Sun is the conscious identity archetype you grow into more fully with each decade. "
            f"Your {asc} Ascendant is what the world encounters before you've said a word — "
            f"the instinctive first impression of your energy, felt before any opinion has formed. "
            f"A {dom_elem}-dominant chart means your natural gifts include {_ELEM_GIFT.get(dom_elem, 'a balanced elemental field')}. "
            f"Your {dom_mod} modality shapes the rhythm of everything: "
            f"how you initiate, how you sustain, when you were built to rest."
        ),
        "shadow": (
            f"{_SHADOW_OPENERS[vs]}"
            f"Your {moon} Moon is the emotional body that activates before your {sun} Sun gets a vote — "
            f"the layer that runs automatically under stress, before choice has entered the room. "
            f"The shadow is not the sign itself. It is what that sign does when it is operating on autopilot. "
            f"{retro_str} "
            f"The shadow side of a {dom_elem}-dominant chart: {_ELEM_SHADOW.get(dom_elem, 'the unexamined elemental tendency')}. "
            f"Naming it clearly takes most of its power away."
        ),
        "synthesis": (
            f"{_SYNTH_OPENERS[vs]}"
            f"Sun ({sun}), Moon ({moon}), Ascendant ({asc}) — who you're becoming, what you're feeling while you do it, how you arrive. "
            f"Your chart ruler — {chart_ruler} — governs the entire birth map. "
            f"Its placement and condition color everything else the chart describes. "
            f"The {lunar_phase} at your birth set the underlying relationship between your Sun's direction and your Moon's need — "
            f"the harmony or friction between those two is the lived texture of every ordinary day. "
            f"The goal is not to resolve the tension. It is to run all three consciously, in concert."
            f"{_SYNTH_CLOSERS[vs]}"
        ),
    }

    # --- Vedic ---
    moon_rashi = ved.get("moon_rashi", "")
    moon_nak = ved.get("moon_nakshatra", "")
    moon_nak_lord = ved.get("moon_nakshatra_lord", "")
    lagna_str = ved.get("lagna", "")
    lagna_lord = ved.get("lagna_lord", "")
    mahadasha = ved.get("starting_mahadasha", "")
    atmakaraka = ved.get("charakarakas", {}).get("Atmakaraka", "")
    lagna_sk = lagna_str.split("(")[0].strip()
    rashis_dict = ved.get("rashis", {})
    rahu_rashi = rashis_dict.get("Rahu", "")
    ketu_rashi = rashis_dict.get("Ketu", "")
    _NAK_GIFTS = {
        "Ashwini": "healing instincts and swift pioneering energy",
        "Bharani": "creative force and the capacity to hold and transform",
        "Krittika": "purifying intensity and fearless truth-telling",
        "Rohini": "sensual richness, creative fertility, and magnetic presence",
        "Mrigashira": "perpetual curiosity and refined aesthetic sense",
        "Ardra": "storm-weathering strength and transformative intelligence",
        "Punarvasu": "renewal, optimism, and restoring what has been lost",
        "Pushya": "nurturing wisdom and the gift of sustaining others",
        "Ashlesha": "penetrating insight and the ability to see beneath surfaces",
        "Magha": "ancestral authority and command that others follow naturally",
        "Purva Phalguni": "creative joy and the gift of bringing delight",
        "Uttara Phalguni": "steadfast service and executive capability",
        "Hasta": "craftsmanship, healing hands, and practical intelligence",
        "Chitra": "architectural brilliance and the eye that sees design in everything",
        "Swati": "independent spirit and the ability to bend without breaking",
        "Vishakha": "focused purpose and harvest at the end of long effort",
        "Anuradha": "devotion and loyalty that outlasts difficulty",
        "Jyeshtha": "elder wisdom and leadership earned through ordeal",
        "Mula": "root-level truth-seeking and metaphysical intelligence",
        "Purva Ashadha": "invincible spirit and confidence that cannot be shaken",
        "Uttara Ashadha": "ultimate victory through right action and enduring achievement",
        "Shravana": "listening intelligence and the gift of transmitting wisdom",
        "Dhanishta": "rhythmic power and the ability to prosper through community",
        "Shatabhisha": "healing at the deepest level and the medicine of truth",
        "Purva Bhadrapada": "fierce idealism and the purification of what no longer serves",
        "Uttara Bhadrapada": "depth of compassion and patient mastery",
        "Revati": "spiritual completion and the wisdom of the journey's end",
    }
    _RAHU_HUNGER = {
        "Mesha (Aries)": "independence, self-authorship, and the courage to initiate without waiting for permission",
        "Vrishabha (Taurus)": "material stability, sensual grounding, and the slow-earned security of building something real",
        "Mithuna (Gemini)": "information, communication, and the versatility to navigate multiple worlds at once",
        "Karka (Cancer)": "belonging, deep emotional connection, and a sense of home that feels genuinely yours",
        "Simha (Leo)": "recognition, creative authorship, and the confidence to be seen fully without apology",
        "Kanya (Virgo)": "mastery, precision, and the quiet satisfaction of service that actually works",
        "Tula (Libra)": "partnership, aesthetic harmony, and the art of genuine relational exchange",
        "Vrishchika (Scorpio)": "depth, transformation, and the territory of hidden truth that most people won't enter",
        "Dhanu (Sagittarius)": "meaning, philosophical expansion, and the horizon that keeps receding just as you reach it",
        "Makara (Capricorn)": "earned authority, structural mastery, and the long-game achievement that outlasts trends",
        "Kumbha (Aquarius)": "originality, collective vision, and the freedom to exist entirely outside conventional frameworks",
        "Meena (Pisces)": "transcendence, mystical experience, and the dissolution of the boundary between self and everything",
    }
    _KETU_FLUENCY = {
        "Mesha (Aries)": "initiating, asserting, and acting independently without needing consensus — you can lead and compete effortlessly. The shadow pull: defaulting to the pioneer role when life is asking you to share the steering wheel",
        "Vrishabha (Taurus)": "building, accumulating, and creating material stability — deeply native. The shadow pull: staying inside security and sameness when growth requires moving through unfamiliar ground",
        "Mithuna (Gemini)": "gathering information, adapting your register, and networking across contexts — built-in versatility. The shadow pull: perpetual information-gathering that substitutes for depth and commitment",
        "Karka (Cancer)": "nurturing, protecting, and creating emotional safety for others — entirely natural. The shadow pull: over-prioritizing others' comfort at the expense of your own trajectory",
        "Simha (Leo)": "leading, performing, and holding center through presence and personality — effortless. The shadow pull: staying in the spotlight when deeper integration requires stepping back and going inward",
        "Kanya (Virgo)": "analyzing, organizing, and solving practical problems with precision — a master. The shadow pull: endless refinement of what already exists instead of launching what doesn't yet",
        "Tula (Libra)": "mediating, harmonizing, and maintaining relational balance — second nature. The shadow pull: keeping the peace at the cost of your own individuation and truth",
        "Vrishchika (Scorpio)": "investigating, transforming, and navigating power and intensity — deeply familiar territory. The shadow pull: staying in crisis-mode and depth-diving when calm and integration are what's actually needed",
        "Dhanu (Sagittarius)": "philosophizing, teaching, and seeking higher meaning — naturally expansive. The shadow pull: living in the world of belief and possibility rather than grounding any of it into reality",
        "Makara (Capricorn)": "building institutions, maintaining discipline, and carrying structural responsibility — built in. The shadow pull: measuring worth through achievement and status when inner development is the actual curriculum",
        "Kumbha (Aquarius)": "holding community, thinking systemically, and operating outside norms — entirely fluent. The shadow pull: over-investing in collective causes while the personal and intimate go unmet",
        "Meena (Pisces)": "dissolving into experience, surrendering, and attuning to invisible currents — a native frequency. The shadow pull: escapism, spiritual bypassing, and losing the self in what isn't yours",
    }
    _MAHADASHA_THEMES = {
        "Ketu": "spirituality, detachment, and completion of past-life patterns — a period for releasing what has been carried long enough and doesn't belong to this chapter",
        "Venus": "relationships, creative expression, and material pleasure — the themes of love, beauty, and value move to the foreground of daily life",
        "Sun": "identity, authority, and visibility — questions of who you are and what legacy you're building become the dominant frequency",
        "Moon": "emotional patterns, inner world, and the need for home — interior life, instincts, and what you need to feel genuinely safe",
        "Mars": "action, courage, boundary-setting, and competitive drive — the will activates and the capacity to fight for what actually matters sharpens",
        "Rahu": "ambition, disruption, and rapid expansion into unfamiliar territory — acceleration that is simultaneously exhilarating and destabilizing",
        "Jupiter": "growth, wisdom, teaching, and expansion of belief — abundance and philosophical maturation, legacy themes, and the harvest of prior effort",
        "Saturn": "discipline, karmic reckoning, and the long game bearing fruit — integrity and sustained effort become their own reward; shortcuts reveal their costs",
        "Mercury": "communication, commerce, intellect, and mastery of information exchange — mental sharpness and relational intelligence come to the fore",
    }
    nak_gift = _NAK_GIFTS.get(moon_nak, "unique lunar intelligence")
    moon_rashi_sk = moon_rashi.split("(")[0].strip()
    _ketu_text = _KETU_FLUENCY.get(ketu_rashi, "what comes most easily can quietly become the default escape from growth")
    _ketu_sentence = (_ketu_text[:1].upper() + _ketu_text[1:]).rstrip(".") + "."
    ved_summ = {
        "light": (
            f"{_LIGHT_OPENERS[vs]}"
            f"The Vedic chart opens with your Moon — not your Sun — because in Jyotish, the emotional body is the root, not the crown. "
            f"Moon in {moon_rashi} is the texture of your interior world: how situations land before you've had time to think about them, "
            f"what restores you, what the body does automatically under pressure. "
            f"The {moon_nak} nakshatra — ruled by {moon_nak_lord} — is the specific quality of that Moon: {nak_gift}. "
            f"This is not abstract cosmology. It is a description of something people have recognized in you since childhood, "
            f"whether it was ever named or not. "
            f"Your {lagna_sk} Lagna is the dharmic vehicle you arrived in — "
            f"how you naturally engage with reality, the energy the world encounters first."
        ),
        "shadow": (
            f"{_SHADOW_OPENERS[vs]}"
            f"Rahu in {rahu_rashi} is the hunger this soul came to integrate — "
            f"the desire that pulls you forward while making you feel like an outsider in it, "
            f"because it is genuinely new territory: {_RAHU_HUNGER.get(rahu_rashi, 'an unfamiliar but irresistible direction')}. "
            f"Ketu in {ketu_rashi} is the fluency you already carry — so native it runs without effort or attention. "
            f"{_ketu_sentence} "
            f"The {mahadasha} Mahadasha running now activates specifically: "
            f"{_MAHADASHA_THEMES.get(mahadasha, 'a distinct chapter of karmic integration')}."
        ),
        "synthesis": (
            f"{_SYNTH_OPENERS[vs]}"
            f"Three coordinates, simultaneously true about the same person. "
            f"Lagna ({lagna_sk}): how you show up and move through the world. "
            f"Moon ({moon_rashi_sk}): what is actually happening inside while you do that. "
            f"Atmakaraka ({atmakaraka}): the planet encoding the soul's deepest lesson — "
            f"what this incarnation is actually about beneath the surface curriculum. "
            f"The Mahadasha sequence is the timeline: the moving window that determines "
            f"which layer of karma rises for integration and when. "
            f"The Vedic chart does not describe your personality. "
            f"It describes your soul's contract — what it chose to navigate, and in what sequence."
            f"{_SYNTH_CLOSERS[vs]}"
        ),
    }

    # --- Human Design ---
    hd_type = hd.get("type", "")
    authority = hd.get("authority", "")
    profile_hd = hd.get("profile", "")
    definition = hd.get("definition", "")
    strategy = hd.get("strategy", "")
    signature = hd.get("signature", "")
    not_self = hd.get("not_self_theme", "")
    defined_centers = hd.get("defined_centers", [])
    open_centers = hd.get("open_centers", [])
    _TYPE_GIFTS = {
        "Generator": "sustainable life-force, the full-body yes of genuine response, and mastery built through joyful engagement",
        "Manifesting Generator": "multi-dimensional speed, the ability to pioneer several lanes at once, and showing others what's possible",
        "Projector": "penetrating insight, the gift of guiding others toward efficiency, and wisdom that arrives through deep observation",
        "Manifestor": "initiatory power, the ability to catalyze new realities without needing permission, and opening doors others walk through",
        "Reflector": "environmental attunement, sampling the full spectrum of human experience, and the wisdom of lunar-cycle timing",
    }
    _OPEN_COND = {
        "Head": "absorbing others' mental pressure and feeling obligated to answer every question that enters awareness",
        "Ajna": "pretending certainty you don't feel, locking into fixed positions to avoid the discomfort of not-knowing",
        "Throat": "speaking to fill silence or initiating to attract attention rather than waiting for genuine invitation",
        "G": "searching for identity in relationships or places rather than resting in the self",
        "Heart": "over-committing to prove worth — making promises driven by ego rather than genuine will",
        "Sacral": "pushing past natural energy limits and ignoring completion signals",
        "Spleen": "holding on to what no longer serves out of fear rather than spontaneous clarity",
        "Solar Plexus": "deciding in emotional reactivity — chasing highs or avoiding lows rather than waiting for the wave to settle",
        "Root": "living in perpetual hurry to escape adrenal pressure — rushing decisions for relief",
    }
    open_cond_parts = [_OPEN_COND.get(c, c) for c in open_centers[:3]]
    open_str = (
        f"Open centers — {', '.join(open_centers)} — are where conditioning enters: {'; '.join(open_cond_parts[:2])}."
        if open_centers else
        "With all centers defined, conditioning points lie in specific channels and gates rather than center architecture."
    )
    defined_str = (
        f"Defined centers — {', '.join(defined_centers)} — provide consistent, reliable energy that others can count on."
        if defined_centers else
        "With no defined centers, your field is entirely responsive and environment-shaped — rare and deeply flexible."
    )
    auth_short = authority.split(" (")[0] if "(" in authority else authority
    hd_summ = {
        "light": (
            f"{_LIGHT_OPENERS[vs]}"
            f"As a {hd_type}, your gift is {_TYPE_GIFTS.get(hd_type, 'unique energetic intelligence')}. "
            f"Your {auth_short} Authority is not a concept — it is a body signal. "
            f"It fires before the mind has time to argue with it. "
            f"That is not a bug. That is the architecture. {defined_str} "
            f"Profile {profile_hd} is the archetype your soul chose — "
            f"the specific way you were designed to engage with people, learn from life, and fulfill your role."
        ),
        "shadow": (
            f"{_SHADOW_OPENERS[vs]}"
            f"When {not_self} arises, you have drifted from your design. That is the whole signal. "
            f"Not a moral failure — a compass reading. "
            f"{open_str} "
            f"Every open center is a place where you amplify and sample what isn't yours. "
            f"The problem is not the openness. The problem is mistaking conditioned input for your own truth. "
            f"The open center shows you the world's range; it is not describing who you are."
        ),
        "synthesis": (
            f"{_SYNTH_OPENERS[vs]}"
            f"Strategy ({strategy}): how you move without resistance. "
            f"{auth_short} Authority: how you make decisions that are actually yours. "
            f"{definition}: how your energy field is built and how it interacts with other fields. "
            f"Profile {profile_hd}: the role your soul came to play. "
            f"Signature ({signature}) — on track. Not-self ({not_self}) — drifted. "
            f"Those four are the complete operating manual. Everything else in Human Design is commentary."
            f"{_SYNTH_CLOSERS[vs]}"
        ),
    }

    # --- Gene Keys ---
    act_seq = gk.get("activation_sequence", [])
    spheres = []
    for s_data in act_seq[:4]:
        gate = s_data.get("gate", 0)
        gk_info = GENE_KEYS.get(gate, ("Unknown", "Unknown", "Unknown", "Unknown"))
        spheres.append({"sphere": s_data.get("sphere", ""), "gate": gate,
                        "name": gk_info[0], "shadow": gk_info[1], "gift": gk_info[2], "siddhi": gk_info[3]})
    if spheres:
        gifts_str = "; ".join(f"{s['sphere']} Gate {s['gate']} — Gift of {s['gift']}" for s in spheres)
        shadows_str = "; ".join(f"{s['sphere']} Gate {s['gate']} — Shadow of {s['shadow']}" for s in spheres)
        siddhis_str = ", ".join(s["siddhi"] for s in spheres)
        lw = spheres[0]
    else:
        gifts_str = "your unique activation sequence gifts"
        shadows_str = "the shadow patterns of your activation gates"
        siddhis_str = "the highest expressions of your sequence"
        lw = {"sphere": "", "gate": 0, "name": "", "shadow": "", "gift": "", "siddhi": ""}
    gk_summ = {
        "light": (
            f"{_LIGHT_OPENERS[vs]}"
            f"The Gene Keys use the same 64-gate structure as Human Design, but as a contemplative system — "
            f"Shadow, Gift, Siddhi: the low, middle, and high frequencies of the same energy. "
            f"Your activation sequence gifts: {gifts_str}. "
            f"The Gift is not something to achieve. It is what naturally emerges when you stop feeding the Shadow. "
            f"Your siddhis — {siddhis_str} — are the ceiling, not the floor. "
            f"Let them be a direction, not a destination."
        ),
        "shadow": (
            f"{_SHADOW_OPENERS[vs]}"
            f"The Gene Keys are direct about this: the Shadow is the doorway. Not the enemy. Not the part to fix. The doorway. "
            f"Repress it and the frequency drops. React to it and you create drama. "
            f"Sit with it — observe it, without judgment — and it begins to transmute on its own. "
            f"Your activation sequence shadows: {shadows_str}. "
            f"The Shadow of your Life's Work — {lw['shadow']} — is the pattern that surfaces when the Gift isn't flowing. "
            f"It is not a character flaw. It is the same energy at a lower bandwidth. The Gift is already in there."
        ),
        "synthesis": (
            f"{_SYNTH_OPENERS[vs]}"
            f"Life's Work (what you are here to do), Evolution (what life is teaching you), "
            f"Radiance (what keeps you vital), Purpose (what grounds you deepest) — "
            f"four spheres, all active simultaneously, all informing each other. "
            f"Your Life's Work Gift — {lw['gift']} — is available right now. "
            f"It lives underneath the Shadow of {lw['shadow']}. "
            f"Contemplation is the mechanism. Not effort. Not willpower. "
            f"Sustained attention to the Shadow, without reacting to it, is sufficient."
            f"{_SYNTH_CLOSERS[vs]}"
        ),
    }

    # --- Communication ---
    comm_arch = comm.get("archetype", "")
    comm_proc = comm.get("processing_style", "")
    comm_delivery = comm.get("delivery", {})
    comm_avoid = comm_delivery.get("avoid", "") if comm_delivery else ""
    comm_fmt = comm_delivery.get("format", "") if comm_delivery else ""
    comm_pacing = comm_delivery.get("pacing", "") if comm_delivery else ""
    comm_strengths = comm.get("strengths", [])
    comm_weaknesses = comm.get("weaknesses", [])
    first_strength = comm_strengths[0]["strength"] if comm_strengths else ""
    first_weakness = comm_weaknesses[0]["weakness"] if comm_weaknesses else ""
    comm_summ = {
        "light": (
            f"{_LIGHT_OPENERS[vs]}"
            f"As {comm_arch}, this is not a communication style preference. "
            f"It is a specific cognitive architecture that determines how information actually reaches you "
            f"and how it comes back out. The processing mode: {comm_proc} "
            f"This is structural, not stylistic. It has been showing up in how you take in and transmit information "
            f"your entire life, whether you named it or not. "
            f"When someone delivers in the format your wiring is built for — "
            f"{comm_fmt.split(' — ')[0] if ' — ' in comm_fmt else comm_fmt} — "
            f"it does not just register. It lands at a completely different depth. "
            f"Your primary cognitive strength is {first_strength}. Already active. Already available right now."
        ),
        "shadow": (
            f"{_SHADOW_OPENERS[vs]}"
            f"The gap between how you communicate in your native mode and how you communicate "
            f"when conditioned out of it is significant — "
            f"and most people spend far more time in the conditioned mode than they realize, "
            f"because it feels normal from the inside. "
            f"The primary pattern to watch: {comm_avoid}. "
            f"That conditioning enters through open centers, amplifies under environmental pressure, "
            f"and can masquerade as genuine self-expression when it is actually adaptive response. "
            f"The underlying vulnerability: {first_weakness}. "
            f"Not a character flaw — a structural feature of this specific combination of centers, profile, and Mercury wiring "
            f"when the environment is running louder than your internal signal."
        ),
        "synthesis": (
            f"Every section of this report was written in the voice your chart describes — "
            f"the pacing, framing, and format calibrated to how {comm_arch} actually receives and integrates information. "
            f"If certain sections landed differently than others, that is the architecture confirming itself in real time. "
            f"The four coordinates of your communication design: archetype ({comm_arch}), processing mode, "
            f"delivery preferences, and the specific conditioning pattern to watch. "
            f"Together they give you a complete map of any exchange: what to lean into, "
            f"what to calibrate for the person in front of you, and what to recognize as environmental noise "
            f"rather than a genuine signal from inside you. "
            f"Test it. Pick a conversation where something didn't land right. "
            f"Run it through these four coordinates. The misalignment will be visible."
            f"{_SYNTH_CLOSERS[vs]}"
        ),
    }

    # --- Grand synthesis ---
    ks_str = ', '.join(str(l) for l in karmic_lessons) if karmic_lessons else "none"
    lw_gate_num = lw["gate"]
    lw_name_grand = lw["name"]
    lw_gift_grand = lw["gift"]
    lw_shadow_grand = lw["shadow"]
    grand_summ = {
        "light": (
            f"{_LIGHT_OPENERS[vs]}"
            f"When all systems are read together, one singular profile emerges with striking coherence. "
            f"Life Path {lp} ({lp_arch}) · {sun} Sun · {hd_type} · Life's Work Gate {lw_gate_num} ({lw_name_grand}): "
            f"four facts from four independent systems, each calculated from the same birth coordinates, "
            f"each pointing to the same core frequency. "
            f"The gift that runs through all of them: {lw_gift_grand}. "
            f"No system invented this independently. Each derived it from the precise moment you were born."
        ),
        "shadow": (
            f"{_SHADOW_OPENERS[vs]}"
            f"The shadow that runs across systems is equally coherent. "
            f"Not-self ({not_self}), karmic lessons ({ks_str}), Life's Work shadow ({lw_shadow_grand}), "
            f"communication conditioning ({comm_avoid}): "
            f"not four separate problems — the same pattern seen through four lenses. "
            f"The cross-system shadow is always some version of the same misalignment: "
            f"operating from conditioned response rather than authentic design. "
            f"Seeing it confirmed across four independent systems makes it impossible to dismiss — "
            f"and what is clearly seen cannot be unconsciously repeated."
        ),
        "synthesis": (
            f"{_GRAND_OPENERS[vs]}"
            f"the same frequency encoded simultaneously into numbers (Numerology), "
            f"planetary positions (Astrology), energy mechanics (Human Design), and contemplative keys (Gene Keys). "
            f"The redundancy is not accident. It is emphasis. "
            f"What all four systems agree on is the irreducible core of who you are. "
            f"Life Path {lp}, {sun} Sun, {hd_type} with {auth_short} Authority, Gate {lw_gate_num}: "
            f"your identity confirmed across four independent methodologies. "
            f"The pillars: your purpose ({lp_arch}), your instrument ({expr} Expression), "
            f"your strategy ({strategy}), your contemplative path (Gate {lw_gate_num} — {lw_name_grand}). "
            f"Nothing here is random. You were specifically designed this way."
            f"{_GRAND_CLOSERS[vs]}"
        ),
    }

    return {
        "numerology": num_summ,
        "western": west_summ,
        "vedic": ved_summ,
        "human_design": hd_summ,
        "gene_keys": gk_summ,
        "communication": comm_summ,
        "grand": grand_summ,
    }


# Short essence phrase per numerology number — reused for the Core Dynamic & Soul Arc
# discovery below, where two of a client's core numbers are set in creative tension.
_NUM_THEME = {
    1: "bold, self-directed initiation", 2: "sensitive, diplomatic partnership",
    3: "joyful, expressive creativity", 4: "grounded, disciplined structure",
    5: "restless, freedom-seeking exploration", 6: "devoted, responsible nurturing",
    7: "private, analytical depth-seeking", 8: "powerful, authoritative material mastery",
    9: "broad, compassionate humanitarian completion",
    11: "electrically intuitive spiritual illumination",
    22: "world-scale visionary building", 33: "selfless, healing universal service",
}


def _chart_standouts(report: BlueprintReport) -> dict:  # noqa: C901
    """
    "Core Blueprint Standouts & Synchronicities" — a holistic pattern-synthesis layer
    read across each system's already-calculated data. Four discoveries per system:
    Master Frequencies & Higher Calling, Golden Threads & Repeating Echoes, The
    Crucible & Sacred Tests, and The Core Dynamic & Soul Arc. Pure pattern detection
    and deterministic templated language over existing values — no new calculations,
    no LLM generation. Voice: warm, grounded mentor speaking directly to "you."
    """
    num = report.numerology
    west = report.western
    ved = report.vedic
    hd = report.human_design
    gk = report.gene_keys

    TITLE = "Core Blueprint Standouts & Synchronicities"

    # ================================================================= NUMEROLOGY ===
    lp = num["life_path"]
    expr = num["expression"]
    soul = num["soul_urge"]
    personality_n = num["personality"]
    attitude = num["attitude"]
    birthday_n = num["birthday"]
    generation_n = num["generation"]
    maturity = num["maturity"]
    balance = num["balance"]
    karmic_debts = num["karmic_debts"]
    karmic_lessons = num["karmic_lessons"]
    pinnacles = num["pinnacles"]
    challenges = num["challenges"]
    MASTERS = {11, 22, 33}

    # 1. Master Frequencies & Higher Calling
    master_fields = []
    for label, val in [
        ("Life Path", lp), ("Expression", expr), ("Soul Urge", soul),
        ("Personality", personality_n), ("Attitude", attitude), ("Birthday", birthday_n),
        ("Generation", generation_n), ("Maturity", maturity), ("Balance", balance),
    ]:
        if val in MASTERS:
            master_fields.append((label, val))
    for i, p in enumerate(pinnacles):
        if p in MASTERS:
            master_fields.append((f"Pinnacle {i + 1}", p))
    if master_fields:
        names = ", ".join(
            f"{label} (value {val})" if label.startswith("Pinnacle") else f"{label} {val}"
            for label, val in master_fields
        )
        if len(master_fields) >= 2:
            master_text = (
                f"You're carrying a master number in more than one place — {names}. "
                f"That's not a coincidence to skim past. Master numbers run at a higher electrical voltage "
                f"than the numbers around them: more sensitivity, more capacity, and more responsibility to actually "
                f"do something with what you're carrying. When one shows up twice, it means this isn't a phase "
                f"you're passing through — it's a frequency your whole life is built to run on. The pressure you've "
                f"likely felt to be \"more\" than what a normal life asks for isn't imagined. It's the design working correctly."
            )
        else:
            label, val = master_fields[0]
            master_text = (
                f"Your {label} carries a master number — {val}. This is a higher-voltage frequency than the single "
                f"digits around it: more sensitivity, more perceptiveness, and a deeper calling underneath the ordinary "
                f"business of daily life. It's not something to live up to. It's something you were already carrying "
                f"before you had language for it — the felt sense, since childhood, that you were here to do or "
                f"understand something a little beyond what was immediately in front of you."
            )
    else:
        master_text = (
            "No master numbers appear anywhere in your core chart. That's not an absence — it means your gifts are "
            "built to operate through mastery of the ordinary numbers rather than the amplified intensity a master "
            "number carries. There's real freedom in that: less internal pressure to be exceptional, more room to "
            "simply become excellent at being exactly who you are."
        )

    # 2. Golden Threads & Repeating Echoes
    # Note: Period Cycles are literally [Attitude, Generation, Life Path] repeated
    # verbatim, not an independent signal — excluded here to avoid double-counting
    # the same three values that are already counted directly below.
    thread_counter = Counter(
        [lp, expr, soul, personality_n, attitude, birthday_n, generation_n, maturity]
        + list(pinnacles) + list(challenges)
    )
    top_number, top_count = thread_counter.most_common(1)[0] if thread_counter else (None, 0)
    if top_count >= 3:
        theme = _NUM_THEME.get(top_number, "a specific, recurring quality")
        thread_text = (
            f"The number {top_number} doesn't show up once in your chart — it shows up {top_count} separate times, "
            f"echoing across your core numbers, your pinnacle peaks, and your challenge cycles. When a single number "
            f"repeats that persistently, it's the chart underlining something it wants you to actually hear: "
            f"{theme} isn't one trait among many — it's a lesson and a gift this entire lifetime keeps circling back to. "
            f"Whatever you've resisted or struggled with around {top_number}'s theme, expect it to keep resurfacing, "
            f"in new forms, until it's genuinely integrated rather than avoided."
        )
    else:
        thread_text = (
            "No single number dominates your chart by repetition — your numbers are genuinely varied rather than "
            "echoing one note again and again. That's its own kind of gift: a versatile, multi-toned instrument "
            "rather than one built around a single, insistent frequency. The lessons here arrive from many "
            "directions rather than one repeating drumbeat."
        )

    # 3. The Crucible & Sacred Tests
    crucible_parts = []
    if karmic_debts:
        debts_str = ", ".join(str(d) for d in karmic_debts)
        crucible_parts.append(
            f"Karmic debt numbers ({debts_str}) are present in your chart. These aren't punishments written into "
            f"your numbers — they're sacred fires. Each one marks a specific, hard-won lesson your soul chose to "
            f"burn through in this lifetime rather than skip. The friction they create isn't a flaw in the design; "
            f"it's the exact resistance that forges the strength and authority you're building toward."
        )
    if karmic_lessons:
        lessons_str = ", ".join(str(l) for l in karmic_lessons)
        crucible_parts.append(
            f"The digits missing from your name — {lessons_str} — are karmic lessons: capacities you weren't handed "
            f"automatically and have had to earn through direct, often difficult, life experience. What comes hardest "
            f"here is exactly what you're here to develop, not evidence that something is missing from you."
        )
    if not crucible_parts:
        crucible_parts.append(
            "You carry no karmic debt numbers and no karmic lesson gaps — every digit is present in your name, and "
            "no unreduced debt number surfaces in your core chain. That's a genuinely lighter karmic load to carry "
            "into this lifetime. It doesn't mean an easier life; it means the sacred tests you do face are more "
            "evenly distributed rather than concentrated in one recurring wound."
        )
    crucible_text = " ".join(crucible_parts)

    # 4. The Core Dynamic & Soul Arc
    expr_theme = _NUM_THEME.get(expr, "your outer instrument")
    soul_theme = _NUM_THEME.get(soul, "your inner drive")
    num_standouts = {
        "title": TITLE,
        "sections": [
            {"heading": "The Master Frequencies & Higher Calling", "text": master_text},
            {"heading": "The Golden Threads & Repeating Echoes", "text": thread_text},
            {"heading": "The Crucible & Sacred Tests", "text": crucible_text},
            {"heading": "The Core Dynamic & Soul Arc", "text": (
                f"Here's the paradox living at the center of your numbers: Expression {expr} gives you "
                f"{expr_theme} as the instrument you show the world, while Soul Urge {soul} is quietly running "
                f"{soul_theme} underneath it the entire time. These aren't in conflict — one is the visible "
                f"instrument, the other is the reason you pick it up at all. Life Path {lp} is the road both of "
                f"them walk together. The moment you stop trying to resolve the paradox and start letting both "
                f"halves operate at once — the outer instrument in full service of the inner drive — is the moment "
                f"this chart stops feeling like tension and starts feeling like home. Walk this path knowing both "
                f"halves were always meant to be here."
            )},
        ],
    }

    # ============================================================= HUMAN DESIGN ===
    hd_type = hd.get("type", "")
    authority = hd.get("authority", "")
    profile_hd = hd.get("profile", "")
    strategy = hd.get("strategy", "")
    definition = hd.get("definition", "")
    defined_centers_hd = hd.get("defined_centers", [])
    open_centers_hd = hd.get("open_centers", [])
    auth_short_hd = authority.split(" (")[0] if "(" in authority else authority

    _RARE_TYPE_NOTE = {
        "Reflector": (
            "You are a Reflector — under 1% of the population, and the rarest design there is. Every center in "
            "your bodygraph is open, which sounds like a vulnerability until you understand what it actually means: "
            "you're built to be a perfect mirror for the health of whatever environment you're in. That is an "
            "extraordinarily high-voltage calling most people never carry."
        ),
        "Manifestor": (
            "You are a Manifestor — roughly 9% of the population, and the only type built to initiate entirely on "
            "your own authority, without waiting for invitation or response. That's a rarer, higher-voltage design "
            "than it might feel like day to day, especially if the world keeps asking you to explain yourself first."
        ),
    }
    if hd_type in _RARE_TYPE_NOTE:
        hd_master_text = _RARE_TYPE_NOTE[hd_type]
    elif len(defined_centers_hd) >= 6:
        hd_master_text = (
            f"With {len(defined_centers_hd)} of your 9 centers defined, you're carrying an unusually loaded, "
            f"high-voltage design. Most of your bodygraph runs on fixed, reliable circuitry rather than open "
            f"sampling — a consistent, always-on presence that fewer people are actually built to carry."
        )
    elif len(defined_centers_hd) <= 2:
        hd_master_text = (
            f"With only {len(defined_centers_hd)} of your 9 centers defined, you're running an unusually open, "
            f"receptive design. That isn't a deficiency — it's a heightened sensitivity to the field around you, "
            f"the rarer calling of being deeply, genuinely responsive rather than fixed."
        )
    else:
        hd_master_text = (
            f"As a {hd_type} with {auth_short_hd} Authority, your design runs at a distinctive, specific frequency — "
            f"not the rarest configuration on the wheel, but a precise architecture built for exactly the way you're "
            f"meant to move through the world."
        )

    personality_acts = hd.get("personality_activations", {})
    design_acts = hd.get("design_activations", {})
    p_gates = {a["gate"] for a in personality_acts.values()}
    d_gates = {a["gate"] for a in design_acts.values()}
    doubled_gates = sorted(p_gates & d_gates)
    if doubled_gates:
        gate = doubled_gates[0]
        hd_thread_text = (
            f"Gate {gate} is activated on both sides of your design — by a Personality (conscious) planet and a "
            f"Design (unconscious, body-level) planet at once. That's a genuine echo: this specific gate's energy "
            f"isn't just something you think or believe, it's something your body runs automatically too. Whatever "
            f"that gate's theme is, expect it to show up both in how you consciously present and in how you "
            f"instinctively act, without you having to try to align the two."
        )
    else:
        hd_thread_text = (
            "No single gate repeats across both your Personality and Design activations — your conscious "
            "presentation and your unconscious, body-level programming draw from genuinely separate gates. "
            "That's its own kind of richness: what you consciously believe and what your body does under pressure "
            "are two distinct instruments, not one note played twice."
        )

    open_list = ", ".join(open_centers_hd) if open_centers_hd else "none"
    hd_crucible_text = (
        (
            f"Your open centers — {open_list} — are the sacred tests built into this design. An open center isn't "
            f"a wound; it's where you were built to take in the world's wisdom rather than carry a fixed truth of "
            f"your own. The hard-won lesson every open center teaches is the same one, over and over: learning to "
            f"feel the difference between what's genuinely yours and what you've absorbed from whoever's standing "
            f"near you. That discernment, forged slowly through real experience, is exactly what turns an open "
            f"center from a vulnerability into a form of wisdom few fixed-center people ever develop."
        ) if open_centers_hd else
        "With no open centers at all, you carry no built-in conditioning points the way most designs do — a rare "
        "architecture where nearly everything about you runs consistently, on your own fixed frequency."
    )

    hd_standouts = {
        "title": TITLE,
        "sections": [
            {"heading": "The Master Frequencies & Higher Calling", "text": hd_master_text},
            {"heading": "The Golden Threads & Repeating Echoes", "text": hd_thread_text},
            {"heading": "The Crucible & Sacred Tests", "text": hd_crucible_text},
            {"heading": "The Core Dynamic & Soul Arc", "text": (
                f"Here's the paradox at the heart of your design: your {strategy} strategy is the outer mechanism — "
                f"how you're meant to move through the world without resistance — while your {auth_short_hd} "
                f"Authority is the inner truth that actually decides. The mind wants to lead; the design insists "
                f"the body already knows. Every moment of friction in your life traces back to one of these two "
                f"trying to do the other's job. Profile {profile_hd} is the specific role your soul chose to learn "
                f"this exact lesson through. Walk this path by making the strategy your outer rhythm and the "
                f"authority your inner compass — not fighting each other, but each fully doing its own job."
            )},
        ],
    }

    # ================================================================ GENE KEYS ===
    act_seq_gk = gk.get("activation_sequence", [])
    sphere_gates = {s.get("sphere", ""): s.get("gate", 0) for s in act_seq_gk}
    lw_gate = sphere_gates.get("Life's Work", 0)
    ev_gate = sphere_gates.get("Evolution", 0)
    ra_gate = sphere_gates.get("Radiance", 0)
    pu_gate = sphere_gates.get("Purpose", 0)

    partner_pairs = []
    spheres_list = [("Life's Work", lw_gate), ("Evolution", ev_gate), ("Radiance", ra_gate), ("Purpose", pu_gate)]
    for i in range(len(spheres_list)):
        for j in range(i + 1, len(spheres_list)):
            name_a, gate_a = spheres_list[i]
            name_b, gate_b = spheres_list[j]
            if gate_a and gate_b and programming_partner(gate_a) == gate_b:
                partner_pairs.append((name_a, gate_a, name_b, gate_b))

    if partner_pairs:
        name_a, gate_a, name_b, gate_b = partner_pairs[0]
        gk_master_text = (
            f"Your {name_a} (Gate {gate_a}) and your {name_b} (Gate {gate_b}) are Programming Partners — exact "
            f"opposites on the Gene Keys wheel, 32 positions apart. This is a genuine synchronicity, not a coincidence "
            f"of the math: it means two entirely different domains of your life — {name_a.lower()} and "
            f"{name_b.lower()} — are wired to mirror and complete each other. Growth in one will almost always "
            f"show up as movement in the other, whether or not you consciously connect the two."
        )
    else:
        gk_master_text = (
            f"Your four spheres — Life's Work (Gate {lw_gate}), Evolution (Gate {ev_gate}), Radiance (Gate {ra_gate}), "
            f"and Purpose (Gate {pu_gate}) — draw from four distinct gates rather than mirroring each other directly. "
            f"That's its own high-voltage signature: four genuinely different frequencies, all active in you "
            f"simultaneously, each doing its own distinct work."
        )

    gate_counts = Counter(g for _, g in spheres_list if g)
    repeated_gate = next((g for g, c in gate_counts.items() if c >= 2), None)
    if repeated_gate:
        spheres_sharing = [name for name, g in spheres_list if g == repeated_gate]
        gk_thread_text = (
            f"Gate {repeated_gate} appears more than once in your hologenetic profile — across {' and '.join(spheres_sharing)}. "
            f"The same shadow-to-gift-to-siddhi theme is running through more than one domain of your life at once, "
            f"which means whatever that gate is teaching you isn't confined to one area — it's a thread woven through "
            f"multiple layers of who you're becoming."
        )
    else:
        gk_thread_text = (
            "No gate repeats across your four spheres — each of Life's Work, Evolution, Radiance, and Purpose draws "
            "its own distinct lesson. Your growth here comes from four separate directions rather than one theme "
            "echoing through every layer."
        )

    gk_shadows = []
    for s in act_seq_gk:
        gate = s.get("gate", 0)
        info = GENE_KEYS.get(gate, ("", "", "", ""))
        if info[1]:
            gk_shadows.append(f"{s.get('sphere','')} (Gate {gate}) carries the Shadow of {info[1]}")
    gk_crucible_text = (
        (
            "The Gene Keys are direct about this: your shadows are not flaws to fix, they're sacred fires — the exact "
            "doorway your gifts walk through. " + "; ".join(gk_shadows) + ". Sit with each one without reacting to it, "
            "and it begins to transmute into its Gift on its own. Repress it or react to it, and it just gets louder."
        ) if gk_shadows else
        "Your activation sequence's shadow patterns weren't fully available to name here, but the same principle "
        "holds for whatever surfaces: it's a doorway to sit with, not a flaw to fix."
    )

    gk_standouts = {
        "title": TITLE,
        "sections": [
            {"heading": "The Master Frequencies & Higher Calling", "text": gk_master_text},
            {"heading": "The Golden Threads & Repeating Echoes", "text": gk_thread_text},
            {"heading": "The Crucible & Sacred Tests", "text": gk_crucible_text},
            {"heading": "The Core Dynamic & Soul Arc", "text": (
                f"Gate {lw_gate} (your Life's Work — what you're here to do) and Gate {pu_gate} (your Purpose — "
                f"what grounds you deepest) form the core paradox of this system: one is active outward expression, "
                f"the other is quiet inner ground. You're not meant to resolve them into one thing. You're meant to "
                f"let your Life's Work rise out of a Purpose that's already settled and steady underneath it. "
                f"Contemplation, not effort, is how both mature together — sustained, non-reactive attention to "
                f"whatever shadow shows up next."
            )},
        ],
    }

    # ================================================================= VEDIC ===
    rashis_raw = ved.get("rashis", {})
    nakshatras_v = ved.get("nakshatras", {})
    retro_bodies = set(west.get("dominant_retrogrades", [])) | {"Rahu", "Ketu"}
    retro_grahas = [b for b in rashis_raw if b != "Lagna" and b in retro_bodies]

    if retro_grahas:
        ved_master_text = (
            f"{', '.join(retro_grahas)} {'is' if len(retro_grahas) == 1 else 'are'} retrograde in your sidereal chart. "
            f"In Vedic astrology, retrograde motion isn't weakness — classically it's considered an intensification, "
            f"a planet whose lessons run deeper and more internally than a direct placement. Whatever "
            f"{'this graha governs' if len(retro_grahas) == 1 else 'these grahas govern'} is being worked out at a "
            f"higher, more private voltage than most people experience with that same placement."
        )
    else:
        ved_master_text = (
            "No grahas run retrograde in your sidereal chart (beyond Rahu and Ketu, which always do). Every planetary "
            "energy here moves in its direct, outwardly-expressed mode — nothing is being processed in an unusually "
            "internalized or intensified register."
        )

    rashi_names_v = [_parse_rashi(r)[0] for b, r in rashis_raw.items() if b != "Lagna"]
    rashi_counts = Counter(rashi_names_v)
    stellium_rashi, stellium_count = rashi_counts.most_common(1)[0] if rashi_counts else (None, 0)
    lord_counts = Counter(n.get("lord", "") for b, n in nakshatras_v.items() if n.get("lord"))
    top_lord, top_lord_count = lord_counts.most_common(1)[0] if lord_counts else (None, 0)

    if stellium_count >= 3:
        ved_thread_text = (
            f"{stellium_count} of your grahas cluster together in {stellium_rashi} — a genuine stellium. When that "
            f"many planetary energies concentrate in one rashi, that sign's theme isn't a background note in your "
            f"chart, it's the dominant key nearly everything else is playing in."
        )
    elif top_lord_count >= 3:
        ved_thread_text = (
            f"{top_lord} rules the nakshatra of {top_lord_count} of your grahas at once. That's a real echo — a "
            f"single planetary intelligence quietly running underneath multiple placements in your chart, tying "
            f"them together more than their surface differences suggest."
        )
    else:
        ved_thread_text = (
            "Your grahas are genuinely spread across the sidereal zodiac — no single sign or nakshatra lord "
            "dominates by repetition. Your chart draws its strength from breadth rather than one concentrated point."
        )

    rahu_rashi_v = rashis_raw.get("Rahu", "")
    ketu_rashi_v = rashis_raw.get("Ketu", "")
    ved_crucible_text = (
        f"Your Rahu–Ketu axis — Rahu in {rahu_rashi_v}, Ketu in {ketu_rashi_v} — is the sacred test running underneath "
        f"this entire incarnation. Ketu is the fluency you already carry from lifetimes of practice — so native it "
        f"asks nothing of you. Rahu is the growth edge: unfamiliar, slightly uncomfortable, and exactly where this "
        f"lifetime's real curriculum lives. The discomfort of leaning toward Rahu isn't a warning sign to retreat "
        f"from — it's the precise sensation of the soul doing the work it came here to do."
    )

    moon_rashi_v = _parse_rashi(rashis_raw.get("Moon", ""))[0]
    lagna_str_v = ved.get("lagna", "")
    lagna_sk_v = _parse_rashi(lagna_str_v)[0] if "(" in lagna_str_v else lagna_str_v

    ved_standouts = {
        "title": TITLE,
        "sections": [
            {"heading": "The Master Frequencies & Higher Calling", "text": ved_master_text},
            {"heading": "The Golden Threads & Repeating Echoes", "text": ved_thread_text},
            {"heading": "The Crucible & Sacred Tests", "text": ved_crucible_text},
            {"heading": "The Core Dynamic & Soul Arc", "text": (
                f"Your {lagna_sk_v} Lagna is how you arrive in any room — the engagement the world meets first. Your "
                f"{moon_rashi_v} Moon is what's actually happening inside you the whole time, often quite different "
                f"from that outer arrival. This isn't a contradiction to fix. It's the design working as intended: "
                f"the Lagna is the vehicle, the Moon is the passenger. Confidence here doesn't come from making the "
                f"two match — it comes from trusting that both are honestly yours, running at the same time."
            )},
        ],
    }

    # =============================================================== WESTERN ===
    sun_w = west.get("sun_sign", "")
    moon_w = west.get("moon_sign", "")
    asc_w = west.get("ascendant", "")
    chart_ruler_w = west.get("chart_ruler", "")
    elem_bal_w = west.get("element_balance", {}) or {}
    retro_w = west.get("dominant_retrogrades", [])
    placements_w = west.get("placements", {})
    saturn_sign_w = placements_w.get("Saturn", {}).get("sign_name", "")
    saturn_retro_w = "Saturn" in retro_w

    dom_elem_count = max(elem_bal_w.values()) if elem_bal_w else 0
    dom_elem_w = max(elem_bal_w, key=elem_bal_w.get) if elem_bal_w else ""
    if dom_elem_count >= 5:
        west_master_text = (
            f"{dom_elem_count} of your planetary bodies concentrate in {dom_elem_w} — an unusually loaded, "
            f"high-voltage elemental signature. This isn't a mild leaning, it's the dominant key your entire chart "
            f"is playing in. Whatever {dom_elem_w} represents for you, expect it to color nearly every part of how "
            f"you move through life, not just one corner of it."
        )
    else:
        west_master_text = (
            f"Your chart's elements are reasonably distributed, with {dom_elem_w} carrying a modest lead rather than "
            f"an overwhelming concentration. That balance is its own gift — access to multiple registers rather than "
            f"being locked into a single elemental key."
        )

    sign_matches = []
    if sun_w and sun_w == moon_w:
        sign_matches.append(("Sun and Moon", sun_w))
    if sun_w and sun_w == asc_w:
        sign_matches.append(("Sun and Rising", sun_w))
    if moon_w and moon_w == asc_w:
        sign_matches.append(("Moon and Rising", moon_w))
    if sign_matches:
        pair_label, shared_sign = sign_matches[0]
        west_thread_text = (
            f"Your {pair_label} both fall in {shared_sign} — a genuine echo. When two of your three most personal "
            f"placements share a sign, that sign's theme isn't just one layer of you, it's reinforced from two "
            f"separate directions at once, which is usually why it reads as more concentrated or more obviously "
            f"\"you\" than any single placement alone would suggest."
        )
    else:
        west_thread_text = (
            f"Your Sun ({sun_w}), Moon ({moon_w}), and Rising ({asc_w}) each land in different signs — three "
            f"genuinely distinct notes rather than one repeating chord. That's real range: identity, emotional "
            f"nature, and first impression each speak in their own dialect."
        )

    retro_list_str = ", ".join(retro_w) if retro_w else "none"
    west_crucible_text = (
        (
            f"{retro_list_str} {'runs' if len(retro_w) == 1 else 'run'} retrograde in your chart. Retrograde planets "
            f"turn their energy inward before it can express outward — the sacred test here is that this energy's "
            f"real work happens in private, in depth, well before it's ever visible to anyone else. "
        ) if retro_w else ""
    ) + (
        f"Your Saturn in {saturn_sign_w}{' (retrograde)' if saturn_retro_w else ''} is the classical tester of this "
        f"entire chart — the planet of earned authority, structure, and the long, sometimes hard road to genuine "
        f"mastery. {'Retrograde Saturn suggests discipline that was built early, through real hardship, rather than handed to you gently.' if saturn_retro_w else 'A direct Saturn suggests discipline built more conventionally, through visible, external structure.'} "
        f"Either way, wherever Saturn presses hardest is exactly where your deepest, most earned authority is being built."
    )

    west_standouts = {
        "title": TITLE,
        "sections": [
            {"heading": "The Master Frequencies & Higher Calling", "text": west_master_text},
            {"heading": "The Golden Threads & Repeating Echoes", "text": west_thread_text},
            {"heading": "The Crucible & Sacred Tests", "text": west_crucible_text},
            {"heading": "The Core Dynamic & Soul Arc", "text": (
                f"Your {sun_w} Sun is the identity you're consciously growing into. Your {moon_w} Moon is the "
                f"emotional weather running underneath it, often before your Sun has had a chance to weigh in. "
                f"That's the paradox: the part of you that's building forward and the part of you that's feeling "
                f"everything right now aren't always saying the same thing, and they were never meant to. Your "
                f"{asc_w} Rising is the vehicle that carries both of them into every room, with {chart_ruler_w} — "
                f"your chart ruler — quietly governing how easily that vehicle moves. Confidence here means letting "
                f"the Sun lead the direction while the Moon is honestly felt, not overridden."
            )},
        ],
    }

    return {
        "numerology": num_standouts,
        "human_design": hd_standouts,
        "gene_keys": gk_standouts,
        "vedic": ved_standouts,
        "western": west_standouts,
    }


def _build_synthesis_panels(report: BlueprintReport, vs: str) -> dict:
    """Build Core Identity, Strengths, Shadow, and Complete Synthesis panels for the Summary page."""
    num = report.numerology
    west = report.western
    ved = report.vedic or {}
    hd = report.human_design or {}
    gk = report.gene_keys or {}
    comm = report.communication or {}

    lp = num["life_path"]
    expr = num["expression"]
    soul = num["soul_urge"]
    lp_arch = LP_ARCHETYPES.get(lp, "unique frequency")
    lp_theme = _LP_THEMES.get(lp, ("unique soul path", "a persistent pull"))[0]
    lp_pull = _LP_THEMES.get(lp, ("", "the tension between your path's demands and the easier route"))[1]

    sun = west.get("sun_sign", "")
    moon = west.get("moon_sign", "")
    asc = west.get("ascendant", "")
    elem_bal = west.get("element_balance", {})
    dom_elem = max(elem_bal, key=elem_bal.get) if elem_bal else ""

    hd_type = hd.get("type", "")
    authority = hd.get("authority", "")
    auth_short = authority.split(" (")[0] if "(" in authority else authority
    profile_hd = hd.get("profile", "")
    strategy = hd.get("strategy", "")

    lagna_str = ved.get("lagna", "")
    lagna_sk = lagna_str.split("(")[0].strip() if lagna_str else ""
    moon_rashi = ved.get("moon_rashi", "")
    moon_rashi_sk = moon_rashi.split("(")[0].strip() if moon_rashi else ""
    moon_nak = ved.get("moon_nakshatra", "")
    rahu_rashi = ved.get("rashis", {}).get("Rahu", "")
    rahu_sk = rahu_rashi.split("(")[0].strip() if rahu_rashi else ""
    ketu_rashi = ved.get("rashis", {}).get("Ketu", "")
    ketu_sk = ketu_rashi.split("(")[0].strip() if ketu_rashi else ""
    mahadasha = ved.get("starting_mahadasha", "")
    atmakaraka = ved.get("charakarakas", {}).get("Atmakaraka", "")

    act_seq = gk.get("activation_sequence", [])
    lw = act_seq[0] if act_seq else {}
    lw_gate = lw.get("gate", 0)
    lw_info = GENE_KEYS.get(lw_gate, ("", "", "", ""))
    lw_name, lw_shadow, lw_gift, lw_siddhi = lw_info

    comm_arch = comm.get("archetype", "")
    comm_avoid = (comm.get("delivery", {}) or {}).get("avoid", "")

    # Core Identity paragraph
    core_id_text = (
        f"Let's start with what's actually written into your birth moment, because nothing here is guesswork — "
        f"it's what five separate systems, calculated independently from the same birth date, time, and place, all arrive at on their own. "
        f"Your Life Path is {lp} — {lp_arch}. In plain terms, that number describes the theme your whole life keeps circling back to: {lp_theme}. "
        f"You've probably lived this out in ordinary moments without ever naming it — the role you keep ending up in at work, the kind of problem people "
        f"bring to you specifically, the thing you can't stop noticing even on days you'd rather not think about it. That's the Life Path, quietly running "
        f"underneath an otherwise ordinary Tuesday. "
        f"Your Sun sits in {sun}. That's the part of you still under construction — the identity you're actively growing into a little more with each year, "
        f"more fully expressed now than it was a decade ago, and it isn't finished yet. "
        f"Your Ascendant is {asc} — this is the very first impression you make, before you've said a word or explained anything about yourself. "
        f"It's what a stranger picks up on in the first few seconds of meeting you, and it's often a different read than the one people get once they actually "
        f"know you. "
        f"In Human Design terms, you're a {hd_type}, and your strategy — {strategy} — isn't a rule you consciously follow so much as a rhythm your energy "
        f"already runs on: when you move with it, things tend to open with less effort than you'd expect; push against it, and the friction usually shows up "
        f"almost immediately, even when you can't quite say why. "
        f"Vedically, your Moon sits in {moon_rashi_sk}, in the {moon_nak} nakshatra — this is your emotional operating system, the layer that reacts before "
        f"your thinking mind has even caught up. It's what you feel first, in your body, before you've had a chance to decide how you feel about it. "
        f"And at the Gene Keys level, Gate {lw_gate} ({lw_name}) is your Life's Work — the specific frequency you're here to put into the world, in whatever "
        f"shape your actual day-to-day life happens to take. "
        f"Five different systems, five different vocabularies, all describing the same person. That's not a coincidence worth shrugging off — "
        f"it's the strongest kind of evidence a reading like this can offer: the same signal, arriving independently, from every direction at once."
    )
    core_id_sources = [
        f"Numerology: Life Path {lp} ({lp_arch})",
        f"Western: {sun} Sun · {asc} Ascendant",
        f"Human Design: {hd_type} · {strategy}",
        f"Vedic: Moon {moon_rashi_sk} · {moon_nak}",
        f"Gene Keys: Gate {lw_gate} ({lw_name})",
    ]

    # Synthesized Strengths
    _ELEM_TALENT: dict[str, str] = {
        "Fire": "you bring energy into a room just by walking into it — the people around you tend to get more motivated, not less, once you're actually engaged in something, which is a genuinely rare effect to have on other people",
        "Earth": "you're the one still standing, calm, once everyone else's plans have fallen apart — not because you don't feel the pressure, but because you were built to hold weight without needing to make a show of it",
        "Air": "you can take something genuinely complicated and hand it back in a way that makes someone say 'oh, that's actually simple' — that's a real skill, not a small one, and it's why people keep asking you to explain things",
        "Water": "you tend to know something's off in a room before anyone's said a word about it — a shift in someone's tone, a look that lasted half a second too long — and you're usually right, even when you can't point to exactly what tipped you off",
    }
    _TYPE_STRENGTH: dict[str, str] = {
        "Generator": "a genuinely renewable kind of energy, but only for work you actually enjoy. Think of the difference between a task that drains you by mid-afternoon and one you could keep doing for hours without noticing the time — that second feeling isn't random, it's your design confirming you're on the right track",
        "Manifesting Generator": "the ability to move fast across more than one thing at once. Where most people need to finish A before starting B, you can genuinely run both — and the shortcuts you take usually aren't cutting corners, they're just your process working the way it's supposed to",
        "Projector": "a kind of insight that comes from watching rather than doing. You tend to see what's actually happening in a group or a system faster than the people standing inside it do, the same way it's easier to spot a play developing from the sideline than from the middle of the field",
        "Manifestor": "the ability to just start something, cleanly, without waiting for a committee to sign off first. Most people wait for a permission that never fully arrives — you're built to move, and let the world catch up around you",
        "Reflector": "an unusually accurate read on the health of whatever room you're standing in. You're picking up something real that most people miss entirely — even if it sometimes leaves you unsure which feelings started with you and which ones you picked up on the way in",
    }
    strengths_list = []
    if lp and lp_arch:
        strengths_list.append({
            "text": f"Your Life Path is {lp} — {lp_arch}. {lp_theme.capitalize()} isn't a phase you're passing through, it's a thread that keeps reappearing across totally different chapters of your life — different jobs, different relationships, sometimes different cities — because it was never really about the circumstances. If you look back at the moments that actually felt meaningful, this is very likely the reason why.",
            "sources": [f"Numerology: Life Path {lp}"],
        })
    if hd_type:
        strengths_list.append({
            "text": f"You're a {hd_type} in Human Design terms, and that comes with a specific, built-in gift: {_TYPE_STRENGTH.get(hd_type, 'a unique energetic intelligence that others tend to sense before they can put a name to it')}. This isn't a personality quirk — it's the actual architecture of how your energy moves through the day.",
            "sources": [f"Human Design: {hd_type}"],
        })
    if dom_elem:
        strengths_list.append({
            "text": f"Your chart leans heavily {dom_elem} — it's the dominant element across your placements. In practice: {_ELEM_TALENT.get(dom_elem, 'you draw from a fairly balanced elemental field, able to shift registers as the moment calls for it')}. This is the register you operate in without having to try.",
            "sources": [f"Western Astrology: {dom_elem} element dominant"],
        })
    if lw_gate and lw_gift:
        strengths_list.append({
            "text": f"Your Life's Work is Gate {lw_gate} ({lw_name}), and its Gift — {lw_gift} — is what naturally comes online once the {lw_shadow} pattern stops running the show. It's broadcast from your Sun, the most visible part of your design, which means it shows up whether or not you're consciously trying to access it. The people who actually know you have probably already felt this in you, even without a name for it.",
            "sources": [f"Gene Keys: Gate {lw_gate}", "Human Design: Personality Sun"],
        })

    # Synthesized Shadow
    _RAHU_CHAL: dict[str, str] = {
        "Mesha (Aries)": "jumping into things before you've actually thought them through, which can look like impulsiveness from the outside even though it's really an unfinished pioneer instinct",
        "Vrishabha (Taurus)": "holding onto what already feels safe a little too tightly, sometimes at the cost of the next real step forward",
        "Mithuna (Gemini)": "getting pulled in five directions at once, which can quietly keep you from ever going deep enough into the one thing that would actually satisfy you",
        "Karka (Cancer)": "feeling flooded when you're not sure you belong somewhere — the uncertainty itself becomes the hardest part, more than whatever actually happened",
        "Simha (Leo)": "needing someone else to notice you before you'll fully believe in yourself, when the real work is learning to generate that confidence from the inside",
        "Kanya (Virgo)": "polishing something for so long it never actually gets finished or shared, because it never quite feels ready",
        "Tula (Libra)": "bending toward whoever you're with until you lose track of what you actually wanted in the first place",
        "Vrishchika (Scorpio)": "an intensity that can push people away right when you need them closest, or turn into a power struggle instead of the connection you were actually looking for",
        "Dhanu (Sagittarius)": "always reaching for the next, bigger meaning instead of committing to the one already right in front of you",
        "Makara (Capricorn)": "measuring your worth by what you've achieved, when the actual work this lifetime is asking for is quieter and more internal than that",
        "Kumbha (Aquarius)": "caring so much about the big picture and the collective that the people closest to you can end up feeling like an afterthought",
        "Meena (Pisces)": "losing track of where you end and someone else's feelings begin",
    }
    shadow_list = [
        {
            "text": f"Your Life Path is {lp}, and the friction that comes with it is real: {lp_pull}. It's tempting to read that as a flaw — something to apologize for or fix — but it's closer to the resistance a muscle actually needs in order to get stronger. Take the friction away, and you'd also be taking away the thing that's building your capacity for whatever this path is actually asking of you.",
            "sources": [f"Numerology: Life Path {lp}"],
        },
    ]
    if rahu_sk:
        shadow_list.append({
            "text": f"In Vedic astrology, your Rahu — the point that shows what this lifetime is actually growing you toward — sits in {rahu_sk}. The pattern that tends to show up along the way: {_RAHU_CHAL.get(rahu_rashi, 'navigating genuinely new territory without the fluency you already have in other areas of life')}. The discomfort you feel around this isn't a sign something's wrong. It's usually the opposite — it's what growth into real new territory actually feels like while it's happening.",
            "sources": [f"Vedic Astrology: Rahu in {rahu_sk}"],
        })
    if lw_shadow:
        shadow_list.append({
            "text": f"Gate {lw_gate}'s Shadow frequency is {lw_shadow}, and it's worth understanding this correctly: it isn't a character flaw, and it isn't the enemy. It's the doorway. The Gift of {lw_gift} you actually want is sitting on the other side of being honest with yourself about when {lw_shadow} is running the show — not fighting it, just noticing it clearly, out loud if that's what it takes.",
            "sources": [f"Gene Keys: Gate {lw_gate} ({lw_name})"],
        })
    if comm_avoid:
        shadow_list.append({
            "text": f"There's a specific pattern in how you communicate worth naming plainly: {comm_avoid}. This usually isn't a conscious choice — it tends to sneak in through whatever parts of your design are wide open, picking up pressure from whoever's in the room with you, until it can start to feel like it's genuinely yours. Once you can catch it happening in real time, most of the actual work is already done.",
            "sources": [f"Communication Profile: {comm_arch}", "Human Design: open center architecture"],
        })

    # Complete Synthesis paragraph
    complete_text = (
        f"Here's what it looks like when you step back and look at the whole picture instead of any one piece of it. "
        f"Five systems — Numerology, Western astrology, Human Design, Vedic astrology, and Gene Keys — were each calculated separately from "
        f"the exact same birth data, and every one of them lands on some version of the same theme: {lp_theme}. "
        f"That's not a role you sat down and picked. It's closer to a signal that keeps showing up in your life whether you're actively "
        f"listening for it or not. "
        f"Your {sun} Sun keeps growing more fully into itself with each year that passes, the way it's meant to. "
        f"As a {hd_type}, the path that actually works for you opens specifically through {strategy.lower()} — not by pushing harder, "
        f"not by out-thinking the situation, but specifically through that one mechanism, because that's how your particular design is "
        f"built to operate. "
        f"Your Rahu in {rahu_sk} points toward the specific hunger this lifetime is growing you into — the kind of want that doesn't fully "
        f"settle until you've actually lived inside it for a while, not just thought about it. "
        f"Gate {lw_gate} ({lw_name}) and its Gift of {lw_gift} are the frequency you're here to put into the world, in whatever form your "
        f"actual life happens to take. "
        f"You're currently moving through a {mahadasha} Mahadasha — the specific chapter your life is asking you to focus on right now — "
        f"and underneath all of it, your Atmakaraka is {atmakaraka}, the planet carrying your soul's deepest, quietest lesson, the one "
        f"running underneath every surface theme in this reading. "
        f"None of this ended up in five unrelated systems by accident. It was written once, at a single moment of birth, and five completely "
        f"different traditions — working independently, with no knowledge of each other — each found their own way to describe the same "
        f"person. That kind of agreement isn't a curiosity to file away. It's the clearest evidence a reading like this can offer that what "
        f"you're looking at here is actually you."
    )
    complete_sources = [
        f"Numerology: Life Path {lp} ({lp_arch}) · Expression {expr} · Soul Urge {soul}",
        f"Western Astrology: {sun} Sun · {moon} Moon · {asc} Ascendant · {dom_elem or 'balanced'} element",
        f"Human Design: {hd_type} · {strategy} · Profile {profile_hd} · {auth_short} Authority",
        f"Vedic Astrology: Rahu {rahu_sk} / Ketu {ketu_sk} · {mahadasha} Mahadasha · Atmakaraka {atmakaraka}",
        f"Gene Keys: Gate {lw_gate} ({lw_name}) · Gift of {lw_gift} · Siddhi of {lw_siddhi}",
    ]

    return {
        "core_identity": {"text": core_id_text, "sources": core_id_sources},
        "strengths": strengths_list,
        "shadow": shadow_list,
        "complete_synthesis": {"text": complete_text, "sources": complete_sources},
    }


# ---- Helpers ----

def _jd_to_utc_str(jd: float) -> str:
    year, month, day, hour_frac = swe.revjul(jd, 1)  # 1 = Gregorian
    h = int(hour_frac)
    m = int((hour_frac - h) * 60)
    s = int(((hour_frac - h) * 60 - m) * 60)
    return f"{year:04d}-{month:02d}-{day:02d} {h:02d}:{m:02d}:{s:02d}"


def _ayanamsa_dms(degrees: float) -> str:
    deg = int(degrees)
    mf = (degrees - deg) * 60
    minute = int(mf)
    second = round((mf - minute) * 60)
    return f"{deg}°{minute:02d}'{second:02d}\""


def _parse_rashi(rashi_combined: str) -> tuple[str, str]:
    """Parse 'Mesha (Aries)' → ('Mesha', 'Aries')."""
    m = re.match(r"(.+?)\s+\((.+?)\)", rashi_combined)
    if m:
        return m.group(1), m.group(2)
    return rashi_combined, rashi_combined


def _num_obj(
    numerology: dict,
    key: str,
    archetype_map: dict[int, str] | None = None,
    karmic_map: dict[int, str] | None = None,
) -> dict:
    n = numerology[key]
    chain = numerology.get("reduction_chains", {}).get(key, [n])
    is_master = n in (11, 22, 33)
    reduction = " → ".join(str(x) for x in chain) if len(chain) > 1 else str(n)
    subtitle = ""
    if archetype_map:
        raw = chain[0] if chain else n
        if karmic_map and raw in karmic_map:
            subtitle = karmic_map[raw]
        else:
            subtitle = archetype_map.get(n, "")
    return {"number": n, "is_master": is_master, "reduction": reduction, "letters": "", "subtitle": subtitle}


def _longitude_from_placement(placement: dict) -> float:
    return placement["sign_index"] * 30.0 + placement["degrees_in_sign"]


# ---- Main adapter ----

def adapt(report: BlueprintReport) -> dict:
    """Translate BlueprintReport → frontend JSON contract."""

    # ---- profile ----
    profile = {
        "name": report.name,
        "birth_date": report.birth_date,
        "birth_time": report.birth_time,
        "birth_place": report.birth_place,
    }

    # ---- numerology (full) ----
    def _simple_num(n: int) -> dict:
        return {"number": n, "is_master": n in (11, 22, 33), "reduction": str(n), "letters": ""}

    numerology = {
        # Core identity
        "life_path":   _num_obj(report.numerology, "life_path",   LP_ARCHETYPES,   KARMIC_ARCHETYPES),
        "expression":  _num_obj(report.numerology, "expression",  EXPR_ARCHETYPES, KARMIC_ARCHETYPES),
        "soul_urge":   _num_obj(report.numerology, "soul_urge",   SOUL_ARCHETYPES, KARMIC_ARCHETYPES),
        "personality": _num_obj(report.numerology, "personality", PERS_ARCHETYPES),
        # Birth-date pillars
        "attitude":    _num_obj(report.numerology, "attitude",    ATT_ARCHETYPES),
        "birthday":    _num_obj(report.numerology, "birthday",    BDAY_ARCHETYPES),
        "generation":  _num_obj(report.numerology, "generation",  GEN_ARCHETYPES),
        # Derived numbers
        "maturity":    _num_obj(report.numerology, "maturity",    MAT_ARCHETYPES),
        "balance": _simple_num(report.numerology["balance"]),
        "subconscious_self": report.numerology["subconscious_self"],
        # Karmic patterns
        "karmic_debts": report.numerology["karmic_debts"],
        "karmic_lessons": report.numerology["karmic_lessons"],
        # Active timing
        "personal_year": report.numerology["personal_year"],
        "personal_month": report.numerology["personal_month"],
        "personal_day": report.numerology["personal_day"],
        # Life cycles
        "pinnacles": report.numerology["pinnacles"],
        "challenges": report.numerology["challenges"],
        "periods": report.numerology["periods"],
        "cycle_age_ranges": report.numerology["cycle_age_ranges"],
    }

    # ---- location / time context ----
    coords = report.coordinates
    utc_dt = report.utc_datetime

    tz = ZoneInfo(coords.timezone)
    local_dt = utc_dt.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz)
    offset = local_dt.utcoffset()
    total_min = int(offset.total_seconds() / 60)
    sign = "+" if total_min >= 0 else "-"
    abs_min = abs(total_min)
    utc_offset_str = f"{sign}{abs_min // 60:02d}:{abs_min % 60:02d}"

    location = {
        "resolved": coords.display_name,
        "latitude": coords.latitude,
        "longitude": coords.longitude,
        "timezone": coords.timezone,
    }
    time_info = {
        "local": local_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "utc": utc_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "utc_offset": utc_offset_str,
    }

    # ---- western astrology ----
    placements = report.western["placements"]
    retrogrades = set(report.western["dominant_retrogrades"])

    planets = []
    for body, data in placements.items():
        if body in ("Ascendant", "Midheaven"):
            continue
        lon = _longitude_from_placement(data)
        planets.append({
            "name": body,
            "glyph": BODY_GLYPHS.get(body, "?"),
            "sign_index": data["sign_index"],
            "sign": data["sign_name"],
            "sign_glyph": SIGN_GLYPHS.get(data["sign_name"], ""),
            "degrees_in_sign": data["degrees_in_sign"],
            "dms_string": data["dms_string"],
            "position": data["dms_string"],
            "longitude": lon,
            "retrograde": body in retrogrades,
        })

    house_cusps_raw = report.western.get("house_cusps", [])
    houses = [
        {
            "house": hc["house"],
            "sign_glyph": SIGN_GLYPHS.get(hc["sign_name"], ""),
            "sign": hc["sign_name"],
            "position": hc["dms_string"],
            "longitude": hc["longitude"],
        }
        for hc in house_cusps_raw
    ]

    asc_lon = _longitude_from_placement(placements["Ascendant"])
    mc_lon = _longitude_from_placement(placements["Midheaven"])
    dsc_lon = (asc_lon + 180) % 360
    ic_lon = (mc_lon + 180) % 360
    dsc_data = bridge_tropical_to_sign(dsc_lon)
    ic_data = bridge_tropical_to_sign(ic_lon)

    def _angle_obj(data: dict, lon: float) -> dict:
        return {
            "sign": data["sign_name"],
            "sign_glyph": SIGN_GLYPHS.get(data["sign_name"], ""),
            "position": data["dms_string"],
            "longitude": lon,
        }

    angles = {
        "ascendant": _angle_obj(placements["Ascendant"], asc_lon),
        "midheaven": _angle_obj(placements["Midheaven"], mc_lon),
        "descendant": _angle_obj(dsc_data, dsc_lon),
        "imum_coeli": _angle_obj(ic_data, ic_lon),
    }

    western = {
        "planets": planets,
        "houses": houses,
        "angles": angles,
        "element_balance": report.western["element_balance"],
        "modality_balance": report.western["modality_balance"],
        "lunar_phase_angle": report.western["lunar_phase_angle"],
        "lunar_phase_name": report.western["lunar_phase_name"],
        "aspects": report.western["aspects"],
    }

    # ---- vedic astrology ----
    sidereal = report.vedic["sidereal_longitudes"]
    rashis_raw = report.vedic["rashis"]   # {body: "Mesha (Aries)"}
    nakshatras = report.vedic["nakshatras"]
    ayanamsa_val = report.ledger.value("P3-8")

    grahas = []
    for body in _VEDIC_ORDER:
        if body not in rashis_raw or body == "Lagna":
            continue
        lon = sidereal.get(body, 0.0)
        rashi_combined = rashis_raw[body]
        rashi_sk, rashi_en = _parse_rashi(rashi_combined)

        deg_in = lon % 30
        d = int(deg_in)
        mf = (deg_in - d) * 60
        mi = int(mf)
        sc = round((mf - mi) * 60)
        position = f"{d}°{mi:02d}'{sc:02d}\" {rashi_sk}"

        nak = nakshatras.get(body, {})
        retrograde = body in retrogrades  # Rahu/Ketu always retrograde (mean nodes)
        if body in ("Rahu", "Ketu"):
            retrograde = True

        grahas.append({
            "name": body,
            "glyph": BODY_GLYPHS.get(body, "?"),
            "rashi": rashi_sk,
            "sign": rashi_en,
            "rashi_index": RASHI_NAMES.index(rashi_combined),
            "position": position,
            "nakshatra": nak.get("nakshatra_name", ""),
            "nakshatra_lord": nak.get("lord", ""),
            "pada": nak.get("pada", ""),
            "retrograde": retrograde,
        })

    # Lagna info
    lagna_combined = report.vedic["lagna"]
    lagna_sk, lagna_en = _parse_rashi(lagna_combined)
    lagna_lon = sidereal.get("Lagna", 0.0)
    ld = lagna_lon % 30
    ld_int = int(ld)
    lm = (ld - ld_int) * 60
    lm_int = int(lm)
    ls = round((lm - lm_int) * 60)
    lagna_nak = nakshatras.get("Moon", {})  # Lagna nakshatra not always computed separately

    vedic = {
        "ayanamsa_dms": _ayanamsa_dms(ayanamsa_val),
        "ayanamsa_name": "Lahiri",
        "lagna": {
            "rashi": lagna_sk,
            "sign": lagna_en,
            "rashi_index": RASHI_NAMES.index(lagna_combined),
            "position": f"{ld_int}°{lm_int:02d}'{ls:02d}\"",
            "nakshatra": report.vedic.get("moon_nakshatra", ""),
            "pada": lagna_nak.get("pada", ""),
        },
        "grahas": grahas,
        "starting_mahadasha": report.vedic.get("starting_mahadasha", ""),
    }

    # ---- human design ----
    hd = report.human_design

    def _build_activations(acts: dict) -> list:
        out = []
        for body, act in acts.items():
            gate = act["gate"]
            gk_info = GENE_KEYS.get(gate, ("Unknown", "", "", ""))
            zodiac = bridge_tropical_to_sign(act["longitude"])["dms_string"]
            out.append({
                "glyph": BODY_GLYPHS.get(body, "?"),
                "body": body,
                "notation": act["notation"],
                "gate": gate,
                "line": act["line"],
                "gate_name": gk_info[0],
                "zodiac": zodiac,
            })
        return out

    channels = [
        {
            "label": f"Gate {g1} – Gate {g2}",
            "centers": [GATE_TO_CENTER[g1], GATE_TO_CENTER[g2]],
            "gates": [g1, g2],
        }
        for g1, g2 in hd["defined_channels"]
    ]

    design_jd = report.ledger.value("P3-9")
    design_moment_utc = _jd_to_utc_str(design_jd)
    solar_arc = round(report.julian_day - design_jd, 2)

    profile_str = hd["profile"]
    profile_parts = [int(x) for x in profile_str.split("/")]
    profile_label = (
        f"{LINE_NAMES[profile_parts[0]]} / {LINE_NAMES[profile_parts[1]]}"
        if len(profile_parts) == 2
        else profile_str
    )

    hd_definition = hd["definition"]
    if not hd_definition.endswith(" Definition"):
        hd_definition = hd_definition + " Definition"

    human_design = {
        "type": hd["type"],
        "authority": HD_AUTHORITY_LABELS.get(hd["authority"], hd["authority"]),
        "profile": profile_str,
        "profile_label": profile_label,
        "definition": hd_definition,
        "strategy": hd["strategy"],
        "signature": hd["signature"],
        "not_self": hd["not_self_theme"],
        "defined_centers": hd["defined_centers"],
        "open_centers": hd["open_centers"],
        "active_gates": hd["active_gates"],
        "channels": channels,
        "personality": {"activations": _build_activations(hd["personality_activations"])},
        "design": {
            "activations": _build_activations(hd["design_activations"]),
            "moment_utc": design_moment_utc,
            "solar_arc": str(solar_arc),
        },
    }

    # ---- gene keys ----
    gk = report.gene_keys

    # Build gate → sources list from HD activations. Includes each source's own
    # gate.line notation — a gate can be activated by multiple bodies at different
    # lines (e.g. Saturn and Neptune both landing in the same gate), so the line
    # isn't collapsed into a single value here the way hologenetic_profile does.
    gate_sources: dict[int, list[str]] = {}
    for body, act in hd["personality_activations"].items():
        gate_sources.setdefault(act["gate"], []).append(f"Personality {body} ({act['notation']})")
    for body, act in hd["design_activations"].items():
        gate_sources.setdefault(act["gate"], []).append(f"Design {body} ({act['notation']})")

    def _build_sphere_entries(entries: list[dict]) -> list[dict]:
        out = []
        for entry in entries:
            sphere = entry["sphere"]
            gate = entry["gate"]
            gk_info = GENE_KEYS.get(gate, ("Unknown", "Unknown", "Unknown", "Unknown"))
            out.append({
                "sphere": sphere,
                "source": SPHERE_SOURCE.get(sphere, sphere),
                "notation": entry["notation"],
                "gene_key": gate,
                "name": gk_info[0],
                "meaning": SPHERE_MEANING.get(sphere, ""),
                "shadow": gk_info[1],
                "gift": gk_info[2],
                "siddhi": gk_info[3],
                "sources": gate_sources.get(gate, []),
            })
        return out

    activation_sequence = _build_sphere_entries(gk["activation_sequence"])
    venus_sequence = _build_sphere_entries(gk.get("venus_sequence", []))
    pearl_sequence = _build_sphere_entries(gk.get("pearl_sequence", []))

    all_keys = []
    for gate_num, key_data in sorted(gk["hologenetic_profile"].items()):
        gk_info = GENE_KEYS.get(gate_num, ("Unknown", "Unknown", "Unknown", "Unknown"))
        all_keys.append({
            "gene_key": gate_num,
            "name": gk_info[0],
            "shadow": gk_info[1],
            "gift": gk_info[2],
            "siddhi": gk_info[3],
            "sources": gate_sources.get(gate_num, []),
        })

    gene_keys = {
        "activation_sequence": activation_sequence,
        "venus_sequence": venus_sequence,
        "pearl_sequence": pearl_sequence,
        "all_keys": all_keys,
    }

    # ---- communication ----
    communication = report.communication or {}

    # ---- section summaries (deterministic, cross-system) ----
    summaries = _section_summaries(report)

    # ---- chart standouts & synchronicities (deterministic, cross-system) ----
    standouts = _chart_standouts(report)

    # ---- synthesis ----
    headlines = report.synthesis["headlines"]
    n_h = headlines["numerology"]
    w_h = headlines["western"]
    h_h = headlines["human_design"]
    gk_h = headlines["gene_keys"]

    lifes_work_notation = gk_h.get("lifes_work", "1.1")
    try:
        lifes_work_gate = int(lifes_work_notation.split(".")[0])
        lifes_work_name = GENE_KEYS.get(lifes_work_gate, ("",))[0]
    except (ValueError, IndexError):
        lifes_work_name = ""

    archetypes = [
        {"label": "Life Path",    "value": str(n_h["life_path"]),  "detail": LP_ARCHETYPES.get(n_h["life_path"], ""),  "headline_key": "life_path"},
        {"label": "Sun Sign",     "value": w_h["sun_sign"],        "detail": SIGN_GLYPHS.get(w_h["sun_sign"], ""),    "headline_key": "sun_sign"},
        {"label": "Moon Sign",    "value": w_h["moon_sign"],       "detail": SIGN_GLYPHS.get(w_h["moon_sign"], ""),   "headline_key": "moon_sign"},
        {"label": "Ascendant",    "value": w_h["ascendant"],       "detail": SIGN_GLYPHS.get(w_h["ascendant"], ""),   "headline_key": "ascendant"},
        {"label": "HD Type",      "value": h_h["type"],            "detail": h_h["strategy"],                         "headline_key": "hd_type"},
        {"label": "Authority",    "value": h_h["authority"],       "detail": HD_AUTHORITY_LABELS.get(h_h["authority"], h_h["authority"]), "headline_key": "authority"},
        {"label": "Profile",      "value": h_h["profile"],         "detail": PROFILE_LABELS.get(h_h["profile"], ""),  "headline_key": "profile"},
        {"label": "Life's Work",  "value": lifes_work_notation,    "detail": lifes_work_name,                         "headline_key": "lifes_work"},
    ]

    # Build personalized headline descriptions for clickable chips
    headline_descs = _headline_descriptions(
        num=report.numerology,
        west=report.western,
        hd=report.human_design,
        ved=report.vedic,
        gk=report.gene_keys,
        comm=report.communication or {},
    )

    # ---- synthesis panels (cross-system identity narrative) ----
    _voice_comm = report.communication or {}
    _vs = _derive_voice(_voice_comm)["style"]
    syn_panels = _build_synthesis_panels(report, _vs)

    # ---- top 10 boxes (2 per system) ----
    _act_seq_t10 = report.gene_keys.get("activation_sequence", [])
    _lw_t10 = _act_seq_t10[0] if _act_seq_t10 else {}
    _evo_t10 = _act_seq_t10[1] if len(_act_seq_t10) > 1 else {}
    _lw_gate_t10 = _lw_t10.get("gate", 0)
    _evo_gate_t10 = _evo_t10.get("gate", 0)
    _lw_info_t10 = GENE_KEYS.get(_lw_gate_t10, ("", "", "", ""))
    _evo_info_t10 = GENE_KEYS.get(_evo_gate_t10, ("", "", "", ""))
    _hd_raw = report.human_design
    _auth_raw = _hd_raw.get("authority", "")
    _auth_short_t10 = _auth_raw.split(" (")[0] if "(" in _auth_raw else _auth_raw
    _sun_t10 = report.western.get("sun_sign", "")
    _moon_t10 = report.western.get("moon_sign", "")
    _ved_t10 = report.vedic or {}
    _moon_nak_t10 = _ved_t10.get("moon_nakshatra", "")
    _moon_rashi_t10 = _ved_t10.get("moon_rashi", "")
    _rahu_t10 = _ved_t10.get("rashis", {}).get("Rahu", "")
    _rahu_sk_t10 = _rahu_t10.split("(")[0].strip() if _rahu_t10 else ""
    _lp_t10 = report.numerology["life_path"]
    _soul_t10 = report.numerology["soul_urge"]

    top_10_boxes = [
        {"system": "Gene Keys",    "label": "Life's Work",    "value": _lw_t10.get("notation", f"Gate {_lw_gate_t10}"),   "subtitle": _lw_info_t10[0],  "detail": f"Gift: {_lw_info_t10[2]}",  "headline_key": "lifes_work"},
        {"system": "Gene Keys",    "label": "Evolution",      "value": _evo_t10.get("notation", f"Gate {_evo_gate_t10}"), "subtitle": _evo_info_t10[0], "detail": f"Gift: {_evo_info_t10[2]}", "headline_key": "gk_evolution"},
        {"system": "Human Design", "label": "Type",           "value": _hd_raw.get("type", ""),                           "subtitle": _hd_raw.get("strategy", ""), "detail": f"Strategy: {_hd_raw.get('strategy', '')}", "headline_key": "hd_type"},
        {"system": "Human Design", "label": "Authority",      "value": _auth_short_t10,                                   "subtitle": "Inner compass",             "detail": HD_AUTHORITY_LABELS.get(_auth_raw, _auth_raw), "headline_key": "authority"},
        {"system": "Numerology",   "label": "Life Path",      "value": str(_lp_t10),                                      "subtitle": LP_ARCHETYPES.get(_lp_t10, ""), "detail": "Birth date sum — life's recurring theme", "headline_key": "life_path"},
        {"system": "Numerology",   "label": "Soul Urge",      "value": str(_soul_t10),                                    "subtitle": "Soul Urge",                                      "detail": "Interior yearning — vowels of the birth name", "headline_key": "soul_urge"},
        {"system": "Vedic",        "label": "Moon Nakshatra", "value": _moon_nak_t10,                                     "subtitle": _moon_rashi_t10.split("(")[0].strip() if _moon_rashi_t10 else "", "detail": "Sidereal Moon mansion — emotional root", "headline_key": "vedic_moon_nak"},
        {"system": "Vedic",        "label": "Rahu Direction", "value": _rahu_sk_t10,                                      "subtitle": "Soul's growth vector",        "detail": "The hunger this incarnation came to integrate", "headline_key": "vedic_rahu"},
        {"system": "Western",      "label": "Sun Sign",       "value": _sun_t10,                                          "subtitle": SIGN_GLYPHS.get(_sun_t10, ""), "detail": "Tropical Sun — the conscious identity",  "headline_key": "sun_sign"},
        {"system": "Western",      "label": "Moon Sign",      "value": _moon_t10,                                         "subtitle": SIGN_GLYPHS.get(_moon_t10, ""), "detail": "Tropical Moon — the emotional architecture", "headline_key": "moon_sign"},
    ]

    # ---- core numbers 6 ----
    core_numbers_6 = [
        {"key": "life_path",     "label": "Life Path",    "number": numerology["life_path"]["number"],   "is_master": numerology["life_path"]["is_master"],   "subtitle": "Life Path",    "headline_key": "life_path"},
        {"key": "expression",    "label": "Expression",   "number": numerology["expression"]["number"],  "is_master": numerology["expression"]["is_master"],  "subtitle": "Expression",   "headline_key": "expression"},
        {"key": "soul_urge",     "label": "Soul Urge",    "number": numerology["soul_urge"]["number"],   "is_master": numerology["soul_urge"]["is_master"],   "subtitle": "Soul Urge",    "headline_key": "soul_urge"},
        {"key": "personality",   "label": "Personality",  "number": numerology["personality"]["number"], "is_master": numerology["personality"]["is_master"], "subtitle": "Personality",  "headline_key": None},
        {"key": "maturity",      "label": "Maturity",     "number": numerology["maturity"]["number"],    "is_master": numerology["maturity"]["is_master"],    "subtitle": "Maturity",     "headline_key": None},
        {"key": "personal_year", "label": "Personal Year","number": numerology["personal_year"],         "is_master": numerology["personal_year"] in (11, 22, 33), "subtitle": "Personal Year", "headline_key": None},
    ]

    # ---- celestial 6 (3 western + 3 vedic) ----
    _sun_planet = next((p for p in planets if p["name"] == "Sun"), {})
    _moon_planet = next((p for p in planets if p["name"] == "Moon"), {})
    _moon_graha = next((g for g in grahas if g["name"] == "Moon"), {})
    celestial_6 = {
        "western": [
            {"label": "Sun",       "glyph": _sun_planet.get("sign_glyph", ""),           "value": _sun_planet.get("sign", ""),        "sub": _sun_planet.get("position", ""),             "headline_key": "sun_sign"},
            {"label": "Moon",      "glyph": _moon_planet.get("sign_glyph", ""),          "value": _moon_planet.get("sign", ""),       "sub": _moon_planet.get("position", ""),            "headline_key": "moon_sign"},
            {"label": "Ascendant", "glyph": angles["ascendant"]["sign_glyph"],           "value": angles["ascendant"]["sign"],        "sub": angles["ascendant"]["position"],             "headline_key": "ascendant"},
        ],
        "vedic": [
            {"label": "Moon Nakshatra", "glyph": "☽",                                   "value": _moon_graha.get("nakshatra", ""),   "sub": f"{_moon_graha.get('rashi', '')} · Pada {_moon_graha.get('pada', '')}", "headline_key": "vedic_moon_nak"},
            {"label": "Lagna",          "glyph": "⊕",                                   "value": vedic["lagna"]["rashi"],            "sub": vedic["lagna"]["position"],                  "headline_key": None},
            {"label": "Rahu Direction", "glyph": "☊",                                   "value": _rahu_sk_t10,                      "sub": "Soul's growth vector",                      "headline_key": "vedic_rahu"},
        ],
    }

    # ---- HD summary (6 aspects) ----
    hd_summary_6 = [
        {"label": "Type",       "value": human_design["type"],                                       "sub": f"Strategy: {human_design['strategy']}",                           "headline_key": "hd_type"},
        {"label": "Authority",  "value": human_design["authority"].split(" (")[0],                   "sub": "Inner compass — how the body knows",                              "headline_key": "authority"},
        {"label": "Profile",    "value": human_design["profile"],                                    "sub": human_design["profile_label"],                                     "headline_key": "profile"},
        {"label": "Definition", "value": human_design["definition"].replace(" Definition", ""),      "sub": "Energy field architecture",                                       "headline_key": None},
        {"label": "Signature",  "value": human_design["signature"],                                  "sub": "The feeling when you're aligned",                                 "headline_key": None},
        {"label": "Not-Self",   "value": human_design["not_self"],                                   "sub": "The signal you've drifted from your design",                      "headline_key": None},
    ]

    # ---- GK summary (4 activation spheres) ----
    gk_summary_4 = [
        {
            "sphere": s["sphere"],
            "gate": s.get("gate", 0),
            "notation": s["notation"],
            "name": s["name"],
            "gift": s["gift"],
            "shadow": s["shadow"],
            "siddhi": s["siddhi"],
            "meaning": s["meaning"],
            "headline_key": "lifes_work" if s["sphere"] == "Life's Work" else ("gk_evolution" if s["sphere"] == "Evolution" else None),
        }
        for s in activation_sequence
    ]

    synthesis = {
        "paragraph": report.synthesis["paragraph"],
        "archetypes": archetypes,
        "top_10_boxes": top_10_boxes,
        "headline_descriptions": headline_descs,
        "section_summary": summaries["grand"],
        "core_identity": syn_panels["core_identity"],
        "synthesized_strengths": syn_panels["strengths"],
        "synthesized_shadow": syn_panels["shadow"],
        "complete_synthesis": syn_panels["complete_synthesis"],
        "core_numbers_6": core_numbers_6,
        "celestial_6": celestial_6,
        "hd_summary_6": hd_summary_6,
        "gk_summary_4": gk_summary_4,
    }

    # ---- attach section summaries ----
    numerology["section_summary"] = summaries["numerology"]
    western["section_summary"] = summaries["western"]
    vedic["section_summary"] = summaries["vedic"]
    human_design["section_summary"] = summaries["human_design"]
    gene_keys["section_summary"] = summaries["gene_keys"]
    if isinstance(communication, dict):
        communication["section_summary"] = summaries["communication"]

    # ---- attach chart standouts & synchronicities ----
    numerology["standouts"] = standouts["numerology"]
    western["standouts"] = standouts["western"]
    vedic["standouts"] = standouts["vedic"]
    human_design["standouts"] = standouts["human_design"]
    gene_keys["standouts"] = standouts["gene_keys"]

    # ---- assemble ----
    astrology = {
        "available": True,
        "reason": None,
        "location": location,
        "time": time_info,
        "western": western,
        "vedic": vedic,
        "human_design": human_design,
        "gene_keys": gene_keys,
        "communication": communication,
    }

    return {
        "profile": profile,
        "numerology": numerology,
        "astrology": astrology,
        "synthesis": synthesis,
        "big_five": report.big_five,
    }
