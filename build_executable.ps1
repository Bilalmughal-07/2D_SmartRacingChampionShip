$ErrorActionPreference = "Stop"
python -m PyInstaller --noconfirm --clean --windowed --name SmartRacingChampionship --paths src --add-data "src\smart_racing\tracks;smart_racing\tracks" run_game.py
if (-not (Test-Path -LiteralPath "dist\SmartRacingChampionship\SmartRacingChampionship.exe")) {
    throw "PyInstaller did not produce the expected executable"
}
Write-Host "Executable created at dist\SmartRacingChampionship\SmartRacingChampionship.exe"
python -m PyInstaller --noconfirm --clean --windowed --name SmartRacingChampionshipArcade --paths src --add-data "src\smart_racing\tracks;smart_racing\tracks" --add-data "assets;assets" run_arcade.py
if (-not (Test-Path -LiteralPath "dist\SmartRacingChampionshipArcade\SmartRacingChampionshipArcade.exe")) {
    throw "PyInstaller did not produce the expected Arcade executable"
}
Write-Host "Arcade executable created at dist\SmartRacingChampionshipArcade\SmartRacingChampionshipArcade.exe"
