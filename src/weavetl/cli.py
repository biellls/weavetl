"""Command line interface for the WeaveTL project."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from .project import PROJECT_FILENAME, init_project, load_project

app = typer.Typer(help="Tools for managing WeaveTL projects.")


@app.command()
def init(
    name: str = typer.Option(
        ..., prompt=True, help="Name of the WeaveTL project to initialize."
    ),
    directory: Optional[Path] = typer.Option(
        None,
        "--directory",
        "-d",
        help="Directory where the project should be initialized. Defaults to the current working directory.",
        dir_okay=True,
        file_okay=False,
        exists=False,
        writable=True,
        resolve_path=True,
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite/--no-overwrite",
        help="Allow overwriting an existing project configuration.",
    ),
) -> None:
    """Initialize a new WeaveTL project configuration file."""

    target_dir = directory or Path.cwd()
    try:
        project_path = init_project(target_dir, name=name, overwrite=overwrite)
    except FileExistsError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    typer.secho(f"Created {PROJECT_FILENAME} at {project_path}", fg=typer.colors.GREEN)


@app.command()
def info(
    directory: Optional[Path] = typer.Option(
        None,
        "--directory",
        "-d",
        help="Directory to inspect for a WeaveTL project.",
        dir_okay=True,
        file_okay=False,
        exists=False,
        resolve_path=True,
    )
) -> None:
    """Display information about the current WeaveTL project."""

    target_dir = directory or Path.cwd()
    try:
        project = load_project(target_dir)
    except FileNotFoundError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc
    except ValueError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Project name: {project.name}")
    typer.echo(f"Project directory: {project.path}")
    typer.echo(f"Project file: {project.path / PROJECT_FILENAME}")


def main() -> None:
    """Entry point for running the CLI via ``python -m weavetl.cli``."""

    app()


if __name__ == "__main__":
    main()
