[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][ValidateSet("msi", "nsis")][string]$InstallerKind,
    [Parameter(Mandatory = $true)][string]$BaselineInstaller,
    [Parameter(Mandatory = $true)][string]$CandidateInstaller,
    [Parameter(Mandatory = $true)][string]$OutputDirectory,
    [Parameter(Mandatory = $true)][ValidatePattern("^[0-9a-f]{40}$")][string]$BaselineCommit,
    [Parameter(Mandatory = $true)][ValidatePattern("^[0-9a-f]{40}$")][string]$CandidateCommit
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$ProductName = "PhoenixCore Desktop"
$BaselineVersion = "0.1.0"
$CandidateVersion = "0.1.1"
$BaselineInstaller = (Resolve-Path -LiteralPath $BaselineInstaller).Path
$CandidateInstaller = (Resolve-Path -LiteralPath $CandidateInstaller).Path
$OutputDirectory = [System.IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null

function Invoke-CheckedProcess {
    param([string]$FilePath, [string]$Arguments, [int[]]$AllowedExitCodes = @(0))
    Write-Host "PROCESS file=$FilePath arguments=$Arguments"
    $p = Start-Process -FilePath $FilePath -ArgumentList $Arguments -Wait -PassThru
    Write-Host "PROCESS_EXIT file=$FilePath exit_code=$($p.ExitCode)"
    if ($AllowedExitCodes -notcontains $p.ExitCode) { throw "Process failed: $FilePath exit=$($p.ExitCode)" }
    return $p.ExitCode
}

function Get-UninstallEntries {
    $paths = @(
        "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*",
        "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*",
        "HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*"
    )
    $entries = @()
    foreach ($path in $paths) {
        $entries += Get-ItemProperty -Path $path -ErrorAction SilentlyContinue |
            Where-Object { $_.PSObject.Properties.Name -contains "DisplayName" -and $_.DisplayName -eq $ProductName }
    }
    return @($entries)
}

function Find-Executable {
    $entries = @(Get-UninstallEntries)
    $candidates = @()
    foreach ($entry in $entries) {
        if ($entry.PSObject.Properties.Name -contains "InstallLocation" -and -not [string]::IsNullOrWhiteSpace([string]$entry.InstallLocation)) {
            $base = ([string]$entry.InstallLocation).Trim().Trim('"')
            $candidates += Join-Path $base "PhoenixCore Desktop.exe"
            $candidates += Join-Path $base "phoenixcore-desktop.exe"
        }
        if ($entry.PSObject.Properties.Name -contains "DisplayIcon" -and -not [string]::IsNullOrWhiteSpace([string]$entry.DisplayIcon)) {
            $candidates += ([string]$entry.DisplayIcon).Trim().Trim('"').Split(',')[0]
        }
    }
    if ($env:ProgramFiles) { $candidates += Join-Path $env:ProgramFiles "PhoenixCore Desktop\PhoenixCore Desktop.exe" }
    if ($env:LOCALAPPDATA) { $candidates += Join-Path $env:LOCALAPPDATA "PhoenixCore Desktop\PhoenixCore Desktop.exe" }
    foreach ($candidate in $candidates | Select-Object -Unique) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) { return (Resolve-Path -LiteralPath $candidate).Path }
    }
    throw "Installed PhoenixCore Desktop executable not found."
}

function Find-NsisUninstaller {
    $exe = Find-Executable
    $local = Join-Path (Split-Path -Parent $exe) "uninstall.exe"
    if (Test-Path -LiteralPath $local -PathType Leaf) { return (Resolve-Path -LiteralPath $local).Path }
    foreach ($entry in @(Get-UninstallEntries)) {
        if ($entry.PSObject.Properties.Name -contains "UninstallString") {
            $raw = [string]$entry.UninstallString
            if ($raw -match '^"([^"]+\.exe)"' -and (Test-Path -LiteralPath $Matches[1] -PathType Leaf)) {
                return (Resolve-Path -LiteralPath $Matches[1]).Path
            }
        }
    }
    throw "NSIS uninstaller not found."
}

function Install-Package {
    param([string]$Path, [string]$Tag)
    if ($InstallerKind -eq "msi") {
        return Invoke-CheckedProcess "msiexec.exe" "/i `"$Path`" /qn /norestart /L*V `"$(Join-Path $OutputDirectory "$Tag-install.log")`"" @(0, 3010)
    }
    return Invoke-CheckedProcess $Path "/S" @(0)
}

function Uninstall-Current {
    param([string]$MsiPath, [string]$Tag)
    if ($InstallerKind -eq "msi") {
        return Invoke-CheckedProcess "msiexec.exe" "/x `"$MsiPath`" /qn /norestart /L*V `"$(Join-Path $OutputDirectory "$Tag-uninstall.log")`"" @(0, 3010)
    }
    return Invoke-CheckedProcess (Find-NsisUninstaller) "/S" @(0)
}

