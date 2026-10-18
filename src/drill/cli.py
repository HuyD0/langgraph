"""The terminal you actually practise in.

    uv run drill start                 # weakest topic picks the problem
    uv run drill start --problem two_sum
    uv run drill start --topic sliding-window
    uv run drill list
    uv run drill stats
    uv run drill check <file.py> --problem two_sum   # just run the tests, no tutor
    uv run drill build-page                          # the Daily Drill page -> dist/daily-drill.html
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from drill.config import PROJECT_ROOT, DrillSettings
from drill.problems import TOPICS, Problem, get_problem, list_problems
from drill.progress import ProgressStore
from drill.sandbox import first_failure, run_submission

app = typer.Typer(
    add_completion=False,
    help="An agentic coding-interview tutor built on LangGraph and MLflow.",
)
console = Console()


def _load_dotenv() -> None:
    """Load a .env at the repo root, if there is one.

    Keeps your Azure keys out of your shell history and out of git (.env is
    gitignored). Real environment variables always win over the file.
    """
    try:
        from dotenv import load_dotenv

        load_dotenv(PROJECT_ROOT / ".env", override=False)
    except Exception:
        pass  # a .env is optional: the CLI must start without one, and without python-dotenv


@app.callback()
def _main() -> None:
    """Runs before every command."""
    _load_dotenv()


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def show_problem(problem: Problem) -> None:
    console.print()
    console.print(
        Panel(
            Markdown(problem.prompt),
            title=f"[bold]{problem.title}[/bold]  ·  {problem.difficulty}  ·  {problem.topic}",
            subtitle=f"target: {problem.target_complexity}",
            border_style="cyan",
        )
    )
    if problem.samples:
        table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
        table.add_column("example call")
        table.add_column("expected")
        for case in problem.samples:
            args = ", ".join(repr(a) for a in case.args)
            table.add_row(f"{problem.function_name}({args})", repr(case.expected))
        console.print(table)
        console.print()


def show_result(result: dict) -> None:
    if result.get("fatal_error"):
        console.print(Panel(result["fatal_error"].strip(), title="[red]did not run[/red]",
                            border_style="red"))
        return

    passed, total = result.get("passed_count", 0), result.get("total", 0)
    colour = "green" if passed == total else "yellow"
    console.print(f"[{colour}]{passed}/{total} test cases passed[/{colour}]")

    case = first_failure(result)
    if case is None:
        return
    args = ", ".join(repr(a) for a in case["args"])
    lines = [f"call:     ({args})", f"expected: {case['expected']!r}"]
    lines.append(
        f"raised:   {case['error'].strip().splitlines()[-1]}"
        if case["error"]
        else f"got:      {case['actual']!r}"
    )
    console.print(Panel("\n".join(lines), title="[yellow]first failing case[/yellow]",
                        border_style="yellow"))


# ---------------------------------------------------------------------------
# Collecting a submission
# ---------------------------------------------------------------------------


def edit_submission(problem: Problem, request: dict) -> str:
    """Open $EDITOR on a scratch file and return whatever you wrote.

    Falls back to reading from stdin when there is no usable editor, which is what
    happens in CI and in a piped shell.
    """
    attempt = request.get("attempt", 1)
    console.print(f"[dim]attempt {attempt} of {request.get('max_attempts', 3)}[/dim]")

    editor = os.environ.get("EDITOR") or os.environ.get("VISUAL")
    if not editor or not sys.stdin.isatty():
        console.print("[dim]Paste your solution, then Ctrl-D:[/dim]")
        return sys.stdin.read()

    with tempfile.TemporaryDirectory(prefix="drill-edit-") as tmp:
        path = Path(tmp) / f"{problem.id}.py"
        path.write_text(problem.starter_code, encoding="utf-8")
        try:
            done = subprocess.run([*editor.split(), str(path)], check=False)
        except OSError:  # $EDITOR names a program that isn't installed
            console.print(f"[yellow]Couldn't open your editor ({editor}). Paste your solution instead, then Ctrl-D.[/yellow]")
            return sys.stdin.read()
        if done.returncode != 0:
            console.print(f"[yellow]Your editor ({editor}) stopped with an error; using what was saved in the file.[/yellow]")
        return path.read_text(encoding="utf-8")


def _problem_or_exit(problem_id: str) -> Problem:
    """The problem with this id, or a plain one-line message (not a traceback) for a typo."""
    try:
        return get_problem(problem_id)
    except KeyError:
        console.print(f"[red]No problem called '{problem_id}'.[/red] Try: drill list")
        raise typer.Exit(1) from None


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@app.command("list")
def list_cmd(
    topic: str = typer.Option(None, help="Filter by topic."),
    difficulty: str = typer.Option(None, help="easy | medium | hard"),
) -> None:
    """Show the problem bank."""
    settings = DrillSettings.from_env()
    solved = ProgressStore(settings.progress_path).solved_ids()

    table = Table(title="problem bank", header_style="bold")
    table.add_column(""); table.add_column("id"); table.add_column("title")
    table.add_column("topic"); table.add_column("difficulty"); table.add_column("pattern")
    for problem in list_problems(topic=topic, difficulty=difficulty):
        table.add_row(
            "[green]done[/green]" if problem.id in solved else "",
            problem.id, problem.title, problem.topic, problem.difficulty,
            problem.pattern.split(". ")[0].rstrip("."),  # the first sentence; `drill solution` has the rest
        )
    console.print(table)
    console.print(f"[dim]topics: {', '.join(TOPICS)}[/dim]")


@app.command("stats")
def stats_cmd() -> None:
    """Show how you are doing, per topic."""
    settings = DrillSettings.from_env()
    store = ProgressStore(settings.progress_path)
    stats = store.stats_by_topic()

    if not stats:
        console.print("No sessions recorded yet. Run [bold]drill start[/bold].")
        return

    table = Table(title="your progress", header_style="bold")
    table.add_column("topic"); table.add_column("sessions", justify="right")
    table.add_column("solved", justify="right"); table.add_column("rate", justify="right")
    for topic, row in sorted(stats.items()):
        rate = row["solved"] / row["attempted"]
        table.add_row(topic, str(row["attempted"]), str(row["solved"]), f"{rate:.0%}")
    console.print(table)

    weakest = store.weakest_topic()
    if weakest:
        console.print(f"\nweakest topic: [bold yellow]{weakest}[/bold yellow] — "
                      f"run [bold]drill start[/bold] and you will get one of these.")
    console.print(f"[dim]history: {settings.progress_path}[/dim]")


@app.command("check")
def check_cmd(
    solution: Path = typer.Argument(..., exists=True, dir_okay=False, help="Python file containing your solution."),
    problem: str = typer.Option(..., "--problem", "-p", help="Which problem it answers."),
) -> None:
    """Run the tests against a file, with no tutor and no LLM call.

    Useful when you want the grader but not the conversation - and it works with
    no Azure credentials configured at all.
    """
    prob = _problem_or_exit(problem)
    settings = DrillSettings.from_env()
    result = run_submission(prob, solution.read_text(encoding="utf-8"),
                            timeout=settings.sandbox_timeout)
    show_result(result)  # type: ignore[arg-type]
    raise typer.Exit(0 if result["passed"] else 1)


@app.command("solution")
def solution_cmd(
    problem: str = typer.Argument(..., help="Problem id."),
) -> None:
    """Print the reference solution. Use it after you have genuinely tried."""
    prob = _problem_or_exit(problem)
    console.print(Panel(f"[bold]{prob.pattern}[/bold]\n[dim]{prob.target_complexity}[/dim]",
                        border_style="dim"))
    console.print(Syntax(prob.reference_solution, "python", theme="ansi_dark"))


@app.command("start")
def start_cmd(
    problem: str = typer.Option(None, "--problem", "-p", help="Practise a specific problem."),
    topic: str = typer.Option(None, "--topic", "-t", help="Practise a specific topic."),
) -> None:
    """Start a tutored practice session. Requires Azure AI Foundry credentials."""
    from drill.deps import Deps
    from drill.graph import build_drill_graph
    from drill.llm import MissingCredentials
    from drill.session import run_session
    from drill.tracking import setup_tracing

    if problem:
        _problem_or_exit(problem)  # a typo gets one plain line, before any model is set up
    if topic and topic not in TOPICS:
        console.print(f"[red]No topic called '{topic}'.[/red] Topics: {', '.join(TOPICS)}")
        raise typer.Exit(1)
    settings = DrillSettings.from_env()
    try:
        deps = Deps.from_env()
    except MissingCredentials as exc:
        console.print(Panel(str(exc), title="[red]not configured[/red]", border_style="red"))
        console.print("[dim]You can still use[/dim] drill check [dim]and[/dim] drill list "
                      "[dim]without credentials.[/dim]")
        raise typer.Exit(1)

    if setup_tracing(settings):
        console.print(f"[dim]tracing to MLflow experiment '{settings.mlflow_experiment}' "
                      f"— view with: uv run mlflow ui[/dim]")

    def on_event(kind: str, payload: dict) -> None:
        if kind == "problem":
            show_problem(payload["problem"])
        elif kind == "hint":
            if payload.get("result"):
                show_result(payload["result"])
            console.print(Panel(Markdown(payload["hint"]), title="[cyan]hint[/cyan]",
                                border_style="cyan"))
        elif kind == "finished":
            title = "[green]solved[/green]" if payload["solved"] else "[yellow]walkthrough[/yellow]"
            console.print(Panel(Markdown(payload["feedback"]), title=title,
                                border_style="green" if payload["solved"] else "yellow"))

    try:
        outcome = run_session(
            build_drill_graph(), deps, edit_submission,
            problem_id=problem, topic=topic, on_event=on_event,
        )
    except (ConnectionError, TimeoutError) as exc:
        _model_unreachable(exc)
    except Exception as exc:
        # The model SDKs raise their own error types for "couldn't connect" and "timed out".
        if "connect" in type(exc).__name__.lower() or "timeout" in type(exc).__name__.lower():
            _model_unreachable(exc)
        raise

    verb = "Solved" if outcome.solved else "Not solved"
    console.print(f"\n{verb} [bold]{outcome.problem.title}[/bold] in {outcome.attempts} "
                  f"attempt(s) with {len(outcome.hints)} hint(s).")
    raise typer.Exit(0)


@app.command("build-page")
def build_page_cmd(
    out: Path | None = typer.Option(None, "--out", "-o", help="Directory to write into (default dist/, or dist/private/ with --pack)."),
    pack: list[Path] = typer.Option([], "--pack", help="A content pack folder to include; repeat for several. Its output is private: never publish it."),
) -> None:
    """Build the Daily Drill page (web) from src/drill/content, checking every exercise first."""
    from drill.content.build import main as build_main

    args = ["--out", str(out)] if out else ["--out", str(PROJECT_ROOT / "dist")] if not pack else []
    for p in pack:
        args += ["--pack", str(p)]
    raise typer.Exit(build_main(args))


content_app = typer.Typer(add_completion=False, help="The curriculum's content: lessons due for a fact check, and content packs to check and preview.")
app.add_typer(content_app, name="content")


@content_app.command("stale")
def content_stale(
    days: int = typer.Option(180, help="Flag lessons last checked more than this many days ago."),
    all_: bool = typer.Option(False, "--all", help="Also list the fresh lessons."),
) -> None:
    """List lessons whose facts are due for another check, with the pages to check them against."""
    import datetime

    from drill.content import modules
    from drill.content.freshness import freshness

    report = freshness(modules.load(), datetime.date.today(), days)
    for row in report["due"]:
        what = "content as of" if row.get("as_of") else "checked"
        console.print(f"[yellow]due[/] {row['id']} ({row['module']}): {what} {row['checked']}, {row['age']} days ago")
        for title, url in row["sources"]:
            console.print(f"     {title}: {url}")
    if all_:
        for row in report["fresh"]:
            what = "content as of" if row.get("as_of") else "checked"
            console.print(f"[dim]fresh[/] {row['id']} ({row['module']}): {what} {row['checked']}")
    sourced = sum(1 for r in report["fresh"] + report["due"] if r["sources"])
    console.print(f"{len(report['fresh'])} fresh, {len(report['due'])} due; {sourced} checked against sources")
    raise typer.Exit(1 if report["due"] else 0)


review_app = typer.Typer(add_completion=False, help="The use case review prompt: score it on cards with planted gaps before publishing a change.")
app.add_typer(review_app, name="review")


@review_app.command("eval")
def review_eval_cmd(
    judge: bool = typer.Option(False, "--judge", help="Also ask the model whether every claim is backed by the card."),
    tier: str = typer.Option("default", "--tier", help="Which model tier to ask: default or complex."),
    no_mlflow: bool = typer.Option(False, "--no-mlflow", help="Score and print only, without an MLflow evaluation run."),
) -> None:
    """Ask the model to review each planted-gap card and score the reviews. Fails if a must-pass case fails."""
    from rich.table import Table

    from drill import review_eval
    from drill.content.review import REVIEW_VERSION

    rows = review_eval.run(tier=tier, judge=judge, use_mlflow=not no_mlflow)
    keys = [k for k in ("all_pillars", "gaps_flagged", "no_verdict", "high_risk_named", "grounded", "must_pass") if any(k in r for r in rows)]
    table = Table(title=f"Review prompt {REVIEW_VERSION}: {len(rows)} cases")
    table.add_column("case")
    for k in keys:
        table.add_column(k.replace("_", " "))
    for r in rows:
        table.add_row(r["case"], *["-" if k not in r else ("yes" if r[k] is True else "no" if r[k] is False else str(r[k])) for k in keys])
    console.print(table)
    failed = [r["case"] for r in rows if not r.get("must_pass")]
    if failed:
        console.print(f"[red]Must-pass failed:[/red] {', '.join(failed)}")
        raise typer.Exit(1)
    console.print("Every must-pass case passed: every planted gap flagged, and no verdict.")


@review_app.command("label")
def review_label_cmd(n: int = typer.Option(10, "--n", help="How many reviews to label this time.")) -> None:
    """Label recent reviews: did each one invent a fact the card does not contain? Saved on the trace in MLflow."""
    from rich.panel import Panel

    from drill import review_ops

    def ask(answer: str, card_text: str, card: dict):
        console.rule("A review to label")
        console.print(Panel(card_text, title="The card", expand=False))
        console.print(Panel(answer, title="The review", expand=False))
        choice = typer.prompt("Did it invent a fact the card does not contain? [y]es / [n]o / [s]kip / [q]uit", default="s").strip().lower()[:1]
        if choice == "q":
            raise typer.Exit(0)
        if choice not in ("y", "n"):
            return None, ""
        note = typer.prompt("Which claim? (Enter to leave blank)", default="", show_default=False) if choice == "y" else ""
        return choice == "n", note

    done = review_ops.label(n, ask)
    console.print(f"Labelled {done} review{'s' if done != 1 else ''}. Next: uv run drill review calibrate")


@review_app.command("calibrate")
def review_calibrate_cmd(tier: str = typer.Option("default", "--tier", help="Which model tier the judge uses.")) -> None:
    """Run the groundedness judge on the reviews you labelled, and show how well it agrees with you."""
    from drill import review_ops

    r = review_ops.calibrate(tier=tier)
    if not r["n"]:
        console.print("No labelled reviews yet. Run: uv run drill review label")
        raise typer.Exit(1)
    kappa = r["kappa"] if r["kappa"] is not None else "not enough variety yet (every label is the same)"
    console.print(f"Judge {r['judge_version']} on {r['n']} reviews you labelled: agrees {r['agreement']:.0%} of the time, kappa {kappa}.")
    if r["n"] < 20:
        console.print(f"Only {r['n']} labelled so far: label at least 20, including some with inventions, before trusting these numbers.")
    console.print(f"Missed an invention you found: {r['judge_missed']}. Flagged one you did not see: {r['judge_false_alarm']}.")
    console.print("Rough guide: kappa above 0.6 is good enough to lean on; below 0.4, keep reading the reviews yourself.")


@review_app.command("register")
def review_register_cmd() -> None:
    """Put the review and challenge prompts in MLflow's prompt registry, and point 'production' at them."""
    from drill import review_ops

    for p in review_ops.register():
        state = "new version" if p["registered_new"] else "unchanged"
        console.print(f"{p['name']}: version {p['version']} ({p['drill_version']}, {state}), alias production -> {p['uri']}")


