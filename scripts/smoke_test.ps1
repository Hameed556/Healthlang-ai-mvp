<#
PowerShell smoke test for Healthlang AI MVP

Usage:
  # Run against local server and also inspect DB (optional)
  .\scripts\smoke_test.ps1 -BaseUrl http://127.0.0.1:8001 -DatabaseUrl "postgresql+psycopg2://user:pass@host:5432/healthlang?sslmode=require"

What it does:
  - Registers a unique test user
  - Logs in (form-encoded) to obtain a Bearer token
  - Creates a conversation and prints the returned conversation object
  - Sends a message using the API's `text` query parameter
  - Optionally sets $env:DATABASE_URL and runs scripts/db_inspect.py to show DB counts

Note: keep credentials and DB URL secure. This script is for quick local/dev verification only.
#>

param(
    [string]$BaseUrl = 'http://127.0.0.1:8001',
    [string]$DatabaseUrl = ''
)

$ErrorActionPreference = 'Stop'

# unique username for the run
$id = Get-Random -Minimum 1000 -Maximum 9999
$username = "smoketest_$id"
$email = "$username@example.com"
Write-Host "Using test user: $username ($email)"

# Register
$reg = @{ username = $username; email = $email; password = 'Secret123!' } | ConvertTo-Json
Write-Host "Registering user..."
try {
    $regResp = Invoke-RestMethod -Method Post -Uri "${BaseUrl}/api/v1/auth/register" -Body $reg -ContentType 'application/json'
    Write-Host "REGISTER_RESPONSE:"; $regResp | ConvertTo-Json -Depth 10 | Out-Host
} catch {
    Write-Host "REGISTER_FAILED:" -ForegroundColor Red
    if ($_.Exception.Response) { $_.Exception.Response.Content | Out-Host } else { $_.Exception.Message | Out-Host }
    exit 1
}

# Login (form-encoded)
$form = @{ username = $username; password = 'Secret123!' }
Write-Host "Logging in..."
try {
    $loginResp = Invoke-RestMethod -Method Post -Uri "${BaseUrl}/api/v1/auth/login" -Body $form -ContentType 'application/x-www-form-urlencoded'
    Write-Host "LOGIN_RESPONSE:"; $loginResp | ConvertTo-Json -Depth 10 | Out-Host
    $token = $loginResp.access_token
} catch {
    Write-Host "LOGIN_FAILED:" -ForegroundColor Red
    if ($_.Exception.Response) { $_.Exception.Response.Content | Out-Host } else { $_.Exception.Message | Out-Host }
    exit 1
}

# Create conversation
$headers = @{ Authorization = "Bearer $token" }
$convBody = @{ title = 'Smoke Chat' } | ConvertTo-Json
Write-Host "Creating conversation..."
try {
    $conv = Invoke-RestMethod -Method Post -Uri "${BaseUrl}/api/v1/chat/conversations" -Headers $headers -Body $convBody -ContentType 'application/json'
    Write-Host "CREATE_CONV_RESPONSE:"; $conv | ConvertTo-Json -Depth 10 | Out-Host
    $convId = $conv.conversation_id
    Write-Host "convId = $convId"
} catch {
    Write-Host "CREATE_CONV_FAILED:" -ForegroundColor Red
    if ($_.Exception.Response) { $_.Exception.Response.Content | Out-Host } else { $_.Exception.Message | Out-Host }
    exit 1
}

if (-not $convId) {
    Write-Host "No conversation id returned. Aborting." -ForegroundColor Red
    exit 1
}

# Send message (API expects ?text=...)
$text = [System.Uri]::EscapeDataString('Hello from smoke test')
$uri = "${BaseUrl}/api/v1/chat/conversations/$convId/messages?text=$text"
Write-Host "POSTING to: $uri"
try {
    $reply = Invoke-RestMethod -Method Post -Uri $uri -Headers $headers -ContentType 'application/json'
    Write-Host "SEND_MESSAGE_REPLY:"; $reply | ConvertTo-Json -Depth 10 | Out-Host
} catch {
    Write-Host "SEND_MSG_FAILED:" -ForegroundColor Red
    if ($_.Exception.Response) { $_.Exception.Response.Content | Out-Host } else { $_.Exception.Message | Out-Host }
    exit 1
}

# Optional DB inspect
if ($DatabaseUrl -ne '') {
    Write-Host "Running DB inspect with provided DATABASE_URL..."
    $env:DATABASE_URL = $DatabaseUrl
    try {
        .\.venv\Scripts\python.exe scripts/db_inspect.py
    } catch {
        Write-Host "DB inspect failed:" -ForegroundColor Yellow
        $_.Exception.Message | Out-Host
    }
} else {
    Write-Host "No DatabaseUrl supplied; skipping DB inspect. To run inspect, pass -DatabaseUrl '<your DATABASE_URL>'"
}

Write-Host "Smoke test complete."