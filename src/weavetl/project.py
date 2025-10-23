"""Utilities for working with WeaveTL project metadata."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from .connections.config import ConnectionsProjectConfig

PROJECT_FILENAME = "weavetl_project.yaml"
LEGACY_PROJECT_FILENAMES = ("weavetl_project.yml",)


class WeavetlProject(BaseModel):
    """Representation of a WeaveTL project configuration."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(..., min_length=1)
    path: Path
    """Directory containing the project configuration file."""
    connections: ConnectionsProjectConfig = Field(
        default_factory=ConnectionsProjectConfig
    )

    @field_validator("name")
    @classmethod
    def _validate_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Project name must be a non-empty string")
        return value


def project_file_path(directory: Optional[Path] = None) -> Path:
    """Return the expected project file path for ``directory``.

    Parameters
    ----------
    directory:
        The directory to use. When ``None`` (default) the current working
        directory is used.
    """

    base_dir = directory or Path.cwd()
    return base_dir / PROJECT_FILENAME


def find_project_file(directory: Optional[Path] = None) -> Optional[Path]:
    """Look for a project file in ``directory``.

    Parameters
    ----------
    directory:
        Directory where the search should start. Only the exact directory is
        inspected, as requested by the current CLI design. When ``None`` the
        current working directory is used.

    Returns
    -------
    Optional[Path]
        The path to the project file if it exists, otherwise ``None``.
    """

    candidate = project_file_path(directory)
    if candidate.exists():
        return candidate

    base_dir = directory or Path.cwd()
    for legacy_name in LEGACY_PROJECT_FILENAMES:
        legacy_candidate = base_dir / legacy_name
        if legacy_candidate.exists():
            return legacy_candidate
    return None


def init_project(directory: Optional[Path] = None, *, name: str, overwrite: bool = False) -> Path:
    """Create a new project configuration file.

    Parameters
    ----------
    directory:
        Directory where the project file should be created. Defaults to the
        current working directory.
    name:
        The project name to record.
    overwrite:
        Whether to overwrite an existing configuration file. When ``False`` and
        the file exists, :class:`FileExistsError` is raised.

    Returns
    -------
    Path
        The path to the created project file.
    """

    target = project_file_path(directory)
    if target.exists() and not overwrite:
        msg = f"A WeaveTL project already exists at {target}"
        raise FileExistsError(msg)

    data = {
        "name": name,
        "connections": {"backends": []},
    }
    with target.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh, sort_keys=False)

    return target


def load_project(directory: Optional[Path] = None) -> WeavetlProject:
    """Load project metadata from ``directory``.

    Parameters
    ----------
    directory:
        Directory containing the project file. Defaults to the current working
        directory.

    Returns
    -------
    WeavetlProject
        The parsed project configuration.

    Raises
    ------
    FileNotFoundError
        If the project file does not exist in ``directory``.
    ValueError
        If the project file is malformed or missing required keys.
    """

    project_path = find_project_file(directory)
    if project_path is None:
        raise FileNotFoundError(
            f"Unable to locate {PROJECT_FILENAME} in {directory or Path.cwd()}"
        )

    with project_path.open("r", encoding="utf-8") as fh:
        data: Any = yaml.safe_load(fh) or {}

    if not isinstance(data, dict):
        raise ValueError(f"Invalid project configuration format in {project_path}")

    project_dir = project_path.parent
    data_with_path = {**data, "path": project_dir}

    try:
        return WeavetlProject.model_validate(data_with_path)
    except ValidationError as exc:
        raise ValueError(
            f"Invalid project configuration in {project_path}: {exc}"
        ) from exc


__all__ = [
    "PROJECT_FILENAME",
    "WeavetlProject",
    "find_project_file",
    "init_project",
    "load_project",
    "project_file_path",
]