tutor_app = typer.Typer(add_completion=False, help="Material for a chat tutor (a Claude Project): the curriculum map and a snapshot of your progress.")
app.add_typer(tutor_app, name="tutor")


@tutor_app.command("map")
def tutor_map_cmd() -> None:
    """Write docs/tutor/CURRICULUM_MAP.md from the lessons: every module, lesson, exercise, notebook and term."""
    from drill import tutor

    path = tutor.write_map()
    console.print(f"Wrote {path.relative_to(PROJECT_ROOT)}")


@tutor_app.command("feedback")
def tutor_feedback_cmd(
    days: float = typer.Option(7.0, "--days", help="Read answers from this many days back."),
    dataset: bool = typer.Option(False, "--dataset", help="Also add the answers that didn't help to the tutor_cases eval dataset."),
    target: str = typer.Option("", "--target", help="Read the deployed app's traces on Databricks instead of this Mac's (personal or work)."),
    profile: str = typer.Option(None, "--profile", "-p", help="Databricks CLI profile (default: the one databricks.yml names for the target)."),
) -> None:
    """How often the tutor's answers worked (Got it / Still stuck and the quiet signals), and the eval cases they make."""
    import os

    import mlflow

    from drill import mlflow_names, tutor_feedback

    if target:
        from drill import cloud

        prof = _cloud(lambda: cloud.profile_for(target, profile))
        saved = cloud.read_overrides(target)
        if "experiment_id" not in saved:
            console.print(f"[red]Run `uv run drill cloud setup --target {target}` first.[/red]")
            raise typer.Exit(1)
        if saved.get("warehouse_id"):
            os.environ.setdefault("MLFLOW_TRACING_SQL_WAREHOUSE_ID", saved["warehouse_id"])
        mlflow.set_tracking_uri(f"databricks://{prof}" if prof else "databricks")
        experiment_id = saved["experiment_id"]
    else:
        if not os.getenv("MLFLOW_TRACKING_URI"):
            from drill.server.store import data_dir

            mlflow.set_tracking_uri(f"sqlite:///{data_dir() / 'mlflow.db'}")  # where drill-server traces by default
        found = mlflow.get_experiment_by_name(mlflow_names.experiment())
        if found is None:
            console.print(f"No experiment named {mlflow_names.experiment()} yet: ask the tutor something with drill-server running first.")
            return
        experiment_id = found.experiment_id
    answers = tutor_feedback.read(experiment_id, days)
    if not answers:
        console.print("No tutor answers in that window.")
        return
    s = tutor_feedback.summarise(answers)
    share = lambda v: "no ratings yet" if v is None else f"{v:.0%}"  # noqa: E731
    console.print(f"{s['answers']} answers ({s['first_answers']} first answers, {s['rated']} rated Got it or Still stuck)")
    console.print(f"  First answer worked (Got it): {share(s['first_answer_resolved'])}")
    console.print(f"  Still stuck: {s['still_stuck']}; the simpler answer then worked: {share(s['retry_resolved'])}")
    for name in tutor_feedback.SIGNALS:
        console.print(f"  {name}: {s[name]['true']} of {s[name]['answers']}")
    if s["lessons_most_stuck"]:
        console.print("  Lessons where answers most often didn't help: " + ", ".join(f"{k} ({v})" for k, v in s["lessons_most_stuck"]))
    if dataset:
        records = tutor_feedback.cases(answers)
        if not records:
            console.print("No answers that didn't help, so nothing to add to tutor_cases.")
            return
        saved_ds = tutor_feedback.save_cases(mlflow, experiment_id, records)
        if saved_ds is not None:
            console.print(f"Added {len(records)} cases to {mlflow_names.dataset_name('tutor_cases')}.")


