"""Soul Blueprint synthesis.

Weaves the headline results of every engine — numerology, tropical
astrology, Human Design, and Gene Keys — into a single narrative
paragraph plus a compact archetype grid for the Summary tab.
"""

from __future__ import annotations

LIFE_PATH_THEMES = {
    1: "independent leadership and the drive to originate",
    2: "diplomacy, partnership, and intuitive sensitivity",
    3: "creative expression and communicative joy",
    4: "steady building, order, and devoted work",
    5: "freedom, versatility, and the appetite for change",
    6: "nurturing responsibility and harmonizing service",
    7: "analysis, introspection, and the search for deeper truth",
    8: "material mastery, ambition, and executive power",
    9: "humanitarian compassion and completion",
    11: "illumination, inspiration, and heightened intuition",
    22: "master building — turning grand visions into concrete form",
    33: "master teaching through compassion and healing service",
}

SIGN_TRAITS = {
    "Aries": "bold, initiating fire",
    "Taurus": "grounded, sensual steadiness",
    "Gemini": "curious, quicksilver intellect",
    "Cancer": "protective, deeply feeling instincts",
    "Leo": "radiant, wholehearted self-expression",
    "Virgo": "precise, service-oriented discernment",
    "Libra": "harmonizing, relational grace",
    "Scorpio": "penetrating, transformative depth",
    "Sagittarius": "expansive, truth-seeking optimism",
    "Capricorn": "disciplined, mountain-climbing mastery",
    "Aquarius": "innovative, future-facing vision",
    "Pisces": "porous, imaginative compassion",
}

TYPE_THEMES = {
    "Manifestor": "you are built to initiate — acting first and informing those in your impact field",
    "Generator": "you are built to respond — your sustainable life force lights up when the world brings the right work to you",
    "Manifesting Generator": "you are built to respond, then move fast — a multi-passionate life force that compresses steps",
    "Projector": "you are built to guide — seeing systems and people clearly, and thriving when your wisdom is recognized and invited",
    "Reflector": "you are built to mirror — sampling the community around you and needing a full lunar cycle for clarity",
}


def compose(numerology: dict, western: dict, human_design: dict, genekeys: dict) -> dict:
    """Build the Soul Blueprint narrative and archetype grid."""
    life_path = numerology["life_path"]["number"]
    expression = numerology["expression"]["number"]

    planets = {planet["name"]: planet for planet in western["planets"]}
    sun_sign = planets["Sun"]["sign"]
    moon_sign = planets["Moon"]["sign"]
    asc_sign = western["angles"]["ascendant"]["sign"]

    lifes_work = genekeys["activation_sequence"][0]

    paragraph = (
        f"Your Life Path {life_path} centers this blueprint on "
        f"{LIFE_PATH_THEMES.get(life_path, 'its own singular lesson')}, "
        f"while your Expression {expression} colors how that purpose speaks "
        f"through you. The sky refines the picture: a {sun_sign} Sun brings "
        f"{SIGN_TRAITS[sun_sign]}, a {moon_sign} Moon gives your inner world "
        f"{SIGN_TRAITS[moon_sign]}, and with {asc_sign} rising you meet life "
        f"through {SIGN_TRAITS[asc_sign]}. In Human Design you are a "
        f"{human_design['type']} with {human_design['authority']} authority — "
        f"{TYPE_THEMES[human_design['type']]} — carrying the "
        f"{human_design['profile']} profile of the {human_design['profile_label']}. "
        f"The Gene Keys name your Life's Work as Key {lifes_work['gene_key']} "
        f"({lifes_work['name']}): the journey from the Shadow of "
        f"{lifes_work['shadow']} into the Gift of {lifes_work['gift']}, opening "
        f"toward the Siddhi of {lifes_work['siddhi']}. Read together, the "
        f"numbers describe the path, the planets describe the weather, and the "
        f"bodygraph describes the vehicle — one blueprint seen from three angles."
    )

    archetypes = [
        {"label": "Life Path", "value": str(life_path), "detail": "Numerology"},
        {"label": "Sun", "value": sun_sign, "detail": planets["Sun"]["position"]},
        {"label": "Moon", "value": moon_sign, "detail": planets["Moon"]["position"]},
        {"label": "Ascendant", "value": asc_sign, "detail": western["angles"]["ascendant"]["position"]},
        {"label": "Type", "value": human_design["type"], "detail": human_design["strategy"]},
        {"label": "Authority", "value": human_design["authority"].split(" (")[0], "detail": "Human Design"},
        {"label": "Profile", "value": human_design["profile"], "detail": human_design["profile_label"]},
        {"label": "Life's Work", "value": f"GK {lifes_work['notation']}", "detail": lifes_work["gift"]},
    ]

    return {"paragraph": paragraph, "archetypes": archetypes}
