"""Connection models and backends for WeaveTL."""

from .config import (
    ConfiguredBackend,
    ConnectionBackendConfig,
    ConnectionsProjectConfig,
    build_resolver,
    configure_backends,
)
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
    "ConnectionBackendConfig",
    "ConnectionResolver",
    "ConnectionsProjectConfig",
    "ConfiguredBackend",
    "Endpoint",
    "OAuth2Auth",
    "OAuth2Flow",
    "TokenAuth",
    "TokenPlacement",
    "YAMLConnectionBackend",
    "AirflowConnectionBackend",
    "build_resolver",
    "configure_backends",
]