@tutor_app.command("prepare")
def tutor_prepare_cmd(
    profile: str = typer.Option(None, "--profile", "-p", help="Databricks CLI profile whose serving endpoints draft and judge (costs money)."),
    module: str = typer.Option("", "--module", "-m", help="Only this module (for example use-case)."),
    lesson: str = typer.Option("", "--lesson", help="Only this lesson."),
    limit: int = typer.Option(0, "--limit", help="At most this many answers (0: all that are missing or out of date)."),
    redo: bool = typer.Option(False, "--redo", help="Draft again even answers that are ready (or rejected)."),
    draft_model: str = typer.Option("", "--draft-model", help="Serving endpoint that drafts (default: the strongest Claude)."),
    judge_model: str = typer.Option("", "--judge-model", help="Serving endpoint that judges (default: a different Claude)."),
    workers: int = typer.Option(6, "--workers", help="Answers drafted at the same time."),
) -> None:
    """Draft and judge answers to the tutor's standard questions, so Ask works with no model. Costs money on Databricks."""
    from drill import tutor_prepared as tp
    from drill.content.build import build_data

    data = build_data()
    answers = tp.load()
    work = tp.todo(data, answers, module or None, lesson or None, redo)
    if limit:
        work = work[:limit]
    if not work:
        console.print("Nothing to prepare: every answer is ready. `drill tutor prepared` shows the counts.")
        return
    draft_model, judge_model = draft_model or tp.DRAFT_MODEL, judge_model or tp.JUDGE_MODEL
    console.print(f"Preparing {len(work)} answers: drafted by {draft_model}, judged by {judge_model}.")
    passed = failed = 0

    def done(lid, chip, rec):
        nonlocal passed, failed
        passed += rec["status"] == "passed"
        failed += rec["status"] != "passed"
        if rec["status"] != "passed":
            console.print(f"  [yellow]failed[/yellow] {lid} {chip['key']}: {rec.get('judge', {}).get('notes', '')}")
        if (passed + failed) % 25 == 0:
            console.print(f"  {passed + failed} of {len(work)} done ({passed} passed)")

    # One MLflow run for the batch (in the app's experiment), one trace per answer, the model calls inside.
    import contextlib
    import time

    import mlflow

    from drill import mlflow_names, tutor_prepared_eval as tpe
    from drill.server.observe import app_version

    run_ctx = contextlib.nullcontext()
    try:
        mlflow.set_experiment(mlflow_names.experiment())
        mlflow.openai.autolog()
        prompts = tpe.register_prompts(mlflow)
        scope = f"lesson {lesson}" if lesson else f"module {module}" if module else "all missing"
        run_ctx = mlflow.start_run(run_name=f"prepare answers · {scope} · draft {draft_model.removeprefix('databricks-')} "
                                            f"· judge {judge_model.removeprefix('databricks-')} · {len(work)} answers")
        traced = True
    except Exception as exc:  # noqa: BLE001 - no MLflow: prepare anyway, untraced
        console.print(f"[yellow]MLflow unavailable ({str(exc)[:80]}): preparing without traces.[/yellow]")
        prompts, traced = {}, False
    with run_ctx:
        if traced:
            mlflow.set_tags({**mlflow_names.context_tags(app_version()), "kind": "tutor_prepare", "mlflow.source.git.commit": tpe.git_commit(),
                             "mlflow.note.content": (
                                 f"**Question:** which of {len(work)} new prepared tutor answers ({scope}) are good enough to show "
                                 "learners?\n\n"
                                 f"**What ran:** {draft_model} drafted each answer from its lesson with the registered drafting prompt; "
                                 f"{judge_model}, a different model, judged it against the five checks.\n\n"
                                 "**How it's measured:** an answer is served only if every check passes (correct, answers it, plain, no "
                                 "giveaway, standalone); pass rate and cost are logged.\n\n"
                                 f"**Reproduce:** `uv run drill tutor prepare --profile {profile or 'DEFAULT'}"
                                 + (f" --lesson {lesson}" if lesson else f" --module {module}" if module else "")
                                 + f" --draft-model {draft_model} --judge-model {judge_model}` (git commit {tpe.git_commit()[:7]}).")})
            mlflow.log_params({"draft_model": draft_model, "judge_model": judge_model, "answers": len(work), "module": module or "all",
                               "lesson": lesson or "all", "redo": redo, "workers": workers,
                               **{f"{k}_prompt": f"{v.name}/{v.version}" for k, v in prompts.items()}})
        drafter, judger = tp.databricks_chat(draft_model, profile), tp.databricks_chat(judge_model, profile)
        tp.run(data, work, drafter, judger, answers, workers=workers, on_done=done, traced=traced,
               draft_model=draft_model, judge_model=judge_model)
        spend = {f"{who}_{k}": float(chat.usage[k]) for who, chat in (("draft", drafter), ("judge", judger)) for k in ("calls", "input_tokens", "output_tokens", "seconds")}
        total = sum(tp.cost(chat.model, chat.usage["input_tokens"], chat.usage["output_tokens"]) for chat in (drafter, judger))
        console.print(f"Cost at list price: ${total:.2f} (${total / max(1, len(work)):.4f} an answer). The DBU charge is in system.billing.usage.")
        if traced:
            mlflow.log_metrics({"passed": passed, "failed": failed, "pass_rate": passed / max(1, passed + failed), **spend,
                                "cost_usd": total, "cost_per_answer_usd": total / max(1, len(work))})
    console.print(f"Done: {passed} passed, {failed} failed. Saved in src/drill/content/prepared/. Rebuild the page to serve them.")


