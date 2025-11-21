"""Command line interface for the WeaveTL project."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from .connections import Connection
from .connections.config import configure_backends
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


@app.command()
def connections(
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
    """Show basic information about project connections."""

    target_dir = directory or Path.cwd()
    try:
        project = load_project(target_dir)
    except (FileNotFoundError, ValueError) as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    try:
        configured_backends = configure_backends(project.connections, project.path)
    except (RuntimeError, ValueError) as exc:
        typer.secho(f"Failed to configure connection backends: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    if not configured_backends:
        typer.echo("No connection backends are configured for this project.")
        return

    resolved: dict[str, tuple[Connection, str]] = {}
    shadowed: dict[str, list[str]] = {}
    skipped_backends: list[str] = []

    for configured in configured_backends:
        backend = configured.backend
        description = configured.description
        try:
            connections_iter = list(backend.iter_connections())
        except NotImplementedError:
            skipped_backends.append(description)
            continue
        except Exception as exc:  # pragma: no cover - defensive logging
            typer.secho(
                f"Failed to load connections from {description}: {exc}",
                fg=typer.colors.RED,
            )
            continue

        for connection in connections_iter:
            if connection.id in resolved:
                shadowed.setdefault(connection.id, []).append(description)
                continue
            resolved[connection.id] = (connection, description)

    if not resolved:
        typer.echo("No connections are currently available from the configured backends.")
    else:
        typer.echo("Connections (higher-precedence backends listed first):")

        headers = ("ID", "Type", "Endpoint", "Auth", "Source")
        table_rows: list[tuple[str, str, str, str, str]] = []
        for connection, origin in resolved.values():
            endpoint = (
                str(connection.endpoint.baseUrl)
                if connection.endpoint and connection.endpoint.baseUrl
                else "-"
            )
            auth_kind = "-"
            if connection.auth is not None:
                auth_kind = getattr(connection.auth, "kind", connection.auth.__class__.__name__)
            table_rows.append(
                (
                    connection.id,
                    connection.type,
                    endpoint,
                    auth_kind,
                    origin,
                )
            )

        column_widths = [len(header) for header in headers]
        for row in table_rows:
            for index, cell in enumerate(row):
                column_widths[index] = max(column_widths[index], len(cell))

        def format_row(row: tuple[str, ...]) -> str:
            return " | ".join(cell.ljust(column_widths[idx]) for idx, cell in enumerate(row))

        header_line = format_row(headers)
        separator_line = "-+-".join("-" * width for width in column_widths)
        typer.echo(header_line)
        typer.echo(separator_line)
        for row in table_rows:
            typer.echo(format_row(row))

    if shadowed:
        typer.echo()
        typer.echo("Shadowed connections (overridden by higher-precedence backends):")
        for connection_id, sources in shadowed.items():
            for source in sources:
                typer.echo(f"  {connection_id} from {source}")

    if skipped_backends:
        typer.echo()
        typer.echo("Backends that do not support listing connections:")
        for description in skipped_backends:
            typer.echo(f"  {description}")


def main() -> None:
    """Entry point for running the CLI via ``python -m weavetl.cli``."""

    app()


if __name__ == "__main__":
    main()
