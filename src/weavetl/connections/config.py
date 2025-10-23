"""Configuration helpers for connection backends."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .airflow_backend import AirflowConnectionBackend
from .resolution import ConnectionBackend, ConnectionResolver
from .yaml_backend import YAMLConnectionBackend


class ConnectionBackendConfig(BaseModel):
    """Configuration for a single connection backend."""

    model_config = ConfigDict(frozen=True)

    type: Literal["yaml", "airflow"]
    path: Optional[Path] = Field(default=None)

    @model_validator(mode="after")
    def _validate_requirements(self) -> "ConnectionBackendConfig":
        if self.type == "yaml":
            if self.path is None:
                msg = "YAML backends require a path"
                raise ValueError(msg)
        else:
            if self.path is not None:
                msg = "Only YAML backends accept a path"
                raise ValueError(msg)
        return self

    def resolved_path(self, project_dir: Path) -> Path:
        """Resolve the backend path relative to ``project_dir``."""

        if self.path is None:
            msg = "Backend does not define a path"
            raise ValueError(msg)
        if self.path.is_absolute():
            return self.path
        return project_dir / self.path

    def describe(self, project_dir: Path) -> str:
        """Return a human-friendly description of the backend."""

        if self.type == "yaml":
            return str(self.resolved_path(project_dir))
        return "airflow"


class ConnectionsProjectConfig(BaseModel):
    """Connections configuration stored in the project file."""

    model_config = ConfigDict(frozen=True)

    backends: List[ConnectionBackendConfig] = Field(default_factory=list)


@dataclass(frozen=True)
class ConfiguredBackend:
    """Runtime representation of a configured backend."""

    config: ConnectionBackendConfig
    backend: ConnectionBackend
    description: str


def configure_backends(
    config: ConnectionsProjectConfig, project_dir: Path
) -> List[ConfiguredBackend]:
    """Instantiate backends defined in the project configuration."""

    configured: List[ConfiguredBackend] = []
    for backend_config in config.backends:
        if backend_config.type == "yaml":
            path = backend_config.resolved_path(project_dir)
            backend = YAMLConnectionBackend(path)
            description = str(path)
        elif backend_config.type == "airflow":
            backend = AirflowConnectionBackend()
            description = "airflow"
        else:  # pragma: no cover - defensive future-proofing
            msg = f"Unsupported backend type: {backend_config.type}"
            raise ValueError(msg)

        configured.append(
            ConfiguredBackend(
                config=backend_config,
                backend=backend,
                description=description,
            )
        )

    return configured


def build_resolver(
    config: ConnectionsProjectConfig, project_dir: Path
) -> ConnectionResolver:
    """Create a :class:`ConnectionResolver` for the configured backends."""

    configured_backends = configure_backends(config, project_dir)
    return ConnectionResolver(backend.backend for backend in configured_backends)


__all__ = [
    "ConnectionBackendConfig",
    "ConnectionsProjectConfig",
    "ConfiguredBackend",
    "configure_backends",
    "build_resolver",
]