@tutor_app.command("prepared")
def tutor_prepared_cmd(
    sample: int = typer.Option(0, "--sample", help="Show every failed answer and this many passed ones, for a spot check."),
    check: list[str] = typer.Option([], "--check", help="Mark lesson_id/key as checked by you (repeatable)."),
    reject: list[str] = typer.Option([], "--reject", help="Mark lesson_id/key as rejected: never served (repeatable)."),
) -> None:
    """How many prepared answers are ready, failed or out of date; a spot-check sample; your verdicts."""
    from drill import tutor_prepared as tp
    from drill.content.build import build_data

    data, answers = build_data(), tp.load()
    for verdict, items in (("checked", check), ("rejected", reject)):
        for item in items:
            lid, _, key = item.partition("/")
            if key not in answers.get(lid, {}):
                console.print(f"[red]No prepared answer {item}[/red]")
                raise typer.Exit(1)
            tp.mark(answers, lid, key, verdict)
    if check or reject:
        tp.save(data, answers)
    counts = tp.status(data, answers)
    console.print(", ".join(f"{k}: {v}" for k, v in counts.items()))
    for lid, key, rec in tp.sample(answers, sample) if sample else []:
        judge = rec.get("judge", {})
        console.print(f"\n[bold]{lid}/{key}[/bold] [{rec.get('status')}] {rec['q']}\n{rec['a']}")
        if judge.get("notes"):
            console.print(f"[dim]judge: {judge['notes']}[/dim]")


