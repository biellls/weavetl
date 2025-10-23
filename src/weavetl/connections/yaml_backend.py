"""YAML-based connection backend."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, Mapping, MutableMapping, Optional

import yaml

from .models import Connection, parse_connection
from .resolution import ConnectionBackend

_ENV_PATTERN = re.compile(r"\$\{([^}]+)\}")


def _substitute_env(value: object, env: Mapping[str, str], *, strict: bool) -> object:
    """Recursively substitute ``${VAR}`` placeholders in ``value``."""

    if isinstance(value, str):
        def _replace(match: re.Match[str]) -> str:
            key = match.group(1)
            if key not in env:
                if strict:
                    msg = f"Environment variable '{key}' is not defined"
                    raise KeyError(msg)
                return match.group(0)
            return env[key]

        return _ENV_PATTERN.sub(_replace, value)
    if isinstance(value, list):
        return [_substitute_env(item, env, strict=strict) for item in value]
    if isinstance(value, dict):
        return {
            key: _substitute_env(item, env, strict=strict)
            for key, item in value.items()
        }
    return value


class YAMLConnectionBackend(ConnectionBackend):
    """Read connections from a YAML file."""

    def __init__(
        self,
        path: Path,
        *,
        env: Optional[Mapping[str, str]] = None,
        strict_env: bool = True,
    ) -> None:
        self._path = path
        self._env = dict(env) if env is not None else dict(os.environ)
        self._strict_env = strict_env
        self._cache_mtime: Optional[float] = None
        self._cache: Dict[str, Connection] = {}

    def _load(self) -> None:
        if not self._path.exists():
            self._cache = {}
            self._cache_mtime = None
            return

        mtime = self._path.stat().st_mtime
        if self._cache_mtime is not None and mtime == self._cache_mtime:
            return

        with self._path.open("r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh) or {}

        if not isinstance(raw, MutableMapping):
            raise ValueError(f"Invalid YAML format in {self._path}")

        connections_data = raw.get("connections", [])
        if not isinstance(connections_data, list):
            raise ValueError(
                f"Expected 'connections' list in {self._path}, got {type(connections_data)!r}"
            )

        parsed: Dict[str, Connection] = {}
        for entry in connections_data:
            if not isinstance(entry, MutableMapping):
                raise ValueError(
                    f"Invalid connection entry in {self._path}: {entry!r}"
                )
            substituted = _substitute_env(entry, self._env, strict=self._strict_env)
            connection = parse_connection(substituted)
            parsed[connection.id] = connection

        self._cache = parsed
        self._cache_mtime = mtime

    def get_connection(self, connection_id: str) -> Optional[Connection]:
        self._load()
        return self._cache.get(connection_id)


__all__ = ["YAMLConnectionBackend"]
