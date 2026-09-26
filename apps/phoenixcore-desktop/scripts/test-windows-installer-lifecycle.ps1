[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("msi", "nsis")]
    [string]$InstallerKind,

    [Parameter(Mandatory = $true)]
    [string]$InstallerPath,

    [Parameter(Mandatory = $true)]
    [string]$OutputDirectory,

    [Parameter(Mandatory = $true)]
    [ValidatePattern("^[0-9a-f]{40}$")]
    [string]$SourceCommit
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$ProductName = "PhoenixCore Desktop"
$AppId = "phoenixcore-desktop"
$Version = "0.1.0"
$InstallerPath = (Resolve-Path -LiteralPath $InstallerPath).Path
$OutputDirectory = [System.IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null

$InstallLog = Join-Path $OutputDirectory "$InstallerKind-install.log"
$UninstallLog = Join-Path $OutputDirectory "$InstallerKind-uninstall.log"
$SmokeReceiptPath = Join-Path $OutputDirectory "$InstallerKind-installed-smoke.json"
$LifecycleReceiptPath = Join-Path $OutputDirectory "$InstallerKind-lifecycle-receipt.json"
$FailureReceiptPath = Join-Path $OutputDirectory "$InstallerKind-lifecycle-failure.json"

function Write-JsonFile {
    param([Parameter(Mandatory = $true)][object]$Value, [Parameter(Mandatory = $true)][string]$Path)
    $Value | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $Path -Encoding utf8
}

function Invoke-CheckedProcess {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string]$Arguments,
        [int[]]$AllowedExitCodes = @(0)
    )
    Write-Host "PROCESS file=$FilePath arguments=$Arguments"
    $Process = Start-Process -FilePath $FilePath -ArgumentList $Arguments -Wait -PassThru
    Write-Host "PROCESS_EXIT file=$FilePath exit_code=$($Process.ExitCode)"
    if ($AllowedExitCodes -notcontains $Process.ExitCode) {
        throw "Process failed: $FilePath exited with $($Process.ExitCode); allowed=$($AllowedExitCodes -join ',')"
    }
    return $Process.ExitCode
}

function Get-DesktopUninstallEntries {
    $RegistryPaths = @(
        "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*",
        "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*",
        "HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*"
    )
    $Entries = @()
    foreach ($RegistryPath in $RegistryPaths) {
        $Entries += Get-ItemProperty -Path $RegistryPath -ErrorAction SilentlyContinue |
            Where-Object {
                $_.PSObject.Properties.Name -contains "DisplayName" -and
                $_.DisplayName -eq $ProductName
            }
    }
    return @($Entries)
}

function Add-CandidatePath {
    param(
        [AllowEmptyCollection()][System.Collections.Generic.List[string]]$Candidates,
        [AllowNull()][string]$Path
    )
    if ([string]::IsNullOrWhiteSpace($Path)) { return }
    $Clean = $Path.Trim().Trim('"')
    if ($Clean -match "^(.*?\.exe)(?:,\d+)?$") { $Clean = $Matches[1] }
    if (-not [string]::IsNullOrWhiteSpace($Clean) -and -not $Candidates.Contains($Clean)) {
        $Candidates.Add($Clean)
    }
}

function Find-DesktopExecutable {
    param([Parameter(Mandatory = $true)][object[]]$UninstallEntries)
    $Candidates = [System.Collections.Generic.List[string]]::new()
    foreach ($Entry in $UninstallEntries) {
        if ($Entry.PSObject.Properties.Name -contains "InstallLocation") {
            $InstallLocation = ([string]$Entry.InstallLocation).Trim().Trim('"')
            if (-not [string]::IsNullOrWhiteSpace($InstallLocation)) {
                Add-CandidatePath -Candidates $Candidates -Path (Join-Path $InstallLocation "PhoenixCore Desktop.exe")
                Add-CandidatePath -Candidates $Candidates -Path (Join-Path $InstallLocation "phoenixcore-desktop.exe")
            }
        }
        if ($Entry.PSObject.Properties.Name -contains "DisplayIcon") {
            Add-CandidatePath -Candidates $Candidates -Path ([string]$Entry.DisplayIcon)
        }
    }
    if ($env:ProgramFiles) {
        Add-CandidatePath -Candidates $Candidates -Path (Join-Path $env:ProgramFiles "PhoenixCore Desktop\PhoenixCore Desktop.exe")
    }
    if (${env:ProgramFiles(x86)}) {
        Add-CandidatePath -Candidates $Candidates -Path (Join-Path ${env:ProgramFiles(x86)} "PhoenixCore Desktop\PhoenixCore Desktop.exe")
    }
    if ($env:LOCALAPPDATA) {
        Add-CandidatePath -Candidates $Candidates -Path (Join-Path $env:LOCALAPPDATA "PhoenixCore Desktop\PhoenixCore Desktop.exe")
    }
    foreach ($Candidate in $Candidates) {
        if (Test-Path -LiteralPath $Candidate -PathType Leaf) {
            return (Resolve-Path -LiteralPath $Candidate).Path
        }
    }
    throw "Installed PhoenixCore Desktop executable was not found. Candidates: $($Candidates -join '; ')"
}

