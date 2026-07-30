"""
Big Five Traits Interpretive Layer — read-only mapping to existing blueprint data.

This layer consumes already-calculated Soul Blueprint output (Numerology, Human Design,
Gene Keys, Vedic Astrology, Western Astrology) and maps it to a Big Five-style trait
breakdown. NO calculations of its own. Only lookup and interpretation keying to values
the generator has already produced.
"""
from __future__ import annotations


LOOKUP_TABLES = {
    "agreeableness_hd_type": {
        "Projector": {
            "technical": "Sets the behavioral default for how someone engages others. Projectors read as accommodating, responding when invited.",
            "plain": "This system says this person isn't built to force their way into things. They do their best work when someone else opens the door first, then they step in fully.",
        },
        "Generator": {
            "technical": "Generators read as responsive but can push back hard once engaged.",
            "plain": "This person tends to go along with things easily at first, but once they're invested, they push back firmly if something isn't right.",
        },
        "Manifesting Generator": {
            "technical": "Similar to Generator but with added speed and multi-tracking.",
            "plain": "This person often seems easy to work with across several things at once, but can change direction suddenly.",
        },
        "Manifestor": {
            "technical": "Manifestors read as least naturally agreeable, built to initiate unilaterally.",
            "plain": "This person is built to act on their own initiative rather than wait for permission or agreement from others.",
        },
        "Reflector": {
            "technical": "Reflectors mirror the energy of their environment, agreeableness is highly variable.",
            "plain": "This person's agreeableness shifts a lot depending on who they're around.",
        },
    },
    "agreeableness_expression": {
        "1": {"technical": "Leans toward independence, initiates rather than accommodates.", "plain": "This person's mind naturally wants to lead and decide for themselves."},
        "2": {"technical": "Leans strongly toward accommodation and diplomacy.", "plain": "This person's mind naturally looks for common ground."},
        "3": {"technical": "Leans toward sociable accommodation through charm.", "plain": "This person tends to smooth things over through warmth and communication."},
        "4": {"technical": "Leans toward practical cooperation within agreed structure.", "plain": "This person cooperates readily as long as the plan makes sense."},
        "5": {"technical": "Leans toward independence and resistance to being boxed in.", "plain": "This person resists being told what to do."},
        "6": {"technical": "Leans strongly toward accommodation through responsibility.", "plain": "This person tends to prioritize others' needs and will go along with things to keep peace."},
        "7": {"technical": "Leans toward independence, verifies before accepting.", "plain": "This person's mind wants to check things out before agreeing."},
        "8": {"technical": "Leans toward assertive independence around authority.", "plain": "This person tends to want to be the one steering things."},
        "9": {"technical": "Leans toward broad accommodation through empathy.", "plain": "This person tends to be accommodating in a compassionate way."},
        "11": {"technical": "Agreeableness filtered through whether something feels true.", "plain": "This person's mind wants to understand clearly before agreeing, social pressure alone won't move them."},
        "22": {"technical": "Leans toward practical cooperation in service of larger structure.", "plain": "This person is often willing to cooperate because it serves a bigger goal."},
        "33": {"technical": "Leans toward deep accommodation through service.", "plain": "This person has a strong pull to help and care for others."},
    },
    "agreeableness_venus": {
        "Aries": {"technical": "Direct and enthusiastic, less patient with prolonged accommodation.", "plain": "This person shows care directly but doesn't have much patience for going along with things they don't want."},
        "Taurus": {"technical": "Steady and loyal, agreeableness consistent once trust established.", "plain": "This person is reliably warm once they trust someone."},
        "Gemini": {"technical": "Socially adaptable, agreeableness through conversation.", "plain": "This person connects and gets along mostly through conversation and ideas."},
        "Cancer": {"technical": "Warm and protective toward people inside established bond.", "plain": "This person is warm and protective with people they already trust."},
        "Leo": {"technical": "Warm and generous, agreeableness depends on feeling valued.", "plain": "This person is warm and generous, especially when they feel appreciated."},
        "Virgo": {"technical": "Shows care through practical acts, functional rather than emotional.", "plain": "This person shows they care by doing helpful, practical things."},
        "Libra": {"technical": "Strongly values harmony and fairness, high natural agreeableness.", "plain": "This person places a high value on keeping things fair and peaceful."},
        "Scorpio": {"technical": "Intense and selective, agreeableness reserved for trusted circle.", "plain": "This person doesn't extend warmth widely, but what they do extend is intense."},
        "Sagittarius": {"technical": "Warm but values honesty over accommodation.", "plain": "This person is friendly but would rather be honest than simply agreeable."},
        "Capricorn": {"technical": "Reserved, shows care through commitment and reliability.", "plain": "This person shows they care through being dependable and committed."},
        "Aquarius": {"technical": "Values friendship and shared ideals over conventional accommodation.", "plain": "This person gets along with others through shared ideas and causes."},
        "Pisces": {"technical": "Deeply empathetic and accommodating, sometimes to point of self-dissolution.", "plain": "This person tends to be very accommodating, sometimes losing track of their own needs."},
    },
    "conscientiousness_life_path": {
        "1": {"technical": "Strong drive for structure and autonomy in execution.", "plain": "This person has built-in drive to organize and execute independently."},
        "2": {"technical": "Conscientiousness expressed through steadiness in relationships.", "plain": "This person is reliable in maintaining partnerships and agreements."},
        "3": {"technical": "Conscientiousness expressed through creative completion.", "plain": "This person's follow-through shows up strongest in creative projects."},
        "4": {"technical": "Strong built-in structure orientation, foundation-builder.", "plain": "This person has a natural inclination to build solid, organized structures."},
        "5": {"technical": "Conscientiousness expressed through thorough research.", "plain": "This person commits follow-through to thorough investigation."},
        "6": {"technical": "Conscientiousness expressed through responsible care.", "plain": "This person's follow-through centers on being there for others."},
        "7": {"technical": "Conscientiousness expressed through depth and verification.", "plain": "This person won't move forward without understanding things deeply."},
        "8": {"technical": "Strong built-in structure orientation, power and mastery focus.", "plain": "This person has a natural drive to build and control systems."},
        "9": {"technical": "Conscientiousness expressed through universal completion.", "plain": "This person's follow-through is broadest when serving everyone."},
        "11": {"technical": "Conscientiousness filtered through whether something feels true.", "plain": "This person commits follow-through only to what aligns with their vision."},
        "22": {"technical": "Strong built-in structure orientation, world-scale building.", "plain": "This person has powerful drive to build large, lasting structures."},
        "33": {"technical": "Conscientiousness expressed through service and healing.", "plain": "This person's follow-through centers on helping and caring."},
    },
    "extraversion_rising": {
        "Aries": {"technical": "Fire sign, immediate presence, direct approach.", "plain": "This person has an immediate, energetic presence that comes across right away."},
        "Taurus": {"technical": "Earth sign, steady presence, solid and grounded.", "plain": "This person comes across as solid and dependable from first contact."},
        "Gemini": {"technical": "Air sign, communicative, engages through conversation.", "plain": "This person engages socially through conversation and ideas."},
        "Cancer": {"technical": "Water sign, receptive presence, reads the room.", "plain": "This person reads the room and responds emotionally to what's needed."},
        "Leo": {"technical": "Fire sign, commanding presence, draws attention.", "plain": "This person naturally draws attention and commands the room."},
        "Virgo": {"technical": "Earth sign, analytical presence, observant and detail-focused.", "plain": "This person comes across as observant and focused on accuracy."},
        "Libra": {"technical": "Air sign, balanced presence, seeks connection.", "plain": "This person naturally seeks balance and connection in interactions."},
        "Scorpio": {"technical": "Water sign, intense presence, probing and deep.", "plain": "This person has an intense, probing presence that goes beneath surface."},
        "Sagittarius": {"technical": "Fire sign, expansive presence, outward-looking.", "plain": "This person has an expansive presence, drawn to exploration and ideas."},
        "Capricorn": {"technical": "Earth sign, reserved presence, serious and structured.", "plain": "This person comes across as serious and structured from first contact."},
        "Aquarius": {"technical": "Air sign, detached presence, intellectually engaged.", "plain": "This person engages intellectually while maintaining a degree of detachment."},
        "Pisces": {"technical": "Water sign, dreamy presence, empathetic and impressionable.", "plain": "This person has a soft, empathetic presence that picks up on everything."},
    },
    "openness_expression": {
        "1": {"technical": "Practical, proven methods orientation.", "plain": "This person tends toward what's already proven to work."},
        "2": {"technical": "Conventional, relationship-based orientation.", "plain": "This person prefers tried-and-true approaches within relationship."},
        "3": {"technical": "Creative novelty-seeking, experimental expression.", "plain": "This person is naturally drawn to new creative ideas and experiments."},
        "4": {"technical": "Concrete, proven-foundation orientation.", "plain": "This person wants to build on solid, proven ground."},
        "5": {"technical": "Strong novelty and exploration orientation.", "plain": "This person has a strong drive to explore and try new things."},
        "6": {"technical": "Relational continuity orientation, cautious with novelty.", "plain": "This person prefers what's familiar and trusted in relationships."},
        "7": {"technical": "Depth and exploration through investigation.", "plain": "This person explores deeply through research and analysis."},
        "8": {"technical": "Power and proven-method orientation.", "plain": "This person focuses on methods and systems that yield real results."},
        "9": {"technical": "Universal and broad-spectrum exploration.", "plain": "This person is open to many perspectives and approaches."},
        "11": {"technical": "Intuitive openness to what feels true.", "plain": "This person is open to ideas that resonate with their inner knowing."},
        "22": {"technical": "Openness to structures that serve a larger vision.", "plain": "This person is open to new structures that serve big-picture goals."},
        "33": {"technical": "Openness to approaches that serve others.", "plain": "This person is open to new ways of helping and caring."},
    },
    "emotional_stability_authority": {
        "Splenic": {
            "technical": "Real-time but non-repeating instinct, no memory trail.",
            "plain": "This person's gut instinct is accurate now, but doesn't leave a paper trail to reference later.",
        },
        "Emotional": {
            "technical": "Requires riding out emotional wave, clarity not available in moment.",
            "plain": "This person needs time for their feelings to settle before a decision is reliable.",
        },
        "Sacral": {
            "technical": "Reliable, repeatable gut-response system.",
            "plain": "This person has a dependable gut yes/no response they can trust in the moment.",
        },
        "Self-Projected": {
            "technical": "Requires externalized verbal processing for clarity.",
            "plain": "This person needs to talk something through out loud before they know how they feel.",
        },
        "Ego": {
            "technical": "Willpower-based stability, tied to genuine commitment.",
            "plain": "This person's stability is tied to their own will and desire.",
        },
        "Lunar": {
            "technical": "Requires full lunar cycle for reliable clarity.",
            "plain": "This person needs real time, up to a month, before a decision is fully reliable.",
        },
        "Mental/Environment": {
            "technical": "Clarity through external reference and environment.",
            "plain": "This person finds stability through understanding how things connect in the world around them.",
        },
    },
}


