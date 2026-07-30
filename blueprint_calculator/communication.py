"""
Communication Style Engine — deterministic cross-system analysis.

Scores five cognitive axes from Human Design, Western Astrology, and
Numerology indicators, then derives an archetype and delivery preferences.
No LLM or probabilistic reasoning — every output traces to a specific
data point already computed in the pipeline.
"""
from __future__ import annotations

from .constants.hd_wheel import LINE_NAMES


def record_communication(numerology: dict, western: dict, hd: dict, gk: dict) -> dict:
    """Derive communication style profile from cross-system data."""

    # -- Extract indicators --
    defined_centers = set(hd.get("defined_centers", []))
    open_centers = set(hd.get("open_centers", []))
    profile = hd.get("profile", "")
    profile_lines = [int(x) for x in profile.split("/")] if "/" in profile else []
    channels_list = hd.get("defined_channels", [])
    channel_set = set(tuple(sorted(c)) for c in channels_list)

    mercury_sign = western.get("placements", {}).get("Mercury", {}).get("sign_name", "")
    element_balance = western.get("element_balance", {})
    dominant_element = max(element_balance, key=element_balance.get) if element_balance else None

    expression = numerology.get("expression", 5)
    life_path = numerology.get("life_path", 5)
    hd_type = hd.get("type", "Generator")

    # -- Step 1: Score cognitive axes --
    mental_certainty = (
        (2 if "Ajna" in defined_centers else 0) +
        (1 if "Head" in defined_centers else 0) +
        (1 if 1 in profile_lines else 0) +
        (1 if 5 in profile_lines else 0)
    )
    relational = (
        (1 if 2 in profile_lines else 0) +
        (1 if 4 in profile_lines else 0) +
        (1 if 6 in profile_lines else 0) +
        (1 if "Throat" in open_centers else 0)
    )
    experiential = (
        (2 if 3 in profile_lines else 0) +
        (1 if {(3, 60), (36, 35)} & channel_set else 0)
    )
    analytical = (
        (2 if mercury_sign in ("Virgo", "Capricorn", "Aquarius") else 0) +
        (1 if expression in (7, 9) else 0) +
        (1 if {(17, 62), (4, 63)} & channel_set else 0)
    )
    intuitive = (
        (2 if mercury_sign in ("Pisces", "Scorpio", "Cancer") else 0) +
        (1 if dominant_element == "Water" else 0) +
        (1 if "Ajna" in open_centers else 0)
    )

    scores = {
        "mental_certainty": mental_certainty,
        "relational": relational,
        "experiential": experiential,
        "analytical": analytical,
        "intuitive": intuitive,
    }

    # -- Step 2: Derive archetype --
    if analytical > intuitive and mental_certainty >= 3:
        archetype = "The Systematic Analyst"
        summary = "You process information through structured frameworks and proven methodologies. Rigorous mental infrastructure gives you the confidence to teach and be taught systematically."
        processing_style = "Linear, logical, evidence-based — you build understanding step by step, needing the 'why' behind each claim before you move on."
    elif intuitive > analytical and relational >= 2:
        archetype = "The Empathic Visionary"
        summary = "You receive information through feeling, pattern recognition, and relational context. Complex ideas land faster through metaphor and personal story than through data alone."
        processing_style = "Non-linear, holistic — you sense the whole before examining the parts, and trust gut-level knowing as valid intelligence."
    elif experiential >= 2:
        archetype = "The Trial-and-Error Pioneer"
        summary = "Your deepest learning comes through direct experience and iterative discovery. Abstract concepts crystallize only once you've touched them."
        processing_style = "Hands-on, kinesthetic — you need to try things to truly understand them. Failure is data, not defeat."
    elif relational >= 2 and (4 in profile_lines or 6 in profile_lines):
        archetype = "The Networked Strategist"
        summary = "You assimilate information through trusted relationships and community context. The right introduction opens more doors than the most thorough research."
        processing_style = "Social, collaborative — ideas come alive through dialogue and shared meaning rather than solo study."
    elif analytical > intuitive:
        archetype = "The Methodical Researcher"
        summary = "You approach information through careful analysis and systematic inquiry, preferring depth over breadth."
        processing_style = "Detailed, thorough — you need complete information before drawing conclusions and resist being rushed."
    elif intuitive > analytical:
        archetype = "The Intuitive Synthesizer"
        summary = "You integrate complex information through gut feeling and creative leaps, often arriving at conclusions before you can explain how."
        processing_style = "Associative, fluid — insights arrive whole rather than step by step; you trust internal knowing."
    elif mental_certainty >= 2:
        archetype = "The Conceptual Architect"
        summary = "You build mental models to understand and communicate complex systems. You teach best when you can map the territory first."
        processing_style = "Conceptual, abstract — you need the big picture before the details, and think best in frameworks."
    else:
        archetype = "The Adaptive Communicator"
        summary = "Your communication style is context-sensitive and fluidly responsive to the moment, the person, and the environment."
        processing_style = "Flexible, present-oriented — you read each situation and adapt accordingly rather than defaulting to a fixed approach."

    # -- Step 3: Delivery preferences --
    if life_path in (1, 8) or expression in (1, 8):
        tone = "Direct and authoritative — lead with the bottom line; context supports, not precedes."
    elif life_path in (2, 6, 9) or expression in (2, 6, 9):
        tone = "Warm and relational — anchor ideas in personal relevance and shared meaning."
    elif life_path in (11, 22, 33) or expression in (11, 22, 33):
        tone = "Visionary and inspiring — connect everyday detail to the larger purpose and possibility."
    else:
        tone = "Thoughtful and curious — balance information density with open-ended inquiry."

    if dominant_element == "Fire":
        fmt = "Stories, inspiration, and big-picture vision — lead with the WHY, not the HOW."
    elif dominant_element == "Earth":
        fmt = "Practical steps and tangible examples — ground every concept in real-world application."
    elif dominant_element == "Air":
        fmt = "Concepts, frameworks, and comparative analysis — maps and models over raw data."
    else:
        fmt = "Metaphor, emotional resonance, and narrative arc — feeling first, then facts."

    if "Sacral" in defined_centers:
        pacing = "Respond in the moment when the energy is alive — sustained focus follows the natural gut response."
    elif hd_type == "Manifestor":
        pacing = "Initiate when the impulse is clear — allow pauses between initiatives for the field to integrate."
    elif hd_type == "Projector":
        pacing = "Invite-driven depth over broad coverage — quality of understanding over speed of delivery."
    elif hd_type == "Reflector":
        pacing = "Slow, cyclical integration — revisit ideas over a lunar cycle before drawing final conclusions."
    else:
        pacing = "Follow the natural response rhythm — trust the gut-yes as the green light to proceed."

    avoids = []
    if "Head" in open_centers:
        avoids.append("information overload from unfiltered mental pressure")
    if "Ajna" in open_centers:
        avoids.append("premature certainty or fixed mental positions")
    if "Throat" in open_centers:
        avoids.append("speaking to fill silence — wait for genuine invitation")
    if "G" in open_centers:
        avoids.append("identity-based filtering — stay curious rather than fixed in self-concept")
    if "Sacral" in open_centers:
        avoids.append("pushing past natural energy limits — honor completion signals")
    if "Solar Plexus" in open_centers:
        avoids.append("emotionally amplified urgency — avoid decisions made in reactive states")
    avoid = avoids[0] if avoids else "No significant conditioning patterns identified"

    delivery = {"tone": tone, "format": fmt, "pacing": pacing, "avoid": avoid}

    # -- Step 4b: Cognitive weaknesses — each cites 2+ data points, specific to this combination --
    weakness_pool = []

    if "Head" in open_centers:
        if hd_type == "Projector":
            weakness_pool.append({
                "weakness": "Absorbing Others' Mental Agendas",
                "source": (
                    f"Open Head + {hd_type}: you pick up and amplify unresolved questions from those you guide, "
                    f"which can feel like your own insight-drive — the difference is whether the urgency arrived "
                    f"with a person or was already present when you were alone"
                ),
            })
        elif life_path in (11, 22, 33):
            weakness_pool.append({
                "weakness": "Master Frequency Amplifying Conditioned Pressure",
                "source": (
                    f"Open Head + Life Path {life_path}: master number carriers already run at elevated sensitivity — "
                    f"the open Head adds environmental mental-field amplification, making conditioned urgency feel "
                    f"like spiritual signal when it's often ambient noise"
                ),
            })
        else:
            weakness_pool.append({
                "weakness": "Obligation to Others' Unanswered Questions",
                "source": (
                    f"Open Head + {hd_type}: questions that enter awareness generate pressure to resolve them — "
                    f"the design test is distinguishing your own genuine inquiry from questions you've inherited "
                    f"from the people and environments around you"
                ),
            })

    if "Ajna" in open_centers:
        if expression in (7, 9):
            weakness_pool.append({
                "weakness": "Analysis Loop Without Stable Landing",
                "source": (
                    f"Open Ajna + Expression {expression}: the depth-drive of {expression} keeps analyzing, "
                    f"but the open Ajna can't hold a fixed position — conclusions shift, analysis continues, "
                    f"and sharing gets postponed indefinitely waiting for certainty that structurally can't arrive"
                ),
            })
        elif 1 in profile_lines:
            weakness_pool.append({
                "weakness": "Research Without Foundational Closure",
                "source": (
                    f"Open Ajna + Profile {profile} line 1 (Investigator): line 1 needs a solid foundation "
                    f"before moving forward, but the shifting Ajna makes the foundation feel perpetually incomplete — "
                    f"the next layer of research never quite answers the question underneath"
                ),
            })
        else:
            weakness_pool.append({
                "weakness": "Borrowed Certainty Under Social Pressure",
                "source": (
                    f"Open Ajna + {hd_type}: mental positions that form under environmental pressure can feel "
                    f"like genuine conviction — the tell is whether the position dissolves as soon as "
                    f"the pressure (person, setting, conversation) lifts"
                ),
            })

    if "Throat" in open_centers:
        if 5 in profile_lines:
            weakness_pool.append({
                "weakness": "Speaking to Fill the Projection",
                "source": (
                    f"Open Throat + Profile {profile} line 5 (Heretic): others project savior and "
                    f"solution-provider roles onto line 5, which activates the open Throat to respond — "
                    f"words that come from the pressure of others' expectations rather than from internal readiness"
                ),
            })
        elif 4 in profile_lines:
            weakness_pool.append({
                "weakness": "Relational Activation of Premature Expression",
                "source": (
                    f"Open Throat + Profile {profile} line 4 (Opportunist): relational orientation can "
                    f"bypass the body's wait signal, activating expression to sustain connection "
                    f"rather than because there's genuine internal readiness to speak"
                ),
            })
        else:
            weakness_pool.append({
                "weakness": "Variable Vocal Presence Without Consistency",
                "source": (
                    f"Open Throat + {hd_type}: expression is environment-dependent rather than self-initiated — "
                    f"powerful and recognized when genuinely invited, scattered or invisible when initiated outside of strategy"
                ),
            })

    if "Solar Plexus" in open_centers:
        if dominant_element == "Water":
            weakness_pool.append({
                "weakness": "Emotional Field Absorption Blurring Internal Signal",
                "source": (
                    f"Open Solar Plexus + Water-dominant chart: Water element brings natural emotional attunement; "
                    f"the open Solar Plexus amplifies that — the result is deep sensitivity that can blur "
                    f"the line between what you feel and what you've absorbed from the field around you"
                ),
            })
        else:
            weakness_pool.append({
                "weakness": "Emotionally Charged Decision Pressure",
                "source": (
                    f"Open Solar Plexus + {hd_type}: emotional states absorbed from the environment "
                    f"can generate urgency that feels like your own — the design functions best "
                    f"with a pause before commitment rather than deciding in the heat of the charge"
                ),
            })

    if 3 in profile_lines:
        weakness_pool.append({
            "weakness": "Trial Catalogued as Personal Failure",
            "source": (
                f"Profile {profile} line 3 (Martyr): the learning engine requires direct experience and "
                f"iteration by design — the shadow is attaching emotional weight to 'wrong turns,' "
                f"treating necessary discovery as personal inadequacy rather than design-aligned data"
            ),
        })

    if 5 in profile_lines:
        weakness_pool.append({
            "weakness": "Living Under Constant Projection Pressure",
            "source": (
                f"Profile {profile} line 5 (Heretic): others persistently project savior and "
                f"universal-problem-solver expectations — the gap between what others need you to be "
                f"and who you actually are is a real, ongoing, invisible energy cost"
            ),
        })

    if hd_type == "Projector" and "Sacral" in open_centers:
        weakness_pool.append({
            "weakness": "Borrowed Energy Ending Without Warning",
            "source": (
                f"Projector + open Sacral: you can access and amplify the Sacral energy of others, "
                f"which feels like genuine sustained capacity — until it abruptly runs out, because "
                f"it wasn't your energy base. The completion signal arrives faster and harder than expected"
            ),
        })

    if "Root" in open_centers:
        weakness_pool.append({
            "weakness": "Adrenalized Urgency Mistaken for Real Pressure",
            "source": (
                f"Open Root + {hd_type}: environmental time-pressure and stress get absorbed and amplified — "
                f"deadlines and urgency that belong to other people or the room can register as your own, "
                f"pushing decisions faster than the design actually needs"
            ),
        })

    if "Spleen" in open_centers:
        weakness_pool.append({
            "weakness": "Fear Absorbed as Instinct",
            "source": (
                f"Open Spleen + {hd_type}: other people's fears, health anxieties, and survival-level worries "
                f"are picked up and can read as your own instinctive caution — the tell is whether the fear "
                f"has a specific, present-tense source or is ambient and hard to pin down"
            ),
        })

    if "G" in open_centers:
        if life_path in (11, 22, 33):
            weakness_pool.append({
                "weakness": "Identity Instability Under a Heightened Signal",
                "source": (
                    f"Open G + Life Path {life_path}: master number carriers already run an elevated, "
                    f"visible frequency — the open G means direction and self-concept shift with whoever "
                    f"and wherever you are, so the vision can feel unstable in its container even when it's genuine"
                ),
            })
        else:
            weakness_pool.append({
                "weakness": "Direction Borrowed From Whoever's in the Room",
                "source": (
                    f"Open G + {hd_type}: sense of identity and life direction is environment-dependent — "
                    f"conviction that feels solid in one setting can dissolve entirely in another, "
                    f"making consistent long-term direction genuinely harder to hold onto alone"
                ),
            })

    if "Heart" in open_centers:
        weakness_pool.append({
            "weakness": "Overcommitting to Prove Worth",
            "source": (
                f"Open Heart + {hd_type}: willpower and self-worth get referenced externally — the open Heart "
                f"can drive over-promising or overworking to earn value that was never actually in question, "
                f"then resentment when the effort goes unacknowledged"
            ),
        })

    if 2 in profile_lines and "Throat" in defined_centers:
        weakness_pool.append({
            "weakness": "Called Out of Natural Hermit Rhythm",
            "source": (
                f"Profile {profile} line 2 (Hermit) with a defined Throat: the natural talent needs private "
                f"incubation time, but the defined Throat makes expression reliable and visible — others call "
                f"on you for that visible talent faster and more often than the line 2 rhythm actually wants"
            ),
        })

    weaknesses = weakness_pool[:5] if weakness_pool else [
        {"weakness": "No dominant conditioning vulnerabilities identified",
         "source": "Current configuration shows balanced open-center awareness across the profile"}
    ]

    # -- Step 4: Cognitive strengths — 2 obvious (single-system) + 1 non-obvious (cross-system) --
    strength_descriptions = {
        "mental_certainty": (
            "Structured Mental Processing",
            f"Defined {'Ajna ' if 'Ajna' in defined_centers else ''}{'and Head centers provide' if 'Head' in defined_centers else 'center provides'} consistent, reliable cognitive frameworks that others can count on",
        ),
        "relational": (
            "Relational Intelligence",
            f"Profile {profile} orientation attunes naturally to interpersonal dynamics — social context is data, not distraction",
        ),
        "experiential": (
            "Experiential Learning Drive",
            f"Profile line 3 creates deep knowledge through direct trial and iteration — each failure is a data point, not a verdict",
        ),
        "analytical": (
            "Analytical Depth",
            f"Mercury in {mercury_sign or 'analytical signs'} with Expression {expression} sharpens precision and logical structure — conclusions are earned, not assumed",
        ),
        "intuitive": (
            "Intuitive Pattern Recognition",
            f"Mercury in {mercury_sign or 'receptive signs'}{' in a Water-dominant chart' if dominant_element == 'Water' else ''} attunes to non-logical signals — you sense the whole before examining the parts",
        ),
    }

    top_strengths = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    strengths = [
        {"strength": strength_descriptions[k][0], "source": strength_descriptions[k][1], "is_obvious": True}
        for k, v in top_strengths
        if v > 0
    ]

    # Cross-system non-obvious strengths — earned by the combination, not readable from any single
    # system alone. Collects every combination that genuinely matches (capped at 2), rather than
    # stopping at the first one, so a client matching multiple rare combinations sees all of them.
    cross_strengths = []
    if "Ajna" in defined_centers and mercury_sign in ("Pisces", "Scorpio", "Cancer"):
        cross_strengths.append({
            "strength": "Structured Intuition — the Rare Synthesis",
            "source": (
                f"Defined Ajna (consistent cognitive framework) combined with Mercury in {mercury_sign} "
                f"(intuitive, non-linear signal): most people get one or the other. Your defined Ajna gives "
                f"a stable container to hold and translate what Mercury delivers non-logically. "
                f"This cross-system combination is rarely seen and almost never discussed."
            ),
            "is_obvious": False,
        })
    if life_path in (11, 22, 33) and ("Sacral" in defined_centers or "Solar Plexus" in defined_centers):
        anchor = "Sacral" if "Sacral" in defined_centers else "Solar Plexus"
        cross_strengths.append({
            "strength": "Master Frequency With Somatic Grounding",
            "source": (
                f"Life Path {life_path} (master number — elevated sensitivity and vision) combined with "
                f"defined {anchor} center (reliable physical anchor): most master-number carriers lack "
                f"a stable somatic home for the frequency they run. Your defined {anchor} gives it one. "
                f"The result is vision that can actually land in the body, not just circulate in the mind."
            ),
            "is_obvious": False,
        })
    if 4 in profile_lines and mercury_sign in ("Virgo", "Gemini", "Aquarius"):
        cross_strengths.append({
            "strength": "Network Intelligence Filtered by Precision",
            "source": (
                f"Profile line 4 (learns and influences through close relationships) combined with "
                f"Mercury in {mercury_sign} (analytical, precise): the line 4 typically gathers data "
                f"relationally — emotionally, contextually. Your Mercury strips that data to structure "
                f"in real time. You extract transferable pattern from conversation in a way few line 4s do."
            ),
            "is_obvious": False,
        })
    if dominant_element == "Fire" and expression in (7, 9):
        cross_strengths.append({
            "strength": "Visionary Drive Anchored by Rare Depth",
            "source": (
                f"Fire-dominant chart (fast, inspirational, action-oriented) combined with "
                f"Expression {expression} (depth, introspection, long-arc completion): most Fire communicators "
                f"run fast and shallow. The {expression} expression pulls you into sustained inquiry and "
                f"meaningful completion — which is unexpected from someone with a Fire signature and is "
                f"what makes your vision more than enthusiasm."
            ),
            "is_obvious": False,
        })
    if "Head" in open_centers and 3 in profile_lines:
        cross_strengths.append({
            "strength": "Pressure-Free Iteration — Learning Without Debt",
            "source": (
                f"Open Head (not bound by fixed questions or mental pressure) combined with "
                f"Profile line 3 (trial-and-error learning): the open Head means your trials don't need "
                f"to 'answer' a pre-existing question — you're not carrying a mental agenda into the experiment. "
                f"This makes your iteration faster and emotionally lighter than defined-Head pioneers, "
                f"who carry the weight of needing the experiment to close a loop."
            ),
            "is_obvious": False,
        })
    if analytical >= 2 and relational >= 2:
        cross_strengths.append({
            "strength": "Analytical Depth Delivered With Relational Warmth",
            "source": (
                f"High analytical score (Mercury in {mercury_sign or 'earth/air sign'}, Expression {expression}) "
                f"combined with high relational score (Profile {profile}): most precision-oriented communicators "
                f"lose the room with rigor. Most relational communicators sacrifice precision for connection. "
                f"Your combination holds both — the rare ability to be thorough and warm simultaneously."
            ),
            "is_obvious": False,
        })
    if "Ego" in defined_centers and hd_type in ("Projector", "Reflector"):
        cross_strengths.append({
            "strength": "Willpower Without the Type's Usual Push",
            "source": (
                f"Defined Ego/Heart center combined with {hd_type} (a non-Sacral, non-forcing type): "
                f"most defined-Ego people lead with will and drive it outward. Your {hd_type} strategy "
                f"means that willpower waits for invitation or the lunar cycle rather than pushing — "
                f"a rarer combination of genuine resolve and patience."
            ),
            "is_obvious": False,
        })

    if not cross_strengths:
        # Generic fallback — always find something cross-system
        cross_strengths.append({
            "strength": "Adaptive Intelligence Across Contexts",
            "source": (
                f"Life Path {life_path} (core purpose archetype) combined with HD Type {hd_type} "
                f"(energy and strategy) and Mercury in {mercury_sign or 'current sign'}: "
                f"the combination creates a communicator who can switch registers — technical to emotional, "
                f"big-picture to granular — without losing coherence. Consistency across contexts is rarer "
                f"than most people realize."
            ),
            "is_obvious": False,
        })

    strengths.extend(cross_strengths[:2])

    # -- Step 5: Key indicators (top 5 cross-system) --
    line_label_0 = LINE_NAMES.get(profile_lines[0], "") if profile_lines else ""
    line_label_1 = LINE_NAMES.get(profile_lines[1], "") if len(profile_lines) > 1 else ""

    key_indicators = []
    if mercury_sign:
        key_indicators.append({
            "system": "Western Astrology",
            "indicator": f"Mercury in {mercury_sign}",
            "implication": "Shapes raw cognitive wiring, communication style, and language pattern",
        })
    if profile:
        key_indicators.append({
            "system": "Human Design",
            "indicator": f"Profile {profile} ({line_label_0} / {line_label_1})" if line_label_1 else f"Profile {profile}",
            "implication": "Defines the social role, learning archetype, and interaction strategy",
        })
    if defined_centers:
        key_indicators.append({
            "system": "Human Design",
            "indicator": f"Defined: {', '.join(sorted(defined_centers))}",
            "implication": "Consistent, reliable energetic channels that others can count on",
        })
    key_indicators.append({
        "system": "Numerology",
        "indicator": f"Life Path {life_path} · Expression {expression}",
        "implication": "Core purpose and natural communication register encoded in birth data",
    })
    if dominant_element:
        key_indicators.append({
            "system": "Western Astrology",
            "indicator": f"{dominant_element} element dominant",
            "implication": "Informs preferred delivery medium, learning modality, and emotional register",
        })

    return {
        "archetype": archetype,
        "summary": summary,
        "processing_style": processing_style,
        "delivery": delivery,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "key_indicators": key_indicators[:5],
    }
