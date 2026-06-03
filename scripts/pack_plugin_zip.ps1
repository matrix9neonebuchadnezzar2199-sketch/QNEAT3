# QNEAT3 NEO を QGIS「ZIP からインストール」用にパッケージする。
# 出力: dist\QNEAT3-neo-<version>.zip（ルートに QNEAT3\ フォルダが入る形式）

$ErrorActionPreference = "Stop"
# 本スクリプトは QNEAT3\scripts\ に置く
$src = Split-Path $PSScriptRoot -Parent
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
$dist = Join-Path $src "dist"
New-Item -ItemType Directory -Force -Path $dist | Out-Null
$zipName = "QNEAT3-neo-$version.zip"
$zipPath = Join-Path $dist $zipName
$staging = Join-Path $env:TEMP "QNEAT3-neo-pack"
if (Test-Path $staging) { Remove-Item $staging -Recurse -Force }
$dest = Join-Path $staging "QNEAT3"
New-Item -ItemType Directory -Force -Path $dest | Out-Null
$exclude = @('dist', 'scripts', '.git', '__pycache__', '*.pyc', 'debug-*.log', 'NEO_load_error.txt')
robocopy $src $dest /E /XD dist scripts .git __pycache__ /XF *.pyc debug-*.log NEO_load_error.txt /NFL /NDL /NJH /NJS | Out-Null
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
python (Join-Path $src "scripts\validate_metadata.py")
if ($LASTEXITCODE -ne 0) { throw "metadata.txt validation failed" }
python (Join-Path $src "scripts\validate_all_symbol_refs.py")
if ($LASTEXITCODE -ne 0) { throw "symbol reference validation failed" }
python (Join-Path $src "scripts\validate_network_errors.py")
if ($LASTEXITCODE -ne 0) { throw "network error template validation failed" }
python (Join-Path $src "scripts\verify_provider_register.py")
if ($LASTEXITCODE -ne 0) { throw "Provider register validation failed" }
Compress-Archive -Path $dest -DestinationPath $zipPath -Force
Remove-Item $staging -Recurse -Force
Write-Host "Created: $zipPath"
Write-Host "Install in QGIS: Plugins -> Install from ZIP (do not use Reinstall from catalog)"
