#!/usr/bin/env bash
# Blueprint Calculator — one-command launcher.
# Creates the virtual environment on first run, installs dependencies,
# runs the verification suite, then starts the dashboard on port 8000.
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d venv ]; then
  echo "→ Creating virtual environment..."
  python3 -m venv venv
fi

source venv/bin/activate

echo "→ Syncing dependencies..."
pip install --quiet -r requirements.txt

echo "→ Running verification tests..."
python -m pytest tests/ -q

echo "→ Starting Blueprint Calculator at http://localhost:8000"
exec uvicorn main:app --host 0.0.0.0 --port 8000 "$@"
