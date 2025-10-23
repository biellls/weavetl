"""Pydantic models that describe canonical connection objects."""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Literal, Optional, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    ValidationError,
    field_validator,
    model_validator,
)


class OAuth2Flow(str, Enum):
    """Supported OAuth 2.0 flows."""

    CLIENT_CREDENTIALS = "client_credentials"
    AUTHORIZATION_CODE = "authorization_code"
    DEVICE_CODE = "device_code"


class Endpoint(BaseModel):
    """Definition of an HTTPS endpoint."""

    baseUrl: HttpUrl = Field(..., alias="baseUrl")

    model_config = ConfigDict(populate_by_name=True, frozen=True)

    @field_validator("baseUrl")
    @classmethod
    def _ensure_https(cls, value: HttpUrl) -> HttpUrl:
        if value.scheme != "https":
            msg = "Endpoints must use an HTTPS baseUrl"
            raise ValueError(msg)
        return value


class BasicAuth(BaseModel):
    """Basic authentication credentials."""

    kind: Literal["basic"]
    username: str
    password: str

    model_config = ConfigDict(frozen=True)


class TokenPlacement(str, Enum):
    """Supported token placements."""

    HEADER = "header"
    QUERY = "query"
    COOKIE = "cookie"


class TokenAuth(BaseModel):
    """Token-based authentication."""

    kind: Literal["token"]
    token: str
    placement: TokenPlacement = TokenPlacement.HEADER
    name: Optional[str] = None
    prefix: Optional[str] = None

    model_config = ConfigDict(frozen=True)

    @model_validator(mode="after")
    def _assign_defaults(self) -> "TokenAuth":
        if self.name:
            return self

        defaults = {
            TokenPlacement.HEADER: "Authorization",
            TokenPlacement.QUERY: "api_key",
            TokenPlacement.COOKIE: "auth_token",
        }
        object.__setattr__(self, "name", defaults[self.placement])
        return self


class OAuth2Auth(BaseModel):
    """OAuth2 authentication configuration."""

    kind: Literal["oauth2"]
    flow: OAuth2Flow
    tokenEndpoint: HttpUrl
    clientId: str
    clientSecret: Optional[str] = None
    scopes: Optional[List[str]] = None
    audience: Optional[str] = None
    refreshToken: Optional[str] = None
    redirectUri: Optional[HttpUrl] = None
    options: Optional[Dict[str, Union[str, int, float, bool]]] = None

    model_config = ConfigDict(populate_by_name=True, frozen=True)

    @model_validator(mode="after")
    def _validate_client_secret(self) -> "OAuth2Auth":
        if self.flow == OAuth2Flow.CLIENT_CREDENTIALS and not self.clientSecret:
            msg = "clientSecret is required for client_credentials flow"
            raise ValueError(msg)
        if self.flow == OAuth2Flow.AUTHORIZATION_CODE:
            if not self.redirectUri:
                msg = "redirectUri is required for authorization_code flow"
                raise ValueError(msg)
            if not self.refreshToken:
                msg = "refreshToken is required for authorization_code flow"
                raise ValueError(msg)
        return self


AuthConfig = Union[BasicAuth, TokenAuth, OAuth2Auth]


class ConnectionOptions(BaseModel):
    """Optional connection settings."""

    headers: Optional[Dict[str, str]] = None
    timeoutSeconds: Optional[float] = Field(default=30, ge=0)
    retries: Optional[int] = Field(default=3, ge=0)
    verifyTLS: Optional[Union[bool, str]] = Field(default=True)

    model_config = ConfigDict(populate_by_name=True, frozen=True)


class Connection(BaseModel):
    """Canonical connection representation."""

    id: str
    type: str
    endpoint: Optional[Endpoint] = None
    auth: Optional[AuthConfig] = None
    labels: Optional[List[str]] = None
    metadata: Optional[Dict[str, Union[str, int, float, bool]]] = None
    options: ConnectionOptions = Field(default_factory=ConnectionOptions)

    model_config = ConfigDict(populate_by_name=True, frozen=True)

    @field_validator("id")
    @classmethod
    def _validate_id(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("id must be a non-empty string")
        return value

    @model_validator(mode="after")
    def _validate_http_requirements(self) -> "Connection":
        if self.type == "http":
            if self.endpoint is None:
                raise ValueError("HTTP connections require an endpoint")
            if self.auth is None:
                raise ValueError("HTTP connections require an auth configuration")
        # Additional connection types can extend validation here in the future.
        return self


def parse_connection(data: Dict[str, object]) -> Connection:
    """Parse a connection dictionary and return a :class:`Connection` instance."""

    try:
        return Connection.model_validate(data)
    except ValidationError as exc:
        msg = "Invalid connection configuration"
        raise ValueError(msg) from exc


class ConnectionsDocument(BaseModel):
    """Top-level YAML document that contains connection definitions."""

    connections: List[Connection] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)


def parse_connections_document(data: Dict[str, object]) -> "ConnectionsDocument":
    """Parse a YAML connections document."""

    try:
        return ConnectionsDocument.model_validate(data)
    except ValidationError as exc:
        msg = "Invalid connections document"
        raise ValueError(msg) from exc


__all__ = [
    "AuthConfig",
    "BasicAuth",
    "Connection",
    "ConnectionsDocument",
    "ConnectionOptions",
    "Endpoint",
    "OAuth2Auth",
    "OAuth2Flow",
    "TokenAuth",
    "TokenPlacement",
    "parse_connection",
    "parse_connections_document",
]
