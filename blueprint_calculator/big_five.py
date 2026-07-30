"""
Big Five Traits Interpretive Layer — read-only mapping to existing blueprint data.

This layer consumes already-calculated Soul Blueprint output (Numerology, Human Design,
Gene Keys, Vedic Astrology, Western Astrology) and maps it to a Big Five-style trait
breakdown. NO calculations of its own. Only lookup and interpretation keying to values
the generator has already produced.

Every data point placed here passes a fixed four-question test before it's added:

  1. Fixed characteristic, or timing/sequence?
     Timing/sequence data (Personal Year, Pinnacles, Dashas, transits) is excluded
     outright — it describes an active season, not a standing trait, and does not
     belong in this section under any tier.
  2. Which trait does it actually describe (Agreeableness / Conscientiousness /
     Extraversion / Openness / Emotional Stability), independent of which system
     it comes from? If it doesn't clearly match one, it isn't placed — a trait is
     never padded with a data point that doesn't genuinely belong to it.
  3. Is it a Gene Keys shadow/gift/siddhi gate? If so it is not a standalone tier
     entry — it's a register modifier attached to whichever fixed (Tier 1) entry
     it philosophically conditions, because it describes which mode a trait is
     currently being run from, not a trait itself.
  4. Otherwise: does the source system frame it as operating consistently and
     hard to override (Tier 1 — Type, Authority, core number, defined/open
     center), as conditioning/shifting a Tier 1 default depending on context
     (Tier 2 — a placement like Venus/Mercury/Saturn, a Profile line, a
     secondary number like Personality), or as an underlying want/background
     temperament invisible until specifically activated (Tier 3 — Soul Urge,
     Moon/Nakshatra, Maturity number, Karmic Lesson)?
"""
from __future__ import annotations