function Find-NsisUninstaller {
    param([Parameter(Mandatory = $true)][string]$ExecutablePath, [Parameter(Mandatory = $true)][object[]]$UninstallEntries)
    $LocalCandidate = Join-Path (Split-Path -Parent $ExecutablePath) "uninstall.exe"
    if (Test-Path -LiteralPath $LocalCandidate -PathType Leaf) {
        return (Resolve-Path -LiteralPath $LocalCandidate).Path
    }
    foreach ($Entry in $UninstallEntries) {
        if ($Entry.PSObject.Properties.Name -contains "UninstallString") {
            $Raw = [string]$Entry.UninstallString
            if ($Raw -match '^"([^"]+\.exe)"') {
                if (Test-Path -LiteralPath $Matches[1] -PathType Leaf) { return (Resolve-Path -LiteralPath $Matches[1]).Path }
            } elseif ($Raw -match '^(.*?\.exe)(?:\s|$)') {
                $Candidate = $Matches[1].Trim('"')
                if (Test-Path -LiteralPath $Candidate -PathType Leaf) { return (Resolve-Path -LiteralPath $Candidate).Path }
            }
        }
    }
    throw "NSIS uninstaller was not found."
}

$Installed = $false
$InstalledExecutable = $null
$InstalledEntries = @()

