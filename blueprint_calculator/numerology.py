"""
Phase 4: Numerology (Pythagorean).

Parallel Branch A -- Steps 7 through 11. Pure name + date arithmetic,
zero ephemeris dependency. Master numbers 11/22/33 are preserved at
every stage except where the outline explicitly calls for an exception
(Attitude, and the Challenge numbers, which are timing/comparison
figures that always resolve to a single digit).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .preprocessing import NormalizedName
from .provenance import Ledger, Status

DEFAULT_MASTERS = (11, 22, 33)
KARMIC_DEBT_NUMBERS = (13, 14, 16, 19)


def digit_sum(n: int) -> int:
    return sum(int(c) for c in str(abs(n)))


def reduce_number(n: int, preserve_masters: bool = True, masters=DEFAULT_MASTERS) -> tuple[int, list[int]]:
    """Sum-of-digits reduction. Returns (final_value, full_chain)."""
    chain = [n]
    while n > 9 and not (preserve_masters and n in masters):
        n = digit_sum(n)
        chain.append(n)
    return n, chain


def reduce_to_single_digit(n: int) -> int:
    value, _ = reduce_number(n, preserve_masters=False)
    return value


@dataclass(frozen=True)
class ReducedValue:
    value: int
    raw: int
    chain: list[int]


def _reduced(n: int, preserve_masters: bool = True) -> ReducedValue:
    value, chain = reduce_number(n, preserve_masters=preserve_masters)
    return ReducedValue(value=value, raw=chain[0], chain=chain)


# --------------------------------------------------------------- NBD-1 ----

def life_path_number(birth_date: str) -> ReducedValue:
    digits = [int(c) for c in birth_date if c.isdigit()]
    return _reduced(sum(digits))


# --------------------------------------------------------------- NBD-2 ----

def attitude_number(birth_date: str) -> ReducedValue:
    y, m, d = (int(x) for x in birth_date.split("-"))
    total = digit_sum(m) + digit_sum(d)
    value, chain = reduce_number(total, preserve_masters=True)
    return ReducedValue(value=value, raw=total, chain=chain)


# --------------------------------------------------------------- NBD-3 ----

def birthday_number(birth_date: str) -> ReducedValue:
    _, _, d = (int(x) for x in birth_date.split("-"))
    value, chain = reduce_number(digit_sum(d), preserve_masters=True, masters=(11, 22))
    return ReducedValue(value=value, raw=digit_sum(d), chain=chain)


# --------------------------------------------------------------- NBD-4 ----

def generation_number(birth_date: str) -> ReducedValue:
    y, _, _ = (int(x) for x in birth_date.split("-"))
    total = digit_sum(y)
    value, chain = reduce_number(total, preserve_masters=False)
    return ReducedValue(value=value, raw=total, chain=chain)


# ------------------------------------------------------------ NC-1..3 ----

def expression_number(name: NormalizedName) -> ReducedValue:
    return _reduced(sum(l.value for l in name.letters))


def soul_urge_number(name: NormalizedName) -> ReducedValue:
    return _reduced(sum(l.value for l in name.letters if l.is_vowel))


def personality_number(name: NormalizedName) -> ReducedValue:
    return _reduced(sum(l.value for l in name.letters if l.is_consonant))


# ------------------------------------------------------------ ND-1..6 ----

def maturity_number(expression: ReducedValue, life_path: ReducedValue) -> ReducedValue:
    return _reduced(expression.value + life_path.value)


def balance_number(name: NormalizedName) -> ReducedValue:
    initials = []
    for wi in range(len(name.words)):
        first_letter = next(l for l in name.letters if l.word_index == wi)
        initials.append(first_letter.value)
    return _reduced(sum(initials))


def karmic_debt_numbers(*chains: list[int]) -> list[int]:
    found = set()
    for chain in chains:
        for v in chain[:-1]:  # only intermediate/raw values, not the final reduced result
            if v in KARMIC_DEBT_NUMBERS:
                found.add(v)
    return sorted(found)


def karmic_lesson_numbers(name: NormalizedName) -> list[int]:
    present = {l.value for l in name.letters}
    return sorted(set(range(1, 10)) - present)


def subconscious_self_number(karmic_lessons: list[int]) -> int:
    return 9 - len(karmic_lessons)


# ------------------------------------------------------------ NT-1..3 ----

def personal_year_number(life_path: ReducedValue, today: date) -> int:
    lp_single = reduce_to_single_digit(life_path.value)
    year_single = reduce_to_single_digit(digit_sum(today.year))
    return reduce_to_single_digit(lp_single + year_single)


def personal_month_number(personal_year: int, today: date) -> int:
    return reduce_to_single_digit(personal_year + today.month)


def personal_day_number(personal_month: int, today: date) -> int:
    return reduce_to_single_digit(personal_month + today.day)


# --------------------------------------------------------------- NT-4 ----

def pinnacle_numbers(attitude: int, generation: int, life_path: int) -> list[int]:
    first = reduce_number(attitude + generation)[0]
    second = reduce_number(attitude + life_path)[0]
    third = reduce_number(first + second)[0]
    fourth = reduce_number(generation + life_path)[0]
    return [first, second, third, fourth]


def cycle_age_ranges(life_path: int) -> list[tuple[int, int | None]]:
    """
    Age brackets for the four Pinnacle/Challenge life-cycle periods, standard
    numerology convention: Pinnacle 1 runs from birth to (36 - Life Path),
    Pinnacles 2 and 3 each run 9 years, Pinnacle 4 runs the rest of life.
    Challenge periods run concurrently with the same four brackets.
    """
    end1 = 36 - life_path
    end2 = end1 + 9
    end3 = end2 + 9
    return [(0, end1), (end1, end2), (end2, end3), (end3, None)]


# --------------------------------------------------------------- NT-5 ----

def challenge_numbers(attitude: int, generation: int, life_path: int) -> list[int]:
    a = reduce_to_single_digit(attitude)
    g = reduce_to_single_digit(generation)
    lp = reduce_to_single_digit(life_path)
    first = abs(a - g)
    second = abs(a - lp)
    third = abs(first - second)
    main = abs(g - lp)
    return [first, second, third, main]


# --------------------------------------------------------------- NT-6 ----

def period_cycles(attitude: int, generation: int, life_path: int) -> list[int]:
    return [attitude, generation, life_path]


# --------------------------------------------------------------- driver ----

def record_numerology(
    ledger: Ledger, *, name: NormalizedName, birth_date: str, today: date,
    current_name: str | None = None,
) -> dict:
    lp = life_path_number(birth_date)
    ledger.record(
        "NBD-1", system="Numerology", phase="Phase 4, Step 7", label="Life Path Number",
        value=lp.value, source=["P1"],
        calculation=f"digits({birth_date.replace('-', '')}) sum={lp.raw}; chain {lp.chain}",
    )
    att = attitude_number(birth_date)
    ledger.record(
        "NBD-2", system="Numerology", phase="Phase 4, Step 7", label="Attitude Number",
        value=att.value, source=["P1"], calculation=f"month+day digit sum={att.raw}; chain {att.chain}",
    )
    bday = birthday_number(birth_date)
    ledger.record(
        "NBD-3", system="Numerology", phase="Phase 4, Step 7", label="Birthday Number",
        value=bday.value, source=["P1"], calculation=f"day digit sum={bday.raw}; chain {bday.chain}",
    )
    gen = generation_number(birth_date)
    ledger.record(
        "NBD-4", system="Numerology", phase="Phase 4, Step 7", label="Generation Number",
        value=gen.value, source=["P1"], calculation=f"year digit sum={gen.raw}; chain {gen.chain}",
    )

    expr = expression_number(name)
    ledger.record(
        "NC-1", system="Numerology", phase="Phase 4, Step 8", label="Expression Number (Destiny)",
        value=expr.value, source=["NP-1"], calculation=f"sum(all letter values)={expr.raw}; chain {expr.chain}",
    )
    soul = soul_urge_number(name)
    ledger.record(
        "NC-2", system="Numerology", phase="Phase 4, Step 8", label="Soul Urge Number (Heart's Desire)",
        value=soul.value, source=["NP-1"], calculation=f"sum(vowel letter values)={soul.raw}; chain {soul.chain}",
    )
    pers = personality_number(name)
    ledger.record(
        "NC-3", system="Numerology", phase="Phase 4, Step 8", label="Personality Number",
        value=pers.value, source=["NP-1"], calculation=f"sum(consonant letter values)={pers.raw}; chain {pers.chain}",
    )

    maturity = maturity_number(expr, lp)
    ledger.record(
        "ND-1", system="Numerology", phase="Phase 4, Step 9", label="Maturity Number",
        value=maturity.value, source=["NC-1", "NBD-1"], calculation=f"{expr.value}+{lp.value}={maturity.raw}; chain {maturity.chain}",
    )
    balance = balance_number(name)
    ledger.record(
        "ND-2", system="Numerology", phase="Phase 4, Step 9", label="Balance Number",
        value=balance.value, source=["NP-1"], calculation=f"sum(first initials)={balance.raw}; chain {balance.chain}",
    )
    ledger.record(
        "ND-3", system="Numerology", phase="Phase 4, Step 9", label="Rational Thought Number",
        value=None, source=["NP-1"], status=Status.INVENTORY,
        calculation="Outline gives no concrete formula for this secondary/optional point; not computed.",
    )
    debts = karmic_debt_numbers(lp.chain, expr.chain, soul.chain, pers.chain)
    ledger.record(
        "ND-4", system="Numerology", phase="Phase 4, Step 9", label="Karmic Debt Numbers",
        value=debts, source=["NBD-1", "NC-1", "NC-2", "NC-3"],
        calculation="flag any of {13,14,16,19} appearing in NBD-1/NC-1/NC-2/NC-3 reduction chains before final reduction",
    )
    lessons = karmic_lesson_numbers(name)
    ledger.record(
        "ND-5", system="Numerology", phase="Phase 4, Step 9", label="Karmic Lesson Numbers",
        value=lessons, source=["NP-1"], calculation="digits 1-9 absent from the full name's letter values",
    )
    subconscious = subconscious_self_number(lessons)
    ledger.record(
        "ND-6", system="Numerology", phase="Phase 4, Step 9", label="Subconscious Self Number",
        value=subconscious, source=["ND-5"], calculation=f"9 - len(karmic_lessons)=9-{len(lessons)}",
    )

    py = personal_year_number(lp, today)
    ledger.record(
        "NT-1", system="Numerology", phase="Phase 4, Step 10", label="Personal Year Number",
        value=py, source=["NBD-1"], calculation=f"reduce(reduce({lp.value})+reduce(digitsum({today.year}))) as of {today.isoformat()}",
    )
    pm = personal_month_number(py, today)
    ledger.record(
        "NT-2", system="Numerology", phase="Phase 4, Step 10", label="Personal Month Number",
        value=pm, source=["NT-1"], calculation=f"reduce({py}+{today.month})",
    )
    pd = personal_day_number(pm, today)
    ledger.record(
        "NT-3", system="Numerology", phase="Phase 4, Step 10", label="Personal Day Number",
        value=pd, source=["NT-2"], calculation=f"reduce({pm}+{today.day})",
    )
    pinnacles = pinnacle_numbers(att.value, gen.value, lp.value)
    ledger.record(
        "NT-4", system="Numerology", phase="Phase 4, Step 10", label="Pinnacle Numbers",
        value=pinnacles, source=["NBD-2", "NBD-4", "NBD-1"],
        calculation="1st=reduce(Attitude+Generation); 2nd=reduce(Attitude+LifePath); 3rd=reduce(1st+2nd); 4th=reduce(Generation+LifePath)",
    )
    challenges = challenge_numbers(att.value, gen.value, lp.value)
    ledger.record(
        "NT-5", system="Numerology", phase="Phase 4, Step 10", label="Challenge Numbers",
        value=challenges, source=["NBD-2", "NBD-4", "NBD-1"],
        calculation="abs differences of single-digit-reduced Attitude/Generation/LifePath",
    )
    periods = period_cycles(att.value, gen.value, lp.value)
    ledger.record(
        "NT-6", system="Numerology", phase="Phase 4, Step 10", label="Period Cycles",
        value=periods, source=["NBD-2", "NBD-4", "NBD-1"],
        calculation="[Attitude, Generation, LifePath], masters preserved",
    )
    cycle_ages = cycle_age_ranges(lp.value)
    ledger.record(
        "NT-7", system="Numerology", phase="Phase 4, Step 10", label="Pinnacle/Challenge Age Ranges",
        value=cycle_ages, source=["NBD-1"],
        calculation="1st: 0 to (36-LifePath); 2nd/3rd: +9 years each; 4th: to end of life",
    )

    result = {
        "life_path": lp.value, "attitude": att.value, "birthday": bday.value, "generation": gen.value,
        "expression": expr.value, "soul_urge": soul.value, "personality": pers.value,
        "maturity": maturity.value, "balance": balance.value,
        "karmic_debts": debts, "karmic_lessons": lessons, "subconscious_self": subconscious,
        "personal_year": py, "personal_month": pm, "personal_day": pd,
        "cycle_age_ranges": cycle_ages,
        "pinnacles": pinnacles, "challenges": challenges, "periods": periods,
        "expression_raw": expr.raw, "soul_urge_raw": soul.raw, "personality_raw": pers.raw,
        "reduction_chains": {
            "life_path": lp.chain, "attitude": att.chain, "birthday": bday.chain, "generation": gen.chain,
            "expression": expr.chain, "soul_urge": soul.chain, "personality": pers.chain, "maturity": maturity.chain,
        },
    }

    if current_name:
        from .preprocessing import normalize_name
        cur_norm = normalize_name(current_name)
        ledger.record(
            "NCN-1", system="Numerology", phase="Phase 4, Step 11", label="Current Name Normalized",
            value={"words": cur_norm.words}, source=["P1"], calculation="same normalization as NP-1, applied to current/stage name",
        )
        minor_expr = expression_number(cur_norm)
        ledger.record(
            "NCN-2", system="Numerology", phase="Phase 4, Step 11", label="Minor Expression",
            value=minor_expr.value, source=["NCN-1"], calculation=f"chain {minor_expr.chain}",
        )
        minor_soul = soul_urge_number(cur_norm)
        ledger.record(
            "NCN-3", system="Numerology", phase="Phase 4, Step 11", label="Minor Soul Urge",
            value=minor_soul.value, source=["NCN-1"], calculation=f"chain {minor_soul.chain}",
        )
        minor_pers = personality_number(cur_norm)
        ledger.record(
            "NCN-4", system="Numerology", phase="Phase 4, Step 11", label="Minor Personality",
            value=minor_pers.value, source=["NCN-1"], calculation=f"chain {minor_pers.chain}",
        )
        result["current_name"] = {
            "minor_expression": minor_expr.value, "minor_soul_urge": minor_soul.value, "minor_personality": minor_pers.value,
        }

    return result