@tutor_app.command("prepared-eval")
def tutor_prepared_eval_cmd(
    profile: str = typer.Option(None, "--profile", "-p", help="Databricks CLI profile for the judge's serving endpoint (costs a little)."),
    judge_model: str = typer.Option("", "--judge-model", help="Serving endpoint that judges (default: Haiku)."),
    split: str = typer.Option("dev", "--split", help="dev (tune here), test (before a release) or holdout (big decisions only)."),
    holdout_ok: bool = typer.Option(False, "--yes-holdout", help="Confirm a holdout run: once you change things because of it, it is no longer a holdout."),
    workers: int = typer.Option(4, "--workers", help="Answers judged at the same time (the workspace limits tokens per minute)."),
    sample: int = typer.Option(0, "--sample", help="A stratified sample of this many (every reference failure, the rest spread by phase and kind); 0: the whole split."),
) -> None:
    """Judge one split of the prepared answers as an MLflow evaluation: versioned datasets, registered prompts, traces, intervals, kappa."""
    import os

    os.environ["MLFLOW_GENAI_EVAL_MAX_WORKERS"] = str(workers)  # read when the evaluation starts

    from drill import tutor_prepared_eval as tpe

    import mlflow

    if split == "holdout" and not holdout_ok:
        console.print("[red]The holdout is for big decisions only. Add --yes-holdout if this is one.[/red]")
        raise typer.Exit(1)
    console.print(f"MLflow: {mlflow.get_tracking_uri()}  split: {split}")
    result = tpe.evaluate(profile, judge_model or tpe.JUDGE_MODEL, split, workers, sample=sample)
    n = result["numbers"]
    console.print(f"Run {result['run_id']} (experiment {result['experiment_id']}): {result['records']} answers in {split}.")
    if result["strata_missing"]:
        console.print(f"[yellow]Strata missing from a split: {', '.join(result['strata_missing'][:8])}[/yellow]")
    console.print(f"  Catches the reference's failures: {n['catch_rate']:.1%} of {n['catch_n']:.0f} ({n['catch_ci_low']:.0%} to {n['catch_ci_high']:.0%})")
    console.print(f"  Keeps the reference's passes: {n['keep_rate']:.1%} of {n['keep_n']:.0f} ({n['keep_ci_low']:.0%} to {n['keep_ci_high']:.0%})")
    if "weighted_agreement" in n:
        console.print(f"  Agreement re-weighted to the split's real mix: {n['weighted_agreement']:.1%}")
    console.print(f"  Pass rate in this sample: {n['passes_rate']:.1%} (95% interval {n['passes_ci_low']:.1%} to {n['passes_ci_high']:.1%})")
    console.print(f"  Cost: ${n['judge_cost_usd']:.2f} at list price ({n['judge_calls']:.0f} calls, {n['judge_rate_limited']:.0f} rate-limited)")
    console.print(f"  Agreement with the reference judge: {n['passes_agreement']:.1%}, kappa {n.get('passes_kappa', float('nan')):.2f}")
    for check in tpe.CHECKS:
        console.print(f"    {check}: pass {n[check + '_rate']:.1%}, kappa {n.get(check + '_kappa', float('nan')):.2f}")


@tutor_app.command("prepared-compare")
def tutor_prepared_compare_cmd(run_a: str = typer.Argument(..., help="The first eval run id."),
                               run_b: str = typer.Argument(..., help="The second eval run id.")) -> None:
    """Compare two judge runs on the same answers with McNemar's test: only the disagreements count."""
    from drill import tutor_prepared_eval as tpe

    r = tpe.compare(run_a, run_b)
    console.print(f"{r['answers']} answers in both runs. Agreement with the reference: A {r['agreement_a']:.1%}, B {r['agreement_b']:.1%}.")
    console.print(f"Only A agreed on {r['only_a_agrees']}, only B on {r['only_b_agrees']}. McNemar p = {r['p_value']:.3f}"
                  + (" (a real difference)" if r["p_value"] < 0.05 else " (could be luck)"))


@tutor_app.command("snapshot")
def tutor_snapshot_cmd(
    out: Path = typer.Option(None, "--out", "-o", help="Where to write it (default ~/Documents/daily-drill/tutor-snapshot.md)."),
    progress: Path = typer.Option(None, "--progress", exists=True, help="Progress exported from the claude.ai page, to merge in."),
    study: Path = typer.Option(None, "--study", exists=True, help="Study items exported from the claude.ai page (a file or folder), to merge in."),
    copy: bool = typer.Option(False, "--copy", help="Also put the text on the clipboard, to paste into the project."),
) -> None:
    """Write a one-page snapshot of where you are, to give your tutor project. It is personal: keep it out of git."""
    import subprocess

    from drill import tutor

    path = tutor.write_snapshot(out or tutor.SNAPSHOT_PATH, progress, study)
    console.print(f"Wrote {path}")
    if copy:
        subprocess.run(["pbcopy"], input=path.read_text(), text=True, check=False)
        console.print("Copied to the clipboard.")
    console.print("Next: in your tutor project's knowledge, remove last week's tutor-snapshot.md, then add this one.")


tracing_app = typer.Typer(add_completion=False, help="Where MLflow traces go: this Mac's MLflow, or your Databricks workspace.")
app.add_typer(tracing_app, name="tracing")


@tracing_app.command("use")
def tracing_use_cmd(
    target: str = typer.Argument(..., help="local (this Mac's MLflow, free) or databricks (your workspace; reading traces there uses a SQL warehouse)."),
    uri: str = typer.Option(None, "--uri", help="The local MLflow server (default http://localhost:5050)."),
) -> None:
    """Switch where the drill server's traces go, by changing MLFLOW_TRACKING_URI in .env."""
    from drill.config import LOCAL_TRACKING_URI, set_tracking_target

    try:
        value = set_tracking_target(PROJECT_ROOT / ".env", target.lower(), uri or LOCAL_TRACKING_URI)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from None
    console.print(f"Traces now go to {value} (MLFLOW_TRACKING_URI in .env).")
    if value == "databricks":
        console.print("Databricks also needs DATABRICKS_CONFIG_PROFILE in .env; check with `uv run drill tracing check`.")
    console.print("Restart drill-server to pick it up.")


