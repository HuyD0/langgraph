# Connecting a model

`drill list`, `drill check` and `drill solution` work with no credentials at all. The
tutored session (`drill start`) and the local server need a model. Pick one of the four
below, put the values in a `.env` at the repo root (it is gitignored) or export them, and
`drill start` tells you exactly which variable is missing if one is.

Precedence when several are set: `MLFLOW_GATEWAY_ENDPOINT`, then `OLLAMA_MODEL`, then Azure.

## A local model with Ollama

No Azure, no keys, works offline. Install [Ollama](https://ollama.com), pull a model, and
name it:

```bash
brew install ollama && brew services start ollama
ollama pull gemma3:12b
```

```bash
OLLAMA_MODEL=gemma3:12b
# OLLAMA_BASE_URL=http://localhost:11434/v1   # optional, this is the default
```

The tutor only needs plain-text replies, no tool calling, so any instruction-tuned chat
model works. Expect weaker hints than a hosted model. A 12B model needs about 8 GB of free
memory.

## Azure AI Foundry, provisioned from scratch

If you do not have a Foundry resource yet, `scripts/azure_up.sh` creates one and writes
your `.env`. It needs the Azure CLI and `jq`, and it signs you in if you are not already.

```bash
scripts/azure_up.sh          # ~2 minutes, prompts before it creates anything
uv run drill start
```

It makes a resource group, an `AIServices` resource, and one chat deployment named
`drill-chat`. The model is whichever of `gpt-5.4-nano`, `gpt-5-nano`, `gpt-5.4-mini`,
`gpt-5-mini`, `gpt-4.1-mini`, `gpt-4o-mini` your subscription can *actually* deploy in that
region. It skips versions Azure lists but has marked `Deprecating`, which otherwise fail
with `ServiceModelDeprecating`. It then asks the deployed model whether it accepts a custom
temperature (reasoning models reject one) and writes `DRILL_TEMPERATURE` to match.
Deployments are pay-per-token, so an idle resource costs nothing. Re-running the script is
safe: it reuses whatever already exists.

**Your subscription must be Pay-As-You-Go.** Azure allocates *zero* tokens/min of Azure
OpenAI quota to Free Trial, Azure Pass and Lightweight Trial subscriptions, for every model
and every region, so deployment fails with `InsufficientQuota`. The script checks your
offer type up front and says so before creating anything. Upgrading keeps any remaining
free credit.

Override the defaults with environment variables:

```bash
DRILL_LOCATION=swedencentral DRILL_MODEL=gpt-4o scripts/azure_up.sh
```

`DRILL_RG`, `DRILL_LOCATION`, `DRILL_ACCOUNT`, `DRILL_DEPLOYMENT`, `DRILL_MODEL` and
`DRILL_CAPACITY` are all honoured. When you are done, `scripts/azure_down.sh` deletes the
resource group and purges the soft-deleted resource so it stops holding your model quota.

## Azure AI Foundry, a resource you already have

A Foundry resource exposes one of two chat surfaces. You do not have to work out which you
have: the endpoint URL is inspected and the right client is used.

**Azure OpenAI deployments**, endpoint ends in `.openai.azure.com`:

```bash
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=<your-deployment-name>
AZURE_OPENAI_API_KEY=<key>
# AZURE_OPENAI_API_VERSION=2024-10-21   # optional, this is the default
```

**Foundry models endpoint**, endpoint ends in `.services.ai.azure.com/models`:

```bash
AZURE_INFERENCE_ENDPOINT=https://<your-resource>.services.ai.azure.com/models
AZURE_OPENAI_DEPLOYMENT=<your-model-name>
AZURE_OPENAI_API_KEY=<key>
```

**Service principal instead of a key**: set these three and leave the key unset, and an
AAD token is fetched and refreshed for you:

```bash
AZURE_TENANT_ID=...
AZURE_CLIENT_ID=...
AZURE_CLIENT_SECRET=...
```

## An MLflow AI Gateway

An MLflow server (3.x) has a built-in AI Gateway: you create named endpoints in its UI,
each pointed at a model (Ollama, Azure, Databricks...), and every call through it is
recorded. Point the tutor at an endpoint by name:

```bash
MLFLOW_GATEWAY_ENDPOINT=drill-tutor
# MLFLOW_GATEWAY_URL=http://localhost:5050/gateway/mlflow/v1   # optional, this is the default
MLFLOW_TRACKING_URI=http://localhost:5050                      # send the tutor's traces there too
```

Switching the model behind the tutor is then done in the gateway, not in `.env`. The
server must be running while you practise.

## All the knobs

| Variable | Default | What it does |
|---|---|---|
| `DRILL_TEMPERATURE` | `0.2` | Sampling temperature; **empty** omits it, which reasoning models require |
| `DRILL_MAX_ATTEMPTS` | `3` | Tries before the tutor explains |
| `DRILL_SANDBOX_TIMEOUT` | `10` | Seconds a submission may run |
| `DRILL_PROGRESS_PATH` | `.drill/progress.json` | Where the CLI's history is stored |
| `MLFLOW_TRACKING_URI` | *(unset, so `./mlruns`)* | Tracking server |
| `MLFLOW_EXPERIMENT_NAME` | `daily-drill` | Experiment for traces and runs |
| `AZURE_FOUNDRY_FLAVOUR` | *(inferred)* | Force `azure_openai` or `azure_inference` |
| `OLLAMA_MODEL` | *(unset)* | Use a local Ollama model instead of Azure |
| `OLLAMA_BASE_URL` | `http://localhost:11434/v1` | Where Ollama is listening |
| `MLFLOW_GATEWAY_ENDPOINT` | *(unset)* | Use an MLflow AI Gateway endpoint; wins over everything |
| `MLFLOW_GATEWAY_URL` | `http://localhost:5050/gateway/mlflow/v1` | Where the gateway is |

The local server has its own knobs, in [SERVER.md](SERVER.md).

## A new Mac

`setup-mac.sh` at the repo root installs everything this project and the wider stack need
on a fresh Apple Silicon Mac (Homebrew, the CLIs in `Brewfile`, uv, Python 3.12, Docker).
It is safe to re-run.
