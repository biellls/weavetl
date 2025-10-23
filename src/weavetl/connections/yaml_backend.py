"""YAML-based connection backend."""

from __future__ import annotations

from pathlib import Path
from typing import MutableMapping, Optional

import yaml

from .models import Connection, parse_connection
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

        connections_data = raw.get("connections", [])
        if not isinstance(connections_data, list):
            raise ValueError(
                f"Expected 'connections' list in {self._path}, got {type(connections_data)!r}"
            )

        parsed: dict[str, Connection] = {}
        for entry in connections_data:
            if not isinstance(entry, MutableMapping):
                raise ValueError(
                    f"Invalid connection entry in {self._path}: {entry!r}"
                )
            connection = parse_connection(entry)
            parsed[connection.id] = connection

        return parsed

    def get_connection(self, connection_id: str) -> Optional[Connection]:
        return self._load().get(connection_id)


__all__ = ["YAMLConnectionBackend"]
