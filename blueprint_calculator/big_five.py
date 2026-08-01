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

Voice: every "plain" entry speaks directly to the reader ("you"), states the
technical data point first, then goes in depth on what it actually means and
how it tends to show up in ordinary life — grounded in the same fact named in
"technical", never inventing anything beyond it.
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
            "technical": "Sets the behavioral default for how you engage others. Projectors read as accommodating, responding when invited.",
            "plain": "You're not built to force your way into things. Your best work tends to show up once someone else opens the door first — the gap between offering advice nobody asked for and being invited to actually give it is bigger for you than for most people, and that's exactly where you shine.",
        },
        "Generator": {
            "technical": "Generators read as responsive but can push back hard once engaged.",
            "plain": "You tend to go along with things easily at first — right up until you're genuinely invested, and then you'll push back firmly the moment something isn't right. People who've only seen your easygoing side are sometimes caught off guard the first time that firmness shows up.",
        },
        "Manifesting Generator": {
            "technical": "Similar to Generator but with added speed and multi-tracking.",
            "plain": "You can look easy to work with across several things at once, then suddenly change direction with little warning. That's not flakiness on your part — it's your gut recalibrating faster than most people's, and everyone else just needs a beat to catch up.",
        },
        "Manifestor": {
            "technical": "Manifestors read as least naturally agreeable, built to initiate unilaterally.",
            "plain": "You're built to act on your own initiative rather than wait around for permission or agreement — less 'raising your hand,' more 'already moving.' To people expecting you to check in first, that can read as less naturally accommodating than it actually is.",
        },
        "Reflector": {
            "technical": "Reflectors mirror the energy of their environment, agreeableness is highly variable.",
            "plain": "How agreeable you seem shifts a lot depending on who's actually in the room. You might feel completely at ease in one conversation and strangely unsettled in the next — that's not inconsistency, it's you accurately picking up on whatever's really going on around you.",
        },
    },
    "agreeableness_expression": {
        "1": {"technical": "Leans toward independence, initiates rather than accommodates.", "plain": "Your mind naturally wants to lead and decide for itself — you're probably the one in a group project who ends up setting the direction, even when nobody officially put you in charge."},
        "2": {"technical": "Leans strongly toward accommodation and diplomacy.", "plain": "Your mind naturally looks for common ground. In an argument between other people, you're often the one who spots the compromise everyone else is still too worked up to see."},
        "3": {"technical": "Leans toward sociable accommodation through charm.", "plain": "You tend to smooth things over through warmth and communication — you're the one who can defuse a tense room just by cracking the right joke at the right moment."},
        "4": {"technical": "Leans toward practical cooperation within agreed structure.", "plain": "You cooperate readily as long as the plan actually makes sense to you. Give you a clear reason for a request and you're in; skip the reason, and you'll quietly push back."},
        "5": {"technical": "Leans toward independence and resistance to being boxed in.", "plain": "You resist being told what to do, plain and simple. A rule that exists 'just because,' with no real reason behind it, is often the fastest way to make you want to break it."},
        "6": {"technical": "Leans strongly toward accommodation through responsibility.", "plain": "You tend to prioritize others' needs and will go along with things to keep the peace. You're often the one who ends up handling the thing nobody else wanted to deal with, just so it gets done."},
        "7": {"technical": "Leans toward independence, verifies before accepting.", "plain": "Your mind wants to check things out before agreeing to anything. You're the one who actually reads the fine print, even when everyone else already signed."},
        "8": {"technical": "Leans toward assertive independence around authority.", "plain": "You tend to want to be the one steering things. In most group settings, you gravitate toward whoever's actually making the calls — because that's usually where you feel most useful."},
        "9": {"technical": "Leans toward broad accommodation through empathy.", "plain": "You tend to be accommodating in a broad, compassionate way — the type who ends up rooting for the underdog in almost any situation, even ones that have nothing to do with you personally."},
        "11": {"technical": "Agreeableness filtered through whether something feels true.", "plain": "Your mind wants to understand something clearly before you'll agree to it, and social pressure alone won't move you. You can sit in a room where everyone else is nodding along and still hold out until it actually feels true to you."},
        "22": {"technical": "Leans toward practical cooperation in service of larger structure.", "plain": "You're often willing to cooperate on something you don't love in the moment, as long as you can see how it builds toward something bigger down the line."},
        "33": {"technical": "Leans toward deep accommodation through service.", "plain": "You have a strong pull to help and care for others. You're the one who ends up organizing the meal train, or checking in on the person everyone else quietly forgot about."},
    },
    "agreeableness_venus": {
        "Aries": {"technical": "Direct and enthusiastic, less patient with prolonged accommodation.", "plain": "You show care directly and fast, but you don't have much patience for going along with something you don't actually want. Think a quick, genuine 'I've got you' rather than a long, drawn-out gesture."},
        "Taurus": {"technical": "Steady and loyal, agreeableness consistent once trust established.", "plain": "You're reliably warm once someone's earned your trust — the kind of steady that doesn't waver even years later, but takes real time to build in the first place."},
        "Gemini": {"technical": "Socially adaptable, agreeableness through conversation.", "plain": "You connect with people mostly through conversation and shared ideas. You bond over a genuinely good talk more than over a shared activity."},
        "Cancer": {"technical": "Warm and protective toward people inside established bond.", "plain": "You're warm and protective with the people you already trust. Notice how differently you show up for family versus a stranger — that gap runs wider for you than it does for most people."},
        "Leo": {"technical": "Warm and generous, agreeableness depends on feeling valued.", "plain": "You're warm and generous, especially when you feel genuinely appreciated. Watch how much more freely you give once someone's actually said thank you."},
        "Virgo": {"technical": "Shows care through practical acts, functional rather than emotional.", "plain": "You show you care by doing something useful rather than saying something sentimental. Fixing the problem is your version of 'I love you.'"},
        "Libra": {"technical": "Strongly values harmony and fairness, high natural agreeableness.", "plain": "You place a high value on keeping things fair and peaceful. You're often the one in a group who can't fully relax until an unresolved tension actually gets addressed."},
        "Scorpio": {"technical": "Intense and selective, agreeableness reserved for trusted circle.", "plain": "You don't extend warmth widely, but what you do extend runs deep. You'd rather have three people you'd go to the wall for than thirty casual friends."},
        "Sagittarius": {"technical": "Warm but values honesty over accommodation.", "plain": "You're friendly, but you'd rather be honest than simply agreeable. You're the friend who'll actually tell someone the outfit doesn't work."},
        "Capricorn": {"technical": "Reserved, shows care through commitment and reliability.", "plain": "You show you care through being dependable and following through — showing up on time, keeping your word, being the one people can actually count on when it matters."},
        "Aquarius": {"technical": "Values friendship and shared ideals over conventional accommodation.", "plain": "You get along with people through shared ideas and causes more than through emotional closeness. You bond over what you're building together."},
        "Pisces": {"technical": "Deeply empathetic and accommodating, sometimes to point of self-dissolution.", "plain": "You tend to be very accommodating, sometimes to the point of losing track of your own needs. You can end up giving so much that you forget to check in with yourself."},
    },
    # Tier 2 — Profile conditions the HD Type default: odd lines (1,3,5) run more
    # independent/friction-prone, even lines (2,4,6) run more relationally responsive.
    "agreeableness_profile": {
        "1/3": {"technical": "Both lines odd. Foundation built through personal investigation, tested through trial and error, neither step defers to group consensus.", "plain": "You're comfortable working things out for yourself and learning by doing, rather than automatically going along with whatever the group thinks. You'd rather test it yourself than take someone else's word for it."},
        "1/4": {"technical": "Odd/even mix. Independent investigation paired with a fixed network of close ties for support.", "plain": "You're independent-minded, but you do have a small, steady circle of people whose opinions genuinely carry weight with you. Everyone else's input tends to matter a lot less."},
        "2/4": {"technical": "Both lines even. Natural talent expressed through, and drawn out by, a trusted network.", "plain": "You go along easily with the pull of close friends and community. Your natural ability tends to show up most when someone you trust draws it out of you, rather than when you're pushing it forward alone."},
        "2/5": {"technical": "Even/odd mix. Natural, private talent that gets projected upon and pulled into a practical fixer role.", "plain": "You'd honestly rather be left alone, but you frequently get pulled in by people expecting you to solve things for them, whether or not you signed up for that role."},
        "3/5": {"technical": "Both lines odd. Learns through direct trial and error, then gets projected upon as the practical answer to other people's problems.", "plain": "You learn by doing and making mistakes along the way, but you often end up being the person others look to for the answer — whether you went looking for that role or not."},
        "3/6": {"technical": "Odd/even mix. Early trial-and-error experimentation maturing into a witnessed role-model phase.", "plain": "Early on, you learn mostly through direct experience and trial and error. Over time, you settle into being someone others watch and learn from."},
        "4/6": {"technical": "Both lines even. Stable network foundation maturing into a role-model, observer phase.", "plain": "You lean on a close network early in life, and over time you naturally become someone others look up to and model themselves after."},
        "4/1": {"technical": "Even/odd mix. Network-dependent expression built on a foundation of independent investigation.", "plain": "You rely on close relationships to actually be effective, but what you bring to those relationships is built on your own independent groundwork."},
        "5/1": {"technical": "Odd-numbered lines (5 and 1) generally present as more independent or friction-prone rather than automatically relationally responsive.", "plain": "You're comfortable standing apart from the group and forming your own conclusions, rather than automatically going along with whatever everyone else thinks."},
        "5/2": {"technical": "Odd/even mix. Practical fixer role projected from the outside, backed by a natural, private talent.", "plain": "You get pulled into fixing things for other people, even though at heart you'd honestly rather be left alone with your own natural gift."},
        "6/2": {"technical": "Both lines even. Role-model maturity built on natural, private talent.", "plain": "You're comfortable being looked to as an example once trust is established, but at heart you prefer your own space more than the public role suggests."},
        "6/3": {"technical": "Even/odd mix. Role-model maturity reached through direct trial-and-error experience.", "plain": "You become someone others look up to as an example — but only after learning things the hard way yourself first, not from theory."},
    },

    # ── CONSCIENTIOUSNESS ────────────────────────────────────────
    "conscientiousness_life_path": {
        "1": {"technical": "Strong drive for structure and autonomy in execution.", "plain": "You've got a built-in drive to organize and execute things independently. Handed a messy project, your instinct is to build the plan yourself rather than wait for someone to hand you one."},
        "2": {"technical": "Conscientiousness expressed through steadiness in relationships.", "plain": "You're reliable in maintaining partnerships and agreements. If you say you'll be there, you're there — that steadiness is often the thing people count on most from you."},
        "3": {"technical": "Conscientiousness expressed through creative completion.", "plain": "Your follow-through shows up strongest in creative projects. Ask you to finish a spreadsheet and it might sit for a week; ask you to finish something you actually made, and you won't stop until it's right."},
        "4": {"technical": "Strong built-in structure orientation, foundation-builder.", "plain": "You have a natural inclination to build solid, organized structures. Where other people improvise, you're already building the system that makes the improvising unnecessary."},
        "5": {"technical": "Conscientiousness expressed through thorough research.", "plain": "You commit follow-through to thorough investigation. Before you'll fully commit to anything, you tend to want to have actually looked into it yourself."},
        "6": {"technical": "Conscientiousness expressed through responsible care.", "plain": "Your follow-through centers on being there for others. You're the one who remembers the appointment, the birthday, the thing someone else forgot they needed."},
        "7": {"technical": "Conscientiousness expressed through depth and verification.", "plain": "You won't move forward without understanding things deeply first. Skimming the surface of a topic tends to leave you more unsettled than not looking at it at all."},
        "8": {"technical": "Strong built-in structure orientation, power and mastery focus.", "plain": "You have a natural drive to build and control systems. Given enough time in any structure, you tend to end up running it, or at least understanding it better than most people inside it."},
        "9": {"technical": "Conscientiousness expressed through universal completion.", "plain": "Your follow-through is broadest when you're serving everyone, not just yourself. A project that benefits a wider group tends to hold your attention longer than one that only benefits you."},
        "11": {"technical": "Conscientiousness filtered through whether something feels true.", "plain": "You commit follow-through only to what actually aligns with your vision. Ask you to grind through something that doesn't feel genuinely true to you, and your energy for it drops off fast."},
        "22": {"technical": "Strong built-in structure orientation, world-scale building.", "plain": "You have a powerful drive to build large, lasting structures. Small, short-term tasks can bore you; the ones that hold your attention are the ones built to outlast you."},
        "33": {"technical": "Conscientiousness expressed through service and healing.", "plain": "Your follow-through centers on helping and caring for others. You'll push through exhaustion for someone you're actively supporting in a way you wouldn't for yourself alone."},
    },
    # Tier 2 — Saturn placement conditions the Life Path/defined-centers default,
    # same category as Venus and Mercury placements elsewhere in this schema.
    "conscientiousness_saturn_sign": {
        "Aries": {"technical": "Saturn in a cardinal fire sign. Discipline built through direct, sometimes impatient, confrontation with obstacles.", "plain": "Your discipline was likely forged by jumping straight at problems rather than waiting them out — you build patience by doing, not by sitting still."},
        "Taurus": {"technical": "Saturn in its exaltation sign. Discipline expressed through patient, material persistence.", "plain": "Your follow-through is slow, steady, and very hard to knock off course once it's actually set in motion. Other people burn out chasing the same goal you'll still be quietly working toward a year later."},
        "Gemini": {"technical": "Saturn in a mutable air sign. Discipline structured around information and communication.", "plain": "Your consistency shows up most in how carefully you track details and actually follow through on what you said you'd communicate — the email you promised to send, the update you said you'd give."},
        "Cancer": {"technical": "Saturn in its fall. Discipline structured around emotional caretaking, sometimes at real personal cost.", "plain": "Your reliability often shows up as quietly holding things together for others, even when it's genuinely hard on you personally — the one who keeps showing up even when nobody's asking how you're doing."},
        "Leo": {"technical": "Saturn in fixed fire. Discipline tied to sustained, visible personal effort and pride in the work.", "plain": "Your follow-through is strongest when your effort is genuinely seen and respected. Work in a vacuum where no one notices, and your discipline can quietly start to slip."},
        "Virgo": {"technical": "Saturn in a sign it operates well in. Discipline expressed through precision and functional detail.", "plain": "Your reliability shows up as getting the small details right, consistently — the typo other people miss, the step in the process nobody else double-checks."},
        "Libra": {"technical": "Saturn in its exaltation sign. Discipline structured around fairness and formal agreement.", "plain": "You take commitments and fair dealing seriously, and you expect the same back. Someone breaking their word to you tends to cost them more trust than it would with most people."},
        "Scorpio": {"technical": "Saturn in a fixed water sign. Discipline built through enduring intense, often private, pressure.", "plain": "Your staying power was built by getting through genuinely hard, often unseen periods — the kind of resilience nobody watched you develop, because you developed it alone."},
        "Sagittarius": {"technical": "Saturn in mutable fire. Discipline structured around belief systems and long-range meaning.", "plain": "Your follow-through holds strongest when it's tied to something you genuinely believe in. Ask you to grind at something meaningless, and your motivation drains fast."},
        "Capricorn": {"technical": "Saturn in its own sign, carrying strong dignity; retrograde suggests discipline was internalized through early hardship rather than external teaching.", "plain": "Your sense of discipline was shaped early, likely through real hard experience rather than someone gently teaching it to you. You built this one the hard way, which is exactly why it's so hard to shake."},
        "Aquarius": {"technical": "Saturn in its traditional rulership. Discipline structured around principle and long-term systems.", "plain": "Your reliability shows up as sticking to a system or a set of principles, even under real social pressure to bend. You'll hold the line after most people would've already caved."},
        "Pisces": {"technical": "Saturn in its detriment. Discipline built despite, rather than through, natural structure, often unevenly.", "plain": "Consistency doesn't come naturally to you here, and it has to be built deliberately, in fits and starts, rather than arriving as a given."},
    },
    # Tier 3 — Karmic Lesson numbers describe a capacity that has to be learned
    # through life circumstance rather than one that's innate; background until
    # circumstance activates it. Only fires when the number is actually missing
    # from this person's name.
    "conscientiousness_karmic_lesson": {
        "1": {"technical": "1 as a karmic lesson suggests self-directed initiative is a learned capacity, not a default trait.", "plain": "Taking the lead and trusting your own judgment isn't something that came naturally from day one — it's something you've had to build through real experience, not something handed to you."},
        "2": {"technical": "2 as a karmic lesson suggests patience and cooperative follow-through are learned rather than innate.", "plain": "Working steadily alongside others without pushing ahead alone is a skill you've had to develop deliberately, not one you started out with."},
        "3": {"technical": "3 as a karmic lesson suggests sustained follow-through on creative or expressive work is learned rather than automatic.", "plain": "Finishing what you start creatively hasn't always come easily — it's a discipline you've had to build on purpose, not something automatic."},
        "4": {"technical": "4 as a karmic lesson number suggests structured discipline is a learned capacity forced by life circumstance, not a default innate trait.", "plain": "Steady, disciplined structure is something you've specifically had to learn the hard way through life circumstances, not something that came naturally from day one."},
        "5": {"technical": "5 as a karmic lesson suggests consistent follow-through despite the pull toward change is learned rather than automatic.", "plain": "Staying the course when something new and tempting shows up is a discipline you've had to build deliberately, not one that came easily."},
        "6": {"technical": "6 as a karmic lesson suggests sustained responsibility toward others is learned rather than automatic.", "plain": "Following through on commitments to the people around you is something you've had to work at — it hasn't been automatic."},
        "7": {"technical": "7 as a karmic lesson suggests disciplined depth and follow-through on investigation is learned rather than innate.", "plain": "Sticking with something long enough to actually understand it deeply hasn't always come naturally to you — it's a muscle you've had to build."},
        "8": {"technical": "8 as a karmic lesson suggests disciplined management of material responsibility is learned rather than innate.", "plain": "Consistently managing resources, money, or authority well is a skill you've had to build, rather than one you were simply born with."},
        "9": {"technical": "9 as a karmic lesson suggests sustained follow-through in service of something larger than himself is learned rather than automatic.", "plain": "Staying consistent when the payoff serves other people more than it serves you is a discipline you've had to build over time, not one that arrived pre-installed."},
    },

    # ── EXTRAVERSION ─────────────────────────────────────────────
    "extraversion_rising": {
        "Aries": {"technical": "Fire sign, immediate presence, direct approach.", "plain": "You have an immediate, energetic presence that comes across right away — people know you've walked into the room before you've said a word."},
        "Taurus": {"technical": "Earth sign, steady presence, solid and grounded.", "plain": "You come across as solid and dependable from the first contact. Strangers tend to feel like they can lean on you before they've even learned your name."},
        "Gemini": {"technical": "Air sign, communicative, engages through conversation.", "plain": "You engage socially through conversation and ideas — the fastest way to your energy is a genuinely good back-and-forth, not shared silence."},
        "Cancer": {"technical": "Water sign, receptive presence, reads the room.", "plain": "You read the room and respond emotionally to what's needed. You often pick up on the mood of a space before you've consciously registered what's actually being said."},
        "Leo": {"technical": "Fire sign, commanding presence, draws attention.", "plain": "You naturally draw attention and command the room — even in a group of strangers, people's eyes tend to land on you first."},
        "Virgo": {"technical": "Earth sign, analytical presence, observant and detail-focused.", "plain": "You come across as observant and focused on accuracy. People sense, correctly, that you're the one who noticed the detail everyone else missed."},
        "Libra": {"technical": "Air sign, balanced presence, seeks connection.", "plain": "You naturally seek balance and connection in interactions — an unresolved tension in a room bothers you before anyone's actually named it."},
        "Scorpio": {"technical": "Water sign, intense presence, probing and deep.", "plain": "You have an intense, probing presence that goes beneath the surface. People often feel like you're seeing more of them than they intended to show."},
        "Sagittarius": {"technical": "Fire sign, expansive presence, outward-looking.", "plain": "You have an expansive presence, drawn to exploration and ideas — small talk bores you fast, but the right big question can hold you for hours."},
        "Capricorn": {"technical": "Earth sign, reserved presence, serious and structured. Capricorn Rising presents guarded, tested-before-open on first contact.", "plain": "On first meeting, people are more likely to read you as reserved or measured than immediately warm or outgoing. You tend to earn trust before you extend it, in either direction."},
        "Aquarius": {"technical": "Air sign, detached presence, intellectually engaged.", "plain": "You engage intellectually while keeping a degree of detachment — people can feel like they've had a great conversation with you and still not quite know you personally."},
        "Pisces": {"technical": "Water sign, dreamy presence, empathetic and impressionable.", "plain": "You have a soft, empathetic presence that picks up on everything. People often feel unusually understood by you within minutes of meeting you."},
    },
    # Tier 2 — Personality number conditions the Rising sign's first-contact
    # default. This is the corrected home for the Personality number: it governs
    # first-impression presentation specifically, the same function Rising sign
    # serves from a different system, so it backs up or complicates that read,
    # it is not itself a primary signal and it is not about accommodation.
    "extraversion_personality": {
        "1": {"technical": "Personality 1 presents as self-contained and capable.", "plain": "This backs up your Rising sign read: you tend to come across as capable and independent before people get to know you well."},
        "2": {"technical": "Personality 2 presents as gentle and attentive on first contact.", "plain": "Before people get to know you, you tend to come across as soft-spoken and attentive to others."},
        "3": {"technical": "Personality 3 presents as expressive and animated on first contact.", "plain": "First impressions of you tend to be warm and lively — people remember your energy before they remember what you said."},
        "4": {"technical": "Personality 4 presents as steady and grounded on first contact.", "plain": "People tend to read you as solid and dependable before they know anything else about you."},
        "5": {"technical": "Personality 5 presents as energetic and restless on first contact.", "plain": "First impressions of you tend to pick up on a certain restlessness or magnetism — people can sense you're not entirely still, even when you are."},
        "6": {"technical": "Personality 6 presents as warm and responsible on first contact.", "plain": "People tend to read you as caring and dependable right away, often before you've done anything to earn that read specifically."},
        "7": {"technical": "Personality 7 presents as reserved and observant on first contact.", "plain": "First impressions of you tend to pick up on a watchful, slightly private quality — people sense you're taking everything in before you say much."},
        "8": {"technical": "Personality 8 presents as authoritative and capable on first contact.", "plain": "People tend to read you as someone clearly in command of yourself, even in a room full of strangers."},
        "9": {"technical": "Personality 9 presents as warm and worldly on first contact.", "plain": "First impressions of you tend to be broad and welcoming — people feel included around you almost immediately."},
        "11": {"technical": "Personality 11 presents as intense and perceptive on first contact.", "plain": "People tend to sense something unusually perceptive about you right away, even if they can't quite name what tipped them off."},
        "22": {"technical": "Personality 22 presents as quietly commanding on first contact.", "plain": "First impressions of you tend to carry an understated sense of scale or capability — people sense there's more going on than what's on the surface."},
        "33": {"technical": "Personality 33 presents as warm and nurturing on first contact.", "plain": "People tend to feel cared for almost immediately in your presence, often before you've said anything specifically kind."},
    },

    # ── OPENNESS ─────────────────────────────────────────────────
    "openness_expression": {
        "1": {"technical": "Practical, proven methods orientation.", "plain": "You tend toward what's already proven to work. Given a choice between the trendy new method and the one with a track record, you'll usually pick the track record."},
        "2": {"technical": "Conventional, relationship-based orientation.", "plain": "You prefer tried-and-true approaches within relationship — the comfort of a familiar way of doing things with people you already trust matters more to you than novelty for its own sake."},
        "3": {"technical": "Creative novelty-seeking, experimental expression.", "plain": "You're naturally drawn to new creative ideas and experiments. A blank page excites you more than it intimidates you."},
        "4": {"technical": "Concrete, proven-foundation orientation.", "plain": "You want to build on solid, proven ground. An idea has to actually work in practice before you're willing to invest in it."},
        "5": {"technical": "Strong novelty and exploration orientation.", "plain": "You have a strong drive to explore and try new things — routine wears on you faster than it wears on most people."},
        "6": {"technical": "Relational continuity orientation, cautious with novelty.", "plain": "You prefer what's familiar and trusted in relationships. Change is easier for you to accept once it comes from someone you already know well."},
        "7": {"technical": "Depth and exploration through investigation.", "plain": "You explore deeply through research and analysis. A surface-level answer to a question you actually care about rarely satisfies you."},
        "8": {"technical": "Power and proven-method orientation.", "plain": "You focus on methods and systems that yield real results, over ideas that just sound good on paper."},
        "9": {"technical": "Universal and broad-spectrum exploration.", "plain": "You're open to many perspectives and approaches — you tend to genuinely enjoy hearing out a view you don't already hold."},
        "11": {"technical": "Intuitive openness to what feels true.", "plain": "You're open to ideas that resonate with your inner knowing, even ones you can't fully explain yet. The feeling of rightness matters as much to you as the logic."},
        "22": {"technical": "Openness to structures that serve a larger vision.", "plain": "You're open to new structures that serve big-picture goals — a new system is worth adopting to you if it actually serves something you're building toward."},
        "33": {"technical": "Openness to approaches that serve others.", "plain": "You're open to new ways of helping and caring for people. A new method earns your interest fastest when it's actually useful to someone you care about."},
    },
    # Tier 2 — Mercury sign conditions the Expression-number default, same
    # category as Venus/Saturn placements elsewhere in this schema.
    "openness_mercury_sign": {
        "Aries": {"technical": "Mercury in cardinal fire. Quick, decisive thinking, jumps to conclusions fast.", "plain": "Your mind moves fast and decides quickly, sometimes before you've fully explored the alternatives. You'd rather act on a hunch than sit with an open question too long."},
        "Taurus": {"technical": "Mercury in fixed earth. Deliberate, concrete thinking, slow to change a formed opinion.", "plain": "You think things through carefully, and once you've settled on a view, you don't shift it easily. Changing your mind takes real, convincing evidence, not just a good argument."},
        "Gemini": {"technical": "Mercury in its own sign. Naturally curious and quick to connect disparate ideas, supporting an investigative drive with genuine cognitive flexibility.", "plain": "Your mind naturally jumps between ideas and connects things quickly, which supports your investigative streak — you're the one who notices the unexpected link between two unrelated topics."},
        "Cancer": {"technical": "Mercury in its detriment. Thinking colored by memory and feeling rather than pure logic.", "plain": "How you think about something is often shaped by how it feels, more than by cold analysis alone. A fact lands differently for you depending on what it stirs up."},
        "Leo": {"technical": "Mercury in fixed fire. Confident, expressive thinking, opinions held with pride.", "plain": "You tend to state your views with confidence, and you don't love having them challenged. Once you've said something out loud, backing off it doesn't come easily."},
        "Virgo": {"technical": "Mercury in its rulership and exaltation. Precise, analytical, detail-oriented thinking.", "plain": "You naturally notice details and pick apart how things actually work — you're the one who spots the flaw in the plan that everyone else glossed over."},
        "Libra": {"technical": "Mercury in cardinal air. Thinking oriented around weighing both sides and seeking fairness.", "plain": "You naturally see multiple sides of an issue before settling anywhere — landing on a firm opinion fast, especially in a disagreement, doesn't come easily to you."},
        "Scorpio": {"technical": "Mercury in its detriment. Probing, suspicious thinking, drawn to what's hidden.", "plain": "Your mind is drawn to what's underneath the surface, and you don't take things at face value. You're the one who asks what's really going on."},
        "Sagittarius": {"technical": "Mercury in its detriment. Big-picture, philosophical thinking, impatient with fine detail.", "plain": "You think in broad strokes and can lose patience with granular detail — the big idea holds your attention far more than the fine print."},
        "Capricorn": {"technical": "Mercury in fixed earth. Structured, practical thinking oriented around what actually works.", "plain": "Your thinking is practical and results-oriented, more concerned with what works than with theory. A good idea that doesn't function in the real world doesn't hold your interest long."},
        "Aquarius": {"technical": "Mercury in fixed air. Original, systems-oriented thinking, drawn to unconventional ideas.", "plain": "You're drawn to unusual ideas and like thinking about how systems fit together — the unconventional answer often appeals to you more than the obvious one."},
        "Pisces": {"technical": "Mercury in its detriment. Intuitive, impressionistic thinking, less linear than most.", "plain": "Your thinking moves more by impression and intuition than by strict step-by-step logic. You often know an answer before you can fully explain how you got there."},
    },
    # Tier 3 — Attitude number describes the surface-level approach to brand new
    # situations, background until a new situation actually activates it.
    "openness_attitude": {
        "1": {"technical": "Attitude 1 carries an independent, first-mover quality into new situations.", "plain": "Even your surface-level approach to brand-new situations leans toward taking the first step yourself, rather than waiting to see what everyone else does."},
        "2": {"technical": "Attitude 2 carries a cooperative, watch-and-adapt quality into new situations.", "plain": "Your first instinct in something new is to read the room and adapt, rather than push your own agenda right away."},
        "3": {"technical": "Attitude 3 carries a curious, expressive quality into new situations.", "plain": "New situations tend to bring out your more playful, expressive side right away, before you've had time to overthink it."},
        "4": {"technical": "Attitude 4 carries a cautious, structure-seeking quality into new situations.", "plain": "Your first instinct with anything new is to look for the plan or the structure — an unfamiliar situation feels more manageable once you can see the framework underneath it."},
        "5": {"technical": "Attitude 5 carries an eager, exploratory quality into new situations.", "plain": "Something new tends to bring out genuine excitement in you and a pull to dive right in, rather than hang back."},
        "6": {"technical": "Attitude 6 carries a responsible, caretaking quality into new situations.", "plain": "Your first instinct in something new is often to check how it affects the people around you, before you fully turn your attention to yourself."},
        "7": {"technical": "Attitude 7 carries a reserved, evaluating quality into new situations.", "plain": "New situations get a quiet, watchful once-over from you before you actually engage."},
        "8": {"technical": "Attitude 8 carries an assertive, take-charge quality into new situations.", "plain": "Your first instinct with anything new is to size it up in terms of who's actually in control of it."},
        "9": {"technical": "Attitude 9 carries a broad, accepting quality into new situations.", "plain": "New situations tend to be met with an open, big-picture kind of ease from you, rather than suspicion."},
        "11": {"technical": "Surface-level approach to new situations carries the same illuminator/mirror quality as the core Life Path number.", "plain": "Even your surface-level approach to brand-new situations carries that same mirror-like, perceptive quality as your core Life Path — you tend to read a new room accurately, fast."},
        "22": {"technical": "Attitude 22 carries a big-picture, structural quality into new situations.", "plain": "Your first instinct in something new is to size up how it fits into a larger plan, rather than react to it in isolation."},
        "33": {"technical": "Attitude 33 carries a nurturing, service-minded quality into new situations.", "plain": "New situations often get met first through the lens of how you can help, before you've thought much about what's in it for you."},
    },

    # ── EMOTIONAL STABILITY ──────────────────────────────────────
    "emotional_stability_authority": {
        "Splenic": {
            "technical": "Real-time but non-repeating instinct, no memory trail.",
            "plain": "Your gut instinct is accurate right now, in the moment, but it doesn't leave a paper trail you can reference later. If you talk yourself out of it, it won't come back to argue its case a second time — you have to trust it the first time it speaks.",
        },
        "Emotional": {
            "technical": "Requires riding out emotional wave, clarity not available in moment.",
            "plain": "You need time for your feelings to actually settle before a decision is reliable. Whatever you feel about something right this second isn't the final answer — give it a few days and a few emotional ups and downs before you commit.",
        },
        "Sacral": {
            "technical": "Reliable, repeatable gut-response system.",
            "plain": "You have a dependable gut yes-or-no response you can trust in the moment, as long as something real is actually in front of you to respond to. It doesn't work as well on hypotheticals.",
        },
        "Self-Projected": {
            "technical": "Requires externalized verbal processing for clarity.",
            "plain": "You often don't fully know what you think or feel about something until you hear yourself say it out loud to another person. That's not indecision — it's how your clarity is built to arrive.",
        },
        "Ego": {
            "technical": "Willpower-based stability, tied to genuine commitment.",
            "plain": "Your stability is tied to your own will and desire. Your steadiest decisions come from what you genuinely want to commit to, not from what you feel obligated to do."},
        "Lunar": {
            "technical": "Requires full lunar cycle for reliable clarity.",
            "plain": "You need real time — up to a full month — before a decision is genuinely reliable. Quick, same-week answers about anything major usually aren't your most trustworthy ones.",
        },
        "Mental/Environment": {
            "technical": "Clarity through external reference and environment.",
            "plain": "You find stability through understanding how things connect in the world around you. Talking something through out loud, in the right setting, isn't a weakness for you — it's the actual mechanism your clarity runs on.",
        },
    },
    # Tier 3 — Vedic Moon/Nakshatra describes the underlying emotional/mental
    # nature, background temperament rather than a moment-to-moment default.
    "emotional_stability_moon_nakshatra": {
        "Ashwini": {"technical": "Ketu-lorded nakshatra. Quick, instinctive emotional response, resets fast after disturbance.", "plain": "Your emotional reactions come and go quickly — you don't tend to stay upset for long, even after something that really got to you in the moment."},
        "Bharani": {"technical": "Venus-lorded nakshatra. Intense underlying emotional bearing, carries things deeply.", "plain": "Underneath the surface, you tend to feel things very intensely, even on the days it doesn't show at all."},
        "Krittika": {"technical": "Sun-lorded nakshatra. Sharp, purifying emotional nature, cuts through what isn't true.", "plain": "Your underlying emotional temperament doesn't tolerate pretense well — you want things named honestly, even when honesty is uncomfortable."},
        "Rohini": {"technical": "Moon-lorded nakshatra, the Moon's own nakshatra. Deeply sensuous, growth-oriented emotional nature.", "plain": "Your underlying emotional nature is nurturing and steady, drawn toward whatever helps things grow — a plant, a project, a person."},
        "Mrigashira": {"technical": "Mars-lorded nakshatra. Searching, restless underlying emotional temperament.", "plain": "Underneath, there's a quiet emotional restlessness in you — a sense of always looking for something, even when you can't name what it is."},
        "Ardra": {"technical": "Rahu-lorded nakshatra. Turbulent, transformative underlying emotional bearing.", "plain": "Your deeper emotional nature tends to run through intense periods of upheaval that ultimately clear things out — the storm that leaves things cleaner afterward."},
        "Punarvasu": {"technical": "Jupiter-lorded nakshatra. Renewing, optimistic underlying emotional temperament.", "plain": "Underneath, there's a resilient optimism in you — a real capacity to start over after things fall apart, rather than staying stuck in the wreckage."},
        "Pushya": {"technical": "Saturn-lorded nakshatra, traditionally the most nourishing. Steady, protective underlying emotional nature.", "plain": "Your deeper emotional temperament is nurturing and stable. You tend to look after the people around you without making much of a show about it."},
        "Ashlesha": {"technical": "Mercury-lorded nakshatra. Penetrating, guarded underlying emotional bearing.", "plain": "Underneath, you read people and situations closely, and you don't let your guard down easily — you're taking in more than you let on."},
        "Magha": {"technical": "Ketu-lorded nakshatra. Proud, ancestral underlying emotional bearing.", "plain": "There's a deep-seated need in you for your efforts, and where you come from, to actually be respected."},
        "Purva Phalguni": {"technical": "Venus-lorded nakshatra. Pleasure-oriented, relaxed underlying emotional nature.", "plain": "Your underlying temperament leans toward enjoyment and ease rather than tension — you recover your footing through pleasure, not through pushing harder."},
        "Uttara Phalguni": {"technical": "Sun-lorded nakshatra. Generous, dependable underlying emotional bearing.", "plain": "Underneath, there's a steady generosity in you — a genuine wish to be useful to the people around you."},
        "Hasta": {"technical": "Moon-lorded nakshatra. Skillful, self-soothing underlying emotional temperament.", "plain": "You tend to settle yourself by doing — working with your hands, or just focusing on a task, calms you more than talking it through would."},
        "Chitra": {"technical": "Mars-lorded nakshatra. Vivid, image-conscious underlying emotional bearing.", "plain": "Underneath, there's real sensitivity in you to how things look and come together — aesthetically, and otherwise."},
        "Swati": {"technical": "Rahu-lorded nakshatra. Independent, wind-like underlying emotional nature.", "plain": "Your deeper emotional temperament values independence — being tied down, even by something well-meaning, doesn't sit well with you."},
        "Vishakha": {"technical": "Jupiter-lorded nakshatra. Determined, goal-driven underlying emotional bearing.", "plain": "Underneath, there's a strong drive in you to get where you're going, even if it takes far longer than you'd like."},
        "Anuradha": {"technical": "Saturn-lorded nakshatra. Devoted, friendship-oriented underlying emotional nature.", "plain": "Your deeper temperament is loyal — once you commit to people, that bond tends to run deep and last."},
        "Jyeshtha": {"technical": "Mercury-lorded nakshatra. Protective, authority-conscious underlying emotional bearing.", "plain": "Underneath, there's a protective instinct in you, along with real sensitivity around status and respect."},
        "Mula": {"technical": "Ketu-lorded nakshatra. Root-seeking, sometimes disruptive underlying emotional nature.", "plain": "Your deeper temperament wants to get to the actual root of things, even if that means tearing something down first to see what's really underneath."},
        "Purva Ashadha": {"technical": "Venus-lorded nakshatra. Proud, invincible-feeling underlying emotional bearing.", "plain": "Underneath, there's a strong, hard-to-shake confidence in you about your own position."},
        "Uttara Ashadha": {"technical": "Sun-lorded nakshatra. Principled, enduring underlying emotional nature.", "plain": "Your deeper temperament holds firm to what you believe is right, even under real pressure to bend."},
        "Shravana": {"technical": "Moon-lorded nakshatra. Listening, absorptive underlying emotional bearing.", "plain": "Underneath, you take in a great deal from what people tell you, and it stays with you long after the conversation ends."},
        "Dhanishta": {"technical": "Mars-lorded nakshatra. Rhythmic, achievement-oriented underlying emotional nature.", "plain": "Your deeper temperament likes momentum and visible progress — stagnation bothers you more than most people it would."},
        "Shatabhisha": {"technical": "Rahu-lorded nakshatra. Private, healing-oriented underlying emotional bearing.", "plain": "Underneath, you tend to process difficulty alone before you let anyone else in on it."},
        "Purva Bhadrapada": {"technical": "Jupiter-lorded nakshatra. Intense, transformation-seeking underlying emotional nature.", "plain": "Your deeper temperament is drawn to intensity — ordinary steadiness alone doesn't fully satisfy you."},
        "Uttara Bhadrapada": {"technical": "Saturn-lorded nakshatra. Deep, quietly wise underlying emotional bearing.", "plain": "Underneath, there's a slow-moving depth in you — patient, and not easily rattled by whatever's happening on the surface."},
        "Revati": {"technical": "Mercury-lorded nakshatra, the final nakshatra. Gentle, protective, completion-oriented underlying emotional nature.", "plain": "Your deeper temperament is nurturing and unhurried, with a quiet instinct to see things through to a caring close rather than leaving them unfinished."},
    },
    # Tier 3 — Maturity number describes a background orientation that only
    # becomes visible in the second half of life, invisible until activated.
    "emotional_stability_maturity": {
        "1": {"technical": "Maturity 1 points toward growing independence and self-trust as an underlying later-life orientation.", "plain": "As life goes on, expect to rely more and more on your own judgment for a sense of steadiness, rather than on outside reassurance."},
        "2": {"technical": "Maturity 2 points toward growing reliance on partnership as an underlying later-life orientation.", "plain": "As life goes on, you'll likely find more of your stability through close relationships than you did earlier on."},
        "3": {"technical": "Maturity 3 points toward growing self-expression as an underlying later-life orientation.", "plain": "As life goes on, you'll likely find more emotional steadiness through creative expression — making something, rather than just thinking about it."},
        "4": {"technical": "Maturity 4 points toward growing structure and groundedness as an underlying later-life orientation.", "plain": "As life goes on, you'll likely find more stability through order and routine than you needed when you were younger."},
        "5": {"technical": "Maturity 5 points toward growing need for freedom as an underlying later-life orientation.", "plain": "As life goes on, you'll likely need more room to move and change in order to feel steady, not less."},
        "6": {"technical": "Maturity 6 points toward growing responsibility for others as an underlying later-life orientation.", "plain": "As life goes on, you'll likely find more stability through caring for the people close to you."},
        "7": {"technical": "Maturity 7 points toward growing inward reflection as an underlying later-life orientation.", "plain": "As life goes on, you'll likely need more quiet and reflection in order to feel emotionally steady."},
        "8": {"technical": "Maturity 8 points toward growing command over material affairs as an underlying later-life orientation.", "plain": "As life goes on, you'll likely find more stability through getting a stronger handle on resources and authority."},
        "9": {"technical": "Maturity 9 points toward growing universal concern as an underlying later-life orientation.", "plain": "As life goes on, you'll likely find more stability through serving something bigger than yourself."},
        "11": {"technical": "Maturity 11 points toward growing intuitive clarity as an underlying later-life orientation.", "plain": "As life goes on, you'll likely draw more of your stability from your own inner knowing than from outside validation."},
        "22": {"technical": "Maturity 22 points toward growing large-scale purpose as an underlying later-life orientation.", "plain": "As life goes on, you'll likely find more stability through building something that outlasts you."},
        "33": {"technical": "Maturity 33 points toward growing devotion to service as an underlying later-life orientation.", "plain": "As life goes on, you'll likely find your deepest stability through caring for others, more than through anything you build for yourself alone."},
    },
}


