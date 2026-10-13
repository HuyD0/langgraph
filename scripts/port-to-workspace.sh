#!/bin/zsh
# Put Daily Drill into an Azure Databricks workspace (work, by default), from a fresh laptop.
#
#   ./scripts/port-to-workspace.sh
#
# It installs or upgrades the tools it needs, signs you in, asks a few questions, shows the
# plan (`drill cloud port`, which changes nothing), and only applies it if you say yes.
# Safe to run again: every step finds before it creates. See docs/PORTING.md.
#
# Answers can come from the environment instead of the prompts:
#   DRILL_TARGET=work DRILL_PROFILE=work DRILL_HOST=https://adb-<id>.azuredatabricks.net
#   DRILL_CATALOG=<team catalog> DRILL_MODEL=<catalog.schema.service>
#   DRILL_MANAGERS=<group> DRILL_LEARNERS="ana@corp.com bo@corp.com"
set -euo pipefail
cd "$(dirname "$0")/.."

step() { print -P "\n%F{cyan}==> $1%f"; }
ask() {  # ask VAR "question" "default"
  local var=$1 question=$2 default=${3:-} answer
  if [[ -n "${(P)var:-}" ]]; then return; fi
  read "answer?$question${default:+ [$default]}: "
  typeset -g "$var=${answer:-$default}"
}

# ---------- 1. tools ----------
step "Tools: git, uv and the Databricks CLI (v1.20 or newer)"
have_brew=$([[ -x /opt/homebrew/bin/brew || -x /usr/local/bin/brew ]] && echo 1 || echo 0)
for tool in git uv databricks; do
  if ! command -v $tool >/dev/null; then
    if [[ $have_brew == 1 ]]; then
      [[ $tool == databricks ]] && brew install databricks/tap/databricks || brew install $tool
    else
      echo "Install $tool first (Homebrew is not here). uv: https://docs.astral.sh/uv  CLI: https://docs.databricks.com/dev-tools/cli/install"
      exit 1
    fi
  fi
done
version=$(databricks --version | grep -oE '[0-9]+\.[0-9]+' | head -1)
if [[ $(printf '%s\n' 1.20 "$version" | sort -V | head -1) != 1.20 ]]; then
  echo "Databricks CLI $version is too old."
  [[ $have_brew == 1 ]] && brew upgrade databricks/tap/databricks || { echo "Upgrade it to v1.20 or newer."; exit 1; }
fi
echo "ok: git, uv $(uv --version | cut -d' ' -f2), databricks $(databricks --version | grep -oE '[0-9.]+' | head -1)"

step "Python packages"
uv sync --quiet
echo "ok"

# ---------- 2. sign in ----------
step "Sign in"
ask DRILL_TARGET "Which target in databricks.yml" "work"
ask DRILL_PROFILE "CLI profile name" "$DRILL_TARGET"
if ! databricks current-user me --profile "$DRILL_PROFILE" >/dev/null 2>&1; then
  ask DRILL_HOST "Workspace URL" "https://adb-<id>.azuredatabricks.net"
  databricks auth login --host "$DRILL_HOST" --profile "$DRILL_PROFILE"
fi
echo "ok: $(databricks current-user me --profile "$DRILL_PROFILE" -o json | grep -oE '"userName": *"[^"]+"' | cut -d'"' -f4)"

# ---------- 3. what goes where ----------
step "What goes where"
ask DRILL_CATALOG "A catalog your team owns (traces and prompts go in schemas inside it)" ""
ask DRILL_MODEL "The governed model service, catalog.schema.service" ""
ask DRILL_MANAGERS "A managers group to see the dashboard (blank for none)" ""
ask DRILL_LEARNERS "Learners' emails, space-separated (blank for none yet)" ""

args=(--target "$DRILL_TARGET" --profile "$DRILL_PROFILE")
[[ -n "$DRILL_CATALOG" ]] && args+=(--catalog "$DRILL_CATALOG")
[[ -n "$DRILL_MODEL" ]] && args+=(--model "$DRILL_MODEL")

# ---------- 4. the plan, then (if you say so) the work ----------
step "The plan (nothing changes yet)"
if ! uv run drill cloud port "${args[@]}"; then
  echo "\nSomething is blocked: fix the lines marked ✗ above, then run this script again."
  exit 1
fi

apply=(--apply)
[[ -n "$DRILL_MANAGERS" ]] && apply+=(--managers "$DRILL_MANAGERS")
for email in ${=DRILL_LEARNERS}; do apply+=(--learner "$email"); done
read "go?Apply it: create what's missing, grant, deploy and share? [y/N]: "
if [[ "${go:l}" != y* ]]; then
  echo "Nothing changed. Run the script again when you're ready."
  exit 0
fi

step "Applying (the deploy takes a few minutes)"
uv run drill cloud port "${args[@]}" "${apply[@]}"

step "Done"
uv run drill cloud status --target "$DRILL_TARGET" --profile "$DRILL_PROFILE"
echo "
Next:
  - Tell learners their manager can see their progress, study list and questions.
  - Add people later:   uv run drill cloud share <email> --target $DRILL_TARGET
  - Check everything:   uv run drill cloud check --target $DRILL_TARGET
  - Stop billing:       uv run drill cloud stop --target $DRILL_TARGET   (it also stops itself after 30 idle minutes)"
