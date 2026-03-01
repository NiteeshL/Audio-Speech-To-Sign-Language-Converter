param(
    [int]$Port = 8000
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$localCloudflared = Join-Path $repoRoot 'tools\cloudflared.exe'

$cloudflaredPath = $null
$pathCommand = Get-Command cloudflared -ErrorAction SilentlyContinue
if ($pathCommand) {
    $cloudflaredPath = $pathCommand.Source
} elseif (Test-Path $localCloudflared) {
    $cloudflaredPath = $localCloudflared
}

if (-not $cloudflaredPath) {
    Write-Error "cloudflared not found. Put cloudflared.exe in tools/ or install it globally."
    exit 1
}

try {
    Invoke-WebRequest -Uri "http://127.0.0.1:$Port" -UseBasicParsing -TimeoutSec 4 | Out-Null
} catch {
    Write-Warning "Local server http://127.0.0.1:$Port is not reachable right now. Start Django server first."
}

Write-Host "Starting Cloudflare HTTPS tunnel for http://127.0.0.1:$Port ..." -ForegroundColor Cyan
Write-Host "When you see https://*.trycloudflare.com, open that URL on your phone." -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the tunnel." -ForegroundColor Yellow

& $cloudflaredPath tunnel --url "http://127.0.0.1:$Port" --no-autoupdate