def record_big_five(
    numerology: dict,
    human_design: dict,
    western: dict,
) -> dict:
    """
    Map existing blueprint data to Big Five traits.

    Returns dict with 5 traits, each containing list of entries (tier, system, field, value, technical, plain).
    """

    # Extract values
    expression = numerology.get("expression", 5)
    life_path = numerology.get("life_path", 5)
    soul_urge = numerology.get("soul_urge", 5)

    hd_type = human_design.get("type", "Generator")
    authority = human_design.get("authority", "Sacral")
    defined_centers = set(human_design.get("defined_centers", []))
    open_centers = set(human_design.get("open_centers", []))

    western_placements = western.get("placements", {})
    venus_sign = western_placements.get("Venus", {}).get("sign_name", "")
    rising_sign = western.get("angles", {}).get("ascendant", {}).get("sign", "")
    saturn_retrograde = western_placements.get("Saturn", {}).get("retrograde", False)

    # Helper to add entry
    def add_entry(trait_entries, tier, system, field, value, lookup_key=None, tech=None, plain=None):
        if lookup_key is None:
            lookup_key = str(value)
        trait_entries.append({
            "tier": tier,
            "system": system,
            "field": field,
            "value": value,
            "technical": tech or "",
            "plain": plain or "",
        })

    # ── AGREEABLENESS ────────────────────────────────────────────
    agreeableness_entries = []

    # Tier 1: HD Type
    if hd_type in LOOKUP_TABLES["agreeableness_hd_type"]:
        entry = LOOKUP_TABLES["agreeableness_hd_type"][hd_type]
        add_entry(agreeableness_entries, 1, "human_design", "type", hd_type,
                 tech=entry["technical"], plain=entry["plain"])

    # Tier 1: Expression
    if str(expression) in LOOKUP_TABLES["agreeableness_expression"]:
        entry = LOOKUP_TABLES["agreeableness_expression"][str(expression)]
        add_entry(agreeableness_entries, 1, "numerology", "expression", expression,
                 tech=entry["technical"], plain=entry["plain"])

    # Tier 2: Venus Sign
    if venus_sign and venus_sign in LOOKUP_TABLES["agreeableness_venus"]:
        entry = LOOKUP_TABLES["agreeableness_venus"][venus_sign]
        add_entry(agreeableness_entries, 2, "western_astrology", "venus_sign", venus_sign,
                 tech=entry["technical"], plain=entry["plain"])

    # Tier 3: Soul Urge
    if str(soul_urge) in LOOKUP_TABLES["agreeableness_expression"]:
        entry = LOOKUP_TABLES["agreeableness_expression"][str(soul_urge)]
        add_entry(agreeableness_entries, 3, "numerology", "soul_urge", soul_urge,
                 tech=entry["technical"], plain=entry["plain"])

    # ── CONSCIENTIOUSNESS ────────────────────────────────────────
    conscientiousness_entries = []

    # Tier 1: Defined Sacral/Root
    has_sacral = "Sacral" in defined_centers
    has_root = "Root" in defined_centers
    if has_sacral or has_root:
        add_entry(conscientiousness_entries, 1, "human_design", "defined_centers",
                 "Sacral or Root",
                 tech="Defined Sacral or Root centers give sustainable, repeatable energy.",
                 plain="This person has real, dependable energy to draw on for getting things done.")
    else:
        add_entry(conscientiousness_entries, 1, "human_design", "defined_centers",
                 "neither",
                 tech="Open Sacral and Root means energy is inconsistent.",
                 plain="This person's energy for follow-through isn't automatic.")

    # Tier 1: Life Path
    if str(life_path) in LOOKUP_TABLES["conscientiousness_life_path"]:
        entry = LOOKUP_TABLES["conscientiousness_life_path"][str(life_path)]
        add_entry(conscientiousness_entries, 1, "numerology", "life_path", life_path,
                 tech=entry["technical"], plain=entry["plain"])

    # ── EXTRAVERSION ─────────────────────────────────────────────
    extraversion_entries = []

    # Tier 1: Rising Sign
    if rising_sign and rising_sign in LOOKUP_TABLES["extraversion_rising"]:
        entry = LOOKUP_TABLES["extraversion_rising"][rising_sign]
        add_entry(extraversion_entries, 1, "western_astrology", "rising_sign", rising_sign,
                 tech=entry["technical"], plain=entry["plain"])

    # Tier 2: Personality (Expression as first-impression)
    if str(expression) in LOOKUP_TABLES["agreeableness_expression"]:
        entry = LOOKUP_TABLES["agreeableness_expression"][str(expression)]
        add_entry(extraversion_entries, 2, "numerology", "personality", expression,
                 tech=entry["technical"], plain=entry["plain"])

    # ── OPENNESS ─────────────────────────────────────────────────
    openness_entries = []

    # Tier 1: Ajna (defined vs open)
    if "Ajna" in defined_centers:
        add_entry(openness_entries, 1, "human_design", "defined_centers", "Ajna",
                 tech="Defined Ajna holds fixed conclusions more readily.",
                 plain="Once this person lands on a conclusion, they hold onto it firmly.")
    else:
        add_entry(openness_entries, 1, "human_design", "open_centers", "Ajna",
                 tech="Open Ajna tends toward more fluid thinking.",
                 plain="This person tends to stay flexible in how they think.")

    # Tier 1: Expression (novelty orientation)
    if str(expression) in LOOKUP_TABLES["openness_expression"]:
        entry = LOOKUP_TABLES["openness_expression"][str(expression)]
        add_entry(openness_entries, 1, "numerology", "expression", expression,
                 tech=entry["technical"], plain=entry["plain"])

    # ── EMOTIONAL STABILITY ──────────────────────────────────────
    emotional_entries = []

    # Tier 1: Solar Plexus (defined vs open)
    if "Solar Plexus" in defined_centers:
        add_entry(emotional_entries, 1, "human_design", "defined_centers", "Solar Plexus",
                 tech="Defined Solar Plexus has consistent internal emotional wave.",
                 plain="This person has real emotional ups and downs, but those feelings are genuinely theirs.")
    else:
        add_entry(emotional_entries, 1, "human_design", "open_centers", "Solar Plexus",
                 tech="Open Solar Plexus means no fixed internal emotional truth.",
                 plain="This person tends to pick up and absorb whatever emotional energy is nearby.")

    # Tier 1: Authority
    if authority in LOOKUP_TABLES["emotional_stability_authority"]:
        entry = LOOKUP_TABLES["emotional_stability_authority"][authority]
        add_entry(emotional_entries, 1, "human_design", "authority", authority,
                 tech=entry["technical"], plain=entry["plain"])

    # Tier 2: Saturn retrograde
    add_entry(emotional_entries, 2, "western_astrology", "saturn_retrograde", saturn_retrograde,
             tech="Saturn retrograde suggests discipline internalized early through hardship." if saturn_retrograde
                  else "Saturn direct suggests more conventional development of discipline.",
             plain="This person's emotional resilience was built early, through hard experience." if saturn_retrograde
                   else "This person's resilience likely developed in a more straightforward way.")

    # Tier 2: Heart (defined vs open)
    if "Heart" in defined_centers:
        add_entry(emotional_entries, 2, "human_design", "defined_centers", "Heart",
                 tech="Defined Heart gives consistent internal sense of worth.",
                 plain="This person has a steady internal sense of their own worth.")
    else:
        add_entry(emotional_entries, 2, "human_design", "open_centers", "Heart",
                 tech="Open Heart means worth referenced externally.",
                 plain="This person's sense of worth can shift depending on how people treat them.")

    return {
        "agreeableness": {
            "trait": "Agreeableness",
            "description": "Tendency toward compliance, accommodation, and harmony-seeking versus independence, challenge, and friction.",
            "entries": agreeableness_entries,
        },
        "conscientiousness": {
            "trait": "Conscientiousness",
            "description": "Tendency toward discipline, follow-through, organization, and reliability versus spontaneity.",
            "entries": conscientiousness_entries,
        },
        "extraversion": {
            "trait": "Extraversion",
            "description": "Tendency toward outward energy expenditure and social engagement versus inward focus.",
            "entries": extraversion_entries,
        },
        "openness": {
            "trait": "Openness",
            "description": "Tendency toward curiosity, abstract thinking, and novelty-seeking versus convention.",
            "entries": openness_entries,
        },
        "emotional_stability": {
            "trait": "Emotional Stability",
            "description": "Tendency toward steadiness under stress and internal regulation versus reactivity. (Inverse of Neuroticism.)",
            "entries": emotional_entries,
        },
    }