@tracing_app.command("check")
def tracing_check_cmd(
    experiment: str = typer.Option(None, "--experiment", "-e", help="Experiment to check (default DRILL_MLFLOW_EXPERIMENT or daily-drill)."),
    uc_schema: str = typer.Option(None, "--uc-schema", help="Databricks only: create the experiment with its traces in this Unity Catalog schema (catalog.schema)."),
) -> None:
    """Say where traces go, check the connection, create the experiment if needed, and log one test trace."""
    import os

    import mlflow

    from drill.config import (
        databricks_profile,
        databricks_user,
        experiment_path,
        is_databricks_uri,
        uc_trace_location,
    )

    os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")
    uri = os.getenv("MLFLOW_TRACKING_URI", "").strip()
    if not uri:
        from drill.server.store import data_dir

        uri = f"sqlite:///{data_dir() / 'mlflow.db'}"
    mlflow.set_tracking_uri(uri)
    name = experiment or os.getenv("DRILL_MLFLOW_EXPERIMENT") or "daily-drill"
    if is_databricks_uri(uri):
        from databricks.sdk import WorkspaceClient

        user = databricks_user(uri)
        host = WorkspaceClient(profile=databricks_profile(uri)).config.host.rstrip("/")
        console.print(f"Traces go to your Databricks workspace: {host} (profile {databricks_profile(uri) or 'DEFAULT'})")
        name = experiment_path(name, uri, user)
    else:
        host = None
        console.print(f"Traces go to MLflow on this Mac: {uri}")
    if uc_schema and host:
        # Traces in Unity Catalog travel through the Databricks API, so a workspace storage
        # firewall doesn't block them. The link can only be made when the experiment is created.
        from mlflow.entities.trace_location import UnityCatalog

        existing = mlflow.get_experiment_by_name(name)
        if existing and not uc_trace_location(existing):
            console.print(f"[red]{name} already exists with its traces in the experiment.[/red] "
                          "A Unity Catalog link can only be set when an experiment is created: pick another name with -e.")
            raise typer.Exit(1)
        catalog, _, schema = uc_schema.partition(".")
        prefix = "".join(ch if ch.isalnum() else "_" for ch in name.rsplit("/", 1)[-1])
        exp = mlflow.set_experiment(name, trace_location=None if existing else UnityCatalog(catalog, schema, table_prefix=prefix))
    else:
        exp = mlflow.set_experiment(name)
    where = uc_trace_location(exp)
    console.print(f"Experiment: {name}")
    console.print(
        f"Storage: Unity Catalog ({where}), so reading traces needs a SQL warehouse, which costs compute"
        if where else "Storage: the experiment itself (no SQL warehouse needed to read traces)"
    )
    with mlflow.start_span(name="drill tracing check") as span:
        span.set_inputs({"check": "can this machine write a trace here?"})
        span.set_outputs({"ok": True})
    mlflow.flush_trace_async_logging()
    if where and not os.getenv("MLFLOW_TRACING_SQL_WAREHOUSE_ID"):
        console.print("Test trace sent. To read it back here, set MLFLOW_TRACING_SQL_WAREHOUSE_ID to a SQL warehouse id.")
        console.print(f"Open it: {host}/ml/experiments/{exp.experiment_id}/traces")
        return
    try:
        found = mlflow.search_traces(locations=[exp.experiment_id], max_results=1, return_type="list")
    except Exception as exc:
        if "AuthorizationFailure" in str(exc) or "403" in str(exc):
            console.print(
                "[red]The trace's data could not be saved or read.[/red] The workspace's storage account "
                "refused this machine (403 AuthorizationFailure). That usually means the workspace's "
                "storage firewall is on, so only the workspace's own networks may write there. Store the "
                "traces in Unity Catalog instead (they go through the Databricks API): rerun with "
                "--uc-schema catalog.schema and a new -e name. See docs/SERVER.md."
            )
            raise typer.Exit(1) from None
        raise
    console.print(f"Test trace logged and read back: {'yes' if found else 'no'}")
    if host:
        console.print(f"Open it: {host}/ml/experiments/{exp.experiment_id}/traces")


study_app = typer.Typer(add_completion=False, help="The study list on this Mac: export it, or merge another copy in.")
app.add_typer(study_app, name="study")


@study_app.command("export")
def study_export_cmd(out: Path = typer.Argument(..., help="JSON file to write.")) -> None:
    """Write this Mac's study list (the one drill-server's page uses) to a JSON file."""
    import json

    from drill.server import study
    from drill.server.store import open_store

    items = study.load(open_store())
    out.write_text(json.dumps(items, indent=1))
    console.print(f"Wrote {len(items)} study items to {out}")


@study_app.command("import")
def study_import_cmd(
    source: Path = typer.Argument(..., exists=True, help="A JSON file of items, or a folder of item files."),
) -> None:
    """Merge a study list into this Mac's copy: new items are added, and the newer copy of an item wins."""
    from drill.server import study
    from drill.server.store import open_store

    counts = study.import_items(open_store(), study.read_items(source))
    console.print(f"Added {counts['added']}, updated {counts['updated']}, left {counts['unchanged']} as they were.")


store_app = typer.Typer(add_completion=False, help="Where progress is kept: this machine's SQLite file, or Lakebase.")
app.add_typer(store_app, name="store")


@store_app.command("status")
def store_status_cmd() -> None:
    """Say where progress is being saved, as whom, and how many events are recorded."""
    from drill.server.store import open_store

    store = open_store()
    where = "this machine (Lakebase was out of reach)" if store.fallback else store.kind
    console.print(f"Saving to: {where}\nAs: {store.owner}\nEvents recorded: {len(store.events())}")


@store_app.command("push")
def store_push_cmd() -> None:
    """Send this machine's progress, study list and events up to Lakebase.

    Use it after working while Lakebase was out of reach, or once to bring your own
    history (saved as "local") to work. The newer copy of each document wins, and
    events already sent are skipped, so running it twice is harmless.
    """
    from drill.server.store import LOCAL_OWNER, DocStore, local_url, open_store

    target = open_store()
    if target.kind != "lakebase":
        console.print("[red]Lakebase is not set up or out of reach.[/] Set DRILL_LAKEBASE_ENDPOINT and DRILL_DATABASE_URL "
                      "(see docs/SERVER.md), run `databricks auth login`, and try again.")
        raise typer.Exit(1)
    for owner in dict.fromkeys([LOCAL_OWNER, target.owner]):
        counts = DocStore(local_url(), owner=owner).push_to(target)
        console.print(f"From {owner}: {counts['docs']} documents sent, {counts['skipped']} already up to date, "
                      f"{counts['events']} events sent.")





@content_app.command("check")
def content_check_cmd(packs: list[Path] = typer.Argument(None, help="Pack folders (default: DRILL_CONTENT_PACKS).")) -> None:
    """Check content packs: every problem, each naming its file and field. Exits 1 if any."""
    from drill.content import modules
    from drill.content import packs as content_packs

    dirs = packs or content_packs.pack_dirs()
    if not dirs:
        console.print("No pack given. Pass a folder, or set DRILL_CONTENT_PACKS.")
        raise typer.Exit(1)
    taken = {lesson["id"] for m in modules.load() for lesson in m.lessons}
    try:
        content_packs.load_packs(dirs, taken=taken, drafts=True)
        for line in content_packs.report(dirs):
            console.print(f"[green]✓[/green] {line}")
    except content_packs.PackError as exc:
        for problem in exc.problems:
            console.print(f"[red]✗[/red] {problem}")
        console.print(f"\n{len(exc.problems)} problem(s). Fix them and run this again.")
        raise typer.Exit(1)


