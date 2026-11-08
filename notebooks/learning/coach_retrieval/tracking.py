"""The MLflow side of the coach-retrieval lab, kept here so the notebook cells stay short.

Everything a run used goes into MLflow while it happens: the settings, the exact model and data
versions, the git commit, the training loss step by step, the scores and the trained model. The local
server is the one the app uses (``http://localhost:5050``); on Databricks the same calls go to the
workspace once ``MLFLOW_TRACKING_URI=databricks`` is set (stage 8).
"""

from __future__ import annotations

import json
import os
import platform
import subprocess
from importlib.metadata import version
from pathlib import Path

import mlflow

from drill.tutor_prepared_eval import mcnemar, wilson  # noqa: F401  (the course's own: "Margins near 0% and 100%", "Comparing on the same examples")

TRACKING_URI = os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5050")
EXPERIMENT = os.environ.get("DRILL_LAB_EXPERIMENT", "coach-retrieval-lab")
HERE = Path(__file__).resolve().parent
DATA = HERE / "data"  # git-ignored; the registered MLflow datasets are the copy that counts


def short(run_id: str) -> str:
    """The first 8 characters of a run id: enough to find the run, and the only form that goes into a notebook's
    saved output. A full 32-character id looks exactly like an application id, so the repo's scrub test
    (tests/test_scrub.py) refuses to let one be committed."""
    return (run_id or "")[:8]


def run_link(run) -> str:
    """Where to find a run, without its full id: the experiment page, the run's name and its short id."""
    info = run.info
    return f'{TRACKING_URI}/#/experiments/{info.experiment_id} · run "{info.run_name}" ({short(info.run_id)})'


def connect(experiment: str = EXPERIMENT) -> str:
    """Point MLflow at the server and the lab's experiment; returns the experiment's name."""
    import warnings

    # MLflow prints "View run ... at <url with the full id>" when a run ends; the lab prints its own link (run_link).
    os.environ.setdefault("MLFLOW_SUPPRESS_PRINTING_URL_TO_STDOUT", "1")
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")  # progress widgets carry random 32-character ids too
    os.environ.setdefault("TQDM_DISABLE", "1")  # tqdm's notebook widgets save a widget state full of such ids

    # MLflow hints, every time a dataset with a 0/1 column is logged, that integer columns cannot hold missing values. The
    # honest test's ``checked`` flag is such a column on purpose (see ``table_dataset``), so the hint is noise here.
    warnings.filterwarnings("ignore", message="Hint: Inferred schema contains integer column")
    mlflow.set_tracking_uri(TRACKING_URI)
    mlflow.set_experiment(experiment)
    return experiment


def git_commit() -> str:
    """The commit this ran from, with "+changes" when files were edited since."""
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True, cwd=HERE).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--", "."], capture_output=True, text=True, cwd=HERE).stdout.strip()
        return commit + ("+changes" if dirty else "")
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def this_computer() -> dict:
    """The chip, memory, device and library versions, logged so a result can be traced to where it ran."""
    import torch

    device = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"
    memory_gb = None
    try:  # on a chip with shared memory, the whole machine's memory is what the GPU can use
        out = subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True, check=True).stdout.strip()
        memory_gb = round(int(out) / 1024**3)
    except (OSError, subprocess.CalledProcessError, ValueError):
        pass
    return {
        "chip": platform.processor() or platform.machine(),
        "device": device,
        "memory_gb": memory_gb,
        "python": platform.python_version(),
        **{f"version.{name}": version(name) for name in ("torch", "sentence-transformers", "transformers", "mlflow")},
    }


def table_dataset(rows: list[dict], name: str, *, targets: str | None = None):
    """A table of rows as an MLflow dataset: its digest is a fingerprint of the rows' text and number columns, so a
    run says which version of the data it saw, and two runs on the same rows share the same digest.

    What the digest does not see: MLflow hashes only the columns that are all text or all numbers, so a True/False
    column changes nothing. That is why the honest test stores ``checked`` as 0 or 1 (see ``retrieval.build_honest_test``):
    a person's verdicts must change the digest, or a read test and an unread one would look the same in MLflow.
    """
    import warnings

    import pandas as pd

    with warnings.catch_warnings():  # MLflow's hint about integer columns (the 0/1 checked flag) is noise in a notebook
        warnings.filterwarnings("ignore", message="Hint: Inferred schema contains integer column")
        return mlflow.data.from_pandas(pd.DataFrame(rows), name=name, targets=targets)


