#!/usr/bin/env bash
#
# Provision the Azure AI Foundry resource this project needs, and write .env.
#
# Idempotent: re-running it reuses whatever already exists. Everything it makes
# lives in one resource group, so scripts/azure_down.sh can remove all of it.
#
# Override any of these before running:
#   DRILL_RG          resource group name          (default interview-drill-rg)
#   DRILL_LOCATION    region                       (default eastus2)
#   DRILL_ACCOUNT     Foundry resource name        (default drill-foundry-<hash>)
#   DRILL_DEPLOYMENT  deployment name              (default drill-chat)
#   DRILL_MODEL       model to try first           (default gpt-4o-mini)
#   DRILL_CAPACITY    thousands of tokens/min      (default 20)
#   DRILL_YES=1       skip the confirmation prompt

set -euo pipefail

RG="${DRILL_RG:-interview-drill-rg}"
LOCATION="${DRILL_LOCATION:-eastus2}"
DEPLOYMENT="${DRILL_DEPLOYMENT:-drill-chat}"
CAPACITY="${DRILL_CAPACITY:-20}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$REPO_ROOT/.env"

# Preference order: cheap-and-small first. The gpt-4.x chat family is deprecated in
# most regions now, but it stays on the list for regions where it is still GA.
# drill.llm drops `temperature` for the gpt-5 reasoning family, which rejects it.
CANDIDATES="${DRILL_MODEL:-} gpt-5.4-nano gpt-5-nano gpt-5.4-mini gpt-5-mini gpt-4.1-mini gpt-4o-mini"

say()  { printf '\033[1;36m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m!  \033[0m %s\n' "$*"; }
die()  { printf '\033[1;31mx  \033[0m %s\n' "$*" >&2; exit 1; }

command -v az  >/dev/null || die "Azure CLI not found. brew install azure-cli"
command -v jq  >/dev/null || die "jq not found. brew install jq"

# ---------------------------------------------------------------- 1. sign in
if ! az account show >/dev/null 2>&1; then
  say "Not signed in - opening a browser for 'az login'."
  az login --only-show-errors >/dev/null
fi

SUB_NAME=$(az account show --query name -o tsv)
SUB_ID=$(az account show --query id -o tsv)

# Foundry resource names must be globally unique (they become a DNS name), so
# derive a stable suffix from the subscription id rather than a random one.
SUFFIX=$(printf '%s' "$SUB_ID" | shasum | cut -c1-6)
ACCOUNT="${DRILL_ACCOUNT:-drill-foundry-$SUFFIX}"

# Free Trial / Azure Pass / Lightweight Trial subscriptions are allocated 0 TPM for
# every Azure OpenAI model, so deployment fails with InsufficientQuota no matter the
# region. Catch that here rather than after creating a resource group.
QUOTA_ID=$(az rest --method GET \
  --uri "https://management.azure.com/subscriptions/$SUB_ID?api-version=2020-01-01" \
  --query subscriptionPolicies.quotaId -o tsv 2>/dev/null || true)

case "$QUOTA_ID" in
  FreeTrial_*|AzurePass_*|LightweightTrial_*)
    warn "This subscription's offer type is '$QUOTA_ID'."
    warn "That tier gets 0 tokens/min of Azure OpenAI quota for every model, so the"
    warn "model deployment below will fail with InsufficientQuota."
    warn "Upgrade to Pay-As-You-Go in the portal first - any free credit carries over:"
    warn "  https://portal.azure.com  >  Subscriptions  >  $SUB_NAME  >  Upgrade"
    ;;
esac

cat <<SUMMARY

  subscription   $SUB_NAME
                 $SUB_ID
  resource group $RG
  location       $LOCATION
  resource       $ACCOUNT   (kind: AIServices, sku: S0)
  deployment     $DEPLOYMENT

  Pay-per-token: the resource costs nothing while idle, you pay per request.
  Run scripts/azure_down.sh to delete all of it.

SUMMARY

if [ "${DRILL_YES:-0}" != "1" ]; then
  printf 'Create these resources? [y/N] '
  read -r reply
  case "$reply" in [yY]*) ;; *) die "Aborted. Nothing was created." ;; esac
fi

# ------------------------------------------------- 2. provider + resource group
say "Registering the Microsoft.CognitiveServices provider (no-op if already on)."
az provider register --namespace Microsoft.CognitiveServices --wait --only-show-errors