# Gene Keys gate -> (name, shadow, gift, siddhi). Self-contained here (not imported
# from api_adapter.py) so this module has no dependency on the frontend translation
# layer. Used only for register-modifier notes (Question 4), never as a standalone entry.
_GENE_KEY_TEXT: dict[int, tuple[str, str, str, str]] = {
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


LOOKUP_TABLES = {
    # ── AGREEABLENESS ─────────────────────────────────────────────
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
    # Tier 2 — Profile conditions the HD Type default: odd lines (1,3,5) run more
    # independent/friction-prone, even lines (2,4,6) run more relationally responsive.
    "agreeableness_profile": {
        "1/3": {"technical": "Both lines odd. Foundation built through personal investigation, tested through trial and error, neither step defers to group consensus.", "plain": "Someone comfortable working things out for themselves and learning by doing, rather than automatically going along with what others think."},
        "1/4": {"technical": "Odd/even mix. Independent investigation paired with a fixed network of close ties for support.", "plain": "Independent-minded, but with a small, steady circle of people whose opinions actually do carry weight."},
        "2/4": {"technical": "Both lines even. Natural talent expressed through, and drawn out by, a trusted network.", "plain": "Comfortable going along with the pull of close friends and community, natural ability shows up most when someone else brings it out."},
        "2/5": {"technical": "Even/odd mix. Natural, private talent that gets projected upon and pulled into a practical fixer role.", "plain": "Prefers to be left alone but frequently gets pulled in by others expecting them to solve things, whether they agreed to that role or not."},
        "3/5": {"technical": "Both lines odd. Learns through direct trial and error, then gets projected upon as the practical answer to other people's problems.", "plain": "Learns by doing and making mistakes, but ends up being looked to by others for solutions regardless of whether they went looking for that role."},
        "3/6": {"technical": "Odd/even mix. Early trial-and-error experimentation maturing into a witnessed role-model phase.", "plain": "Learns through direct experience early on, then settles into being someone others look to as an example over time."},
        "4/6": {"technical": "Both lines even. Stable network foundation maturing into a role-model, observer phase.", "plain": "Relies on a close network early, and over time settles into being someone others watch and learn from."},
        "4/1": {"technical": "Even/odd mix. Network-dependent expression built on a foundation of independent investigation.", "plain": "Leans on close relationships to be effective, but what they bring to those relationships is built on their own independent groundwork."},
        "5/1": {"technical": "Odd-numbered lines (5 and 1) generally present as more independent or friction-prone rather than automatically relationally responsive.", "plain": "These two numbers together point toward someone comfortable standing apart from the group and forming his own conclusions, rather than automatically going along with what everyone else thinks."},
        "5/2": {"technical": "Odd/even mix. Practical fixer role projected from the outside, backed by a natural, private talent.", "plain": "Gets pulled into fixing things for others, but underneath that role is a natural gift that would rather not be disturbed."},
        "6/2": {"technical": "Both lines even. Role-model maturity built on natural, private talent.", "plain": "Comfortable being looked to as an example once trust is established, but at heart prefers their own natural space."},
        "6/3": {"technical": "Even/odd mix. Role-model maturity reached through direct trial-and-error experience.", "plain": "Becomes someone others look to as an example, but only after learning things the hard way first."},
    },

    # ── CONSCIENTIOUSNESS ────────────────────────────────────────
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
    # Tier 2 — Saturn placement conditions the Life Path/defined-centers default,
    # same category as Venus and Mercury placements elsewhere in this schema.
    "conscientiousness_saturn_sign": {
        "Aries": {"technical": "Saturn in a cardinal fire sign. Discipline built through direct, sometimes impatient, confrontation with obstacles.", "plain": "Discipline was likely forged by jumping straight at problems rather than waiting them out."},
        "Taurus": {"technical": "Saturn in its exaltation sign. Discipline expressed through patient, material persistence.", "plain": "Follow-through here is slow, steady, and very hard to knock off course once it's set."},
        "Gemini": {"technical": "Saturn in a mutable air sign. Discipline structured around information and communication.", "plain": "Consistency shows up most in how carefully they track details and follow through on what they said they'd communicate."},
        "Cancer": {"technical": "Saturn in its fall. Discipline structured around emotional caretaking, sometimes at real personal cost.", "plain": "Reliability often shows up as quietly holding things together for others, even when it's hard on them personally."},
        "Leo": {"technical": "Saturn in fixed fire. Discipline tied to sustained, visible personal effort and pride in the work.", "plain": "Follow-through is strongest when their effort is genuinely seen and respected."},
        "Virgo": {"technical": "Saturn in a sign it operates well in. Discipline expressed through precision and functional detail.", "plain": "Reliability shows up as getting the small details right, consistently."},
        "Libra": {"technical": "Saturn in its exaltation sign. Discipline structured around fairness and formal agreement.", "plain": "This person takes commitments and fair dealing seriously, and expects the same back."},
        "Scorpio": {"technical": "Saturn in a fixed water sign. Discipline built through enduring intense, often private, pressure.", "plain": "Their staying power was built by getting through genuinely hard, often unseen, periods."},
        "Sagittarius": {"technical": "Saturn in mutable fire. Discipline structured around belief systems and long-range meaning.", "plain": "Follow-through holds strongest when it's tied to something they genuinely believe in."},
        "Capricorn": {"technical": "Saturn in its own sign, carrying strong dignity; retrograde suggests discipline was internalized through early hardship rather than external teaching.", "plain": "His sense of discipline was shaped early, likely through hard experience rather than someone teaching it to him gently."},
        "Aquarius": {"technical": "Saturn in its traditional rulership. Discipline structured around principle and long-term systems.", "plain": "Reliability shows up as sticking to a system or set of principles, even under social pressure to bend."},
        "Pisces": {"technical": "Saturn in its detriment. Discipline built despite, rather than through, natural structure, often unevenly.", "plain": "Consistency doesn't come naturally here and has to be built deliberately, in fits and starts."},
    },
    # Tier 3 — Karmic Lesson numbers describe a capacity that has to be learned
    # through life circumstance rather than one that's innate; background until
    # circumstance activates it. Only fires when the number is actually missing
    # from this person's name.
    "conscientiousness_karmic_lesson": {
        "1": {"technical": "1 as a karmic lesson suggests self-directed initiative is a learned capacity, not a default trait.", "plain": "Taking the lead and trusting his own judgment is something this person has had to build through experience, not something that came naturally from day one."},
        "2": {"technical": "2 as a karmic lesson suggests patience and cooperative follow-through are learned rather than innate.", "plain": "Working steadily alongside others without pushing ahead alone is something he's had to develop deliberately."},
        "3": {"technical": "3 as a karmic lesson suggests sustained follow-through on creative or expressive work is learned rather than automatic.", "plain": "Finishing what he starts creatively hasn't always come easily, it's a discipline he's had to build."},
        "4": {"technical": "4 as a karmic lesson number suggests structured discipline is a learned capacity forced by life circumstance, not a default innate trait.", "plain": "This system flags steady, disciplined structure as something he specifically has to learn the hard way through life circumstances, not something that came naturally from day one."},
        "5": {"technical": "5 as a karmic lesson suggests consistent follow-through despite the pull toward change is learned rather than automatic.", "plain": "Staying the course when something new and tempting shows up is a discipline he's had to build deliberately."},
        "6": {"technical": "6 as a karmic lesson suggests sustained responsibility toward others is learned rather than automatic.", "plain": "Following through on commitments to the people around him is something he's had to work at, not something automatic."},
        "7": {"technical": "7 as a karmic lesson suggests disciplined depth and follow-through on investigation is learned rather than innate.", "plain": "Sticking with something long enough to actually understand it deeply hasn't always come naturally to him."},
        "8": {"technical": "8 as a karmic lesson suggests disciplined management of material responsibility is learned rather than innate.", "plain": "Consistently managing resources, money, or authority well is a skill he's had to build rather than one he was simply born with."},
        "9": {"technical": "9 as a karmic lesson suggests sustained follow-through in service of something larger than himself is learned rather than automatic.", "plain": "Staying consistent when the payoff serves other people more than himself is a discipline he's had to build over time."},
    },

    # ── EXTRAVERSION ─────────────────────────────────────────────
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
        "Capricorn": {"technical": "Earth sign, reserved presence, serious and structured. Capricorn Rising presents guarded, tested-before-open on first contact.", "plain": "On first meeting, people are more likely to read this person as reserved or measured than immediately warm or outgoing."},
        "Aquarius": {"technical": "Air sign, detached presence, intellectually engaged.", "plain": "This person engages intellectually while maintaining a degree of detachment."},
        "Pisces": {"technical": "Water sign, dreamy presence, empathetic and impressionable.", "plain": "This person has a soft, empathetic presence that picks up on everything."},
    },
    # Tier 2 — Personality number conditions the Rising sign's first-contact
    # default. This is the corrected home for the Personality number: it governs
    # first-impression presentation specifically, the same function Rising sign
    # serves from a different system, so it backs up or complicates that read,
    # it is not itself a primary signal and it is not about accommodation.
    "extraversion_personality": {
        "1": {"technical": "Personality 1 presents as self-contained and capable.", "plain": "This backs up the Rising sign read, he tends to come across as capable and independent before people get to know him well."},
        "2": {"technical": "Personality 2 presents as gentle and attentive on first contact.", "plain": "Before people get to know him, he tends to come across as soft-spoken and attentive to others."},
        "3": {"technical": "Personality 3 presents as expressive and animated on first contact.", "plain": "First impressions of him tend to be warm and lively."},
        "4": {"technical": "Personality 4 presents as steady and grounded on first contact.", "plain": "People tend to read him as solid and dependable before they know anything else about him."},
        "5": {"technical": "Personality 5 presents as energetic and restless on first contact.", "plain": "First impressions tend to pick up on a certain restlessness or magnetism."},
        "6": {"technical": "Personality 6 presents as warm and responsible on first contact.", "plain": "People tend to read him as caring and dependable right away."},
        "7": {"technical": "Personality 7 presents as reserved and observant on first contact.", "plain": "First impressions tend to pick up on a watchful, slightly private quality."},
        "8": {"technical": "Personality 8 presents as authoritative and capable on first contact.", "plain": "People tend to read him as someone who's clearly in command of himself."},
        "9": {"technical": "Personality 9 presents as warm and worldly on first contact.", "plain": "First impressions tend to be broad and welcoming."},
        "11": {"technical": "Personality 11 presents as intense and perceptive on first contact.", "plain": "People tend to sense something unusually perceptive about him right away, even if they can't name it."},
        "22": {"technical": "Personality 22 presents as quietly commanding on first contact.", "plain": "First impressions tend to carry an understated sense of scale or capability."},
        "33": {"technical": "Personality 33 presents as warm and nurturing on first contact.", "plain": "People tend to feel cared for almost immediately in his presence."},
    },

    # ── OPENNESS ─────────────────────────────────────────────────
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
    # Tier 2 — Mercury sign conditions the Expression-number default, same
    # category as Venus/Saturn placements elsewhere in this schema.
    "openness_mercury_sign": {
        "Aries": {"technical": "Mercury in cardinal fire. Quick, decisive thinking, jumps to conclusions fast.", "plain": "His mind moves fast and decides quickly, sometimes before fully exploring alternatives."},
        "Taurus": {"technical": "Mercury in fixed earth. Deliberate, concrete thinking, slow to change a formed opinion.", "plain": "He thinks things through carefully and, once he's settled on a view, doesn't shift it easily."},
        "Gemini": {"technical": "Mercury in its own sign. Naturally curious and quick to connect disparate ideas, supporting an investigative drive with genuine cognitive flexibility.", "plain": "His mind naturally jumps between ideas and connects things quickly, which supports his investigative streak."},
        "Cancer": {"technical": "Mercury in its detriment. Thinking colored by memory and feeling rather than pure logic.", "plain": "How he thinks about something is often shaped by how it feels, more than by cold analysis alone."},
        "Leo": {"technical": "Mercury in fixed fire. Confident, expressive thinking, opinions held with pride.", "plain": "He tends to state his views with confidence and doesn't love having them challenged."},
        "Virgo": {"technical": "Mercury in its rulership and exaltation. Precise, analytical, detail-oriented thinking.", "plain": "He naturally notices details and picks apart how things actually work."},
        "Libra": {"technical": "Mercury in cardinal air. Thinking oriented around weighing both sides and seeking fairness.", "plain": "He naturally sees multiple sides of an issue before settling anywhere."},
        "Scorpio": {"technical": "Mercury in its detriment. Probing, suspicious thinking, drawn to what's hidden.", "plain": "His mind is drawn to what's underneath the surface, and he doesn't take things at face value."},
        "Sagittarius": {"technical": "Mercury in its detriment. Big-picture, philosophical thinking, impatient with fine detail.", "plain": "He thinks in broad strokes and can lose patience with granular detail."},
        "Capricorn": {"technical": "Mercury in fixed earth. Structured, practical thinking oriented around what actually works.", "plain": "His thinking is practical and results-oriented, more concerned with what works than with theory."},
        "Aquarius": {"technical": "Mercury in fixed air. Original, systems-oriented thinking, drawn to unconventional ideas.", "plain": "He's drawn to unusual ideas and likes thinking about how systems fit together."},
        "Pisces": {"technical": "Mercury in its detriment. Intuitive, impressionistic thinking, less linear than most.", "plain": "His thinking moves more by impression and intuition than by strict step-by-step logic."},
    },
    # Tier 3 — Attitude number describes the surface-level approach to brand new
    # situations, background until a new situation actually activates it.
    "openness_attitude": {
        "1": {"technical": "Attitude 1 carries an independent, first-mover quality into new situations.", "plain": "Even his surface-level approach to brand-new situations leans toward taking the first step himself."},
        "2": {"technical": "Attitude 2 carries a cooperative, watch-and-adapt quality into new situations.", "plain": "His first instinct in something new is to read the room and adapt."},
        "3": {"technical": "Attitude 3 carries a curious, expressive quality into new situations.", "plain": "New situations tend to bring out his more playful, expressive side right away."},
        "4": {"technical": "Attitude 4 carries a cautious, structure-seeking quality into new situations.", "plain": "His first instinct with anything new is to look for the plan or the structure."},
        "5": {"technical": "Attitude 5 carries an eager, exploratory quality into new situations.", "plain": "Something new tends to bring out genuine excitement and a pull to dive in."},
        "6": {"technical": "Attitude 6 carries a responsible, caretaking quality into new situations.", "plain": "His first instinct in something new is often to check how it affects the people around him."},
        "7": {"technical": "Attitude 7 carries a reserved, evaluating quality into new situations.", "plain": "New situations get a quiet, watchful once-over before he engages."},
        "8": {"technical": "Attitude 8 carries an assertive, take-charge quality into new situations.", "plain": "His first instinct with anything new is to size it up in terms of who's in control."},
        "9": {"technical": "Attitude 9 carries a broad, accepting quality into new situations.", "plain": "New situations tend to be met with an open, big-picture kind of ease."},
        "11": {"technical": "Surface-level approach to new situations carries the same illuminator/mirror quality as the core Life Path number.", "plain": "Even his surface-level approach to brand-new situations carries that same mirror-like, perceptive quality as his core life path number."},
        "22": {"technical": "Attitude 22 carries a big-picture, structural quality into new situations.", "plain": "His first instinct in something new is to size up how it fits into a larger plan."},
        "33": {"technical": "Attitude 33 carries a nurturing, service-minded quality into new situations.", "plain": "New situations often get met first through the lens of how he can help."},
    },

    # ── EMOTIONAL STABILITY ──────────────────────────────────────
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
    # Tier 3 — Vedic Moon/Nakshatra describes the underlying emotional/mental
    # nature, background temperament rather than a moment-to-moment default.
    "emotional_stability_moon_nakshatra": {
        "Ashwini": {"technical": "Ketu-lorded nakshatra. Quick, instinctive emotional response, resets fast after disturbance.", "plain": "His emotional reactions come and go quickly, he doesn't tend to stay upset for long."},
        "Bharani": {"technical": "Venus-lorded nakshatra. Intense underlying emotional bearing, carries things deeply.", "plain": "Underneath the surface, he tends to feel things very intensely, even when it doesn't show."},
        "Krittika": {"technical": "Sun-lorded nakshatra. Sharp, purifying emotional nature, cuts through what isn't true.", "plain": "His underlying emotional temperament doesn't tolerate pretense well, he wants things named honestly."},
        "Rohini": {"technical": "Moon-lorded nakshatra, the Moon's own nakshatra. Deeply sensuous, growth-oriented emotional nature.", "plain": "His underlying emotional nature is nurturing and steady, drawn toward what helps things grow."},
        "Mrigashira": {"technical": "Mars-lorded nakshatra. Searching, restless underlying emotional temperament.", "plain": "Underneath, there's a quiet emotional restlessness, a sense of always looking for something."},
        "Ardra": {"technical": "Rahu-lorded nakshatra. Turbulent, transformative underlying emotional bearing.", "plain": "His deeper emotional nature tends to run through intense periods of upheaval that ultimately clear things out."},
        "Punarvasu": {"technical": "Jupiter-lorded nakshatra. Renewing, optimistic underlying emotional temperament.", "plain": "Underneath, there's a resilient optimism, a capacity to start over after things fall apart."},
        "Pushya": {"technical": "Saturn-lorded nakshatra, traditionally the most nourishing. Steady, protective underlying emotional nature.", "plain": "His deeper emotional temperament is nurturing and stable, he tends to look after others without much fuss."},
        "Ashlesha": {"technical": "Mercury-lorded nakshatra. Penetrating, guarded underlying emotional bearing.", "plain": "Underneath, he reads people and situations closely and doesn't let his guard down easily."},
        "Magha": {"technical": "Ketu-lorded nakshatra. Proud, ancestral underlying emotional bearing.", "plain": "There's a deep-seated need for his efforts and lineage to be respected."},
        "Purva Phalguni": {"technical": "Venus-lorded nakshatra. Pleasure-oriented, relaxed underlying emotional nature.", "plain": "His underlying temperament leans toward enjoyment and ease rather than tension."},
        "Uttara Phalguni": {"technical": "Sun-lorded nakshatra. Generous, dependable underlying emotional bearing.", "plain": "Underneath, there's a steady generosity, a wish to be genuinely useful to others."},
        "Hasta": {"technical": "Moon-lorded nakshatra. Skillful, self-soothing underlying emotional temperament.", "plain": "He tends to settle himself by doing, working with his hands or focus calms him."},
        "Chitra": {"technical": "Mars-lorded nakshatra. Vivid, image-conscious underlying emotional bearing.", "plain": "Underneath, there's real sensitivity to how things look and come together, aesthetically and otherwise."},
        "Swati": {"technical": "Rahu-lorded nakshatra. Independent, wind-like underlying emotional nature.", "plain": "His deeper emotional temperament values independence, he doesn't like being tied down."},
        "Vishakha": {"technical": "Jupiter-lorded nakshatra. Determined, goal-driven underlying emotional bearing.", "plain": "Underneath, there's a strong drive to get where he's going, even if it takes a while."},
        "Anuradha": {"technical": "Saturn-lorded nakshatra. Devoted, friendship-oriented underlying emotional nature.", "plain": "His deeper temperament is loyal, once he commits to people, that bond runs deep."},
        "Jyeshtha": {"technical": "Mercury-lorded nakshatra. Protective, authority-conscious underlying emotional bearing.", "plain": "Underneath, there's a protective instinct and real sensitivity around status and respect."},
        "Mula": {"technical": "Ketu-lorded nakshatra. Root-seeking, sometimes disruptive underlying emotional nature.", "plain": "His deeper temperament wants to get to the actual root of things, even if that means tearing something down first."},
        "Purva Ashadha": {"technical": "Venus-lorded nakshatra. Proud, invincible-feeling underlying emotional bearing.", "plain": "Underneath, there's a strong, hard-to-shake confidence in his own position."},
        "Uttara Ashadha": {"technical": "Sun-lorded nakshatra. Principled, enduring underlying emotional nature.", "plain": "His deeper temperament holds firm to what he believes is right, even under pressure."},
        "Shravana": {"technical": "Moon-lorded nakshatra. Listening, absorptive underlying emotional bearing.", "plain": "Underneath, he takes in a great deal from what people tell him, and it stays with him."},
        "Dhanishta": {"technical": "Mars-lorded nakshatra. Rhythmic, achievement-oriented underlying emotional nature.", "plain": "His deeper temperament likes momentum and visible progress."},
        "Shatabhisha": {"technical": "Rahu-lorded nakshatra. Private, healing-oriented underlying emotional bearing.", "plain": "Underneath, he tends to process difficulty alone before he lets anyone else in."},
        "Purva Bhadrapada": {"technical": "Jupiter-lorded nakshatra. Intense, transformation-seeking underlying emotional nature.", "plain": "His deeper temperament is drawn to intensity, ordinary steadiness alone doesn't fully satisfy him."},
        "Uttara Bhadrapada": {"technical": "Saturn-lorded nakshatra. Deep, quietly wise underlying emotional bearing.", "plain": "Underneath, there's a slow-moving depth, patient and not easily rattled."},
        "Revati": {"technical": "Mercury-lorded nakshatra, the final nakshatra. Gentle, protective, completion-oriented underlying emotional nature.", "plain": "His deeper temperament is nurturing and unhurried, with a quiet instinct to see things through to a caring close."},
    },
    # Tier 3 — Maturity number describes a background orientation that only
    # becomes visible in the second half of life, invisible until activated.
    "emotional_stability_maturity": {
        "1": {"technical": "Maturity 1 points toward growing independence and self-trust as an underlying later-life orientation.", "plain": "As life goes on, this points toward relying more and more on his own judgment for a sense of steadiness."},
        "2": {"technical": "Maturity 2 points toward growing reliance on partnership as an underlying later-life orientation.", "plain": "As life goes on, this points toward finding more of his stability through close relationships."},
        "3": {"technical": "Maturity 3 points toward growing self-expression as an underlying later-life orientation.", "plain": "As life goes on, this points toward finding more emotional steadiness through creative expression."},
        "4": {"technical": "Maturity 4 points toward growing structure and groundedness as an underlying later-life orientation.", "plain": "As life goes on, this points toward finding more stability through order and routine."},
        "5": {"technical": "Maturity 5 points toward growing need for freedom as an underlying later-life orientation.", "plain": "As life goes on, this points toward needing more room to move and change to feel steady."},
        "6": {"technical": "Maturity 6 points toward growing responsibility for others as an underlying later-life orientation.", "plain": "As life goes on, this points toward finding stability through caring for the people close to him."},
        "7": {"technical": "Maturity 7 points toward growing inward reflection as an underlying later-life orientation.", "plain": "As life goes on, this points toward needing more quiet and reflection to feel emotionally steady."},
        "8": {"technical": "Maturity 8 points toward growing command over material affairs as an underlying later-life orientation.", "plain": "As life goes on, this points toward finding stability through a stronger handle on resources and authority."},
        "9": {"technical": "Maturity 9 points toward growing universal concern as an underlying later-life orientation.", "plain": "As life goes on, this points toward finding stability through serving something bigger than himself."},
        "11": {"technical": "Maturity 11 points toward growing intuitive clarity as an underlying later-life orientation.", "plain": "As life goes on, this points toward drawing more of his stability from inner knowing rather than outside validation."},
        "22": {"technical": "Maturity 22 points toward growing large-scale purpose as an underlying later-life orientation.", "plain": "As life goes on, this points toward finding stability through building something that outlasts him."},
        "33": {"technical": "Maturity 33 points toward growing devotion to service as an underlying later-life orientation.", "plain": "As life goes on, this points toward finding his deepest stability through caring for others."},
    },
}