# ── DIRECTIONAL CLASSIFICATION ────────────────────────────────────────────
# Categorical labels (never a number) attached to the values already keyed in
# LOOKUP_TABLES above, used only to compute the qualitative range/variance
# below and to check cross-system tension patterns. Never rendered as prose
# directly — the existing "technical"/"plain" text is the only user-facing
# copy. Not every one of the ~180 values above needs a direction; only the
# Tier 1/2 values that materially affect the range calculation are covered
# here, plus a handful of clearly-fitting Tier 3 booleans.

DIRECTIONS = {
    "agreeableness_hd_type": {
        "Projector": "accommodating", "Generator": "responsive",
        "Manifesting Generator": "responsive", "Manifestor": "independent",
        "Reflector": "variable",
    },
    # Also used for Soul Urge — same table LOOKUP_TABLES reuses for both fields.
    "agreeableness_expression": {
        "1": "independent", "2": "harmony-seeking", "3": "moderate", "4": "moderate",
        "5": "independent", "6": "harmony-seeking", "7": "detached", "8": "independent",
        "9": "harmony-seeking", "11": "detached", "22": "structured", "33": "harmony-seeking",
    },
    "agreeableness_venus": {
        "Aries": "independent", "Taurus": "moderate", "Gemini": "moderate",
        "Cancer": "harmony-seeking", "Leo": "moderate", "Virgo": "moderate",
        "Libra": "harmony-seeking", "Scorpio": "detached", "Sagittarius": "moderate",
        "Capricorn": "independent", "Aquarius": "detached", "Pisces": "harmony-seeking",
    },
    "agreeableness_profile": {
        "1/3": "independent", "1/4": "independent", "2/4": "harmony-seeking",
        "2/5": "moderate", "3/5": "independent", "3/6": "moderate",
        "4/6": "harmony-seeking", "4/1": "moderate", "5/1": "independent",
        "5/2": "moderate", "6/2": "harmony-seeking", "6/3": "moderate",
    },
    "conscientiousness_life_path": {
        "1": "structured", "2": "moderate", "3": "spontaneous", "4": "structured",
        "5": "spontaneous", "6": "structured", "7": "moderate", "8": "structured",
        "9": "moderate", "11": "moderate", "22": "structured", "33": "structured",
    },
    "conscientiousness_saturn_sign": {
        "Aries": "pressured", "Taurus": "structured", "Gemini": "spontaneous",
        "Cancer": "moderate", "Leo": "moderate", "Virgo": "structured",
        "Libra": "moderate", "Scorpio": "structured", "Sagittarius": "spontaneous",
        "Capricorn": "structured", "Aquarius": "moderate", "Pisces": "variable",
    },
    "extraversion_rising": {
        "Aries": "outward", "Taurus": "inward", "Gemini": "outward", "Cancer": "inward",
        "Leo": "outward", "Virgo": "inward", "Libra": "outward", "Scorpio": "inward",
        "Sagittarius": "outward", "Capricorn": "inward", "Aquarius": "moderate", "Pisces": "variable",
    },
    "extraversion_personality": {
        "1": "outward", "2": "inward", "3": "outward", "4": "inward", "5": "outward",
        "6": "moderate", "7": "inward", "8": "outward", "9": "outward",
        "11": "outward", "22": "moderate", "33": "moderate",
    },
    "openness_expression": {
        "1": "moderate", "2": "moderate", "3": "open", "4": "conventional", "5": "open",
        "6": "moderate", "7": "open", "8": "conventional", "9": "open",
        "11": "open", "22": "conventional", "33": "moderate",
    },
    "openness_mercury_sign": {
        "Aries": "moderate", "Taurus": "conventional", "Gemini": "open", "Cancer": "moderate",
        "Leo": "moderate", "Virgo": "conventional", "Libra": "moderate", "Scorpio": "open",
        "Sagittarius": "open", "Capricorn": "conventional", "Aquarius": "open", "Pisces": "open",
    },
    "emotional_stability_authority": {
        "Splenic": "stable", "Emotional": "stable", "Sacral": "stable",
        "Self-Projected": "moderate", "Ego": "stable", "Lunar": "variable",
        "Mental/Environment": "reactive",
    },
}


