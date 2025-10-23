"""YAML-based connection backend."""

from __future__ import annotations

from pathlib import Path
from typing import MutableMapping, Optional

import yaml

from .models import Connection, parse_connections_document
from .resolution import ConnectionBackend


class YAMLConnectionBackend(ConnectionBackend):
    """Read connections from a YAML file."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def _load(self) -> dict[str, Connection]:
        if not self._path.exists():
            return {}

        with self._path.open("r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh) or {}

        if not isinstance(raw, MutableMapping):
            raise ValueError(f"Invalid YAML format in {self._path}")

        document = parse_connections_document(raw)
        return {connection.id: connection for connection in document.connections}

    def get_connection(self, connection_id: str) -> Optional[Connection]:
        return self._load().get(connection_id)


__all__ = ["YAMLConnectionBackend"]
