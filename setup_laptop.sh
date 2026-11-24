#!/usr/bin/env bash
# One-command setup for macOS / Linux after cloning the repo.
# Usage: bash setup_laptop.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

echo "==> Backend: create virtual environment"
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

echo "==> Backend: create local .env (if missing)"
if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created backend/.env — add your Groq key there."
else
  echo "backend/.env already exists — left unchanged."
fi

echo "==> Frontend: install dependencies"
cd ../frontend
npm ci
if [ ! -f .env ]; then
  cp .env.example .env
fi

echo
echo "SETUP DONE (macOS/Linux)"
echo "1. Add your key securely:  cd backend && .venv/bin/python -m scripts.set_groq_key"
echo "2. Start API:              cd backend && source .venv/bin/activate && uvicorn app.api.main:app --host 0.0.0.0 --port 8000"
echo "3. Start UI (new terminal): cd frontend && npm run dev"
echo "4. Open:                   http://localhost:5173"
echo "5. Verify:                 cd backend && .venv/bin/python -m scripts.smoke_groq"
