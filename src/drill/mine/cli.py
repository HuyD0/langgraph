"""`drill mine`: practice problems run against your own money and health data.

    uv run drill mine list
    uv run drill mine new spending_by_category          # writes practice/spending_by_category.py
    uv run drill mine check practice/spending_by_category.py -p spending_by_category
    uv run drill mine solution spending_by_category

`check` first runs the small test cases. If those pass, it runs your function on
your real data (read-only, on this Mac) and shows you the answer.
"""

from __future__ import annotations

import copy
import dataclasses
import json
from pathlib import Path

import typer
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from drill.config import PROJECT_ROOT, DrillSettings
from drill.mine import data
from drill.mine.learn import LEARN
from drill.mine.problems import MINE_PROBLEMS, REAL_WORLD, get_mine_problem
from drill.problems import TestCase
from drill.sandbox import run_submission

mine_app = typer.Typer(
    add_completion=False,
    help="Practice on your own money and health data (read-only, stays on this Mac).",
)


def _console():
    # Imported here, not at the top: drill.cli imports this module to register it.
    from drill.cli import console
    return console


def _reference_answer(problem, args):
    namespace: dict = {}
    exec(compile(problem.reference_solution, "<reference>", "exec"), namespace)
    answer = namespace[problem.function_name](*copy.deepcopy(args))
    return json.loads(json.dumps(answer))  # same shape the sandbox reports back


def _money(cents: int) -> str:
    return f"${-cents / 100:,.2f}" if cents < 0 else f"+${cents / 100:,.2f}"


def _present(problem_id: str, args, answer) -> None:
    """Show an answer about your data in a readable way."""
    console = _console()
    if problem_id == "unusual_charges" and isinstance(answer, list):
        txns = args[0]
        table = Table(box=None, padding=(0, 2))
        for col in ("date", "merchant", "amount"):
            table.add_column(col)
        for i in answer:
            if isinstance(i, int) and 0 <= i < len(txns):
                t = txns[i]
                table.add_row(t["date"], str(t["merchant"]), _money(t["amount_cents"]))
        console.print(table if answer else "[dim]Nothing flagged.[/dim]")
    elif isinstance(answer, dict):
        table = Table(box=None, padding=(0, 2))
        table.add_column("")
        table.add_column("", justify="right")
        items = list(answer.items())
        if all(isinstance(v, (int, float)) for _, v in items) and problem_id != "monthly_low_weight":
            items.sort(key=lambda kv: -kv[1])
        for k, v in items[:40]:
            table.add_row(str(k), str(v))
        console.print(table)
        if len(items) > 40:
            console.print(f"[dim]...and {len(items) - 40} more[/dim]")
    elif isinstance(answer, list):
        for line in answer[:40]:
            console.print(f"  {line}")
    else:
        console.print(f"  [bold]{answer}[/bold]")


@mine_app.command("list")
def list_cmd() -> None:
    """Show the money & health problems."""
    table = Table(header_style="bold")
    for col in ("id", "title", "topic", "difficulty"):
        table.add_column(col)
    for p in MINE_PROBLEMS:
        table.add_row(p.id, p.title, p.topic, p.difficulty)
    _console().print(table)


@mine_app.command("new")
def new_cmd(
    problem: str = typer.Argument(..., help="Problem id."),
    guided: bool = typer.Option(False, "--guided", help="Start from step-by-step comments with blanks."),
) -> None:
    """Show a problem and write a starter file to practice/<id>.py."""
    from drill.cli import show_problem

    prob = get_mine_problem(problem)
    show_problem(prob)
    console = _console()
    console.print(Panel(REAL_WORLD[prob.id], title="where this shows up", border_style="dim"))
    path = PROJECT_ROOT / "practice" / f"{prob.id}.py"
    if path.exists():
        console.print(f"[dim]{path.relative_to(PROJECT_ROOT)} already exists, so it was left alone.[/dim]")
    else:
        path.parent.mkdir(exist_ok=True)
        path.write_text(LEARN[prob.id]["guided"] if guided else prob.starter_code, encoding="utf-8")
        console.print(f"Wrote [bold]{path.relative_to(PROJECT_ROOT)}[/bold].")
    console.print(f"When you're ready: [bold]uv run drill mine check practice/{prob.id}.py -p {prob.id}[/bold]")


@mine_app.command("check")
def check_cmd(
    solution: Path = typer.Argument(..., help="Python file containing your solution."),
    problem: str = typer.Option(..., "--problem", "-p", help="Which problem it answers."),
) -> None:
    """Run the test cases, then run your function on your real data."""
    from drill.cli import show_result

    console = _console()
    prob = get_mine_problem(problem)
    source = solution.read_text(encoding="utf-8")
    timeout = DrillSettings.from_env().sandbox_timeout

    result = run_submission(prob, source, timeout=timeout)
    show_result(result)  # type: ignore[arg-type]
    if not result["passed"]:
        console.print("[dim]Get the test cases passing first, then it runs on your real data.[/dim]")
        raise typer.Exit(1)

    try:
        conn = data.connect()
    except FileNotFoundError as e:
        console.print(f"[yellow]{e}[/yellow]")
        raise typer.Exit(1)
    with conn:
        args, label = data.load(prob.id, conn)

    expected = _reference_answer(prob, args)
    real = dataclasses.replace(prob, test_cases=(TestCase(args=tuple(args), expected=expected),))
    outcome = run_submission(real, source, timeout=max(timeout, 30))
    console.print(f"\n[bold]On your real data[/bold] [dim]({label})[/dim]")
    if outcome.get("fatal_error") or not outcome["cases"]:
        console.print(Panel((outcome.get("fatal_error") or "did not finish").strip(),
                            title="[red]did not run[/red]", border_style="red"))
        raise typer.Exit(1)

    case = outcome["cases"][0]
    if case["error"]:
        console.print(Panel(case["error"].strip().splitlines()[-1], title="[red]crashed on your data[/red]",
                            border_style="red"))
        console.print("[dim]Real data has things the tests don't, like missing merchants or "
                      "uncategorized rows. Look for a value your code didn't expect.[/dim]")
        raise typer.Exit(1)

    _present(prob.id, args, case["actual"])
    if case["passed"]:
        console.print("[green]Matches the reference answer on your data.[/green]")
        raise typer.Exit(0)
    console.print("\n[yellow]The reference solution gets a different answer on your data:[/yellow]")
    _present(prob.id, args, expected)
    console.print("[dim]Real data has things the tests don't. Compare the two to find the case "
                  "your code handles differently.[/dim]")
    raise typer.Exit(1)


@mine_app.command("solution")
def solution_cmd(problem: str = typer.Argument(..., help="Problem id.")) -> None:
    """Print the reference solution. Use it after you've genuinely tried."""
    prob = get_mine_problem(problem)
    console = _console()
    console.print(Panel(f"[bold]{prob.pattern}[/bold]\n[dim]Goal: {prob.target_complexity}[/dim]",
                        border_style="dim"))
    console.print(Syntax(prob.reference_solution, "python", theme="ansi_dark"))