@content_app.command("preview")
def content_preview_cmd(
    packs: list[Path] = typer.Argument(..., help="Pack folders to preview."),
    port: int = typer.Option(8790, "--port", help="Where to serve it."),
    drafts: bool = typer.Option(True, "--drafts/--no-drafts", help="Show draft lessons too (marked Draft)."),
) -> None:
    """Serve the page with these packs on this machine (a scratch progress file, not yours)."""
    import os

    from drill.config import PROJECT_ROOT

    os.environ["DRILL_CONTENT_PACKS"] = os.pathsep.join(str(p.resolve()) for p in packs)
    os.environ["DRILL_SHOW_DRAFTS"] = "1" if drafts else "0"
    os.environ["DRILL_PORT"] = str(port)
    os.environ.setdefault("DRILL_DATABASE_URL", f"sqlite:///{PROJECT_ROOT / '.drill' / 'preview.db'}")
    os.environ.setdefault("DRILL_TRACING", "0")
    console.print(f"Previewing {', '.join(p.name for p in packs)} at http://127.0.0.1:{port} (Ctrl+C to stop)")
    from drill.server.api import main as serve

    serve()


cloud_app = typer.Typer(add_completion=False, help="Run the server as a Databricks App: setup, deploy, start, stop, status.")
app.add_typer(cloud_app, name="cloud")

TARGET = typer.Option("personal", "--target", "-t", help="Which workspace, from databricks.yml: personal or work.")
PROFILE = typer.Option(None, "--profile", "-p", help="Databricks CLI profile (default: the one databricks.yml names for the target).")


def _model_unreachable(exc: Exception) -> None:
    console.print(f"[red]The tutor's model didn't answer ({type(exc).__name__}: {exc}).[/red]\n"
                  "Is Ollama running (`ollama serve`), or is your hosted model set in .env?")
    raise typer.Exit(1) from None


def _cloud(step):
    """Run one cloud step, turning its errors into a red line instead of a traceback."""
    from drill.cloud import CloudError

    try:
        return step()
    except CloudError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from None


def _show_status(info: dict) -> None:
    console.print(f"{info['name']}: [bold]{info['state']}[/bold]" + (f"  {info['url']}" if info.get("url") else ""))


@cloud_app.command("setup")
def cloud_setup_cmd(
    target: str = TARGET,
    profile: str = PROFILE,
    project: str = typer.Option("daily-drill", "--lakebase-project", help="The Lakebase project that keeps progress."),
    create_lakebase: bool = typer.Option(False, "--create-lakebase", help="Create the Lakebase project if it is not there."),
    experiment: str = typer.Option(None, "--experiment", help="The app's MLflow experiment (default /Shared/daily-drill, apart from your own)."),
    warehouse: str = typer.Option(None, "--warehouse", help="SQL warehouse id for attaching feedback to traces in Unity Catalog (default: the smallest serverless one)."),
    prompt_schema: str = typer.Option(None, "--prompt-schema", help="catalog.schema of the app's prompts, linked to each version at deploy."),
    trace_schema: str = typer.Option(None, "--trace-schema", help="catalog.schema to keep a new experiment's traces in Unity Catalog (needed behind a storage firewall)."),
    model: str = typer.Option(None, "--model", help="Unity Gateway model service for the tutor, catalog.schema.name (default system.ai.claude-haiku-4-5)."),
    name: str = typer.Option(None, "--name", help="The app's name in the workspace (default daily-drill)."),
) -> None:
    """Once per workspace: find or create the Lakebase project and experiment, and save their values for deploy."""
    from drill import cloud

    prof = _cloud(lambda: cloud.profile_for(target, profile))
    info = _cloud(lambda: cloud.setup(target, prof, project, create_lakebase, experiment, model, name, trace_schema,
                                      warehouse, prompt_schema))
    console.print(f"Lakebase: {info['lakebase_database']}\nTraces: {info['experiment']} ({info['experiment_id']})")
    console.print(f"Saved to {info['file']} (git ignores it). Next: uv run drill cloud deploy --target {target}")


@cloud_app.command("deploy")
def cloud_deploy_cmd(target: str = TARGET, profile: str = PROFILE) -> None:
    """Upload the code and start the app on it. Takes a few minutes; the app bills while it runs."""
    from drill import cloud

    prof = _cloud(lambda: cloud.profile_for(target, profile))
    console.print(f"Deploying to {target}. Installing packages in the app takes a few minutes...")
    info = _cloud(lambda: cloud.deploy(target, prof))
    _show_status(info)
    reg = info.get("registered") or {}
    if reg.get("error"):
        console.print(f"[yellow]Version record not written: {reg['error']}[/yellow]")
    else:
        console.print(f"Version {reg['name']} recorded in the experiment"
                      + (f", linked to {', '.join(reg['prompts'])}" if reg.get("prompts") else "")
                      + (f"; scorers registered: {', '.join(reg['scorers'])}" if reg.get("scorers") else ""))
    console.print(f"Running code {info['version']}. It stops itself after 30 idle minutes.\n\nChecking its permissions:")
    from drill import cloud_check

    found = _cloud(lambda: cloud_check.check(target, prof))
    _show_findings(found)
    if any(f.ok is False for f in found):
        raise typer.Exit(1)


@cloud_app.command("start")
def cloud_start_cmd(target: str = TARGET, profile: str = PROFILE) -> None:
    """Start the app again (it bills about 0.5 DBU an hour while running)."""
    from drill import cloud

    prof = _cloud(lambda: cloud.profile_for(target, profile))
    _show_status(_cloud(lambda: cloud.start(target, prof)))


@cloud_app.command("stop")
def cloud_stop_cmd(target: str = TARGET, profile: str = PROFILE) -> None:
    """Stop the app so it stops billing. Progress stays in Lakebase."""
    from drill import cloud

    prof = _cloud(lambda: cloud.profile_for(target, profile))
    _show_status(_cloud(lambda: cloud.stop(target, prof)))


@cloud_app.command("status")
def cloud_status_cmd(target: str = TARGET, profile: str = PROFILE) -> None:
    """Is the app running, and where."""
    from drill import cloud

    prof = _cloud(lambda: cloud.profile_for(target, profile))
    _show_status(_cloud(lambda: cloud.status(target, prof)))


@cloud_app.command("check")
def cloud_check_cmd(
    target: str = TARGET,
    profile: str = PROFILE,
    fix: bool = typer.Option(False, "--fix", help="Grant what is missing, where you hold MANAGE."),
    live: bool = typer.Option(True, "--live/--no-live", help="Also ask the running app whether its model, Lakebase and tracing work."),
) -> None:
    """Check every permission the app needs, for you before a deploy and for the app after. Exits 1 if any is missing."""
    from drill import cloud, cloud_check

    prof = _cloud(lambda: cloud.profile_for(target, profile))
    found = _cloud(lambda: cloud_check.check(target, prof, live=live))
    if fix and any(f.grant for f in found):
        for line in _cloud(lambda: cloud_check.fix(found, prof)):
            console.print(f"Granted {line}")
        found = _cloud(lambda: cloud_check.check(target, prof, live=live))
    _show_findings(found)
    if any(f.ok is False for f in found):
        raise typer.Exit(1)


