$ErrorActionPreference = "Stop"

# --- Settings ---
$VenvPath = "F:\venvs\Meeting_AI"
$BackendRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$EnvFile = Join-Path $BackendRoot ".env"

Write-Host "Backend root: $BackendRoot"

# --- Activate venv ---
$Activate = Join-Path $VenvPath "Scripts\Activate.ps1"
if (-not (Test-Path $Activate)) {
    throw "Virtualenv not found at $Activate. Update VenvPath in this script."
}
. $Activate

# --- Load .env into this session (for safety; Alembic also loads it in env.py) ---
Get-Content $EnvFile | ForEach-Object {
    if ($_ -match "^\s*#") { return }
    if ($_ -match "^\s*$") { return }
    $kv = $_.Split("=",2)
    if ($kv.Count -eq 2) {
        $name = $kv[0].Trim()
        $value = $kv[1].Trim()
        [System.Environment]::SetEnvironmentVariable($name, $value)
        Set-Item -Path "Env:$name" -Value $value | Out-Null
    }
}

# --- Ensure Docker Compose DB is up ---
Write-Host "Starting Docker Compose (db)..."
Push-Location $BackendRoot
docker compose up -d | Out-Null

# --- Wait for Postgres port ---
$HostPort = 5432
if ($env:DATABASE_URL -and $env:DATABASE_URL -match "localhost:(\d+)") {
    $HostPort = [int]$Matches[1]
}
Write-Host "Waiting for Postgres on port $HostPort..."
for ($i=0; $i -lt 30; $i++) {
    try {
        $client = New-Object System.Net.Sockets.TcpClient("localhost", $HostPort)
        $client.Close()
        Write-Host "Postgres is reachable."
        break
    } catch {
        Start-Sleep -Seconds 1
        if ($i -eq 29) { throw "Postgres did not become reachable on port $HostPort." }
    }
}

# --- Run migrations ---
Write-Host "Applying Alembic migrations..."
alembic upgrade head

# --- Start API ---
Write-Host "Starting Uvicorn..."
uvicorn app.main:app --reload
Pop-Location
