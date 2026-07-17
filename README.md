# Blueprint Calculator

A local, offline, web-based esoteric calculation dashboard that synthesizes
**Numerology**, **Western (Tropical) Astrology**, **Vedic (Sidereal) Astrology**,
**Human Design**, and **Gene Keys** into a single Soul Blueprint.

- **Phase 1** — FastAPI backend, Tailwind dark dashboard shell, Pythagorean
  numerology engine (master numbers 11/22/33 preserved).
- **Phase 2** — Swiss Ephemeris astronomy engine: tropical planets + Chiron,
  Placidus houses, ASC/MC; Lahiri sidereal positions, rashis, nakshatras;
  offline geocoding and historical timezone/DST resolution.
- **Phase 3** — Human Design bodygraph (gates, channels, centers, Type,
  Authority, Profile, Definition, 88° prenatal Design calculation), Gene Keys
  Activation Sequence, the Soul Blueprint synthesis summary, and a
  print-friendly report stylesheet.

## Setup (Chromebook / Crostini Debian 12, ARM64)

```bash
# 1. Compiler toolchain — required so pip can build the pyswisseph
#    C-extension on ARM64 (Snapdragon):
sudo apt update
sudo apt install -y build-essential python3-dev

# 2. Launch (creates venv, installs deps, runs tests, starts server):
cd ~/Blueprint-Calculator
./start.sh
```

Then open **http://localhost:8000** in Chrome. Use the **⎙ Save Report /
PDF** button on the Summary tab (or Ctrl+P) to export the full blueprint as
a clean, light-themed printable report.

Manual setup, if you prefer it over `start.sh`:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m pytest tests/ -q
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Architecture

| Piece | Role |
|---|---|
| `main.py` | FastAPI router — serves the dashboard and `/api/*` endpoints |
| `engines/numerology.py` | Pythagorean core numbers, master-number-safe reduction |
| `engines/geolocation.py` | Offline city gazetteer + historical timezone/DST via `zoneinfo` |
| `engines/ephemeris.py` | Shared Swiss Ephemeris plumbing (bundled `ephe/` data files) |
| `engines/western_astrology.py` | Tropical longitudes, Placidus cusps, ASC/MC/DSC/IC |
| `engines/vedic_astrology.py` | Lahiri ayanamsa, rashis, 27 nakshatras + padas, Rahu/Ketu |
| `engines/human_design.py` | Rave Mandala mapping, 88° Design solver, Type/Authority/Profile |
| `engines/gene_keys.py` | 64-key spectrum data + Activation Sequence |
| `engines/synthesis.py` | Soul Blueprint narrative + archetype grid |
| `templates/index.html` | Single-page Tailwind dashboard, six tabs + print stylesheet |
| `ephe/*.se1` | Swiss Ephemeris data (1800–2400 AD; enables Chiron, full precision) |

Notes on conventions:

- The Human Design wheel is anchored canonically — Gate 41 begins at
  **02°00' Aquarius** (302°), which places the Rave New Year at the Sun's
  Gate-41 ingress (~Jan 22) and 0° Aries inside Gate 25.
- The Design moment solves the solar equation (natal Sun − 88°) by Newton
  iteration on the smallest signed angle, so the 0° Aries crossing cannot
  cause loops.
- Vedic nodes use the mean node (Rahu/Ketu); Human Design uses the true node.
- Numerology treats Y as a vowel when it is not adjacent to another vowel.

## API

- `GET /` — the dashboard
- `POST /api/calculate` — `{name, birth_date, birth_time, birth_place}` →
  numerology + western + vedic + human design + gene keys + synthesis
- `GET /api/verify` — hardcoded numerology reference-profile self-check
- `GET /api/health` — engine status

## Verification profile

All engines are pinned by tests (`python -m pytest tests/ -q`) to the
reference profile **Johnathon Anthony Long — June 23 1989, 21:55,
Atlanta, GA** (EDT → 1989-06-24 01:55 UT):

| System | Result |
|---|---|
| Life Path / Expression / Soul Urge / Personality | 2 / 7 / **33** / 1 |
| Tropical Sun · Moon · ASC · MC | 2°33' Cancer · 2°29' Pisces · 19°16' Capricorn · 8°57' Scorpio |
| Lahiri ayanamsa | 23°42'36" |
| Sidereal Moon | 8°47' Kumbha — Shatabhisha, pada 1 |
| Human Design | Projector · Splenic authority · 5/1 · Split Definition |
| Gene Keys Activation | Life's Work 15.5 · Evolution 10.5 · Radiance 17.1 · Purpose 18.1 |
