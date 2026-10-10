#!/bin/zsh
# One-shot dev setup for a new Apple Silicon Mac: Databricks + LangGraph + Azure.
# Safe to re-run; every step is idempotent.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"

step() { print -P "\n%F{cyan}==> $1%f"; }

# ---------- 1. Xcode Command Line Tools ----------
step "Xcode Command Line Tools"
if ! xcode-select -p &>/dev/null; then
  xcode-select --install 2>/dev/null || true
  echo "A macOS dialog has opened. Click 'Install' and wait for it to finish (5-10 min)."
  until xcode-select -p &>/dev/null; do sleep 10; done
fi
echo "ok: $(xcode-select -p)"

# ---------- 2. Homebrew ----------
step "Homebrew"
if [[ ! -x /opt/homebrew/bin/brew ]]; then
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi
eval "$(/opt/homebrew/bin/brew shellenv)"
touch ~/.zprofile
grep -q 'brew shellenv' ~/.zprofile || echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
echo "ok: $(brew --version | head -1)"

# ---------- 3. Packages ----------
step "brew bundle (CLIs + apps)"
brew trust databricks/tap 2>/dev/null || true
brew bundle --file="$HERE/Brewfile" --no-lock 2>/dev/null || brew bundle --file="$HERE/Brewfile"

step "Docker Desktop (large download, retried, non-fatal)"
if [[ -z "${SKIP_DOCKER:-}" && ! -d /Applications/Docker.app ]]; then
  for i in 1 2 3; do brew install --cask docker-desktop && break; echo "retry $i..."; sleep 5; done || true
fi
[[ -d /Applications/Docker.app ]] && echo "ok: Docker.app" || echo "WARN: Docker not installed; rerun later: brew install --cask docker-desktop"

# ---------- 4. Python via uv ----------
step "Python 3.12 (matches Databricks Runtime 16/17)"
uv python install 3.12
echo "ok: $(uv python find 3.12)"

# ---------- 5. Shell config ----------
step "~/.zshrc"
touch ~/.zshrc
add_line() { grep -qF -- "$1" ~/.zshrc || echo "$1" >> ~/.zshrc; }
add_line '# --- dev setup ---'
add_line 'export PATH="$HOME/.local/bin:$PATH"'
add_line 'autoload -Uz compinit && compinit'
add_line 'eval "$(uv generate-shell-completion zsh)"'
add_line 'eval "$(direnv hook zsh)"'
add_line 'export PYTHONDONTWRITEBYTECODE=1'
add_line 'alias ll="ls -lah"'
echo "ok"

# ---------- 6. Git ----------
step "git config"
if [[ -z "$(git config --global user.name || true)" ]]; then
  read "GIT_NAME?Your name for git commits: "
  git config --global user.name "$GIT_NAME"
fi
git config --global user.email  "huyydo@gmail.com"
git config --global init.defaultBranch main
git config --global pull.rebase true
git config --global core.editor "code --wait"
echo "ok: $(git config --global user.name) <$(git config --global user.email)>"

# ---------- 7. SSH key (for GitHub / Azure DevOps) ----------
step "SSH key"
if [[ ! -f ~/.ssh/id_ed25519 ]]; then
  mkdir -p ~/.ssh && chmod 700 ~/.ssh
  ssh-keygen -t ed25519 -C "huyydo@gmail.com" -f ~/.ssh/id_ed25519
  cat > ~/.ssh/config <<'SSHCFG'
Host *
  AddKeysToAgent yes
  UseKeychain yes
  IdentityFile ~/.ssh/id_ed25519
SSHCFG
  ssh-add --apple-use-keychain ~/.ssh/id_ed25519
fi
echo "public key:"; cat ~/.ssh/id_ed25519.pub

# ---------- 8. VS Code extensions ----------
step "VS Code extensions"
CODE="/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code"
if [[ -x "$CODE" ]]; then
  for ext in \
    ms-python.python ms-python.vscode-pylance ms-toolsai.jupyter charliermarsh.ruff \
    databricks.databricks \
    ms-azuretools.vscode-azureresourcegroups ms-azuretools.vscode-containers ms-vscode.azurecli \
    tamasfe.even-better-toml eamodio.gitlens; do
    "$CODE" --install-extension "$ext" --force >/dev/null && echo "  + $ext"
  done
  # expose `code` on PATH
  add_line 'export PATH="/Applications/Visual Studio Code.app/Contents/Resources/app/bin:$PATH"'
fi

# ---------- 9. Starter project ----------
step "ai-starter project (uv sync)"
cd "$HERE/ai-starter"
uv sync
uv run python -c "import langgraph, langchain_openai, databricks.sdk, mlflow, azure.identity; print('imports ok')"

print -P "\n%F{green}All done.%f Next (interactive, do these yourself):"
cat <<'NEXT'
  1. Open a NEW terminal window so PATH changes load.
  2. az login                                  # Azure
  3. databricks auth login --host https://<your-workspace>.azuredatabricks.net
  4. gh auth login                             # GitHub (paste the SSH key printed above if asked)
  5. Open Docker Desktop once to finish its install.
  6. cd ai-starter && cp .env.example .env     # fill in endpoints, then:
     uv run langgraph dev                      # opens LangGraph Studio in the browser
NEXT
