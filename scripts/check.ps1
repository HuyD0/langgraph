# Build the page and run the fast tests: what every change must pass before a commit.
# The Windows twin of scripts/check.sh. Usage, from PowerShell in the repo:  .\scripts\check.ps1
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
function Run { & $args[0] $args[1..($args.Length - 1)]; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE } }
Run uv run drill build-page
Run uv run drill tutor map | Out-Null   # docs/tutor/CURRICULUM_MAP.md, generated and git-ignored
Run uv run pytest -q -m "not slow"
