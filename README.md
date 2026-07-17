# Blueprint Calculator

A local, web-based esoteric calculation dashboard that will eventually
synthesize Numerology, Western/Vedic Astrology, Human Design, and Gene Keys.

**Phase 1 (current):** FastAPI backend + Tailwind dark-theme dashboard shell +
a complete Pythagorean numerology engine (Life Path, Expression, Soul Urge,
Personality — master numbers 11/22/33 preserved).

## Setup (Chromebook / Crostini Debian 12, ARM64)

```bash
# 1. From the project directory, create and activate a virtual environment
cd ~/Blueprint-Calculator
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the verification tests (hardcoded reference profile)
python tests/test_numerology.py

# 4. Start the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Then open **http://localhost:8000** in Chrome.

## Verification profile

The engine self-checks on startup against a hardcoded reference profile:

| Core Number | Expected | Derivation |
|---|---|---|
| Life Path | 2 | 6 + (23→5) + (1989→27→9) = 20 → 2 |
| Expression | 7 | 97 → 16 → 7 |
| Soul Urge | **33** | vowels total exactly 33 — master number, never reduced |
| Personality | 1 | 64 → 10 → 1 |

The Y in the middle name functions as a vowel (it is not adjacent to another
vowel), which is what produces the master 33 — the engine's Y-handling and
master-number preservation are both exercised by this single profile.

## API

- `GET /` — the dashboard
- `POST /api/calculate` — `{name, birth_date, birth_time, birth_place}` → numerology chart
- `GET /api/verify` — runs the hardcoded reference-profile self-check
- `GET /api/health` — engine status