say "Resource group $RG in $LOCATION."
az group create --name "$RG" --location "$LOCATION" --only-show-errors >/dev/null

# ------------------------------------------------------- 3. Foundry resource
if az cognitiveservices account show -n "$ACCOUNT" -g "$RG" >/dev/null 2>&1; then
  say "Resource $ACCOUNT already exists - reusing it."
else
  say "Creating Foundry resource $ACCOUNT. This takes a minute."
  az cognitiveservices account create \
    --name "$ACCOUNT" \
    --resource-group "$RG" \
    --location "$LOCATION" \
    --kind AIServices \
    --sku S0 \
    --custom-domain "$ACCOUNT" \
    --yes --only-show-errors >/dev/null
fi

# ------------------------------------------------------ 4. pick a live model
say "Looking up which chat models this subscription can deploy in $LOCATION."
MODELS_JSON=$(az cognitiveservices account list-models -n "$ACCOUNT" -g "$RG" -o json)

MODEL_NAME=""; MODEL_VERSION=""; MODEL_FORMAT=""; MODEL_SKU=""
for candidate in $CANDIDATES; do
  [ -z "$candidate" ] && continue
  # Every deployable (version, sku) pair for this model, newest first, with
  # GlobalStandard ahead of Standard when both exist for that version.
  #
  # Two filters matter. `lifecycleStatus` excludes Deprecating/Deprecated versions,
  # which Azure still lists but refuses to deploy (ServiceModelDeprecating), and
  # `chatCompletion` excludes same-family transcribe/tts/image models.
  line=$(printf '%s' "$MODELS_JSON" | jq -r --arg m "$candidate" '
      .[] | select(.name == $m)
      | select(.lifecycleStatus == "GenerallyAvailable")
      | select((.capabilities.chatCompletion // "false") == "true")
      | . as $e
      | ($e.skus // [])[]
      | select(.name == "GlobalStandard" or .name == "Standard")
      | [$e.version, $e.format, .name] | @tsv
    ' | sort -u | sort -t "$(printf '\t')" -k1,1r -k3,3 | head -1)
  if [ -n "$line" ]; then
    MODEL_NAME="$candidate"
    MODEL_VERSION=$(printf '%s' "$line" | cut -f1)
    MODEL_FORMAT=$(printf '%s' "$line" | cut -f2)
    MODEL_SKU=$(printf '%s' "$line" | cut -f3)
    break
  fi
  warn "$candidate is not available here - trying the next one."
done

if [ -z "$MODEL_NAME" ]; then
  warn "None of the candidates ($CANDIDATES) are available in $LOCATION."
  warn "Chat models this resource does offer:"
  printf '%s' "$MODELS_JSON" | jq -r '
    .[] | select(.lifecycleStatus == "GenerallyAvailable")
        | select((.capabilities.chatCompletion // "false") == "true")
        | "  - \(.name) \(.version)"' | sort -u
  die "Re-run with DRILL_MODEL=<one of the above>, or DRILL_LOCATION=<another region>."
fi

say "Using $MODEL_NAME version $MODEL_VERSION ($MODEL_SKU, ${CAPACITY}K tokens/min)."

# ---------------------------------------------------------- 5. the deployment
if az cognitiveservices account deployment show \
     -n "$ACCOUNT" -g "$RG" --deployment-name "$DEPLOYMENT" >/dev/null 2>&1; then
  say "Deployment $DEPLOYMENT already exists - reusing it."
else
  say "Deploying $MODEL_NAME as '$DEPLOYMENT'."
  if ! DEPLOY_ERR=$(az cognitiveservices account deployment create \
    --name "$ACCOUNT" \
    --resource-group "$RG" \
    --deployment-name "$DEPLOYMENT" \
    --model-name "$MODEL_NAME" \
    --model-version "$MODEL_VERSION" \
    --model-format "$MODEL_FORMAT" \
    --sku-name "$MODEL_SKU" \
    --sku-capacity "$CAPACITY" \
    --only-show-errors 2>&1 >/dev/null); then
    printf '%s\n' "$DEPLOY_ERR" >&2
    case "$DEPLOY_ERR" in
      *InsufficientQuota*|*QuotaExceeded*)
        warn "Your subscription has no Azure OpenAI quota in $LOCATION for this model."
        warn "Offer type reported by Azure: ${QUOTA_ID:-unknown}."
        warn "Trial-tier subscriptions get 0 TPM for all models - upgrade to Pay-As-You-Go,"
        warn "or lower DRILL_CAPACITY, or try DRILL_LOCATION=<another region>."
        warn "Check your allocation:  az cognitiveservices usage list -l $LOCATION -o table"
        ;;
    esac
    die "Could not create the model deployment."
  fi
fi

STATE=$(az cognitiveservices account deployment show \
  -n "$ACCOUNT" -g "$RG" --deployment-name "$DEPLOYMENT" \
  --query properties.provisioningState -o tsv)
[ "$STATE" = "Succeeded" ] || die "Deployment is in state '$STATE', expected Succeeded."

# ------------------------------------------------------ 6. endpoint and key
ENDPOINT=$(az cognitiveservices account show -n "$ACCOUNT" -g "$RG" \
  --query properties.endpoints -o json \
  | jq -r '.["OpenAI Language Model Instance API"]
           // .["Azure OpenAI Legacy API - Latest moniker"]
           // empty')
[ -n "$ENDPOINT" ] || ENDPOINT="https://$ACCOUNT.openai.azure.com/"

KEY=$(az cognitiveservices account keys list -n "$ACCOUNT" -g "$RG" --query key1 -o tsv)

# ------------------------------------------- 7. does it accept a temperature?
# Ask the model rather than guessing from its name: reasoning models reject any
# temperature but their default, and which families do that keeps changing.
say "Checking whether $MODEL_NAME accepts a custom temperature."
PROBE=$(curl -sS -X POST \
  "${ENDPOINT%/}/openai/deployments/$DEPLOYMENT/chat/completions?api-version=2024-10-21" \
  -H "api-key: $KEY" -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"hi"}],"temperature":0.2}')

if printf '%s' "$PROBE" | jq -e '.error.code == "unsupported_value"' >/dev/null 2>&1; then
  TEMPERATURE=""
  warn "It does not. Setting DRILL_TEMPERATURE= so the tutor omits the parameter."
else
  TEMPERATURE="0.2"
fi

# ------------------------------------------------------------- 8. write .env
say "Writing $ENV_FILE (existing values for other keys are kept)."
ENDPOINT="$ENDPOINT" DEPLOYMENT="$DEPLOYMENT" KEY="$KEY" TEMPERATURE="$TEMPERATURE" \
  ENV_FILE="$ENV_FILE" python3 <<'PY'
import os, pathlib, shutil, time

path = pathlib.Path(os.environ["ENV_FILE"])
updates = {
    "AZURE_OPENAI_ENDPOINT": os.environ["ENDPOINT"],
    "AZURE_OPENAI_DEPLOYMENT": os.environ["DEPLOYMENT"],
    "AZURE_OPENAI_API_KEY": os.environ["KEY"],
    "DRILL_TEMPERATURE": os.environ["TEMPERATURE"],
}

lines = []
if path.exists():
    shutil.copy(path, path.with_name(f"{path.name}.bak.{int(time.time())}"))
    lines = path.read_text().splitlines()

seen = set()
out = []
for line in lines:
    key = line.split("=", 1)[0].strip() if "=" in line else ""
    if key in updates:
        out.append(f"{key}={updates[key]}")
        seen.add(key)
    else:
        out.append(line)
for key, value in updates.items():
    if key not in seen:
        out.append(f"{key}={value}")

path.write_text("\n".join(out).strip() + "\n")
path.chmod(0o600)
PY

# --------------------------------------------------------- 9. prove it works
say "Smoke-testing the deployment."
RESPONSE=$(curl -sS -X POST \
  "${ENDPOINT%/}/openai/deployments/$DEPLOYMENT/chat/completions?api-version=2024-10-21" \
  -H "api-key: $KEY" -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Reply with the single word: ready"}]}')

REPLY=$(printf '%s' "$RESPONSE" | jq -r '.choices[0].message.content // empty')
if [ -z "$REPLY" ]; then
  warn "The model did not answer. Raw response:"
  printf '%s\n' "$RESPONSE" | jq . 2>/dev/null || printf '%s\n' "$RESPONSE"
  die "Provisioning finished but the endpoint is not serving yet. Wait a minute and re-run."
fi

cat <<DONE

  Model replied: $REPLY

  Ready. Start a tutored session with:

      uv sync --dev
      uv run drill start

  Tear it all down with:

      scripts/azure_down.sh

DONE
