param(
    [string]$RegistrationNumbers = "24I-XXXX_24I-YYYY_24I-ZZZZ",
    [string]$Section = "Section",
    [string]$OutputDirectory = "submission"
)
$ErrorActionPreference = "Stop"
$root = (Get-Location).Path
$staging = Join-Path $root "tmp\submission_staging"
$zipName = "${RegistrationNumbers}_${Section}.zip"
$zipPath = Join-Path $root "$OutputDirectory\$zipName"
if (Test-Path -LiteralPath $staging) { Remove-Item -LiteralPath $staging -Recurse -Force }
New-Item -ItemType Directory -Force -Path $staging | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $staging "report") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $staging "raw_results") | Out-Null
python run_validation.py | Out-Null
python -m pytest
python run_game.py --headless --track circuit_01 | Out-Null
python run_experiments.py
python build_report.py
python -c "import PyInstaller" 2>$null
if ($LASTEXITCODE -eq 0) {
    .\build_executable.ps1
}
Copy-Item -LiteralPath "README.md" -Destination $staging
Copy-Item -LiteralPath "requirements.txt" -Destination $staging
Copy-Item -LiteralPath "pyproject.toml" -Destination $staging
Copy-Item -LiteralPath "requirements-dev.txt" -Destination $staging
Copy-Item -LiteralPath "AGENTS.md" -Destination $staging
Copy-Item -LiteralPath "LICENSES.md" -Destination $staging
Copy-Item -LiteralPath "run_game.py" -Destination $staging
Copy-Item -LiteralPath "run_arcade.py" -Destination $staging
Copy-Item -LiteralPath "run_validation.py" -Destination $staging
Copy-Item -LiteralPath "run_championship.py" -Destination $staging
Copy-Item -LiteralPath "run_experiments.py" -Destination $staging
Copy-Item -LiteralPath "build_executable.ps1" -Destination $staging
Copy-Item -LiteralPath "src" -Destination $staging -Recurse
Copy-Item -LiteralPath "assets" -Destination $staging -Recurse
Copy-Item -LiteralPath "docs" -Destination $staging -Recurse
Copy-Item -LiteralPath "tests" -Destination $staging -Recurse
Copy-Item -LiteralPath "tools" -Destination $staging -Recurse
Copy-Item -LiteralPath "submission\final_checklist.md" -Destination $staging
Copy-Item -LiteralPath "experiments\data" -Destination (Join-Path $staging "raw_results") -Recurse
Copy-Item -LiteralPath "experiments\charts" -Destination $staging -Recurse
Copy-Item -LiteralPath "output\pdf\Smart_Racing_Technical_Report.pdf" -Destination (Join-Path $staging "report")
if (Test-Path -LiteralPath "dist\SmartRacingChampionship") {
    Copy-Item -LiteralPath "dist\SmartRacingChampionship" -Destination (Join-Path $staging "Executable") -Recurse
}
if (Test-Path -LiteralPath "dist\SmartRacingChampionshipArcade") {
    New-Item -ItemType Directory -Force -Path (Join-Path $staging "Executable\Arcade") | Out-Null
    Copy-Item -Path "dist\SmartRacingChampionshipArcade\*" -Destination (Join-Path $staging "Executable\Arcade") -Recurse
}
Get-ChildItem -LiteralPath $staging -Directory -Recurse -Force |
    Where-Object { $_.Name -in @("__pycache__", ".pytest_cache", ".ruff_cache") } |
    Sort-Object FullName -Descending |
    Remove-Item -Recurse -Force
Get-ChildItem -LiteralPath $staging -File -Recurse -Force -Filter "*.pyc" | Remove-Item -Force
$files = Get-ChildItem -LiteralPath $staging -File -Recurse | ForEach-Object {
    $relative = $_.FullName.Substring($staging.Length + 1)
    [PSCustomObject]@{ path = $relative; sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash }
}
$files | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $staging "MANIFEST.json") -Encoding UTF8
if (Test-Path -LiteralPath $zipPath) { Remove-Item -LiteralPath $zipPath -Force }
Compress-Archive -Path (Join-Path $staging "*") -DestinationPath $zipPath -CompressionLevel Optimal
if (-not (Test-Path -LiteralPath $zipPath)) { throw "ZIP was not created" }
$archive = [System.IO.Compression.ZipFile]::OpenRead((Resolve-Path -LiteralPath $zipPath))
try {
    $required = @("README.md", "run_game.py", "run_arcade.py", "src/smart_racing", "report/Smart_Racing_Technical_Report.pdf", "Executable/SmartRacingChampionship.exe", "Executable/Arcade/SmartRacingChampionshipArcade.exe", "MANIFEST.json")
    foreach ($name in $required) {
        if (-not ($archive.Entries.FullName | Where-Object { $_ -eq $name -or $_ -like "$name/*" })) { throw "ZIP missing $name" }
    }
} finally { $archive.Dispose() }
Write-Host "Submission archive created: $zipPath"
