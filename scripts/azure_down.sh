#!/usr/bin/env bash
#
# Delete everything scripts/azure_up.sh created.
#
# Cognitive Services resources are soft-deleted for 48 hours, which blocks reusing
# the same name and keeps holding your quota, so this purges as well as deletes.
#
#   DRILL_RG / DRILL_LOCATION / DRILL_ACCOUNT   same defaults as azure_up.sh
#   DRILL_YES=1                                 skip the confirmation prompt

set -euo pipefail

RG="${DRILL_RG:-interview-drill-rg}"
LOCATION="${DRILL_LOCATION:-eastus2}"

say()  { printf '\033[1;36m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m!  \033[0m %s\n' "$*"; }
die()  { printf '\033[1;31mx  \033[0m %s\n' "$*" >&2; exit 1; }

command -v az >/dev/null || die "Azure CLI not found."
az account show >/dev/null 2>&1 || die "Not signed in. Run 'az login' first."

SUB_ID=$(az account show --query id -o tsv)
SUFFIX=$(printf '%s' "$SUB_ID" | shasum | cut -c1-6)
ACCOUNT="${DRILL_ACCOUNT:-drill-foundry-$SUFFIX}"

if ! az group show --name "$RG" >/dev/null 2>&1; then
  say "Resource group $RG does not exist. Nothing to delete."
  exit 0
fi

say "About to delete resource group '$RG' and everything in it:"
az resource list --resource-group "$RG" --query "[].{name:name, type:type}" -o table || true

if [ "${DRILL_YES:-0}" != "1" ]; then
  printf "\nType the resource group name to confirm deletion: "
  read -r reply
  [ "$reply" = "$RG" ] || die "Aborted. Nothing was deleted."
fi

if az cognitiveservices account show -n "$ACCOUNT" -g "$RG" >/dev/null 2>&1; then
  say "Deleting the Foundry resource $ACCOUNT."
  az cognitiveservices account delete -n "$ACCOUNT" -g "$RG" --only-show-errors

  say "Purging its soft-deleted copy so the name and quota are freed immediately."
  az cognitiveservices account purge \
    -n "$ACCOUNT" -g "$RG" --location "$LOCATION" --only-show-errors \
    || warn "Purge failed - the name stays reserved for up to 48 hours. Harmless."
fi

say "Deleting resource group $RG (running in the background on Azure)."
az group delete --name "$RG" --yes --no-wait --only-show-errors

warn "Your .env still points at the deleted deployment. Re-run scripts/azure_up.sh to rebuild it."
say "Done."
