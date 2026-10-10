"""The terminal you actually practise in.

    uv run drill start                 # weakest topic picks the problem
    uv run drill start --problem two_sum
    uv run drill start --topic sliding-window
    uv run drill list
    uv run drill stats
    uv run drill check <file.py> --problem two_sum   # just run the tests, no tutor
    uv run drill mine list                           # problems on your own money & health data
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
from drill.problems import ALL_PROBLEMS, TOPICS, Problem, get_problem, list_problems
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
        pass


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
        subprocess.run([*editor.split(), str(path)], check=False)
        return path.read_text(encoding="utf-8")


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
            problem.id, problem.title, problem.topic, problem.difficulty, problem.pattern,
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
    solution: Path = typer.Argument(..., help="Python file containing your solution."),
    problem: str = typer.Option(..., "--problem", "-p", help="Which problem it answers."),
) -> None:
    """Run the tests against a file, with no tutor and no LLM call.

    Useful when you want the grader but not the conversation - and it works with
    no Azure credentials configured at all.
    """
    prob = get_problem(problem)
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
    prob = get_problem(problem)
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

    outcome = run_session(
        build_drill_graph(), deps, edit_submission,
        problem_id=problem, topic=topic, on_event=on_event,
    )

    verb = "Solved" if outcome.solved else "Not solved"
    console.print(f"\n{verb} [bold]{outcome.problem.title}[/bold] in {outcome.attempts} "
                  f"attempt(s) with {len(outcome.hints)} hint(s).")
    raise typer.Exit(0)


# Problems about your own money and health data: `drill mine --help`.
from drill.mine.cli import mine_app  # noqa: E402

app.add_typer(mine_app, name="mine")


if __name__ == "__main__":
    app()