try {
    $PreInstallEntries = @(Get-DesktopUninstallEntries)
    if ($PreInstallEntries.Count -ne 0) { throw "Runner is not clean: PhoenixCore Desktop is already registered." }

    $InstallerInfo = Get-Item -LiteralPath $InstallerPath
    if ($InstallerInfo.Length -le 0) { throw "Installer is empty: $InstallerPath" }
    $InstallerHash = (Get-FileHash -LiteralPath $InstallerPath -Algorithm SHA256).Hash.ToLowerInvariant()

    if ($InstallerKind -eq "msi") {
        $InstallExitCode = Invoke-CheckedProcess -FilePath "msiexec.exe" -Arguments "/i `"$InstallerPath`" /qn /norestart /L*V `"$InstallLog`"" -AllowedExitCodes @(0,3010)
    } else {
        $InstallExitCode = Invoke-CheckedProcess -FilePath $InstallerPath -Arguments "/S" -AllowedExitCodes @(0)
        "NSIS silent install exit code: $InstallExitCode" | Set-Content -LiteralPath $InstallLog -Encoding utf8
    }
    $Installed = $true
    Start-Sleep -Seconds 3

    $InstalledEntries = @(Get-DesktopUninstallEntries)
    if ($InstalledEntries.Count -lt 1) { throw "PhoenixCore Desktop did not create uninstall registration." }
    $InstalledExecutable = Find-DesktopExecutable -UninstallEntries $InstalledEntries
    $InstalledExecutableHash = (Get-FileHash -LiteralPath $InstalledExecutable -Algorithm SHA256).Hash.ToLowerInvariant()
    $InstalledExecutableSize = (Get-Item -LiteralPath $InstalledExecutable).Length

    $PreviousSmokeReceipt = $env:PHOENIXCORE_DESKTOP_SMOKE_RECEIPT
    try {
        $env:PHOENIXCORE_DESKTOP_SMOKE_RECEIPT = $SmokeReceiptPath
        $LaunchProcess = Start-Process -FilePath $InstalledExecutable -ArgumentList "--smoke-test" -Wait -PassThru
    } finally {
        if ($null -eq $PreviousSmokeReceipt) { Remove-Item Env:\PHOENIXCORE_DESKTOP_SMOKE_RECEIPT -ErrorAction SilentlyContinue }
        else { $env:PHOENIXCORE_DESKTOP_SMOKE_RECEIPT = $PreviousSmokeReceipt }
    }
    if ($LaunchProcess.ExitCode -ne 0) { throw "Installed smoke process exited with $($LaunchProcess.ExitCode)." }
    if (-not (Test-Path -LiteralPath $SmokeReceiptPath -PathType Leaf)) { throw "Installed smoke receipt missing." }
    $SmokeReceipt = Get-Content -LiteralPath $SmokeReceiptPath -Raw | ConvertFrom-Json
    if ($SmokeReceipt.schema_version -ne "bws.phoenixcore-desktop-installed-smoke/v1") { throw "Unexpected smoke schema." }
    if ($SmokeReceipt.app_id -ne $AppId -or $SmokeReceipt.version -ne $Version) { throw "Installed smoke identity mismatch." }
    if ($SmokeReceipt.source_commit -ne $SourceCommit) { throw "Installed smoke source mismatch: $($SmokeReceipt.source_commit) != $SourceCommit" }
    if ($SmokeReceipt.status -ne "pass") { throw "Installed smoke did not pass." }

    if ($InstallerKind -eq "msi") {
        $UninstallExitCode = Invoke-CheckedProcess -FilePath "msiexec.exe" -Arguments "/x `"$InstallerPath`" /qn /norestart /L*V `"$UninstallLog`"" -AllowedExitCodes @(0,3010)
    } else {
        $NsisUninstaller = Find-NsisUninstaller -ExecutablePath $InstalledExecutable -UninstallEntries $InstalledEntries
        $UninstallExitCode = Invoke-CheckedProcess -FilePath $NsisUninstaller -Arguments "/S" -AllowedExitCodes @(0)
        "NSIS silent uninstall exit code: $UninstallExitCode" | Set-Content -LiteralPath $UninstallLog -Encoding utf8
    }
    $Installed = $false
    Start-Sleep -Seconds 4

    $RemainingEntries = @(Get-DesktopUninstallEntries)
    if ($RemainingEntries.Count -ne 0) { throw "PhoenixCore Desktop uninstall registration remains." }
    if (Test-Path -LiteralPath $InstalledExecutable -PathType Leaf) { throw "PhoenixCore Desktop executable remains after uninstall." }

    $LifecycleReceipt = [ordered]@{
        schema_version = "bws.app-lifecycle/v1"
        app_id = $AppId
        product_name = $ProductName
        version = $Version
        source = [ordered]@{ repository = "Bboy9090/PhoenixCore-"; commit = $SourceCommit }
        target = [ordered]@{ operating_system = "windows"; architecture = "x86_64"; runner = [System.Environment]::OSVersion.VersionString }
        installer = [ordered]@{ kind = $InstallerKind; filename = $InstallerInfo.Name; size_bytes = $InstallerInfo.Length; sha256 = $InstallerHash }
        install = [ordered]@{ status = "pass"; exit_code = $InstallExitCode; uninstall_registration_count = $InstalledEntries.Count; log = [System.IO.Path]::GetFileName($InstallLog) }
        launch = [ordered]@{ status = "pass"; executable_path = $InstalledExecutable; executable_size_bytes = $InstalledExecutableSize; executable_sha256 = $InstalledExecutableHash; process_exit_code = $LaunchProcess.ExitCode; smoke_receipt = [System.IO.Path]::GetFileName($SmokeReceiptPath) }
        update = [ordered]@{ status = "not-run"; reason = "first PhoenixCore Desktop package version" }
        rollback = [ordered]@{ status = "not-run"; reason = "no prior PhoenixCore Desktop package version exists" }
        uninstall = [ordered]@{ status = "pass"; exit_code = $UninstallExitCode; registration_remaining = $false; executable_remaining = $false; log = [System.IO.Path]::GetFileName($UninstallLog) }
        packaged_vite_api_bridge = "not-verified"
        signing = "not-run"
        artifact_class = "unsigned-preview-host-lifecycle"
        status = "install-launch-uninstall-pass-update-rollback-not-run"
        release_eligible = $false
    }
    Write-JsonFile -Value $LifecycleReceipt -Path $LifecycleReceiptPath
    $ReceiptHash = (Get-FileHash -LiteralPath $LifecycleReceiptPath -Algorithm SHA256).Hash.ToLowerInvariant()
    "$ReceiptHash  $([System.IO.Path]::GetFileName($LifecycleReceiptPath))" | Set-Content -LiteralPath "$LifecycleReceiptPath.sha256" -Encoding utf8
    Write-Host "PHOENIXCORE_DESKTOP_LIFECYCLE_PASS kind=$InstallerKind receipt=$LifecycleReceiptPath sha256=$ReceiptHash"
}
catch {
    Write-JsonFile -Value ([ordered]@{ schema_version = "bws.app-lifecycle-failure/v1"; app_id = $AppId; installer_kind = $InstallerKind; source_commit = $SourceCommit; error = $_.Exception.Message; status = "fail" }) -Path $FailureReceiptPath
    throw
}
finally {
    if ($Installed -and $null -ne $InstalledExecutable) {
        try {
            if ($InstallerKind -eq "msi") {
                Start-Process -FilePath "msiexec.exe" -ArgumentList "/x `"$InstallerPath`" /qn /norestart" -Wait | Out-Null
            } else {
                $CleanupEntries = @(Get-DesktopUninstallEntries)
                $CleanupUninstaller = Find-NsisUninstaller -ExecutablePath $InstalledExecutable -UninstallEntries $CleanupEntries
                Start-Process -FilePath $CleanupUninstaller -ArgumentList "/S" -Wait | Out-Null
            }
        } catch { Write-Warning "Best-effort cleanup failed: $($_.Exception.Message)" }
    }
}