# ── CROSS-SYSTEM TENSION DETECTION ────────────────────────────────────────
# Each pattern checks a real combination of already-extracted chart values —
# never invents a connection that isn't actually present in the data. The
# narrative speaks in the same second-person teaching voice as the rest of
# this file: state the two data points in tension, then explain concretely
# how that friction tends to show up.

_ELEMENTS = {
    "Aries": "Fire", "Leo": "Fire", "Sagittarius": "Fire",
    "Taurus": "Earth", "Virgo": "Earth", "Capricorn": "Earth",
    "Gemini": "Air", "Libra": "Air", "Aquarius": "Air",
    "Cancer": "Water", "Scorpio": "Water", "Pisces": "Water",
}
_OPPOSITE_ELEMENTS = {("Fire", "Water"), ("Water", "Fire"), ("Earth", "Air"), ("Air", "Earth")}


def _element_diff(sign1: str, sign2: str) -> int:
    """0 = same/unrelated element pair, 1 = different non-opposing elements, 2 = opposing elements."""
    e1, e2 = _ELEMENTS.get(sign1), _ELEMENTS.get(sign2)
    if not e1 or not e2 or e1 == e2:
        return 0
    return 2 if (e1, e2) in _OPPOSITE_ELEMENTS else 1


_FIRE_SIGNS = {"Aries", "Leo", "Sagittarius"}
_WATER_SIGNS = {"Pisces", "Cancer", "Scorpio"}

