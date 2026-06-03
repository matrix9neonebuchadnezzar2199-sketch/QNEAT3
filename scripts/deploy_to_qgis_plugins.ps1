# QNEAT3 NEO を QGIS ユーザープロファイルへコピー（ZIP 展開と同等）
param(
    [string]$ProfileName = "",
    [string]$PluginsRoot = ""
)

$ErrorActionPreference = "Stop"
$src = Split-Path $PSScriptRoot -Parent

function Find-QgisPluginRoots {
    $roots = @()
    foreach ($base in @(
            (Join-Path $env:APPDATA "QGIS\QGIS3\profiles")
            (Join-Path $env:LOCALAPPDATA "QGIS\QGIS3\profiles")
        )) {
        if (-not (Test-Path $base)) { continue }
        Get-ChildItem $base -Directory | ForEach-Object {
            $plugins = Join-Path $_.FullName "python\plugins"
            if (Test-Path $plugins) { $roots += $plugins }
        }
    }
    $roots | Select-Object -Unique
}

if ($PluginsRoot) {
    $destRoots = @($PluginsRoot)
} elseif ($ProfileName) {
    $destRoots = @(
        (Join-Path $env:APPDATA "QGIS\QGIS3\profiles\$ProfileName\python\plugins")
        (Join-Path $env:LOCALAPPDATA "QGIS\QGIS3\profiles\$ProfileName\python\plugins")
    ) | Where-Object { Test-Path $_ }
} else {
    $destRoots = @(Find-QgisPluginRoots)
}

if (-not $destRoots) {
    Write-Host "QGIS plugins folder not found under:"
    Write-Host "  $env:APPDATA\QGIS\QGIS3\profiles\...\python\plugins"
    Write-Host "  $env:LOCALAPPDATA\QGIS\QGIS3\profiles\...\python\plugins"
    Write-Host ""
    Write-Host "Use QGIS: Plugins -> Install from ZIP:"
    Write-Host "  H:\CURSOR\QNEAT3\dist\QNEAT3-neo-*.zip"
    exit 1
}

Write-Host "Source: $src"
foreach ($destRoot in $destRoots) {
    $dest = Join-Path $destRoot "QNEAT3"
    Write-Host "Dest:   $dest"
    if (Test-Path $dest) {
        Remove-Item $dest -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    robocopy $src $dest /E /XD dist scripts .git __pycache__ /XF *.pyc debug-*.log NEO_load_error.txt /NFL /NDL /NJH /NJS | Out-Null
    $version = "unknown"
    $meta = Join-Path $src "metadata.txt"
    if (Test-Path $meta) {
        foreach ($line in Get-Content $meta -Encoding UTF8) {
            if ($line -match '^version=(.+)$') {
                $version = $Matches[1].Trim()
                break
            }
        }
    }
    $marker = Join-Path $dest "NEO_DEPLOYED.txt"
    @"
deployed_utc=$(Get-Date -Format o)
source=$src
version=$version
"@ | Set-Content -Path $marker -Encoding UTF8
    Write-Host "OK: deployed to $dest"
}

python (Join-Path $src "scripts\validate_metadata.py")
if ($LASTEXITCODE -ne 0) { throw "metadata validation failed" }
python (Join-Path $src "scripts\verify_provider_register.py")
if ($LASTEXITCODE -ne 0) { throw "provider register verification failed" }

Write-Host ""
Write-Host "Restart QGIS and enable 'QNEAT3 NEO'."
Write-Host "Confirm provider shows version from metadata.txt and [NEO] tool names."
