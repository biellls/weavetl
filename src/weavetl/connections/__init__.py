"""Connection models and backends for WeaveTL."""

from .models import (
    BasicAuth,
    Connection,
    Endpoint,
    OAuth2Auth,
    OAuth2Flow,
    TokenAuth,
    TokenPlacement,
)
from .resolution import ConnectionBackend, ConnectionResolver
from .yaml_backend import YAMLConnectionBackend
from .airflow_backend import AirflowConnectionBackend

__all__ = [
    "BasicAuth",
    "Connection",
    "ConnectionBackend",
    "ConnectionResolver",
    "Endpoint",
    "OAuth2Auth",
    "OAuth2Flow",
    "TokenAuth",
    "TokenPlacement",
    "YAMLConnectionBackend",
    "AirflowConnectionBackend",
]
