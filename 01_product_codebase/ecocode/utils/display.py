"""
display.py — Rich terminal output formatting for EcoCode-LLM.

Provides functions for rendering beautiful comparison tables,
syntax-highlighted code, progress indicators, and result summaries.
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text
from rich import box

# Force utf-8 safe console printing
console = Console(legacy_windows=False)


def print_banner():
    """Print the EcoCode-LLM startup banner."""
    banner = Text()
    banner.append("[EcoCode-LLM]", style="bold green")
    banner.append(" — A Green AI Framework for Energy-Efficient Code Generation", style="dim")
    console.print(Panel(banner, border_style="green", padding=(1, 2)))


def print_mode_header(mode: int, description: str):
    """Print a mode header panel."""
    mode_text = f"Mode {mode}: {description}"
    console.print(Panel(mode_text, title="[bold cyan]Active Mode[/]", border_style="cyan"))


def print_candidates_table(candidates: list):
    """
    Print a comparison table of all profiled candidates.

    Args:
        candidates: List of CodeCandidate objects with profile data.
    """
    table = Table(
        title="Candidate Comparison",
        box=box.ROUNDED,
        title_style="bold magenta",
        header_style="bold cyan",
        show_lines=True,
    )

    table.add_column("Candidate", justify="center", style="white", width=12)
    table.add_column("Time (ms)", justify="right", style="yellow")
    table.add_column("Memory (KB)", justify="right", style="blue")
    table.add_column("Energy (J)", justify="right", style="red")
    table.add_column("TOPSIS Score", justify="right", style="green")
    table.add_column("Status", justify="center")

    # Find the winner (lowest score)
    winner_id = None
    if candidates:
        scored = [c for c in candidates if c.topsis_score is not None]
        if scored:
            winner_id = min(scored, key=lambda c: c.topsis_score).id

    for c in candidates:
        # Format the status column
        if not c.is_valid:
            status = "[FAILED]"
            row_style = "dim"
        elif c.id == winner_id:
            status = "[WINNER]"
            row_style = "bold green"
        else:
            status = "[VALID]"
            row_style = ""

        # Format metric values
        if c.profile:
            time_str = f"{c.profile.execution_time_ms:.1f}"
            mem_str = f"{c.profile.peak_memory_kb:.0f}"
            energy_str = f"{c.profile.energy_joules:.4f}"
        else:
            time_str = "-"
            mem_str = "-"
            energy_str = "-"

        score_str = f"{c.topsis_score:.4f}" if c.topsis_score is not None else "-"

        table.add_row(c.id, time_str, mem_str, energy_str, score_str, status, style=row_style)

    console.print(table)


def print_code_block(code: str, title: str = "Code", language: str = "python"):
    """
    Print syntax-highlighted code in a panel.

    Args:
        code: The source code string.
        title: Panel title.
        language: Syntax highlighting language.
    """
    syntax = Syntax(code, language, theme="monokai", line_numbers=True, padding=1)
    console.print(Panel(syntax, title=f"[bold yellow]{title}[/]", border_style="yellow"))


def print_improvement_summary(improvements: dict):
    """
    Print improvement percentages after optimization.

    Args:
        improvements: Dict with keys 'time', 'memory', 'energy' and percentage values.
    """
    table = Table(
        title="Improvement Summary",
        box=box.SIMPLE_HEAVY,
        title_style="bold green",
        header_style="bold",
    )

    table.add_column("Metric", style="cyan")
    table.add_column("Change", justify="right")

    for metric, pct in improvements.items():
        if pct < 0:
            style = "green"
            arrow = "v"
        elif pct > 0:
            style = "red"
            arrow = "^"
        else:
            style = "white"
            arrow = "->"

        table.add_row(metric.capitalize(), f"{arrow} {abs(pct):.1f}%", style=style)

    console.print(table)


def print_success(message: str):
    """Print a success message."""
    console.print(f"[bold green][SUCCESS] {message}[/]")


def print_error(message: str):
    """Print an error message."""
    console.print(f"[bold red][ERROR] {message}[/]")


def print_warning(message: str):
    """Print a warning message."""
    console.print(f"[bold yellow][WARNING] {message}[/]")


def print_info(message: str):
    """Print an informational message."""
    console.print(f"[bold blue][INFO] {message}[/]")
