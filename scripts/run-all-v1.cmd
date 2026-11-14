@echo off
REM Re-run every supported module on example files, outputting to example\v1\
REM Prerequisite: pip install -e . from repo root.
cd /d "%~dp0.."
set "OUTDIR=%~1"
if "%OUTDIR%"=="" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%cd%\scripts\run-all-v1.ps1" -OutDir "%cd%\example\v1" %*
) else (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%cd%\scripts\run-all-v1.ps1" -OutDir "%OUTDIR%" %2 %3 %4 %5 %6 %7 %8 %9
)
