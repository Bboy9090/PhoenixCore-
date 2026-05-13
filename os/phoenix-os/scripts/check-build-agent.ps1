[CmdletBinding()]
param(
    [string]$Distro = "Ubuntu",
    [switch]$CheckWSLDocker
)

$ErrorActionPreference = "Stop"

$script:Failures = 0
$script:Warnings = 0

function Pass([string]$Message) {
    Write-Host "[PASS] $Message" -ForegroundColor Green
}

function Warn([string]$Message) {
    $script:Warnings++
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Fail([string]$Message) {
    $script:Failures++
    Write-Host "[FAIL] $Message" -ForegroundColor Red
}

function Info([string]$Message) {
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

try {
    $build = [Environment]::OSVersion.Version.Build
    if ($build -ge 22000) {
        Pass "Windows build $build detected (Windows 11 compatible)."
    }
    else {
        Warn "Windows build $build detected (below Windows 11 baseline)."
    }
}
catch {
    Warn "Unable to determine Windows build number."
}

$wslCmd = Get-Command wsl -ErrorAction SilentlyContinue
if ($null -eq $wslCmd) {
    Fail "WSL command not found. Install WSL2 first."
}
else {
    Pass "WSL command found: $($wslCmd.Source)"

    try {
        $wslStatus = wsl --status 2>$null
        if ($LASTEXITCODE -eq 0) {
            Pass "WSL status query succeeded."
            if ($wslStatus -match "Default Version:\s*2") {
                Pass "WSL default version is 2."
            }
            else {
                Warn "WSL default version is not reported as 2."
            }
        }
        else {
            Warn "Unable to query WSL status."
        }
    }
    catch {
        Warn "WSL status query threw an error: $($_.Exception.Message)"
    }

    try {
        $distroOutput = wsl -l -v 2>$null
        if ($LASTEXITCODE -eq 0 -and $distroOutput) {
            $joined = ($distroOutput -join "`n")
            if ($joined -match "(?m)^\s*\*?\s*$([regex]::Escape($Distro))\s+") {
                Pass "WSL distro '$Distro' is installed."
                if ($joined -match "(?m)^\s*\*?\s*$([regex]::Escape($Distro))\s+\S+\s+2\s*$") {
                    Pass "WSL distro '$Distro' is running version 2."
                }
                else {
                    Warn "WSL distro '$Distro' is not reported as version 2."
                }
            }
            else {
                Warn "WSL distro '$Distro' was not found in 'wsl -l -v'."
            }
        }
        else {
            Warn "Unable to list WSL distros."
        }
    }
    catch {
        Warn "WSL distro listing failed: $($_.Exception.Message)"
    }
}

$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
if ($null -eq $dockerCmd) {
    Fail "docker command not found in PATH. Install/start Docker Desktop."
}
else {
    Pass "docker command found: $($dockerCmd.Source)"

    try {
        $dockerVersion = docker version --format '{{.Server.Version}}' 2>$null
        if ($LASTEXITCODE -eq 0 -and $dockerVersion) {
            Pass "Docker daemon reachable (server version $dockerVersion)."
        }
        else {
            Fail "Docker daemon unreachable. Ensure Docker Desktop is running."
        }
    }
    catch {
        Fail "Docker daemon check failed: $($_.Exception.Message)"
    }

    try {
        $composeVersion = docker compose version 2>$null
        if ($LASTEXITCODE -eq 0 -and $composeVersion) {
            $composeLine = ($composeVersion | Select-Object -First 1)
            Pass "Docker Compose available: $composeLine"
        }
        else {
            Warn "'docker compose' command failed. Check Compose v2 plugin."
        }
    }
    catch {
        Warn "Docker Compose check failed: $($_.Exception.Message)"
    }
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$containerDir = Join-Path (Split-Path -Parent $scriptDir) "container"
$verifyScript = Join-Path $containerDir "verify-container.sh"
$buildScript = Join-Path $containerDir "build-container.sh"

if (Test-Path $verifyScript) {
    Pass "Found helper: os/phoenix-os/container/verify-container.sh"
}
else {
    Warn "Missing helper: os/phoenix-os/container/verify-container.sh"
}

if (Test-Path $buildScript) {
    Pass "Found helper: os/phoenix-os/container/build-container.sh"
}
else {
    Warn "Missing helper: os/phoenix-os/container/build-container.sh"
}

if ($CheckWSLDocker.IsPresent -and $null -ne $wslCmd) {
    Info "Running WSL Docker cross-check in distro '$Distro'."
    try {
        $checkResult = wsl -d $Distro -- bash -lc "docker version >/dev/null 2>&1 && docker compose version >/dev/null 2>&1"
        if ($LASTEXITCODE -eq 0) {
            Pass "Docker and Compose commands succeeded inside WSL distro '$Distro'."
        }
        else {
            Fail "Docker/Compose failed inside WSL distro '$Distro'."
        }
    }
    catch {
        Fail "WSL Docker cross-check failed: $($_.Exception.Message)"
    }
}
else {
    Info "WSL Docker cross-check skipped. Use -CheckWSLDocker to enable."
}

if ($script:Failures -gt 0) {
    Write-Host ""
    Write-Host "Build-agent preflight FAILED ($script:Failures failures, $script:Warnings warnings)." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Build-agent preflight PASSED (0 failures, $script:Warnings warnings)." -ForegroundColor Green
exit 0