TENSION_PATTERNS = [
    {
        "id": "T-A1", "name": "Action Paradox", "severity": "high",
        "traits": ["agreeableness", "conscientiousness"],
        "check": lambda c: c["hd_type"] in ("Projector", "Reflector") and c["mars_sign"] in _FIRE_SIGNS,
        "narrative": lambda c: (
            f"Your Human Design is built to respond, not initiate — but your Mars in {c['mars_sign']} wants to "
            f"move the second something clicks. You'll feel this as a real pull to jump in immediately, right "
            f"alongside the deeper mechanic that actually works better when you let the invitation come to you "
            f"first. The move that serves you long-term is rarely the move your Mars wants to make in the moment."
        ),
    },
    {
        "id": "T-A2", "name": "Initiative Paradox", "severity": "high",
        "traits": ["agreeableness", "extraversion"],
        "check": lambda c: c["hd_type"] == "Projector" and c["sun_sign"] in _FIRE_SIGNS,
        "narrative": lambda c: (
            f"Your core identity runs hot and forward — {c['sun_sign']} Sun wants to lead from the front. But as "
            f"a Projector, your actual design rewards waiting for the invitation, not forcing the opening "
            f"yourself. That gap can feel like sitting on your own ignition: the fire's there, but the design "
            f"underneath it is built to be recognized, not to charge ahead uninvited."
        ),
    },
    {
        "id": "T-B1", "name": "Identity Fracture", "severity": "medium",
        "traits": ["extraversion", "emotional_stability"],
        "check": lambda c: _element_diff(c["rising_sign"], c["vedic_lagna"]) > 1,
        "narrative": lambda c: (
            f"Your Western Rising in {c['rising_sign']} and your Vedic Lagna in {c['vedic_lagna']} come from "
            f"genuinely different elements — which means the very first impression you give off can shift "
            f"noticeably depending on which lens someone's reading you through. Two people meeting you in "
            f"different contexts can walk away with two believably different first reads on who you are, and "
            f"both of them are actually true."
        ),
    },
    {
        "id": "T-C1", "name": "Timing Paradox", "severity": "high",
        "traits": ["conscientiousness", "emotional_stability"],
        "check": lambda c: c["authority"] == "Splenic" and c["profile"] in ("1/3", "1/4", "5/1"),
        "narrative": lambda c: (
            f"Your Splenic Authority speaks once, right now, and doesn't repeat itself — but your {c['profile']} "
            f"Profile needs real time investigating and testing things before it trusts a conclusion. That's a "
            f"genuine tension: the part of you that knows instantly, and the part of you that needs to look "
            f"before it leaps, aren't always going to agree on when it's actually time to decide."
        ),
    },
    {
        "id": "T-C2", "name": "Patience Paradox", "severity": "medium",
        "traits": ["emotional_stability", "conscientiousness"],
        "check": lambda c: c["authority"] == "Emotional" and c["sun_sign"] in _FIRE_SIGNS,
        "narrative": lambda c: (
            f"Your Emotional Authority needs real time — days, not minutes — before a decision is actually "
            f"reliable. But your {c['sun_sign']} Sun wants the answer right now. Expect a real internal "
            f"push-pull here: the urgency you feel isn't wrong, it's just not yet the whole truth — the version "
            f"of you that's still riding the wave hasn't caught up to the version that'll actually know."
        ),
    },
    {
        "id": "T-D1", "name": "Power Paradox", "severity": "high",
        "traits": ["conscientiousness", "extraversion"],
        "check": lambda c: "Sacral" not in c["defined_centers"] and c["life_path"] in (1, 8, 22),
        "narrative": lambda c: (
            f"Life Path {c['life_path']} hands you a real drive to lead and build at scale — but without a "
            f"defined Sacral, you don't have the sustainable, self-generating motor to carry that ambition "
            f"alone. The vision is legitimately yours; the stamina to run it solo isn't built into your design. "
            f"This is exactly why people under this combination who try to do everything themselves tend to "
            f"burn out — the drive was never meant to be a one-person operation."
        ),
    },
    {
        "id": "T-E1", "name": "Service Paradox", "severity": "medium",
        "traits": ["agreeableness"],
        "check": lambda c: c["soul_urge"] == 33 and c["profile"] == "5/1",
        "narrative": lambda c: (
            "Underneath, Soul Urge 33 gives you a genuine pull to serve and care for people at scale. But your "
            "5/1 Profile casts you into the role of the outside investigator — the heretic who challenges the "
            "very structures other people trust, not the one who blends quietly in to help. You may feel the "
            "wanting-to-help pull, while your actual social role in a room is to be the one questioning what "
            "everyone else has already accepted."
        ),
    },
    {
        "id": "T-F1", "name": "Visibility Paradox", "severity": "high",
        "traits": ["extraversion", "openness"],
        "check": lambda c: c["life_path"] == 11 and c["expression"] == 7 and c["profile"] == "5/1",
        "narrative": lambda c: (
            "Life Path 11 wires you to be seen and to illuminate for others — but Expression 7 wants to verify "
            "everything privately before it speaks, and your 5/1 Profile requires waiting to be invited before "
            "you're recognized at all. Three real, legitimate parts of you are pulling in different directions "
            "at once: built to shine, wired to investigate quietly first, and required to wait for the door to "
            "open. None of them is wrong; they just don't move on the same timeline."
        ),
    },
    {
        "id": "T-G1", "name": "Cognitive Paradox", "severity": "medium",
        "traits": ["openness"],
        "check": lambda c: "Ajna" in c["defined_centers"] and c["mercury_sign"] == "Gemini",
        "narrative": lambda c: (
            "A defined Ajna holds onto conclusions once you've settled on them — but Mercury in Gemini keeps "
            "generating new angles and connections faster than most people can track. You'll notice this as a "
            "mind that keeps producing fresh ideas even after part of you has already locked in an answer, "
            "which can look like you arguing with your own past conclusion in real time."
        ),
    },
    {
        "id": "T-H1", "name": "Emotional Paradox", "severity": "medium",
        "traits": ["emotional_stability"],
        "check": lambda c: "Solar Plexus" not in c["defined_centers"] and c["moon_sign"] in _WATER_SIGNS,
        "narrative": lambda c: (
            f"With an open Solar Plexus, you absorb the emotional weather of whatever room you're in — but your "
            f"{c['moon_sign']} Moon processes feeling deeply and privately, on its own internal timeline. That "
            f"means you can be soaking up everyone else's emotional noise all day, and still end up working "
            f"through what you actually feel completely alone, later, once everyone else has gone home."
        ),
    },
]


