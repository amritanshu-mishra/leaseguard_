# One-command setup for Windows PowerShell after cloning the repo.
# Usage: powershell -ExecutionPolicy Bypass -File setup_laptop.ps1
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

Write-Host "==> Backend: create virtual environment"
Set-Location backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

Write-Host "==> Backend: create local .env (if missing)"
if (-Not (Test-Path .env)) {
  Copy-Item .env.example .env
  Write-Host "Created backend\.env — add your Groq key there."
} else {
  Write-Host "backend\.env already exists — left unchanged."
}

Write-Host "==> Frontend: install dependencies"
Set-Location ..\frontend
npm ci
if (-Not (Test-Path .env)) { Copy-Item .env.example .env }

Write-Host ""
Write-Host "SETUP DONE (Windows)"
Write-Host "1. Add your key securely:  cd backend; python -m scripts.set_groq_key"
Write-Host "2. Start API:              cd backend; .\.venv\Scripts\Activate.ps1; python -m uvicorn app.api.main:app --host 0.0.0.0 --port 8000"
Write-Host "3. Start UI (new terminal): cd frontend; npm run dev"
Write-Host "4. Open:                   http://localhost:5173"
Write-Host "5. Verify:                 cd backend; python -m scripts.smoke_groq"