def _register_note(gate_notation: str, sphere_label: str) -> dict | None:
    """Build a Gene Keys register-modifier note (Question 4) from a gate.line notation
    string like '15.4'. Returns None if the gate can't be resolved — never fabricated."""
    if not gate_notation or "." not in gate_notation:
        return None
    try:
        gate = int(gate_notation.split(".")[0])
    except ValueError:
        return None
    if gate not in _GENE_KEY_TEXT:
        return None
    name, shadow, gift, siddhi = _GENE_KEY_TEXT[gate]
    return {
        "sphere": sphere_label,
        "gate": gate,
        "gate_name": name,
        "shadow": shadow,
        "gift": gift,
        "siddhi": siddhi,
        "technical": f"{sphere_label} Gate {gate} ({name}). Whether this is currently running from Shadow ({shadow}), "
                     f"Gift ({gift}), or Siddhi ({siddhi}) conditions how this trait actually shows up day to day — "
                     f"it is a register, not a fixed value.",
        "plain": f"This isn't fixed either way — whether he's currently coming from the harder {shadow.lower()} pattern "
                  f"or the more resourced {gift.lower()} pattern changes how this shows up day to day, and that can shift "
                  f"with circumstance rather than being locked in permanently.",
    }


def record_big_five(
    numerology: dict,
    human_design: dict,
    western: dict,
    gene_keys: dict | None = None,
    vedic: dict | None = None,
) -> dict:
    """
    Map existing blueprint data to Big Five traits.

    Returns dict with 5 traits, each containing list of entries (tier, system, field,
    value, technical, plain, and an optional register_note for Gene Keys-conditioned
    entries — see module docstring for the four-question placement test).
    """
    gene_keys = gene_keys or {}
    vedic = vedic or {}

    # Extract values
    expression = numerology.get("expression", 5)
    life_path = numerology.get("life_path", 5)
    soul_urge = numerology.get("soul_urge", 5)
    personality_num = numerology.get("personality", 5)
    attitude = numerology.get("attitude", 5)
    maturity = numerology.get("maturity", 5)
    karmic_lessons = numerology.get("karmic_lessons", [])

    hd_type = human_design.get("type", "Generator")
    authority = human_design.get("authority", "Sacral")
    profile = human_design.get("profile", "")
    defined_centers = set(human_design.get("defined_centers", []))

    western_placements = western.get("placements", {})
    venus_sign = western_placements.get("Venus", {}).get("sign_name", "")
    mercury_sign = western_placements.get("Mercury", {}).get("sign_name", "")
    saturn_sign = western_placements.get("Saturn", {}).get("sign_name", "")
    # Fix: rising sign is a plain top-level string (western["ascendant"]), not nested
    # under a non-existent "angles" key — the old path always silently returned "".
    rising_sign = western.get("ascendant", "")
    # Fix: retrograde is never stored on the placements dict itself (bridge_tropical_to_sign
    # returns only sign_index/sign_name/degrees_in_sign/dms_string). The correct source is
    # the dominant_retrogrades list built in western.py's record_western().
    saturn_retrograde = "Saturn" in western.get("dominant_retrogrades", [])

    moon_nakshatra = vedic.get("nakshatras", {}).get("Moon", {}).get("nakshatra_name", "")

    lifes_work_notation = gene_keys.get("lifes_work", "")
    purpose_notation = gene_keys.get("purpose", "")

    # Helper to add entry
    def add_entry(trait_entries, tier, system, field, value, tech=None, plain=None, register_note=None):
        entry = {
            "tier": tier,
            "system": system,
            "field": field,
            "value": value,
            "technical": tech or "",
            "plain": plain or "",
        }
        if register_note is not None:
            entry["register_note"] = register_note
        trait_entries.append(entry)

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

    # Tier 2: HD Profile (conditions HD Type's Tier 1 default, same category as a placement)
    if profile and profile in LOOKUP_TABLES["agreeableness_profile"]:
        entry = LOOKUP_TABLES["agreeableness_profile"][profile]
        add_entry(agreeableness_entries, 2, "human_design", "profile", profile,
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

    # Tier 1: Life Path (Life's Work Gate shadow/gift attaches here as a register
    # modifier — same core "output/what I'm here to do" theme, not a standalone entry)
    if str(life_path) in LOOKUP_TABLES["conscientiousness_life_path"]:
        entry = LOOKUP_TABLES["conscientiousness_life_path"][str(life_path)]
        register_note = _register_note(lifes_work_notation, "Life's Work")
        add_entry(conscientiousness_entries, 1, "numerology", "life_path", life_path,
                 tech=entry["technical"], plain=entry["plain"], register_note=register_note)

    # Tier 2: Saturn Sign
    if saturn_sign and saturn_sign in LOOKUP_TABLES["conscientiousness_saturn_sign"]:
        entry = LOOKUP_TABLES["conscientiousness_saturn_sign"][saturn_sign]
        tech = entry["technical"]
        plain = entry["plain"]
        if saturn_sign == "Capricorn" and saturn_retrograde:
            tech = "Saturn in its own sign, carrying strong dignity; retrograde suggests discipline was internalized through early hardship rather than external teaching."
            plain = "His sense of discipline was shaped early, likely through hard experience rather than someone teaching it to him gently."
        add_entry(conscientiousness_entries, 2, "western_astrology", "saturn_sign", saturn_sign,
                 tech=tech, plain=plain)

    # Tier 3: Karmic Lesson (only fires if actually missing from the name — background,
    # invisible until activated by circumstance, matches the Soul Urge/Moon/Maturity bucket)
    for lesson_num in karmic_lessons:
        key = str(lesson_num)
        if key in LOOKUP_TABLES["conscientiousness_karmic_lesson"]:
            entry = LOOKUP_TABLES["conscientiousness_karmic_lesson"][key]
            add_entry(conscientiousness_entries, 3, "numerology", "karmic_lessons", lesson_num,
                     tech=entry["technical"], plain=entry["plain"])

    # ── EXTRAVERSION ─────────────────────────────────────────────
    extraversion_entries = []

    # Tier 1: Rising Sign — the most direct first-contact presentation signal
    if rising_sign and rising_sign in LOOKUP_TABLES["extraversion_rising"]:
        entry = LOOKUP_TABLES["extraversion_rising"][rising_sign]
        add_entry(extraversion_entries, 1, "western_astrology", "rising_sign", rising_sign,
                 tech=entry["technical"], plain=entry["plain"])

    # Tier 2: Personality number — conditions/cross-checks the Rising sign's first-contact
    # default; this is a corrected fix — previously this entry was mislabeled "personality"
    # while actually pulling and looking up the Expression value. Now pulls the real
    # numerology.personality field against its own dedicated lookup table.
    if str(personality_num) in LOOKUP_TABLES["extraversion_personality"]:
        entry = LOOKUP_TABLES["extraversion_personality"][str(personality_num)]
        add_entry(extraversion_entries, 2, "numerology", "personality", personality_num,
                 tech=entry["technical"], plain=entry["plain"])

    # ── OPENNESS ─────────────────────────────────────────────────
    openness_entries = []

    # Tier 1: Ajna (defined vs open). Purpose Gate shadow/gift attaches here as a register
    # modifier — Purpose Gate's Judgment/Integrity axis maps directly onto fixed-vs-fluid
    # judgment, the same theme this Tier 1 entry already covers, not a standalone entry.
    purpose_register = _register_note(purpose_notation, "Purpose")
    if "Ajna" in defined_centers:
        add_entry(openness_entries, 1, "human_design", "defined_centers", "Ajna",
                 tech="Defined Ajna holds fixed conclusions more readily.",
                 plain="Once this person lands on a conclusion, they hold onto it firmly.",
                 register_note=purpose_register)
    else:
        add_entry(openness_entries, 1, "human_design", "open_centers", "Ajna",
                 tech="Open Ajna tends toward more fluid thinking.",
                 plain="This person tends to stay flexible in how they think.",
                 register_note=purpose_register)

    # Tier 1: Expression (novelty orientation)
    if str(expression) in LOOKUP_TABLES["openness_expression"]:
        entry = LOOKUP_TABLES["openness_expression"][str(expression)]
        add_entry(openness_entries, 1, "numerology", "expression", expression,
                 tech=entry["technical"], plain=entry["plain"])

    # Tier 2: Mercury Sign
    if mercury_sign and mercury_sign in LOOKUP_TABLES["openness_mercury_sign"]:
        entry = LOOKUP_TABLES["openness_mercury_sign"][mercury_sign]
        add_entry(openness_entries, 2, "western_astrology", "mercury_sign", mercury_sign,
                 tech=entry["technical"], plain=entry["plain"])

    # Tier 3: Attitude (surface-level approach to new situations — background until activated)
    if str(attitude) in LOOKUP_TABLES["openness_attitude"]:
        entry = LOOKUP_TABLES["openness_attitude"][str(attitude)]
        add_entry(openness_entries, 3, "numerology", "attitude", attitude,
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

    # Tier 2: Saturn retrograde — fixed extraction bug: was always reading False because
    # placements[...]["retrograde"] never exists; correct source is dominant_retrogrades.
    add_entry(emotional_entries, 2, "western_astrology", "saturn_retrograde", saturn_retrograde,
             tech="Saturn retrograde suggests discipline and emotional defense structures were internalized early, "
                  "through hardship, rather than externally taught." if saturn_retrograde
                  else "Saturn direct suggests more conventional development of discipline.",
             plain="This person's emotional resilience was likely built early, through hard experience rather than "
                   "someone teaching it to them gently." if saturn_retrograde
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

    # Tier 3: Vedic Moon Nakshatra (background emotional temperament)
    if moon_nakshatra and moon_nakshatra in LOOKUP_TABLES["emotional_stability_moon_nakshatra"]:
        entry = LOOKUP_TABLES["emotional_stability_moon_nakshatra"][moon_nakshatra]
        add_entry(emotional_entries, 3, "vedic_astrology", "moon_nakshatra", moon_nakshatra,
                 tech=entry["technical"], plain=entry["plain"])

    # Tier 3: Maturity number (background orientation, invisible until later life)
    if str(maturity) in LOOKUP_TABLES["emotional_stability_maturity"]:
        entry = LOOKUP_TABLES["emotional_stability_maturity"][str(maturity)]
        add_entry(emotional_entries, 3, "numerology", "maturity", maturity,
                 tech=entry["technical"], plain=entry["plain"])

    traits = {
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

    # Coverage check (structural recommendation): count fired entries per trait against
    # the number of rules this module defines for that trait, so a silently-broken
    # extraction (wrong key, case mismatch, null field) surfaces immediately instead of
    # quietly reading as "this client just doesn't have that data point" — every client
    # has a Saturn sign, a Personality number, a Rising sign, they are never missing.
    _RULE_COUNTS = {
        "agreeableness": 4,        # HD Type, Expression, Venus, Profile, Soul Urge (Profile only fires w/ valid combo)
        "conscientiousness": 3,    # centers, Life Path, Saturn sign (+ optional karmic lesson)
        "extraversion": 2,         # Rising, Personality
        "openness": 4,             # Ajna, Expression, Mercury, Attitude
        "emotional_stability": 5,  # Solar Plexus, Authority, Saturn retrograde, Heart, Moon Nakshatra (+ optional Maturity)
    }
    coverage = {}
    for key, data in traits.items():
        expected = _RULE_COUNTS.get(key, 0)
        fired = len(data["entries"])
        coverage[key] = {
            "fired": fired,
            "expected_minimum": expected,
            "under_covered": fired < expected,
        }
    traits["_coverage"] = coverage

    return traits