def _detect_tensions(ctx: dict) -> list[dict]:
    """Check every tension pattern against already-extracted chart values (ctx).
    Never fabricates a connection — each pattern only fires on real data already
    computed elsewhere in the pipeline."""
    detected = []
    for pattern in TENSION_PATTERNS:
        try:
            fires = pattern["check"](ctx)
        except (KeyError, TypeError):
            fires = False
        if fires:
            detected.append({
                "pattern_id": pattern["id"],
                "name": pattern["name"],
                "severity": pattern["severity"],
                "narrative": pattern["narrative"](ctx),
                "affected_traits": pattern["traits"],
            })
    return detected


# ── QUALITATIVE RANGE / VARIANCE ──────────────────────────────────────────
# No invented numbers anywhere here — the range is derived from directional
# consensus among an trait's own entries and from how many/how severe the
# cross-system tensions affecting that trait are.

_OPPOSITE_DIRECTIONS = {
    ("accommodating", "independent"), ("independent", "accommodating"),
    ("harmony-seeking", "independent"), ("independent", "harmony-seeking"),
    ("structured", "spontaneous"), ("spontaneous", "structured"),
    ("outward", "inward"), ("inward", "outward"),
    ("open", "conventional"), ("conventional", "open"),
    ("stable", "reactive"), ("reactive", "stable"),
}

