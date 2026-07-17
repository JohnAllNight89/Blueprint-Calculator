"""Pythagorean numerology calculation engine.

Calculates the four core numbers from a full birth name and birth date:

* Life Path      - month, day, and year reduced independently, then summed.
* Expression     - every letter of the full birth name.
* Soul Urge      - vowels only (Y counts as a vowel when it behaves as one).
* Personality    - consonants only.

Master numbers 11, 22, and 33 are never reduced further, at any stage.
"""

from __future__ import annotations

from datetime import date

MASTER_NUMBERS = frozenset({11, 22, 33})

# Strict Pythagorean mapping: A=1 ... I=9, J=1 ... R=9, S=1 ... Z=8.
PYTHAGOREAN_MAP = {
    "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7, "H": 8, "I": 9,
    "J": 1, "K": 2, "L": 3, "M": 4, "N": 5, "O": 6, "P": 7, "Q": 8, "R": 9,
    "S": 1, "T": 2, "U": 3, "V": 4, "W": 5, "X": 6, "Y": 7, "Z": 8,
}

VOWELS = frozenset("AEIOU")


def reduce_number(n: int) -> tuple:
    """Reduces a number to a single digit (1-9) or a Master Number (11, 22, 33)."""
    steps = [n]
    if n in MASTER_NUMBERS:
        return n, steps
    current = n
    while current > 9:
        if current in MASTER_NUMBERS:
            break
        current = sum(int(d) for d in str(current))
        steps.append(current)
    return current, steps

def _clean_words(name: str) -> list[str]:
    """Split a name into words containing only the letters A-Z."""
    words = []
    for raw in name.upper().split():
        letters = "".join(char for char in raw if char in PYTHAGOREAN_MAP)
        if letters:
            words.append(letters)
    return words


def _y_is_vowel(word: str, index: int) -> bool:
    """Decide whether the Y at word[index] functions as a vowel.

    Y acts as a vowel when it is not adjacent to a true vowel (A, E, I,
    O, U). The Y in ANTHONY (between N and the word boundary) is a
    vowel; the Y in YOLANDA (glued to the O it launches) is a consonant.
    """
    before = word[index - 1] if index > 0 else ""
    after = word[index + 1] if index < len(word) - 1 else ""
    return before not in VOWELS and after not in VOWELS


def _letter_roles(word: str) -> list[tuple[str, bool]]:
    """Tag each letter of a word as (letter, is_vowel)."""
    roles = []
    for index, letter in enumerate(word):
        if letter in VOWELS:
            roles.append((letter, True))
        elif letter == "Y":
            roles.append((letter, _y_is_vowel(word, index)))
        else:
            roles.append((letter, False))
    return roles


def _chain_text(steps: list[int]) -> str:
    return " → ".join(str(step) for step in steps)


def _name_number(name: str, mode: str) -> dict:
    """Compute a core name number.

    mode is one of "all" (Expression), "vowels" (Soul Urge), or
    "consonants" (Personality). The selected letter values are summed
    across the full name, then reduced with master numbers preserved.
    """
    used: list[str] = []
    total = 0
    for word in _clean_words(name):
        for letter, is_vowel in _letter_roles(word):
            if mode == "vowels" and not is_vowel:
                continue
            if mode == "consonants" and is_vowel:
                continue
            value = PYTHAGOREAN_MAP[letter]
            total += value
            used.append(f"{letter}={value}")
        used.append("·")
    if used and used[-1] == "·":
        used.pop()

    number, steps = reduce_number(total)
    return {
        "number": number,
        "is_master": number in MASTER_NUMBERS,
        "total": total,
        "reduction": _chain_text(steps),
        "letters": " ".join(used),
    }


def calculate_life_path(birth_date: date) -> dict:
    """Life Path: sum all digits of the birth date directly to preserve Master Numbers."""
    digits = [int(char) for char in birth_date.strftime("%Y%m%d")]
    combined = sum(digits)
    number, final_steps = reduce_number(combined)
    digits_formula = " + ".join(str(d) for d in digits if d != 0)
    return {
        "number": number,
        "is_master": number in MASTER_NUMBERS,
        "total": combined,
        "reduction": _chain_text(final_steps),
        "letters": f"Digits: {digits_formula} = {combined}",
    }
def calculate_expression(name: str) -> dict:
    return _name_number(name, "all")


def calculate_soul_urge(name: str) -> dict:
    return _name_number(name, "vowels")


def calculate_personality(name: str) -> dict:
    return _name_number(name, "consonants")


def calculate_chart(name: str, birth_date: date) -> dict:
    """Full Phase 1 numerology chart for a name and birth date."""
    return {
        "life_path": calculate_life_path(birth_date),
        "expression": calculate_expression(name),
        "soul_urge": calculate_soul_urge(name),
        "personality": calculate_personality(name),
    }


# --- Reference verification profile -----------------------------------------

REFERENCE_NAME = "Johnathon Anthony Long"
REFERENCE_DATE = date(1989, 6, 23)
REFERENCE_EXPECTED = {
    "life_path": 11,      # 6 + 5 + 9 = 20 → 2
    "expression": 7,     # 97 → 16 → 7
    "soul_urge": 33,     # 33 stays 33 (master number, never reduced)
    "personality": 1,    # 64 → 10 → 1
}


def verify_reference_profile() -> dict:
    """Run the hardcoded verification profile and report pass/fail."""
    chart = calculate_chart(REFERENCE_NAME, REFERENCE_DATE)
    checks = {}
    for key, expected in REFERENCE_EXPECTED.items():
        actual = chart[key]["number"]
        checks[key] = {
            "expected": expected,
            "actual": actual,
            "passed": actual == expected,
        }
    return {
        "profile": f"{REFERENCE_NAME} — {REFERENCE_DATE.isoformat()}",
        "all_passed": all(check["passed"] for check in checks.values()),
        "checks": checks,
    }
