"""Airflow-backed connection loader."""

from __future__ import annotations

from typing import Optional

from .models import (
    BasicAuth,
    Connection,
    Endpoint,
    OAuth2Auth,
    OAuth2Flow,
    TokenAuth,
    TokenPlacement,
)
from .resolution import ConnectionBackend


class AirflowConnectionBackend(ConnectionBackend):
    """Resolve connections using Airflow's connection metadata."""

    def __init__(self) -> None:
        try:
            from airflow.exceptions import AirflowNotFoundException
            from airflow.models.connection import Connection as AirflowConnection
        except ImportError as exc:  # pragma: no cover - optional dependency
            msg = "Airflow is not installed. Install apache-airflow to use this backend."
            raise RuntimeError(msg) from exc

        self._airflow_connection_cls = AirflowConnection
        self._not_found_exc = AirflowNotFoundException

    def _build_base_url(self, airflow_conn) -> str:
        schema = airflow_conn.schema or "https"
        host = airflow_conn.host or ""
        port = f":{airflow_conn.port}" if airflow_conn.port else ""
        if not host:
            msg = f"Airflow connection '{airflow_conn.conn_id}' is missing a host"
            raise ValueError(msg)
        base_url = f"{schema}://{host}{port}"
        return base_url

    def _build_token_auth(self, extra: dict) -> Optional[TokenAuth]:
        bearer_token = extra.get("bearer_token")
        if bearer_token:
            prefix = extra.get("bearer_token_prefix", "Bearer")
            header_name = extra.get("api_key_header", "Authorization")
            return TokenAuth(
                kind="token",
                token=bearer_token,
                placement=TokenPlacement.HEADER,
                name=header_name,
                prefix=prefix,
            )

        api_key = extra.get("api_key")
        if api_key:
            placement = TokenPlacement(extra.get("placement", "header"))
            if placement is TokenPlacement.HEADER:
                name = extra.get("api_key_header") or "Authorization"
            elif placement is TokenPlacement.QUERY:
                name = extra.get("api_key_query_arg") or "api_key"
            else:
                name = extra.get("api_key_cookie_name") or "auth_token"
            prefix = extra.get("api_key_prefix")
            return TokenAuth(
                kind="token",
                token=api_key,
                placement=placement,
                name=name,
                prefix=prefix,
            )
        return None

    def _build_oauth2(self, extra: dict) -> Optional[OAuth2Auth]:
        token_endpoint = extra.get("token_endpoint")
        client_id = extra.get("client_id")
        if not (token_endpoint and client_id):
            return None

        flow_value = extra.get("oauth_flow", "client_credentials")
        flow = OAuth2Flow(flow_value)
        client_secret = extra.get("client_secret")
        scopes = extra.get("scopes")
        audience = extra.get("audience")
        refresh_token = extra.get("refresh_token")
        redirect_uri = extra.get("redirect_uri")

        return OAuth2Auth(
            kind="oauth2",
            flow=flow,
            tokenEndpoint=token_endpoint,
            clientId=client_id,
            clientSecret=client_secret,
            scopes=scopes,
            audience=audience,
            refreshToken=refresh_token,
            redirectUri=redirect_uri,
        )

    def _build_basic(self, airflow_conn) -> Optional[BasicAuth]:
        if airflow_conn.login and airflow_conn.password:
            return BasicAuth(kind="basic", username=airflow_conn.login, password=airflow_conn.password)
        return None

    def _from_airflow(self, airflow_conn) -> Connection:
        if airflow_conn.conn_type != "http":
            raise ValueError(
                f"Unsupported Airflow connection type '{airflow_conn.conn_type}' for {airflow_conn.conn_id}"
            )

        base_url = self._build_base_url(airflow_conn)
        endpoint = Endpoint(baseUrl=base_url)

        extra = airflow_conn.extra_dejson or {}
        auth = self._build_token_auth(extra)
        if auth is None:
            auth = self._build_oauth2(extra)
        if auth is None:
            auth = self._build_basic(airflow_conn)
        if auth is None:
            msg = f"Unable to infer auth configuration for Airflow connection '{airflow_conn.conn_id}'"
            raise ValueError(msg)

        return Connection(
            id=airflow_conn.conn_id,
            type="http",
            endpoint=endpoint,
            auth=auth,
        )

    def get_connection(self, connection_id: str) -> Optional[Connection]:
        try:
            airflow_conn = self._airflow_connection_cls.get_connection_from_secrets(connection_id)
        except self._not_found_exc:
            return None

        return self._from_airflow(airflow_conn)


__all__ = ["AirflowConnectionBackend"]