_DESCRIPTOR_MAP = {
    "accommodating": "High", "harmony-seeking": "High", "responsive": "Moderate–High",
    "independent": "Low", "detached": "Low–Moderate", "structured": "High",
    "pressured": "Moderate–High", "variable": "Moderate", "spontaneous": "Low",
    "outward": "High", "inward": "Low", "open": "High", "conventional": "Low",
    "stable": "High", "reactive": "Low", "moderate": "Moderate",
}

_CENTER_OF_RANGE = {
    "Low–Moderate": "Low", "Moderate–High": "High", "Low–High": "Moderate",
    "Low": "Low", "Moderate": "Moderate", "High": "High",
}


def _dominant_direction(directions: list[str]) -> str | None:
    if not directions:
        return None
    from collections import Counter
    return Counter(directions).most_common(1)[0][0]


def _qualitative_range(tier1_directions: list[str], all_directions: list[str], tension_severities: list[str]) -> tuple[str, str, str]:
    if not all_directions:
        return "Insufficient Data", "Unknown", "low"

    unique = list(set(all_directions))
    if len(unique) == 1:
        consensus = "strong"
    elif len(unique) == 2:
        pair = (unique[0], unique[1])
        consensus = "split" if pair in _OPPOSITE_DIRECTIONS else "moderate"
    else:
        consensus = "mixed"

    high_sev = tension_severities.count("high")
    med_sev = tension_severities.count("medium")
    if high_sev >= 1 or consensus == "split":
        variance = "high"
    elif med_sev >= 1 or consensus == "mixed":
        variance = "moderate"
    else:
        variance = "low"

    dominant = _dominant_direction(tier1_directions) or _dominant_direction(all_directions)
    base_descriptor = _DESCRIPTOR_MAP.get(dominant, "Moderate")

    if variance == "high":
        range_label = {"High": "Moderate–High", "Low": "Low–Moderate"}.get(base_descriptor, "Low–High")
    elif variance == "moderate":
        range_label = {"High": "Moderate–High", "Low": "Low–Moderate"}.get(base_descriptor, base_descriptor)
    else:
        range_label = base_descriptor

    descriptor = _CENTER_OF_RANGE.get(range_label, "Moderate")
    return range_label, descriptor, variance


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
        "plain": f"This isn't locked in one way or the other — whether you're currently coming from the harder "
                  f"{shadow.lower()} pattern or the more resourced {gift.lower()} pattern changes how this shows up "
                  f"for you day to day, and it can shift with circumstance rather than staying fixed permanently.",
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
    entries — see module docstring for the four-question placement test), plus a
    qualitative range_label/descriptor/variance and a "tensions" list of any
    cross-system contradictions affecting that trait (no invented numeric scores —
    see DIRECTIONS / _qualitative_range / TENSION_PATTERNS above). Also returns
    top-level "_coverage" (unchanged) and "cross_system_tensions" (top 3 overall).
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

    # Extracted for cross-system tension detection only (Question 1 timing
    # exclusion doesn't apply — these are natal placements, not timing data).
    mars_sign = western_placements.get("Mars", {}).get("sign_name", "")
    sun_sign = western.get("sun_sign", "")
    moon_sign = western.get("moon_sign", "")
    vedic_lagna = vedic.get("lagna", "")

    # Helper to add entry
    def add_entry(trait_entries, tier, system, field, value, tech=None, plain=None, register_note=None, direction=None):
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
        if direction is not None:
            entry["direction"] = direction
        trait_entries.append(entry)

    # ── AGREEABLENESS ────────────────────────────────────────────
    agreeableness_entries = []

    # Tier 1: HD Type
    if hd_type in LOOKUP_TABLES["agreeableness_hd_type"]:
        entry = LOOKUP_TABLES["agreeableness_hd_type"][hd_type]
        add_entry(agreeableness_entries, 1, "human_design", "type", hd_type,
                 tech=entry["technical"], plain=entry["plain"],
                 direction=DIRECTIONS["agreeableness_hd_type"].get(hd_type))

    # Tier 1: Expression
    if str(expression) in LOOKUP_TABLES["agreeableness_expression"]:
        entry = LOOKUP_TABLES["agreeableness_expression"][str(expression)]
        add_entry(agreeableness_entries, 1, "numerology", "expression", expression,
                 tech=entry["technical"], plain=entry["plain"],
                 direction=DIRECTIONS["agreeableness_expression"].get(str(expression)))

    # Tier 2: Venus Sign
    if venus_sign and venus_sign in LOOKUP_TABLES["agreeableness_venus"]:
        entry = LOOKUP_TABLES["agreeableness_venus"][venus_sign]
        add_entry(agreeableness_entries, 2, "western_astrology", "venus_sign", venus_sign,
                 tech=entry["technical"], plain=entry["plain"],
                 direction=DIRECTIONS["agreeableness_venus"].get(venus_sign))

    # Tier 2: HD Profile (conditions HD Type's Tier 1 default, same category as a placement)
    if profile and profile in LOOKUP_TABLES["agreeableness_profile"]:
        entry = LOOKUP_TABLES["agreeableness_profile"][profile]
        add_entry(agreeableness_entries, 2, "human_design", "profile", profile,
                 tech=entry["technical"], plain=entry["plain"],
                 direction=DIRECTIONS["agreeableness_profile"].get(profile))

    # Tier 3: Soul Urge
    if str(soul_urge) in LOOKUP_TABLES["agreeableness_expression"]:
        entry = LOOKUP_TABLES["agreeableness_expression"][str(soul_urge)]
        add_entry(agreeableness_entries, 3, "numerology", "soul_urge", soul_urge,
                 tech=entry["technical"], plain=entry["plain"],
                 direction=DIRECTIONS["agreeableness_expression"].get(str(soul_urge)))

    # ── CONSCIENTIOUSNESS ────────────────────────────────────────
    conscientiousness_entries = []

    # Tier 1: Defined Sacral/Root
    has_sacral = "Sacral" in defined_centers
    has_root = "Root" in defined_centers
    if has_sacral or has_root:
        add_entry(conscientiousness_entries, 1, "human_design", "defined_centers",
                 "Sacral or Root",
                 tech="Defined Sacral or Root centers give sustainable, repeatable energy.",
                 plain="You have real, dependable energy to draw on for getting things done. It's there for you consistently, not just on the days you happen to feel motivated.",
                 direction="structured")
    else:
        add_entry(conscientiousness_entries, 1, "human_design", "defined_centers",
                 "neither",
                 tech="Open Sacral and Root means energy is inconsistent.",
                 plain="Your energy for follow-through isn't automatic — some days it's genuinely there, and some days you have to work harder to find it, and that's not a discipline problem, it's how this part of your design actually runs.",
                 direction="variable")

    # Tier 1: Life Path (Life's Work Gate shadow/gift attaches here as a register
    # modifier — same core "output/what I'm here to do" theme, not a standalone entry)
    if str(life_path) in LOOKUP_TABLES["conscientiousness_life_path"]:
        entry = LOOKUP_TABLES["conscientiousness_life_path"][str(life_path)]
        register_note = _register_note(lifes_work_notation, "Life's Work")
        add_entry(conscientiousness_entries, 1, "numerology", "life_path", life_path,
                 tech=entry["technical"], plain=entry["plain"], register_note=register_note,
                 direction=DIRECTIONS["conscientiousness_life_path"].get(str(life_path)))

    # Tier 2: Saturn Sign
    if saturn_sign and saturn_sign in LOOKUP_TABLES["conscientiousness_saturn_sign"]:
        entry = LOOKUP_TABLES["conscientiousness_saturn_sign"][saturn_sign]
        tech = entry["technical"]
        plain = entry["plain"]
        if saturn_sign == "Capricorn" and saturn_retrograde:
            tech = "Saturn in its own sign, carrying strong dignity; retrograde suggests discipline was internalized through early hardship rather than external teaching."
            plain = "Your sense of discipline was shaped early, likely through real hard experience rather than someone gently teaching it to you. You built this one the hard way, which is exactly why it's so hard to shake."
        add_entry(conscientiousness_entries, 2, "western_astrology", "saturn_sign", saturn_sign,
                 tech=tech, plain=plain,
                 direction=DIRECTIONS["conscientiousness_saturn_sign"].get(saturn_sign))

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
                 tech=entry["technical"], plain=entry["plain"],
                 direction=DIRECTIONS["extraversion_rising"].get(rising_sign))

    # Tier 2: Personality number — conditions/cross-checks the Rising sign's first-contact
    # default; this is a corrected fix — previously this entry was mislabeled "personality"
    # while actually pulling and looking up the Expression value. Now pulls the real
    # numerology.personality field against its own dedicated lookup table.
    if str(personality_num) in LOOKUP_TABLES["extraversion_personality"]:
        entry = LOOKUP_TABLES["extraversion_personality"][str(personality_num)]
        add_entry(extraversion_entries, 2, "numerology", "personality", personality_num,
                 tech=entry["technical"], plain=entry["plain"],
                 direction=DIRECTIONS["extraversion_personality"].get(str(personality_num)))

    # ── OPENNESS ─────────────────────────────────────────────────
    openness_entries = []

    # Tier 1: Ajna (defined vs open). Purpose Gate shadow/gift attaches here as a register
    # modifier — Purpose Gate's Judgment/Integrity axis maps directly onto fixed-vs-fluid
    # judgment, the same theme this Tier 1 entry already covers, not a standalone entry.
    purpose_register = _register_note(purpose_notation, "Purpose")
    if "Ajna" in defined_centers:
        add_entry(openness_entries, 1, "human_design", "defined_centers", "Ajna",
                 tech="Defined Ajna holds fixed conclusions more readily.",
                 plain="Once you land on a conclusion, you tend to hold onto it firmly — think of how rarely you actually change your mind once you've genuinely settled on a view.",
                 register_note=purpose_register, direction="conventional")
    else:
        add_entry(openness_entries, 1, "human_design", "open_centers", "Ajna",
                 tech="Open Ajna tends toward more fluid thinking.",
                 plain="You tend to stay flexible in how you think, genuinely open to new information changing your mind — a fixed opinion doesn't sit as comfortably with you as it does for other people.",
                 register_note=purpose_register, direction="open")

    # Tier 1: Expression (novelty orientation)
    if str(expression) in LOOKUP_TABLES["openness_expression"]:
        entry = LOOKUP_TABLES["openness_expression"][str(expression)]
        add_entry(openness_entries, 1, "numerology", "expression", expression,
                 tech=entry["technical"], plain=entry["plain"],
                 direction=DIRECTIONS["openness_expression"].get(str(expression)))

    # Tier 2: Mercury Sign
    if mercury_sign and mercury_sign in LOOKUP_TABLES["openness_mercury_sign"]:
        entry = LOOKUP_TABLES["openness_mercury_sign"][mercury_sign]
        add_entry(openness_entries, 2, "western_astrology", "mercury_sign", mercury_sign,
                 tech=entry["technical"], plain=entry["plain"],
                 direction=DIRECTIONS["openness_mercury_sign"].get(mercury_sign))

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
                 plain="You have real emotional ups and downs, but those feelings are genuinely yours — not borrowed from whoever's standing next to you.",
                 direction="stable")
    else:
        add_entry(emotional_entries, 1, "human_design", "open_centers", "Solar Plexus",
                 tech="Open Solar Plexus means no fixed internal emotional truth.",
                 plain="You tend to pick up and absorb whatever emotional energy is nearby — walk into a tense room and you can feel the tension shift in you, even if nothing's actually happened to you personally.",
                 direction="reactive")

    # Tier 1: Authority
    if authority in LOOKUP_TABLES["emotional_stability_authority"]:
        entry = LOOKUP_TABLES["emotional_stability_authority"][authority]
        add_entry(emotional_entries, 1, "human_design", "authority", authority,
                 tech=entry["technical"], plain=entry["plain"],
                 direction=DIRECTIONS["emotional_stability_authority"].get(authority))

    # Tier 2: Saturn retrograde — fixed extraction bug: was always reading False because
    # placements[...]["retrograde"] never exists; correct source is dominant_retrogrades.
    add_entry(emotional_entries, 2, "western_astrology", "saturn_retrograde", saturn_retrograde,
             tech="Saturn retrograde suggests discipline and emotional defense structures were internalized early, "
                  "through hardship, rather than externally taught." if saturn_retrograde
                  else "Saturn direct suggests more conventional development of discipline.",
             plain="Your emotional resilience was likely built early, through real hard experience, rather than "
                   "someone teaching it to you gently." if saturn_retrograde
                   else "Your resilience likely developed in a more straightforward, conventionally supported way, without the same early hardship.",
             direction="stable" if saturn_retrograde else "moderate")

    # Tier 2: Heart (defined vs open)
    if "Heart" in defined_centers:
        add_entry(emotional_entries, 2, "human_design", "defined_centers", "Heart",
                 tech="Defined Heart gives consistent internal sense of worth.",
                 plain="You have a steady internal sense of your own worth — it doesn't swing wildly based on how someone treated you today.",
                 direction="stable")
    else:
        add_entry(emotional_entries, 2, "human_design", "open_centers", "Heart",
                 tech="Open Heart means worth referenced externally.",
                 plain="Your sense of your own worth can shift depending on how people around you are treating you — a good conversation can genuinely lift it, and a cold one can genuinely dent it, more than it would for most people.",
                 direction="reactive")

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

    # Cross-system tension detection — checks real already-extracted values, never
    # fabricates a connection. Narratives are written in the same second-person
    # teaching voice as every "plain" field above.
    tension_ctx = {
        "hd_type": hd_type, "authority": authority, "profile": profile,
        "defined_centers": defined_centers, "life_path": life_path,
        "soul_urge": soul_urge, "expression": expression,
        "mars_sign": mars_sign, "sun_sign": sun_sign, "moon_sign": moon_sign,
        "mercury_sign": mercury_sign, "rising_sign": rising_sign, "vedic_lagna": vedic_lagna,
    }
    all_tensions = _detect_tensions(tension_ctx)

    # Qualitative range/variance per trait — no invented numbers. Derived from
    # directional consensus among that trait's own entries plus the severity of
    # any cross-system tensions affecting it.
    for trait_key, trait_data in traits.items():
        trait_entries = trait_data["entries"]
        tier1_dirs = [e["direction"] for e in trait_entries if e.get("tier") == 1 and e.get("direction")]
        all_dirs = [e["direction"] for e in trait_entries if e.get("direction")]
        trait_tensions = [t for t in all_tensions if trait_key in t["affected_traits"]]
        tension_severities = [t["severity"] for t in trait_tensions]

        range_label, descriptor, variance = _qualitative_range(tier1_dirs, all_dirs, tension_severities)
        trait_data["range_label"] = range_label
        trait_data["descriptor"] = descriptor
        trait_data["variance"] = variance
        trait_data["tensions"] = trait_tensions

    # Top 3 tensions overall, ranked by severity (high before medium before low).
    _SEVERITY_RANK = {"high": 3, "medium": 2, "low": 1}
    cross_system_tensions = sorted(all_tensions, key=lambda t: _SEVERITY_RANK.get(t["severity"], 0), reverse=True)[:3]
    for i, t in enumerate(cross_system_tensions, start=1):
        t["rank"] = i

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
    traits["cross_system_tensions"] = cross_system_tensions

    return traits