def _show_findings(found) -> None:
    from rich.table import Table

    table = Table(show_header=True, header_style="bold", box=None, pad_edge=False)
    for col in ("", "Area", "Needed", "Found"):
        table.add_column(col)
    colour = {True: "green", False: "red", None: "yellow"}
    for f in found:
        table.add_row(f"[{colour[f.ok]}]{f.mark}[/]", f.area, f.need, f.detail)
    console.print(table)
    missing = [f for f in found if f.ok is False]
    for f in missing:
        console.print(f"[red]✗ {f.need}[/red]\n  fix: {f.fix}")
    waiting = [f for f in found if f.ok is None]
    console.print(f"\n{len(found) - len(missing) - len(waiting)} ok, {len(missing)} missing, {len(waiting)} not checked yet."
                  + (" Run with --fix to grant what you can." if any(f.grant for f in missing) else ""))


@cloud_app.command("port")
def cloud_port_cmd(
    target: str = TARGET,
    profile: str = PROFILE,
    catalog: str = typer.Option(None, "--catalog", help="A catalog your team owns: traces go in <catalog>.drill_traces, prompts in <catalog>.daily_drill."),
    model: str = typer.Option(None, "--model", help="The governed Unity Gateway model service, catalog.schema.service."),
    project: str = typer.Option("daily-drill", "--lakebase-project", help="The Lakebase project for progress (created if missing)."),
    experiment: str = typer.Option(None, "--experiment", help="MLflow experiment path (default /Shared/daily-drill)."),
    warehouse: str = typer.Option(None, "--warehouse", help="A serverless SQL warehouse id (default: find or create 'daily-drill')."),
    learner: list[str] = typer.Option([], "--learner", help="Email of someone who may use the app (repeat it)."),
    managers: str = typer.Option(None, "--managers", help="A group that may use the app and read the managers' dashboard."),
    do_apply: bool = typer.Option(False, "--apply", help="Create, grant, deploy and share. Without it, only the plan is shown."),
    no_deploy: bool = typer.Option(False, "--no-deploy", help="With --apply: set everything up but don't deploy yet."),
) -> None:
    """Move Daily Drill into a workspace: check everything, then (with --apply) create, grant, deploy and share."""
    from drill import cloud, port

    prof = _cloud(lambda: cloud.profile_for(target, profile))
    the_plan = _cloud(lambda: port.plan(target, prof, catalog=catalog, model=model, project=project,
                                       experiment=experiment, warehouse=warehouse))
    for step in the_plan.steps:
        line = f"{step.mark} {step.name}" + (f"  [dim]{step.detail}[/dim]" if step.detail else "")
        console.print(line)
        if step.state == "blocked" and step.todo:
            console.print(f"    [red]{step.todo}[/red]")
    if the_plan.blocked:
        console.print(f"\n[red]{len(the_plan.blocked)} blocked.[/red] Fix those, then run this again.")
        raise typer.Exit(1)
    if not do_apply:
        console.print("\nNothing changed. Run again with --apply to create, grant, deploy and share.")
        return
    done = _cloud(lambda: port.apply(the_plan, learners=learner, managers=managers, deploy=not no_deploy, say=console.print))
    for g in done.get("granted", []):
        console.print(f"  granted {g}")
    if done.get("app"):
        _show_status(done["app"])
    if done.get("dashboard"):
        console.print(f"Managers' dashboard: {done['dashboard']['url']}")
    for s in done.get("shared", []):
        console.print(f"  {s}")
    for m in done.get("missing", []):
        console.print(f"[red]  still missing: {m}[/red] (see uv run drill cloud check --target {target})")


@cloud_app.command("share")
def cloud_share_cmd(
    emails: list[str] = typer.Argument(None, help="Emails of people who may use the app."),
    target: str = TARGET,
    profile: str = PROFILE,
    managers: str = typer.Option(None, "--managers", help="A group that may also read the managers' dashboard and its catalog."),
) -> None:
    """Let people use the app (and a managers group read the dashboard)."""
    from drill import cloud, port

    prof = _cloud(lambda: cloud.profile_for(target, profile))
    for line in _cloud(lambda: port.share(target, prof, emails or [], managers)):
        console.print(line)


@cloud_app.command("manager-view")
def cloud_manager_view_cmd(
    target: str = TARGET,
    profile: str = PROFILE,
    warehouse: str = typer.Option(None, "--warehouse", help="A small serverless SQL warehouse id (default: the one saved for the target)."),
    catalog: str = typer.Option(None, "--catalog", help="Unity Catalog name for the app's Lakebase data (default daily_drill_lakebase)."),
) -> None:
    """The managers' dashboard: every learner's progress, where they are stuck, their questions and weekly notes."""
    from drill import cloud

    prof = _cloud(lambda: cloud.profile_for(target, profile))
    info = _cloud(lambda: cloud.manager_view(target, prof, warehouse, catalog))
    console.print(f"Dashboard: {info['url']}\nReads catalog {info['catalog']} with your credentials.")
    console.print("Share it with managers only: it shows every learner's progress, study list and questions.")


traces_app = typer.Typer(add_completion=False, help="The deployed app's traces: score them with the registered scorers.")
app.add_typer(traces_app, name="traces")


@traces_app.command("score")
def traces_score_cmd(
    target: str = TARGET,
    profile: str = PROFILE,
    days: float = typer.Option(1.0, "--days", help="Score traces from this many days back."),
) -> None:
    """Run the answer-rule scorers over the app's recent traces, as one evaluation run with pass rates."""
    import os

    import mlflow

    from drill import cloud, trace_scoring

    prof = _cloud(lambda: cloud.profile_for(target, profile))
    saved = cloud.read_overrides(target)
    if "experiment_id" not in saved:
        console.print(f"[red]Run `uv run drill cloud setup --target {target}` first.[/red]")
        raise typer.Exit(1)
    if saved.get("warehouse_id"):
        os.environ.setdefault("MLFLOW_TRACING_SQL_WAREHOUSE_ID", saved["warehouse_id"])
    mlflow.set_tracking_uri(f"databricks://{prof}" if prof else "databricks")
    result = trace_scoring.score(saved["experiment_id"], days)
    if not result["traces"]:
        console.print("No traces in that window.")
        return
    console.print(f"Scored {result['traces']} traces (run {result['run_id']}):")
    for name, value in sorted(result["metrics"].items()):
        console.print(f"  {name}: {value:.2f}" if isinstance(value, float) else f"  {name}: {value}")


@cloud_app.command("requirements")
def cloud_requirements_cmd() -> None:
    """Rewrite requirements.txt from uv.lock. Run it after changing dependencies, before deploying."""
    from drill import cloud

    path = _cloud(cloud.requirements)
    console.print(f"Wrote {path.relative_to(PROJECT_ROOT)}")

if __name__ == "__main__":
    app()