def save_json(name: str, data) -> Path:
    """Write a lab file under ``data/`` (the git-ignored working copy) and return its path."""
    DATA.mkdir(exist_ok=True)
    path = DATA / name
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False))
    return path


def find_run(experiment: str, name_start: str, require: tuple[str, ...] = ()):
    """The newest finished run in an experiment whose name starts with ``name_start`` (how a notebook replays a real run
    instead of calling a model again).

    A run that crashed half-way is skipped: MLflow marks a run FINISHED when the notebook's kernel exits, even after an
    error, so a run with no params and no metrics is an empty shell, not a result (``guard_run`` stops most of these
    being made). ``require`` names artifact paths the run must hold (e.g. ``("pairs_dev.json",)``), so the caller gets
    "run its step first" instead of a failed download later.
    """
    client = mlflow.MlflowClient()
    exp = client.get_experiment_by_name(experiment)
    if exp is None:
        raise LookupError(f"No experiment named {experiment!r} on {TRACKING_URI}")
    runs = client.search_runs([exp.experiment_id], filter_string="attributes.status = 'FINISHED'",
                              order_by=["attributes.start_time DESC"], max_results=500)
    for run in runs:
        if not (run.info.run_name or "").startswith(name_start):
            continue
        if not run.data.params and not run.data.metrics:
            continue  # an empty shell left by a crashed pass
        have = {a.path for a in client.list_artifacts(run.info.run_id)}
        if all(path in have for path in require):
            return run
    raise LookupError(f"No finished, complete run named '{name_start}...' in {experiment}"
                      + (f" holding {list(require)}" if require else "") + ": run its step first.")


def guard_run() -> None:
    """End the active MLflow run as FAILED if a notebook cell raises, so a crashed pass never looks like a finished one.

    Without this, an error half-way through leaves the run open until the kernel exits, and MLflow then closes it as
    FINISHED with nothing in it; ``find_run`` would later pick that shell up. Call it right after ``mlflow.start_run``.
    Outside IPython (a plain script) it does nothing; a ``with mlflow.start_run()`` block already does the same job there.
    """
    try:
        from IPython import get_ipython
    except ImportError:  # pragma: no cover - notebooks always have IPython
        return
    shell = get_ipython()
    if shell is None:
        return

    def fail_the_run(shell, etype, value, tb, tb_offset=None):
        if mlflow.active_run():
            print(f"Ending MLflow run {short(mlflow.active_run().info.run_id)} as FAILED because a cell raised {etype.__name__}.")
            mlflow.end_run(status="FAILED")
        shell.showtraceback((etype, value, tb), tb_offset=tb_offset)
        return None

    shell.set_custom_exc((Exception,), fail_the_run)


class Guesses:
    """Your guesses, written down before each result, kept in MLflow next to the real answer.

    The habit this practises: commit to a guess first, then look. Over several notebooks the runs show how close your
    guesses get, which is the only way to know whether your feel for the numbers is improving.
    """

    def __init__(self):
        self.made = {}

    def guess(self, key: str, value) -> None:
        if value is None:
            print("No guess written down. The habit only works if you commit to one before you look.")
            return
        self.made[key] = value
        if mlflow.active_run():
            mlflow.log_param(f"guess.{key}", value)
        print(f"Written down: {key} = {value}")

    def reveal(self, key: str, actual: float, as_percent: bool = True) -> None:
        if mlflow.active_run():
            mlflow.log_metric(f"actual.{key}", float(actual))
        shown = (lambda v: f"{v:.1%}") if as_percent else (lambda v: f"{v:,.0f}" if float(v).is_integer() else f"{v:,.3g}")
        if key not in self.made:
            print(f"{key}: it was {shown(actual)} (no guess written down)")
            return
        mine = float(self.made[key])
        if mlflow.active_run():
            mlflow.log_metric(f"guess_off_by.{key}", abs(mine - actual))
        print(f"{key}: you guessed {shown(mine)}; it was {shown(actual)} (off by {shown(abs(mine - actual))})")