function Assert-Smoke {
    param([string]$ExpectedVersion, [string]$ExpectedCommit, [string]$Tag)
    $exe = Find-Executable
    $receiptPath = Join-Path $OutputDirectory "$Tag-smoke.json"
    $old = $env:PHOENIXCORE_DESKTOP_SMOKE_RECEIPT
    try {
        $env:PHOENIXCORE_DESKTOP_SMOKE_RECEIPT = $receiptPath
        $p = Start-Process -FilePath $exe -ArgumentList "--smoke-test" -Wait -PassThru
    } finally {
        if ($null -eq $old) { Remove-Item Env:\PHOENIXCORE_DESKTOP_SMOKE_RECEIPT -ErrorAction SilentlyContinue }
        else { $env:PHOENIXCORE_DESKTOP_SMOKE_RECEIPT = $old }
    }
    if ($p.ExitCode -ne 0) { throw "$Tag smoke exit=$($p.ExitCode)" }
    $receipt = Get-Content -LiteralPath $receiptPath -Raw | ConvertFrom-Json
    if ($receipt.schema_version -ne "bws.phoenixcore-desktop-installed-smoke/v1") { throw "$Tag smoke schema mismatch" }
    if ($receipt.version -ne $ExpectedVersion) { throw "$Tag version mismatch: $($receipt.version) != $ExpectedVersion" }
    if ($receipt.source_commit -ne $ExpectedCommit) { throw "$Tag source mismatch: $($receipt.source_commit) != $ExpectedCommit" }
    if ($receipt.status -ne "pass") { throw "$Tag smoke receipt did not pass" }
    return [ordered]@{
        status = "pass"
        version = $ExpectedVersion
        source_commit = $ExpectedCommit
        executable_sha256 = (Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant()
        smoke_receipt = [System.IO.Path]::GetFileName($receiptPath)
    }
}

if (@(Get-UninstallEntries).Count -ne 0) { throw "Runner is not clean before Desktop update/rollback proof." }

$baselineInstallExit = Install-Package $BaselineInstaller "baseline"
Start-Sleep -Seconds 2
$baselineBefore = Assert-Smoke $BaselineVersion $BaselineCommit "baseline-before-update"

$candidateInstallExit = Install-Package $CandidateInstaller "candidate-update"
Start-Sleep -Seconds 2
$candidateAfter = Assert-Smoke $CandidateVersion $CandidateCommit "candidate-after-update"

$candidateUninstallExit = Uninstall-Current $CandidateInstaller "candidate-rollback-remove"
Start-Sleep -Seconds 2
if (@(Get-UninstallEntries).Count -ne 0) { throw "Candidate registration remains before rollback reinstall." }

$baselineRollbackInstallExit = Install-Package $BaselineInstaller "baseline-rollback"
Start-Sleep -Seconds 2
$baselineAfter = Assert-Smoke $BaselineVersion $BaselineCommit "baseline-after-rollback"

$baselineCleanupExit = Uninstall-Current $BaselineInstaller "baseline-cleanup"
Start-Sleep -Seconds 2
if (@(Get-UninstallEntries).Count -ne 0) { throw "PhoenixCore Desktop registration remains after cleanup." }
try { [void](Find-Executable); throw "PhoenixCore Desktop executable remains after cleanup." } catch { if ($_.Exception.Message -eq "PhoenixCore Desktop executable remains after cleanup.") { throw } }

$receipt = [ordered]@{
    schema_version = "bws.phoenixcore-desktop-update-rollback/v1"
    app_id = "phoenixcore-desktop"
    product_name = $ProductName
    installer_kind = $InstallerKind
    baseline = [ordered]@{
        version = $BaselineVersion
        source_commit = $BaselineCommit
        installer_sha256 = (Get-FileHash -LiteralPath $BaselineInstaller -Algorithm SHA256).Hash.ToLowerInvariant()
        install_exit_code = $baselineInstallExit
        smoke = $baselineBefore
    }
    update = [ordered]@{
        status = "pass"
        from_version = $BaselineVersion
        to_version = $CandidateVersion
        candidate_source_commit = $CandidateCommit
        installer_sha256 = (Get-FileHash -LiteralPath $CandidateInstaller -Algorithm SHA256).Hash.ToLowerInvariant()
        install_exit_code = $candidateInstallExit
        smoke = $candidateAfter
    }
    rollback = [ordered]@{
        status = "pass"
        mechanism = "uninstall-candidate-then-reinstall-known-good-baseline"
        from_version = $CandidateVersion
        to_version = $BaselineVersion
        remove_candidate_exit_code = $candidateUninstallExit
        reinstall_baseline_exit_code = $baselineRollbackInstallExit
        smoke = $baselineAfter
    }
    cleanup = [ordered]@{
        status = "pass"
        uninstall_exit_code = $baselineCleanupExit
        registration_remaining = $false
        executable_remaining = $false
    }
    packaged_vite_api_bridge = "not-verified"
    signing = "not-proven"
    arcwyre_compatibility = "not-proven"
    release_eligible = $false
    status = "update-rollback-pass"
}

$receiptPath = Join-Path $OutputDirectory "$InstallerKind-update-rollback-receipt.json"
$receipt | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $receiptPath -Encoding utf8
$receiptHash = (Get-FileHash -LiteralPath $receiptPath -Algorithm SHA256).Hash.ToLowerInvariant()
Write-Host "PHOENIXCORE_DESKTOP_UPDATE_ROLLBACK_PASS kind=$InstallerKind receipt=$receiptPath sha256=$receiptHash"
