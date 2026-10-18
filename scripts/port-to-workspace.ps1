# Put Daily Drill into an Azure Databricks workspace (work, by default), from a Windows laptop.
# The Windows twin of scripts/port-to-workspace.sh: same steps, same questions.
#
#   .\scripts\port-to-workspace.ps1
#
# (If PowerShell refuses to run scripts: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned)
#
# It installs the tools it needs with winget, signs you in, asks a few questions, shows the
# plan (`drill cloud port`, which changes nothing), and only applies it if you say yes.
# Safe to run again: every step finds before it creates. See docs/PORTING.md.
#
# Answers can come from the environment instead of the prompts:
#   $env:DRILL_TARGET="work"; $env:DRILL_PROFILE="work"; $env:DRILL_HOST="https://adb-<id>.azuredatabricks.net"
#   $env:DRILL_CATALOG="<team catalog>"; $env:DRILL_MODEL="<catalog.schema.service>"
#   $env:DRILL_MANAGERS="<group>"; $env:DRILL_LEARNERS="ana@corp.com bo@corp.com"
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

function Step($text) { Write-Host "`n==> $text" -ForegroundColor Cyan }
function Ask($name, $question, $default = "") {
  $given = [Environment]::GetEnvironmentVariable($name)
  if ($given) { return $given }
  $prompt = if ($default) { "$question [$default]" } else { $question }
  $answer = Read-Host $prompt
  if ($answer) { $answer } else { $default }
}
function Need($exe) { [bool](Get-Command $exe -ErrorAction SilentlyContinue) }

# ---------- 1. tools ----------
Step "Tools: git, uv and the Databricks CLI (v1.20 or newer)"
$winget = @{ git = "Git.Git"; uv = "astral-sh.uv"; databricks = "Databricks.DatabricksCLI" }
foreach ($tool in "git", "uv", "databricks") {
  if (-not (Need $tool)) {
    if (Need "winget") {
      winget install --exact --id $winget[$tool] --accept-source-agreements --accept-package-agreements
      Write-Host "Installed $tool. Close this window, open a new PowerShell and run the script again, so it is found."
      exit 0
    }
    Write-Host "Install $tool first. uv: https://docs.astral.sh/uv  CLI: https://docs.databricks.com/dev-tools/cli/install"
    exit 1
  }
}
$version = [regex]::Match((databricks --version), '\d+\.\d+').Value
if ([version]$version -lt [version]"1.20") {
  Write-Host "Databricks CLI $version is too old."
  if (Need "winget") { winget upgrade --exact --id Databricks.DatabricksCLI } else { Write-Host "Upgrade it to v1.20 or newer."; exit 1 }
}
Write-Host "ok: git, $(uv --version), $(databricks --version)"

Step "Python packages"
uv sync --quiet
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "ok"

# ---------- 2. sign in ----------
Step "Sign in"
$target = Ask "DRILL_TARGET" "Which target in databricks.yml" "work"
$profile_ = Ask "DRILL_PROFILE" "CLI profile name" $target
databricks current-user me --profile $profile_ *> $null
if ($LASTEXITCODE -ne 0) {
  $hostUrl = Ask "DRILL_HOST" "Workspace URL" "https://adb-<id>.azuredatabricks.net"
  databricks auth login --host $hostUrl --profile $profile_
}
$me = databricks current-user me --profile $profile_ -o json | ConvertFrom-Json
Write-Host "ok: $($me.userName)"

# ---------- 3. what goes where ----------
Step "What goes where"
$catalog = Ask "DRILL_CATALOG" "A catalog your team owns (traces and prompts go in schemas inside it)"
$model = Ask "DRILL_MODEL" "The governed model service, catalog.schema.service"
$managers = Ask "DRILL_MANAGERS" "A managers group to see the dashboard (blank for none)"
$learners = Ask "DRILL_LEARNERS" "Learners' emails, space-separated (blank for none yet)"

$planArgs = @("--target", $target, "--profile", $profile_)
if ($catalog) { $planArgs += @("--catalog", $catalog) }
if ($model) { $planArgs += @("--model", $model) }

# ---------- 4. the plan, then (if you say so) the work ----------
Step "The plan (nothing changes yet)"
uv run drill cloud port @planArgs
if ($LASTEXITCODE -ne 0) {
  Write-Host "`nSomething is blocked: fix the lines marked with a cross above, then run this script again."
  exit 1
}

$apply = @("--apply")
if ($managers) { $apply += @("--managers", $managers) }
foreach ($email in ($learners -split "\s+" | Where-Object { $_ })) { $apply += @("--learner", $email) }
$go = Read-Host "Apply it: create what's missing, grant, deploy and share? [y/N]"
if (-not $go.ToLower().StartsWith("y")) {
  Write-Host "Nothing changed. Run the script again when you're ready."
  exit 0
}

Step "Applying (the deploy takes a few minutes)"
uv run drill cloud port @planArgs @apply
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Step "Done"
uv run drill cloud status --target $target --profile $profile_
Write-Host @"

Next:
  - Tell learners their manager can see their progress, study list and questions.
  - Add people later:   uv run drill cloud share <email> --target $target
  - Check everything:   uv run drill cloud check --target $target
  - Stop billing:       uv run drill cloud stop --target $target   (it also stops itself after 30 idle minutes)
"@
