"""Utilities for resolving connections from multiple backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Optional

from .models import Connection


class ConnectionBackend(ABC):
    """Abstract base class for connection backends."""

    @abstractmethod
    def get_connection(self, connection_id: str) -> Optional[Connection]:
        """Return a connection for ``connection_id`` if present."""

    def iter_connections(self) -> Iterable[Connection]:
        """Iterate over all connections known to the backend.

        Backends may override this method to support bulk inspection. The default
        implementation raises :class:`NotImplementedError` to signal that the
        backend does not support enumeration.
        """

        raise NotImplementedError


class ConnectionResolver:
    """Resolve connections from multiple backends based on precedence."""

    def __init__(self, backends: Iterable[ConnectionBackend]):
        self._backends = list(backends)

    def resolve(self, connection_id: str) -> Connection:
        """Resolve ``connection_id`` from the configured backends."""

        for backend in self._backends:
            connection = backend.get_connection(connection_id)
            if connection is not None:
                return connection
        msg = f"Connection '{connection_id}' not found in any backend"
        raise LookupError(msg)


__all__ = ["ConnectionBackend", "ConnectionResolver"]
