# Phoenix OS Build Agent Health Check (Windows Host)

Write-Host "=== Phoenix OS Build Agent: Windows Environment Check ===" -ForegroundColor Cyan

$Success = $true

# 1. Check Docker
Write-Host "Checking Docker Desktop..." -NoNewline
$DockerPath = Get-Command docker -ErrorAction SilentlyContinue
if ($DockerPath) {
    Write-Host " [OK]" -ForegroundColor Green
    docker --version
} else {
    Write-Host " [MISSING]" -ForegroundColor Red
    Write-Host " -> Please install Docker Desktop and add it to PATH."
    $Success = $false
}

# 2. Check WSL2
Write-Host "Checking WSL2 Status..." -NoNewline
$WSLCheck = wsl --list --running --quiet -ErrorAction SilentlyContinue
if ($null -ne $WSLCheck) {
    Write-Host " [OK]" -ForegroundColor Green
} else {
    Write-Host " [NOT RUNNING]" -ForegroundColor Yellow
    Write-Host " -> Ensure WSL2 is installed and a distribution (e.g. Ubuntu) is running."
}

# 3. Check Privileged Mode Capability
if ($DockerPath) {
    Write-Host "Checking Privileged Container Support..." -NoNewline
    try {
        $PrivCheck = docker run --rm --privileged debian:bookworm-slim echo "SUCCESS" -ErrorAction SilentlyContinue
        if ($PrivCheck -eq "SUCCESS") {
            Write-Host " [OK]" -ForegroundColor Green
        } else {
            Write-Host " [FAIL]" -ForegroundColor Red
            $Success = $false
        }
    } catch {
        Write-Host " [UNAVAILABLE]" -ForegroundColor Red
        $Success = $false
    }
}

Write-Host "---------------------------------------"
if ($Success) {
    Write-Host "STATUS: Local Build Agent is READY." -ForegroundColor Green
} else {
    Write-Host "STATUS: Local Build Agent is NOT READY." -ForegroundColor Red
    Write-Host "Refer to docs/LOCAL_BUILD_AGENT.md for setup instructions."
}
